# 导入YOLO核心库
from ultralytics import YOLO
import os

# -------------------------- 配置路径（根据你的实际路径修改） --------------------------
# 模型文件路径（使用原始字符串避免转义问题）
model_path = r"F:\jmjtc\UndergraduateInformation\graduation_project\yolostudy\trainfood101\runs\classify\train\weights\best.pt"
# 待测试图片路径
img_path = r"F:\jmjtc\UndergraduateInformation\graduation_project\yolostudy\trainfood101\test.jpg"

# -------------------------- 核心预测逻辑 --------------------------
# 1. 加载训练好的分类模型
try:
    model = YOLO(model_path)
    print(f"✅ 成功加载模型：{model_path}")
except Exception as e:
    print(f"❌ 模型加载失败：{e}")
    exit()

# 2. 检查图片是否存在
if not os.path.exists(img_path):
    print(f"❌ 图片不存在：{img_path}")
    exit()

# 3. 执行预测（conf=0.5 表示置信度阈值，可根据需要调整）
print(f"🔍 正在预测图片：{img_path}")
results = model(img_path, conf=0.5)

# 4. 解析并打印预测结果
result = results[0]  # 单张图片只有一个结果
# 获取预测的类别名称和对应的置信度
top1_class = result.names[result.probs.top1]  # 置信度最高的类别
top1_conf = result.probs.top1conf.item()     # 最高置信度（转换为浮点数）

# 打印结果
print("\n📊 预测结果：")
print(f"   最可能的类别：{top1_class}")
print(f"   置信度：{top1_conf:.4f} (即 {top1_conf*100:.2f}%)")

# 可选：打印前5个预测结果（如果需要）
print("\n📈 前5个预测类别（按置信度排序）：")
for i, (cls_idx, conf) in enumerate(zip(result.probs.top5, result.probs.top5conf)):
    cls_name = result.names[cls_idx]
    print(f"   第{i+1}名：{cls_name} (置信度：{conf.item():.4f})")

# 可选：保存预测结果图片（带类别标注）
save_path = r"F:\jmjtc\UndergraduateInformation\graduation_project\yolostudy\trainfood101\predict_result.jpg"
result.save(filename=save_path)
print(f"\n💾 预测结果图片已保存至：{save_path}")