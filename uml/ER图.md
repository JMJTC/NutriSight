@startuml

!theme plain
top to bottom direction
skinparam linetype ortho

class dept {
   created_at: timestamp
   updated_at: timestamp
   name: varchar(20)
   desc: varchar(500)
   is_deleted: int
   order: int
   parent_id: int
   id: integer
}
class food_category {
   created_at: timestamp
   updated_at: timestamp
   name: varchar(100)
   code: int
   food_type: varchar(50)
   description: varchar(255)
   image_url: varchar(255)
   chinese_name: varchar(100)
   id: integer
}
class nutrition {
   created_at: timestamp
   updated_at: timestamp
   energy: real
   protein: real
   fat: real
   carbohydrate: real
   fiber: real
   sodium: real
   food_id: bigint
   id: integer
}
class nutrition_analysis {
   created_at: timestamp
   updated_at: timestamp
   total_energy: real
   total_protein: real
   total_fat: real
   total_carbohydrate: real
   summary: text
   record_id: bigint
   total_fiber: real
   total_sodium: real
   id: integer
}
class nutrition_recommendation {
   created_at: timestamp
   updated_at: timestamp
   content: text
   reference: varchar(255)
   user_id: bigint
   record_id: bigint
   id: integer
}
class recognition_detail {
   created_at: timestamp
   updated_at: timestamp
   confidence: real
   bbox: json
   food_id: bigint
   record_id: bigint
   id: integer
}
class recognition_record {
   created_at: timestamp
   updated_at: timestamp
   image_path: varchar(255)
   status: varchar(20)
   user_id: bigint
   annotated_image_path: varchar(255)
   id: integer
}
class role {
   created_at: timestamp
   updated_at: timestamp
   name: varchar(20)
   desc: varchar(500)
   id: integer
}
class user {
   created_at: timestamp
   updated_at: timestamp
   username: varchar(20)
   alias: varchar(30)
   email: varchar(255)
   phone: varchar(20)
   password: varchar(128)
   is_active: int
   is_superuser: int
   last_login: timestamp
   dept_id: int
   avatar: varchar(255)
   gender: int
   weight_kg: varchar(40)
   age: int
   height_cm: int
   id: integer
}
class user_role {
   user_id: bigint
   role_id: bigint
}

nutrition                 -[#595959,plain]-^  food_category            : "food_id:id"
nutrition_analysis        -[#595959,plain]-^  recognition_record       : "record_id:id"
nutrition_recommendation  -[#595959,plain]-^  user                     : "user_id:id"
recognition_detail        -[#595959,plain]-^  food_category            : "food_id:id"
recognition_detail        -[#595959,plain]-^  recognition_record       : "record_id:id"
recognition_record        -[#595959,plain]-^  user                     : "user_id:id"
user                      -[#595959,plain]-^  dept                     : "dept_id:id"
user_role                 -[#595959,plain]-^  role                     : "role_id:id"
user_role                 -[#595959,plain]-^  user                     : "user_id:id"
@enduml
