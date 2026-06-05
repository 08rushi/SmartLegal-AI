"""Test auth endpoints"""
import asyncio
import json
import sys
import os

# Ensure we're in the right directory for relative paths
os.chdir('backend')
sys.path.insert(0, '.')

# Initialize database first
from database import init_db
asyncio.run(init_db())

# Now import and test
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

print("=" * 70)
print("TESTING AUTH ENDPOINTS")
print("=" * 70)

# Test 1: Registration
print("\n1. Testing REGISTER endpoint...")
try:
    payload = {
        "name": "Test User",
        "email": "test_register@example.com",
        "password": "SecurePass123!"
    }
    print(f"   Sending: {json.dumps(payload, indent=2)}")

    response = client.post("/api/v1/auth/register", json=payload)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:500]}")

    if response.status_code == 201:
        data = response.json()
        print(f"   [SUCCESS] User registered: {data['user']['email']}")
    else:
        print(f"   [ERROR] Registration failed")
except Exception as e:
    print(f"   [EXCEPTION] {type(e).__name__}: {e}")

# Test 2: Login
print("\n2. Testing LOGIN endpoint...")
try:
    # Use form data for OAuth2PasswordRequestForm
    payload = {
        "username": "test_register@example.com",
        "password": "SecurePass123!"
    }
    print(f"   Sending: username={payload['username']}, password=***")

    response = client.post("/api/v1/auth/login", data=payload)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:500]}")

    if response.status_code == 200:
        data = response.json()
        print(f"   [SUCCESS] User logged in: {data['user']['email']}")
        print(f"   Token: {data['access_token'][:20]}...")
    else:
        print(f"   [ERROR] Login failed")
except Exception as e:
    print(f"   [EXCEPTION] {type(e).__name__}: {e}")

print("\n" + "=" * 70)
