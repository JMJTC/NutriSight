from datetime import datetime, timedelta, timezone
import os
import uuid
import shutil

from fastapi import APIRouter, UploadFile, File

from app.controllers.user import user_controller
from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth
from app.models.admin import Api, Menu, Role, User
from app.schemas.base import Fail, Success
from app.schemas.login import *
from app.schemas.users import UpdatePassword, UserRegister, UserCreate
from app.settings import settings
from app.utils.jwt_utils import create_access_token
from app.utils.password import get_password_hash, verify_password

router = APIRouter()


@router.post("/access_token", summary="获取token")
async def login_access_token(credentials: CredentialsSchema):
    user: User = await user_controller.authenticate(credentials)
    await user_controller.update_last_login(user.id)
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + access_token_expires

    data = JWTOut(
        access_token=create_access_token(
            data=JWTPayload(
                user_id=user.id,
                username=user.username,
                is_superuser=user.is_superuser,
                exp=expire,
            )
        ),
        username=user.username,
    )
    return Success(data=data.model_dump())


@router.post("/register", summary="用户注册")
async def user_register(obj_in: UserRegister):
    # 1. 检查用户名是否已存在
    user = await user_controller.get_by_username(obj_in.username)
    if user:
        return Fail(code=400, msg="用户名已被注册")
    
    # 2. 检查邮箱是否已存在
    user = await user_controller.get_by_email(obj_in.email)
    if user:
        return Fail(code=400, msg="邮箱已被注册")
    
    # 3. 创建用户
    user_create = UserCreate(
        username=obj_in.username,
        email=obj_in.email,
        password=obj_in.password,
        height_cm=obj_in.height_cm,
        weight_kg=obj_in.weight_kg,
        gender=obj_in.gender,
        age=obj_in.age,
        is_active=True,
        is_superuser=False
    )
    new_user = await user_controller.create_user(obj_in=user_create)
    
    # 4. 分配"普通用户"角色 (Role ID 默认为 2)
    user_role = await Role.filter(name="普通用户").first()
    if user_role:
        await new_user.roles.add(user_role)
    
    return Success(msg="注册成功")


@router.get("/userinfo", summary="查看用户信息", dependencies=[DependAuth])
async def get_userinfo():
    user_id = CTX_USER_ID.get()
    user_obj = await user_controller.get(id=user_id)
    data = await user_obj.to_dict(exclude_fields=["password"])
    if not data.get("avatar"):
        data["avatar"] = "https://avatars.githubusercontent.com/u/54677442?v=4"
    return Success(data=data)


@router.get("/usermenu", summary="查看用户菜单", dependencies=[DependAuth])
async def get_user_menu():
    user_id = CTX_USER_ID.get()
    user_obj = await User.filter(id=user_id).first()
    menus: list[Menu] = []
    if user_obj.is_superuser:
        menus = await Menu.all()
    else:
        role_objs: list[Role] = await user_obj.roles
        for role_obj in role_objs:
            menu = await role_obj.menus
            menus.extend(menu)
        menus = list(set(menus))
    parent_menus: list[Menu] = []
    for menu in menus:
        if menu.parent_id == 0:
            parent_menus.append(menu)
    res = []
    for parent_menu in parent_menus:
        parent_menu_dict = await parent_menu.to_dict()
        parent_menu_dict["children"] = []
        for menu in menus:
            if menu.parent_id == parent_menu.id:
                parent_menu_dict["children"].append(await menu.to_dict())
        res.append(parent_menu_dict)
    return Success(data=res)


@router.get("/userapi", summary="查看用户API", dependencies=[DependAuth])
async def get_user_api():
    user_id = CTX_USER_ID.get()
    user_obj = await User.filter(id=user_id).first()
    if user_obj.is_superuser:
        api_objs: list[Api] = await Api.all()
        apis = [api.method.lower() + api.path for api in api_objs]
        return Success(data=apis)
    role_objs: list[Role] = await user_obj.roles
    apis = []
    for role_obj in role_objs:
        api_objs: list[Api] = await role_obj.apis
        apis.extend([api.method.lower() + api.path for api in api_objs])
    apis = list(set(apis))
    return Success(data=apis)


@router.post("/update_password", summary="修改密码", dependencies=[DependAuth])
async def update_user_password(req_in: UpdatePassword):
    user_id = CTX_USER_ID.get()
    user = await user_controller.get(user_id)
    verified = verify_password(req_in.old_password, user.password)
    if not verified:
        return Fail(msg="旧密码验证错误！")
    user.password = get_password_hash(req_in.new_password)
    await user.save()
    return Success(msg="修改成功")


@router.post("/update_avatar", summary="修改头像", dependencies=[DependAuth])
async def update_user_avatar(file: UploadFile = File(...)):
    # 1. 验证文件类型
    if not file.content_type.startswith("image/"):
        return Fail(msg="只支持图片文件上传")
    
    # 2. 验证文件大小 (2MB)
    MAX_SIZE = 2 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_SIZE:
        return Fail(msg="图片大小不能超过 2MB")
    await file.seek(0)
    
    # 3. 保存文件
    upload_dir = os.path.join(settings.BASE_DIR, "deploy", "static", "uploads", "avatars")
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        
    file_ext = file.filename.split(".")[-1] if file.filename else "png"
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(upload_dir, file_name)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        return Fail(msg=f"头像保存失败: {str(e)}")
        
    # 4. 更新数据库
    user_id = CTX_USER_ID.get()
    relative_path = f"/static/uploads/avatars/{file_name}"
    await user_controller.update_avatar(user_id, relative_path)
    
    return Success(data={"avatar": relative_path}, msg="头像更新成功")
