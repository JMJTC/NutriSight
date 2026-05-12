@startuml
top to bottom direction

skinparam backgroundColor white
skinparam shadowing false
skinparam defaultFontName "Microsoft YaHei"
skinparam linetype ortho
skinparam nodesep 35
skinparam ranksep 35
skinparam packageStyle rectangle
skinparam wrapWidth 150

skinparam rectangle {
    BackgroundColor white
    BorderColor black
    FontColor black
}

package "① 登录认证" {
    rectangle "用户登录\n提交用户名和密码" as Login
    rectangle "校验用户名\n和密码" as CheckPwd
    rectangle "认证通过？" as AuthOK
    rectangle "生成JWT令牌\n载荷:user_id\n有效期:7天" as GenJWT
    rectangle "返回登录失败" as LoginFail
}

package "② Token解析与权限校验" {
    rectangle "接口请求\nHeader携带token" as Request
    rectangle "AuthControl\n解析token\n获取user_id" as ParseToken
    rectangle "token有效？" as TokenOK
    rectangle "PermissionControl\nRBAC权限校验\n超级管理员直接放行\n否则匹配角色API权限" as RBAC
    rectangle "具有权限？" as PermissionOK
    rectangle "返回401\n未认证" as Unauthorized
    rectangle "返回403\n禁止访问" as Forbidden
}

package "③ 审计日志与业务处理" {
    rectangle "记录审计日志\n异步写入数据库" as Audit
    rectangle "执行业务接口" as Business
    rectangle "返回接口响应" as Response
}

Login -right-> CheckPwd
CheckPwd -right-> AuthOK
AuthOK -right-> GenJWT : 是
AuthOK -down-> LoginFail : 否

GenJWT -down-> Request

Request -right-> ParseToken
ParseToken -right-> TokenOK
TokenOK -right-> RBAC : 是
TokenOK -down-> Unauthorized : 否

RBAC -right-> PermissionOK
PermissionOK -down-> Forbidden : 否
PermissionOK -down-> Audit : 是

Audit -right-> Business
Business -right-> Response

@enduml