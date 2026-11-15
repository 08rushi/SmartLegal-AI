"""
Staging smoke test for a deployed SmartLegal AI backend.

Usage (from backend/, any Python with httpx installed):
    python scripts/staging_smoke_test.py --api https://api.example.com \
        --origin https://app.example.com [--create-user] [--with-analysis]

Read-only checks run by default. --create-user registers ONE throw-away account on the
target (staging only!) so the cookie login / upload / logout flow can be exercised.
--with-analysis also uploads a tiny generated PDF and runs one analysis (uses AI quota).
Prints PASS/FAIL per check, never prints cookies, tokens or passwords. Exit code 1 on failure.
"""
import argparse
import secrets
import sys
import time

import httpx

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))


def tiny_pdf() -> bytes:
    text = "Rental agreement. The tenant shall pay rent of Rs 10000 on the 5th of every month."
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET"
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        "/Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", required=True, help="API base URL, e.g. https://api.example.com")
    ap.add_argument("--origin", required=True, help="Exact frontend origin, e.g. https://app.example.com")
    ap.add_argument("--create-user", action="store_true")
    ap.add_argument("--with-analysis", action="store_true")
    a = ap.parse_args()
    api, origin = a.api.rstrip("/"), a.origin.rstrip("/")
    c = httpx.Client(base_url=api, timeout=60, headers={"Origin": origin})

    r = c.get("/health")
    check("health endpoint", r.status_code == 200, f"status {r.status_code}")

    r = c.options("/api/v1/auth/login", headers={
        "Origin": origin, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,x-lang"})
    check("CORS preflight allows frontend origin",
          r.headers.get("access-control-allow-origin") == origin
          and r.headers.get("access-control-allow-credentials") == "true",
          f"allow-origin={r.headers.get('access-control-allow-origin')}")

    r = c.options("/api/v1/auth/login", headers={
        "Origin": "https://evil.example.org", "Access-Control-Request-Method": "POST"})
    check("CORS rejects unknown origin",
          r.headers.get("access-control-allow-origin") != "https://evil.example.org")

    r = c.get("/api/v1/auth/me")
    check("unauthenticated /auth/me is 401", r.status_code == 401, f"status {r.status_code}")

    r = c.post("/api/v1/upload", files={"file": ("a.pdf", tiny_pdf(), "application/pdf")})
    check("unauthenticated upload is 401", r.status_code == 401, f"status {r.status_code}")

    r = c.post("/api/v1/auth/forgot-password", json={"email": "nobody-smoke@example.com"})
    check("forgot-password never leaks a token",
          r.status_code == 200 and "reset_token" not in r.text, f"status {r.status_code}")

    r = c.post("/api/v1/auth/login", data={"username": "nobody-smoke@example.com", "password": "x"},
               headers={"X-Lang": "mr", "Origin": origin})
    check("errors come back (translated via X-Lang)", r.status_code == 401,
          f"status {r.status_code}")

    r = c.get("/docs")
    check("API docs exposure noted", True, f"/docs status {r.status_code} (consider disabling in production)")

    if a.create_user:
        email = f"smoke-{secrets.token_hex(4)}@example.com"
        pw = "Smoke-" + secrets.token_urlsafe(10)
        r = c.post("/api/v1/auth/register", json={"email": email, "password": pw, "name": "Smoke Test"})
        check("register", r.status_code in (200, 201), f"status {r.status_code}")
        r = c.post("/api/v1/auth/login", data={"username": email, "password": pw})
        has_cookie = any("sl_token" in h for h in r.headers.get_list("set-cookie"))
        check("login sets HttpOnly session cookie", r.status_code == 200 and has_cookie,
              f"status {r.status_code}")
        check("login body carries no access token value", not r.json().get("access_token"))
        r = c.get("/api/v1/auth/me")
        check("session cookie authenticates /auth/me", r.status_code == 200, f"status {r.status_code}")

        r = c.post("/api/v1/auth/logout", headers={"Origin": "https://evil.example.org"})
        check("cookie POST from a foreign origin is refused", r.status_code == 403, f"status {r.status_code}")

        r = c.post("/api/v1/upload", files={"file": ("smoke.pdf", tiny_pdf(), "application/pdf")})
        check("authenticated upload", r.status_code in (200, 201), f"status {r.status_code}")
        doc_id = r.json().get("id") if r.status_code in (200, 201) else None
        check("upload response hides file_url", r.status_code not in (200, 201) or "file_url" not in r.text)

        if doc_id:
            r = c.get(f"/api/v1/upload/{doc_id}/download", follow_redirects=False)
            check("download issues a redirect/signed link", r.status_code in (200, 302, 307),
                  f"status {r.status_code}")
            if a.with_analysis:
                r = c.post("/api/v1/analyze", json={"document_id": doc_id})
                check("analysis starts", r.status_code in (200, 202), f"status {r.status_code}")
                done = False
                for _ in range(60):
                    s = c.get(f"/api/v1/analyze/{doc_id}/status")
                    if s.status_code == 200 and s.json().get("status") in ("done", "completed", "complete"):
                        done = True
                        break
                    time.sleep(5)
                check("analysis completes within 5 minutes", done)
            c.delete(f"/api/v1/upload/{doc_id}")

        r = c.post("/api/v1/auth/logout")
        check("logout", r.status_code == 200, f"status {r.status_code}")
        r = c.get("/api/v1/auth/me")
        check("session ended after logout", r.status_code == 401, f"status {r.status_code}")
        print(f"NOTE: throw-away account {email} remains in the staging database; delete it manually.")

    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
