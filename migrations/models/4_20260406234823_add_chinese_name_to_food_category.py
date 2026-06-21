from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "food_category" ADD "chinese_name" VARCHAR(100)   /* 食物中文名称 */;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "food_category" DROP COLUMN "chinese_name";"""
