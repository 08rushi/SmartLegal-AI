import asyncio
from database import init_db_pool, get_db_ctx
from routers.yojana import SchemeMatchRequest, evaluate_scheme_eligibility, match_citizen_eligibility
from fastapi import Request

async def main():
    await init_db_pool()
    async with get_db_ctx() as db:
        req = SchemeMatchRequest(
            state="Maharashtra",
            age=32,
            gender="female",
            occupation="farmer",
            annual_income=180000,
            category="OBC",
            land_holding_acres=1.5
        )
        print("Testing Profile:", req.dict())
        
        # Test evaluation function directly
        fake_req = type('Req', (), {'state': req})()
        
        rows = await db.fetch("SELECT * FROM yojana_schemes")
        import json
        for r in rows:
            item = dict(r)
            item["benefits"] = json.loads(item.get("benefits_json") or "[]")
            item["eligibility"] = json.loads(item.get("eligibility_json") or "{}")
            item["required_docs"] = json.loads(item.get("required_docs_json") or "[]")
            res = evaluate_scheme_eligibility(item, req)
            print(f"Scheme: {res['scheme']['title']} -> Match Score: {res['match_score']}% ({res['status']})")

if __name__ == "__main__":
    asyncio.run(main())
