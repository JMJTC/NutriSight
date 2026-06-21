from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ADD "api_key" TEXT   /* 用户AI API Key（加密存储） */;
        ALTER TABLE "user" ADD "ai_model" VARCHAR(100)   DEFAULT 'deepseek-chat' /* 用户选择的AI模型 */;
        ALTER TABLE "user" ADD "ai_base_url" VARCHAR(255)   /* 自定义AI API地址 */;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" DROP COLUMN "api_key";
        ALTER TABLE "user" DROP COLUMN "ai_model";
        ALTER TABLE "user" DROP COLUMN "ai_base_url";"""
