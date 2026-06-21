import requests
import json

# 首先登录获取 token
login_url = "http://localhost:9999/api/v1/auth/access_token"
login_data = {
    "username": "admin",  # 假设有 admin 用户
    "password": "123456"  # 默认密码
}

print("正在获取认证 token...")
login_response = requests.post(login_url, json=login_data)
if login_response.status_code == 200:
    token_data = login_response.json()
    token = token_data["data"]["access_token"]
    print(f"✓ 成功获取 token: {token[:20]}...")

    # 测试食物识别 API
    url = "http://localhost:9999/api/v1/food/recognize"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    # 使用现有的测试图片
    test_image_path = "deploy/sample-picture/1.jpg"

    print(f"正在测试食物识别 API，使用图片: {test_image_path}")
    try:
        with open(test_image_path, "rb") as f:
            files = {"file": ("1.jpg", f, "image/jpeg")}
            response = requests.post(url, headers=headers, files=files)

        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print("✓ API 调用成功!")
            print("响应内容:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print("✗ API 调用失败")
            print("响应内容:")
            print(response.text)
    except FileNotFoundError:
        print(f"✗ 测试图片不存在: {test_image_path}")
        print("请确保图片文件存在")
    except Exception as e:
        print(f"✗ 测试过程中出错: {str(e)}")
else:
    print(f"✗ 登录失败: {login_response.status_code} - {login_response.text}")