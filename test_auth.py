import requests

BASE_URL = "http://localhost:8000/api/auth"

# 1. 测试注册
print("=== 测试注册 ===")
response = requests.post(f"{BASE_URL}/register/", json={
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test123456",
    "password_confirm": "Test123456"  # ← 添加确认密码字段
})
print(f"状态码: {response.status_code}")
print(f"响应: {response.json()}")
print()

# 2. 测试登录
print("=== 测试登录 ===")
response = requests.post(f"{BASE_URL}/login/", json={
    "username": "testuser",
    "password": "Test123456"
})
print(f"状态码: {response.status_code}")
data = response.json()
print(f"响应: {data}")
access_token = data.get('access_token')
print()

# 3. 测试获取用户信息
if access_token:
    print("=== 测试获取用户信息 ===")
    response = requests.get(f"{BASE_URL}/profile/", headers={
        "Authorization": f"Bearer {access_token}"
    })
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()
else:
    print("=== 跳过获取用户信息测试（无 token）===")
    print()

# 4. 测试未授权访问
print("=== 测试未授权访问 ===")
response = requests.get(f"{BASE_URL}/profile/")
print(f"状态码: {response.status_code}")
print(f"响应: {response.json()}")
