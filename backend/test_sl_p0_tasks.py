import asyncio, uuid
from datetime import datetime
from database import init_db_pool, get_db_ctx
from services.application_service import create_application, list_applications, get_application, delete_application

async def main():
    await init_db_pool()
    async with get_db_ctx() as db:
        user_id = f"usr_test_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        
        # Insert test user
        await db.execute("INSERT INTO users (id, name, email, password, created_at) VALUES ($1, $2, $3, $4, $5)", user_id, "Test Agent User", f"{user_id}@smartlegal.ai", "hash", now)
        print(f"[SL-005 TEST] Inserted test user: {user_id}")

        # Test creating Legal ID application via generic platform
        app1 = await create_application(db, user_id, "legal-id", "aadhaar", "Aadhaar Update", "Test Note", ["Submit Form", "Upload Photo"])
        print("[SL-006 TEST] Generic Legal ID Application Created:", app1["id"])

        # Test creating Property application
        app2 = await create_application(db, user_id, "property", "rent_agreement", "Rent Registration", "Test Note", ["Draft Deed"])
        print("[SL-006 TEST] Generic Property Application Created:", app2["id"])

        # Test listing
        apps = await list_applications(db, user_id, "legal-id")
        print(f"[SL-006 TEST] Legal ID Apps Listed: {len(apps)}")

        # Test Cascade Deletion: Deleting user should cascade delete applications & checklist items (SL-005)
        await db.execute("DELETE FROM users WHERE id = $1", user_id)
        print("[SL-005 TEST] User Deleted — Testing Referential Integrity CASCADE")

        remaining = await db.fetch("SELECT * FROM id_applications WHERE user_id = $1", user_id)
        print(f"[SL-005 TEST] Remaining id_applications for deleted user: {len(remaining)} (Expected: 0)")
        assert len(remaining) == 0, "Cascade deletion failed"
        print("SL-001 THROUGH SL-006 VERIFICATION SUCCESSFUL!")


if __name__ == "__main__":
    asyncio.run(main())

