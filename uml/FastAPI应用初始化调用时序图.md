@startuml
title FastAPI应用初始化调用时序图

skinparam backgroundColor white
skinparam shadowing false
skinparam defaultFontName "Microsoft YaHei"
skinparam sequence {
    ArrowColor black
    LifeLineBorderColor black
    LifeLineBackgroundColor white
    ParticipantBorderColor black
    ParticipantBackgroundColor white
}

actor "系统启动器" as Launcher
participant "create_app()\n应用工厂" as Factory
participant "FastAPI应用实例\n食智眸" as App
participant "init_data()\n初始化入口" as InitData
participant "init_db()\n数据库迁移初始化" as InitDB
participant "init_yolo_model()\n模型初始化" as InitYolo
participant "init_superuser()\n超级用户初始化" as InitUser
participant "init_menus()\n菜单初始化" as InitMenu
participant "init_apis()\nAPI权限同步" as InitApi
participant "init_roles()\n角色初始化" as InitRole
participant "init_food_data()\n食物数据初始化" as InitFood

Launcher -> Factory : 调用 create_app()
activate Factory

Factory -> App : 创建 FastAPI 实例
Factory -> App : 设置应用标题“食智眸”
Factory -> App : 配置 CORS 中间件
Factory -> App : 注册全局异常处理器
Factory -> App : 挂载静态文件目录
Factory -> App : 注册 API 路由前缀 /api

Factory -> InitData : 应用启动时调用 init_data()
activate InitData

InitData -> InitDB : 初始化数据库与迁移
activate InitDB
InitDB -> InitDB : 安全创建数据库
InitDB -> InitDB : 初始化 Aerich 配置
InitDB -> InitDB : 检测模型变更并生成迁移脚本
InitDB -> InitDB : 执行 upgrade() 升级表结构
alt 迁移历史异常
    InitDB -> InitDB : 重建迁移目录
end
InitDB --> InitData : 数据库初始化完成
deactivate InitDB

InitData -> InitYolo : 加载 YOLOv11 模型
activate InitYolo
InitYolo -> InitYolo : 获取 YoloService 单例
InitYolo -> InitYolo : 优先加载 weights/best.pt
alt best.pt 不存在
    InitYolo -> InitYolo : 回退加载 weights/last.pt
end
InitYolo -> InitYolo : 模型预热
InitYolo --> InitData : 模型初始化完成
deactivate InitYolo

InitData -> InitUser : 初始化超级管理员
activate InitUser
InitUser -> InitUser : 检查用户表是否为空
alt 用户表为空
    InitUser -> InitUser : 创建 admin / 123456
    InitUser -> InitUser : 使用 Argon2 哈希密码
end
InitUser --> InitData : 超级用户初始化完成
deactivate InitUser

InitData -> InitMenu : 初始化系统菜单
activate InitMenu
InitMenu -> InitMenu : 创建系统管理一级目录
InitMenu -> InitMenu : 创建六个子菜单项
InitMenu --> InitData : 菜单初始化完成
deactivate InitMenu

InitData -> InitApi : 同步 API 权限
activate InitApi
InitApi -> InitApi : 扫描 FastAPI 已注册路由
InitApi -> InitApi : 同步路径、方法、摘要信息
InitApi --> InitData : API权限同步完成
deactivate InitApi

InitData -> InitRole : 初始化基础角色
activate InitRole
InitRole -> InitRole : 创建管理员角色
InitRole -> InitRole : 创建普通用户角色
InitRole -> InitRole : 分配对应权限
InitRole --> InitData : 角色初始化完成
deactivate InitRole

InitData -> InitFood : 初始化食物类别与营养数据
activate InitFood
InitFood -> InitFood : 检查 FoodCategory 表是否为空
alt FoodCategory 表为空
    InitFood -> InitFood : 导入15种常见食物类别
    InitFood -> InitFood : 导入营养成分数据
end
InitFood --> InitData : 食物数据初始化完成
deactivate InitFood

InitData --> Factory : 初始化完成
deactivate InitData

Factory --> Launcher : 返回 FastAPI 应用实例
deactivate Factory

@enduml