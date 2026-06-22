## 五、数据库设计（工程化完善）

本系统采用 **MySQL 关系型数据库**作为数据存储方案，用于管理用户信息、食物类别数据、营养成分数据、食物识别记录以及营养分析与推荐结果。数据库设计遵循规范化原则，兼顾系统扩展性与查询效率，能够满足系统在实际运行中的数据管理需求。

---

### 5.1 用户信息表（user）

用于存储系统用户的基础信息，为饮食记录统计、营养分析及个性化推荐提供用户维度的数据支撑。

| 字段名         | 数据类型         | 说明         |
| ----------- | ------------ | ---------- |
| id          | INT          | 用户唯一标识，主键  |
| username    | VARCHAR(50)  | 用户名        |
| password    | VARCHAR(100) | 用户密码（加密存储） |
| gender      | VARCHAR(10)  | 性别         |
| age         | INT          | 年龄         |
| height      | FLOAT        | 身高（cm）     |
| weight      | FLOAT        | 体重（kg）     |
| create_time | DATETIME     | 注册时间       |
| update_time | DATETIME     | 信息更新时间     |

---

### 5.2 食物类别表（food）

用于存储系统支持识别的食物类别信息，与 YOLOv11 模型输出的类别标签保持一致。

| 字段名         | 数据类型         | 说明               |
| ----------- | ------------ | ---------------- |
| id          | INT          | 食物类别唯一标识，主键      |
| food_name   | VARCHAR(100) | 食物名称             |
| food_type   | VARCHAR(50)  | 食物类型（如主食、肉类、蔬菜等） |
| description | VARCHAR(255) | 食物描述             |
| create_time | DATETIME     | 创建时间             |

---

### 5.3 营养信息表（nutrition）

用于存储食物的标准营养成分数据，是营养分析与推荐模块的核心数据来源。

| 字段名          | 数据类型     | 说明            |
| ------------ | -------- | ------------- |
| id           | INT      | 营养信息记录唯一标识，主键 |
| food_id      | INT      | 对应食物类别 ID     |
| energy       | FLOAT    | 热量（kcal/100g） |
| protein      | FLOAT    | 蛋白质含量（g）      |
| fat          | FLOAT    | 脂肪含量（g）       |
| carbohydrate | FLOAT    | 碳水化合物含量（g）    |
| fiber        | FLOAT    | 膳食纤维含量（g）     |
| sodium       | FLOAT    | 钠含量（mg）       |
| create_time  | DATETIME | 数据创建时间        |

---

### 5.4 食物识别记录表（recognition_record）

用于记录用户每次食物识别的详细信息，为饮食统计与模型评估提供数据支持。

| 字段名            | 数据类型         | 说明          |
| -------------- | ------------ | ----------- |
| id             | INT          | 识别记录唯一标识，主键 |
| user_id        | INT          | 用户 ID       |
| image_path     | VARCHAR(255) | 上传图片存储路径    |
| recognize_time | DATETIME     | 识别时间        |
| status         | VARCHAR(20)  | 识别状态（成功/失败） |

---

### 5.5 识别结果明细表（recognition_detail）

用于存储单次识别中检测到的多种食物目标信息，支持一图多目标的检测结果记录。

| 字段名        | 数据类型         | 说明          |
| ---------- | ------------ | ----------- |
| id         | INT          | 明细记录唯一标识，主键 |
| record_id  | INT          | 识别记录 ID     |
| food_id    | INT          | 识别到的食物类别 ID |
| confidence | FLOAT        | 模型预测置信度     |
| bbox       | VARCHAR(100) | 目标位置信息（边界框） |

---

### 5.6 营养分析结果表（nutrition_analysis）

用于存储系统对用户饮食摄入情况的营养分析结果。

| 字段名                | 数据类型     | 说明          |
| ------------------ | -------- | ----------- |
| id                 | INT      | 分析结果唯一标识，主键 |
| user_id            | INT      | 用户 ID       |
| total_energy       | FLOAT    | 总热量摄入       |
| total_protein      | FLOAT    | 蛋白质摄入总量     |
| total_fat          | FLOAT    | 脂肪摄入总量      |
| total_carbohydrate | FLOAT    | 碳水化合物摄入总量   |
| analysis_result    | TEXT     | 营养分析结论      |
| create_time        | DATETIME | 生成时间        |

---

### 5.7 营养推荐表（nutrition_recommendation）

用于存储系统生成的饮食建议与推荐信息。

| 字段名             | 数据类型         | 说明          |
| --------------- | ------------ | ----------- |
| id              | INT          | 推荐记录唯一标识，主键 |
| user_id         | INT          | 用户 ID       |
| recommendation  | TEXT         | 饮食建议内容      |
| reference_basis | VARCHAR(255) | 推荐依据说明      |
| create_time     | DATETIME     | 推荐生成时间      |

---

### 5.8 数据库设计说明

通过上述数据库表结构设计，系统能够完整支撑食物识别、营养信息管理、饮食统计与营养推荐等功能需求。数据库结构支持用户多次识别记录的存储与关联分析，并为后续引入个性化推荐或长期健康评估功能预留了扩展空间，具备较好的工程可行性与维护性。