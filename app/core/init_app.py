import shutil

from aerich import Command
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from tortoise.expressions import Q

from app.api import api_router
from app.controllers.api import api_controller
from app.controllers.user import UserCreate, user_controller
from app.core.exceptions import (
    DoesNotExist,
    DoesNotExistHandle,
    HTTPException,
    HttpExcHandle,
    IntegrityError,
    IntegrityHandle,
    RequestValidationError,
    RequestValidationHandle,
    ResponseValidationError,
    ResponseValidationHandle,
    CustomException,
    CustomExceptionHandle,
)
from app.log import logger
from app.models.admin import Api, Menu, Role
from app.schemas.menus import MenuType
from app.settings.config import settings

from .middlewares import BackGroundTaskMiddleware, HttpAuditLogMiddleware


def make_middlewares():
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.CORS_ALLOW_METHODS,
            allow_headers=settings.CORS_ALLOW_HEADERS,
        ),
        Middleware(BackGroundTaskMiddleware),
        Middleware(
            HttpAuditLogMiddleware,
            methods=["GET", "POST", "PUT", "DELETE"],
            exclude_paths=[
                "/api/v1/base/access_token",
                "/docs",
                "/openapi.json",
            ],
        ),
    ]
    return middleware


def register_exceptions(app: FastAPI):
    app.add_exception_handler(DoesNotExist, DoesNotExistHandle)
    app.add_exception_handler(HTTPException, HttpExcHandle)
    app.add_exception_handler(IntegrityError, IntegrityHandle)
    app.add_exception_handler(RequestValidationError, RequestValidationHandle)
    app.add_exception_handler(ResponseValidationError, ResponseValidationHandle)
    app.add_exception_handler(CustomException, CustomExceptionHandle)


def register_routers(app: FastAPI, prefix: str = "/api"):
    app.include_router(api_router, prefix=prefix)


async def init_superuser():
    user = await user_controller.model.exists()
    if not user:
        await user_controller.create_user(
            UserCreate(
                username="admin",
                email="admin@admin.com",
                password="123456",
                is_active=True,
                is_superuser=True,
            )
        )


async def init_menus():
    menus = await Menu.exists()
    if not menus:
        parent_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="系统管理",
            path="/system",
            order=1,
            parent_id=0,
            icon="carbon:gui-management",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/system/user",
        )
        children_menu = [
            Menu(
                menu_type=MenuType.MENU,
                name="用户管理",
                path="user",
                order=1,
                parent_id=parent_menu.id,
                icon="material-symbols:person-outline-rounded",
                is_hidden=False,
                component="/system/user",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="角色管理",
                path="role",
                order=2,
                parent_id=parent_menu.id,
                icon="carbon:user-role",
                is_hidden=False,
                component="/system/role",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="菜单管理",
                path="menu",
                order=3,
                parent_id=parent_menu.id,
                icon="material-symbols:list-alt-outline",
                is_hidden=False,
                component="/system/menu",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="API管理",
                path="api",
                order=4,
                parent_id=parent_menu.id,
                icon="ant-design:api-outlined",
                is_hidden=False,
                component="/system/api",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="部门管理",
                path="dept",
                order=5,
                parent_id=parent_menu.id,
                icon="mingcute:department-line",
                is_hidden=False,
                component="/system/dept",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="审计日志",
                path="auditlog",
                order=6,
                parent_id=parent_menu.id,
                icon="ph:clipboard-text-bold",
                is_hidden=False,
                component="/system/auditlog",
                keepalive=False,
            ),
        ]
        await Menu.bulk_create(children_menu)
        await Menu.create(
            menu_type=MenuType.MENU,
            name="一级菜单",
            path="/top-menu",
            order=2,
            parent_id=0,
            icon="material-symbols:featured-play-list-outline",
            is_hidden=False,
            component="/top-menu",
            keepalive=False,
            redirect="",
        )


async def init_apis():
    apis = await api_controller.model.exists()
    if not apis:
        await api_controller.refresh_api()


async def init_db():
    command = Command(tortoise_config=settings.TORTOISE_ORM)
    try:
        await command.init_db(safe=True)
    except FileExistsError:
        pass

    await command.init()
    try:
        await command.migrate()
    except AttributeError:
        logger.warning("unable to retrieve model history from database, model history will be created from scratch")
        shutil.rmtree("migrations")
        await command.init_db(safe=True)

    await command.upgrade(run_in_transaction=True)


async def init_roles():
    roles = await Role.exists()
    if not roles:
        admin_role = await Role.create(
            name="管理员",
            desc="管理员角色",
        )
        user_role = await Role.create(
            name="普通用户",
            desc="普通用户角色",
        )

        # 分配所有API给管理员角色
        all_apis = await Api.all()
        await admin_role.apis.add(*all_apis)
        # 分配所有菜单给管理员和普通用户
        all_menus = await Menu.all()
        await admin_role.menus.add(*all_menus)
        await user_role.menus.add(*all_menus)

        # 为普通用户分配基本API
        basic_apis = await Api.filter(Q(method__in=["GET"]) | Q(tags="基础模块"))
        await user_role.apis.add(*basic_apis)


async def init_food_data():
    """初始化食物识别模块数据。

    优先使用 deploy/integrated_food_mapping.json（如果存在）进行批量初始化。
    如果映射文件不存在，则回退到内置的 `app.scripts.init_food_data.init_food_data()`。
    该初始化仅在 `FoodCategory` 表为空时执行（即首次启动）。
    """
    try:
        from pathlib import Path
        from app.models.food import FoodCategory, Nutrition
        # 首先判断是否已存在食物类别
        count = await FoodCategory.all().count()
        if count > 0:
            logger.info(f"Food categories already initialized. Total: {count}")
            return

        # 尝试读取集成映射文件
        mapping_path = Path(settings.BASE_DIR) / "deploy" / "integrated_food_mapping.json"
        if mapping_path.exists():
            logger.info(f"Mapping file found at {mapping_path}, initializing from mapping...")
            try:
                import json
                with open(mapping_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                created = 0
                skipped = 0
                for key, item in data.items():
                    try:
                        existing = await FoodCategory.get_or_none(code=item.get('code'))
                        if existing:
                            skipped += 1
                            continue

                        category = await FoodCategory.create(
                            name=item.get('english_name') or item.get('name'),
                            chinese_name=item.get('chinese_name'),
                            code=item.get('code'),
                            food_type=item.get('food_type'),
                            description=item.get('description'),
                            image_url=item.get('image_url'),
                        )

                        nutrition_data = item.get('nutrition') or {}
                        await Nutrition.create(
                            food=category,
                            energy=nutrition_data.get('energy', 0.0),
                            protein=nutrition_data.get('protein', 0.0),
                            fat=nutrition_data.get('fat', 0.0),
                            carbohydrate=nutrition_data.get('carbohydrate', 0.0),
                            fiber=nutrition_data.get('fiber', 0.0),
                            sodium=nutrition_data.get('sodium', 0.0),
                        )

                        created += 1
                    except Exception as e:
                        logger.error(f"Failed to insert mapping item {key}: {str(e)}")
                        skipped += 1

                logger.info(f"Mapping initialization complete. Created: {created}, Skipped/Errors: {skipped}")
                return
            except Exception as e:
                logger.error(f"Failed to initialize from mapping file: {str(e)}")

        # 回退到内置默认初始化脚本
        try:
            from app.scripts.init_food_data import init_food_data as _init_default_food
            logger.info("Initializing default food data...")
            result = await _init_default_food()
            logger.info(f"Food data initialization complete. Created: {result.get('created')}, Skipped: {result.get('skipped')}")
        except Exception as e:
            logger.error(f"Failed to run default food data initializer: {str(e)}")

    except Exception as e:
        logger.error(f"Failed to initialize food data: {str(e)}")


def init_yolo_model():
    """在应用启动时初始化 YOLO 模型"""
    try:
        from app.services.yolo_service import yolo_service
        logger.info("Initializing YOLO model...")
        if yolo_service.load_model():
            logger.info("✓ YOLO model loaded successfully")
        else:
            logger.warning(f"✗ YOLO model failed to load: {yolo_service._load_error}")
    except Exception as e:
        logger.error(f"Failed to initialize YOLO model: {str(e)}")


async def init_data():
    await init_db()
    init_yolo_model()  # 初始化 YOLO 模型
    await init_superuser()
    await init_menus()
    await init_apis()
    await init_roles()
    await init_food_data()
