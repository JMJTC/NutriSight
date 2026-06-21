from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return ""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return ""
