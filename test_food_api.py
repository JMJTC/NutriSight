import requests
import json

# 首先登录获取 token
login_url = "http://localhost:9999/api/v1/auth/access_token"
login_data = {
    "username": "admin",  # 假设有 admin 用户
    "password": "admin123"  # 假设密码
}

login_response = requests.post(login_url, json=login_data)
if login_response.status_code == 200:
    token_data = login_response.json()
    token = token_data["data"]["access_token"]
    print(f"✓ Got token: {token[:20]}...")

    # 测试食物识别 API
    url = "http://localhost:9999/api/v1/food/recognize"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    # 使用现有的测试图片
    test_image_path = "deploy/sample-picture/1.jpg"

    try:
        with open(test_image_path, "rb") as f:
            files = {"file": ("1.jpg", f, "image/jpeg")}
            response = requests.post(url, headers=headers, files=files)

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except FileNotFoundError:
        print(f"Test image not found: {test_image_path}")
else:
    print(f"Login failed: {login_response.status_code} - {login_response.text}")