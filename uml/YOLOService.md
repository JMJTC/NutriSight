@startuml

left to right direction

skinparam backgroundColor white
skinparam shadowing false
skinparam defaultFontName "Microsoft YaHei"
skinparam linetype ortho
skinparam nodesep 45
skinparam ranksep 40

actor "API请求" as Request

component "FoodRecognitionService\n识别业务服务" as FoodService
component "asyncio.to_thread()\n线程池调度" as ThreadPool

component "YoloService\n单例模型服务\n\n核心状态：\n_model\n_model_loaded\n_load_error\n_model_path\n\n核心方法：\n__new__\nload_model\nis_ready\npredict\npredict_with_annotation" as YoloService

component "Ultralytics YOLO\n模型实例" as Model
artifact "weights\nbest.pt / last.pt" as Weights

rectangle "加载锁\n_load_lock\n\n保证模型只加载一次" as LoadLock
rectangle "推理锁\n_predict_lock\n\n串行化推理请求" as PredictLock

Request --> FoodService : 识别请求
FoodService --> ThreadPool : 调度同步推理
ThreadPool --> YoloService : 调用推理方法

YoloService --> Weights : 加载权重
YoloService --> Model : 持有模型实例
YoloService --> LoadLock : load_model加锁
YoloService --> PredictLock : predict加锁

note bottom of YoloService
通过__new__保证全局唯一实例；
多个请求共享同一份模型权重，
避免重复加载和显存浪费。
end note

note bottom of PredictLock
YOLO推理属于CPU/GPU密集型同步操作，
推理锁用于避免并发访问同一模型实例。
end note

@enduml