#!/usr/bin/env python
import os
import sys
sys.path.append('.')

from app import app
from fastapi.testclient import TestClient

# Test if static files can be accessed
client = TestClient(app)

test_url = "/static/uploads/049ac5f6-038e-4882-a1c4-a1ee5aac85de.jpg"
print(f"Testing URL: {test_url}")

try:
    response = client.head(test_url)
    print(f"Status: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
    
# Also test if the route exists
print("\nAvailable routes:")
for route in app.routes:
    print(f"  {route.path} - {route.methods if hasattr(route, 'methods') else 'unknown'}")
