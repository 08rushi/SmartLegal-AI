import asyncio
import httpx
import time
import json

async def test():
    async with httpx.AsyncClient() as client:
        # Generate unique email
        email = f"test_{int(time.time() * 1000)}@example.com"

        # Test Register
        print("=== Testing Register ===")
        register_data = {
            'name': 'Test User',
            'email': email,
            'password': 'TestPass123'
        }
        try:
            resp = await client.post('http://localhost:8000/api/v1/auth/register', json=register_data, timeout=10)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
            if resp.status_code == 201:
                data = resp.json()
                token = data['access_token']
                print(f"Token received: {token[:20]}...")

                # Test Login
                print("\n=== Testing Login ===")
                login_data = {
                    'username': email,
                    'password': 'TestPass123'
                }
                resp = await client.post('http://localhost:8000/api/v1/auth/login',
                    data=login_data, timeout=10)
                print(f"Status: {resp.status_code}")
                print(f"Response: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    asyncio.run(test())
