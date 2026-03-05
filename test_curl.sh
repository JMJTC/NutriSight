# 获取 token
curl -X POST "http://localhost:9999/api/v1/auth/access_token" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.data.access_token' > token.txt

# 使用 token 测试食物识别
TOKEN=$(cat token.txt)
curl -X POST "http://localhost:9999/api/v1/food/recognize" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@deploy/sample-picture/1.jpg" \
  -v