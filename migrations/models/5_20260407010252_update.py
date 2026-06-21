from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ADD "gender" INT   /* 性别 (1:男, 2:女, 3:其他) */;
        ALTER TABLE "user" ADD "weight_kg" VARCHAR(40)   /* 体重(kg) */;
        ALTER TABLE "user" ADD "age" INT   /* 年龄 */;
        ALTER TABLE "user" ADD "height_cm" INT   /* 身高(cm) */;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" DROP COLUMN "gender";
        ALTER TABLE "user" DROP COLUMN "weight_kg";
        ALTER TABLE "user" DROP COLUMN "age";
        ALTER TABLE "user" DROP COLUMN "height_cm";"""
