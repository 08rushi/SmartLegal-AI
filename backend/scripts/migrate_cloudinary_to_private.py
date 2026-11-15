"""
Re-type existing PUBLIC Cloudinary raw assets as PRIVATE ("authenticated").

Usage (from backend/):
    python scripts/migrate_cloudinary_to_private.py            # dry run: counts only
    python scripts/migrate_cloudinary_to_private.py --apply    # perform the migration

For each documents.file_url that is a Cloudinary `.../upload/...` URL of our own cloud the
asset is renamed in place to delivery type "authenticated" (public_id unchanged) and the
DB row is updated to the new `.../authenticated/...` URL. Idempotent: already-private and
local:// rows are skipped. Output is counts only (no URLs, ids or names).

Uses DATABASE_URL and CLOUDINARY_* from the environment / backend/.env. Take a DB backup
first; --apply modifies Cloudinary and the database.
"""
import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import storage  # noqa: E402


def _classify(url: str) -> str:
    if not url or url.startswith("local://"):
        return "skipped_local"
    info = storage.parse_cloudinary_url(url)
    if info is None or not storage.is_allowed_cloud_url(url):
        return "skipped_foreign"
    return "private" if info["type"] != "upload" else "public"


def _rename_to_private(url: str) -> str:
    """Rename the asset to type=authenticated in Cloudinary; return the new stored URL."""
    import cloudinary
    import cloudinary.uploader

    s = storage.settings
    cloudinary.config(cloud_name=s.cloudinary_cloud_name, api_key=s.cloudinary_api_key,
                      api_secret=s.cloudinary_api_secret, secure=True)
    info = storage.parse_cloudinary_url(url)
    pid = info["public_id"]
    cloudinary.uploader.rename(pid, pid, resource_type=info["resource_type"],
                               type="upload", to_type="authenticated", invalidate=True)
    return url.replace(f"/{info['resource_type']}/upload/", f"/{info['resource_type']}/authenticated/", 1)


async def migrate(conn, apply: bool, rename=_rename_to_private) -> dict:
    counts = {"total": 0, "public": 0, "private": 0, "skipped_local": 0, "skipped_foreign": 0,
              "migrated": 0, "failed": 0}
    rows = await conn.fetch("SELECT id, file_url FROM documents")
    for row in rows:
        counts["total"] += 1
        kind = _classify(row["file_url"] or "")
        counts[kind] += 1
        if kind != "public" or not apply:
            continue
        try:
            new_url = rename(row["file_url"])
            await conn.execute("UPDATE documents SET file_url = $1 WHERE id = $2", new_url, row["id"])
            counts["migrated"] += 1
        except Exception:
            counts["failed"] += 1
    return counts


async def _main(apply: bool) -> int:
    from database import get_db_ctx, close_db_pool

    try:
        async with get_db_ctx() as conn:
            counts = await migrate(conn, apply)
    finally:
        await close_db_pool()
    mode = "APPLY" if apply else "DRY RUN (no changes; pass --apply to migrate)"
    print(f"[migrate_cloudinary_to_private] mode: {mode}")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="actually migrate (default is a dry run)")
    args = ap.parse_args()
    sys.exit(asyncio.run(_main(args.apply)))
