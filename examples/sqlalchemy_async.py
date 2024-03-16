from __future__ import annotations

import asyncio
import os

from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from pgvector.sqlalchemy import Vector
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Define the models
class Base(DeclarativeBase):
    pass


class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)
    embedding = mapped_column(Vector(3))


async def insert_objects(async_session: async_sessionmaker[AsyncSession]) -> None:
    async with async_session() as session:
        async with session.begin():
            session.add_all(
                [
                    Item(embedding=[1, 2, 3]),
                    Item(embedding=[-1, 1, 3]),
                    Item(embedding=[0, -1, -2]),
                ]
            )


async def select_and_update_objects(
    async_session: async_sessionmaker[AsyncSession],
) -> None:
    async with async_session() as session:
        # Find 2 closest vectors to [3, 1, 2]
        closest = await session.scalars(select(Item).order_by(Item.embedding.l2_distance([3, 1, 2])).limit(2))
        for item in closest:
            print(item.embedding)

        # Calculate distance between [3, 1, 2] and the first vector
        distance = (await session.scalars(select(Item.embedding.l2_distance([3, 1, 2])))).first()
        print(distance)

        # Find vectors within distance 5 from [3, 1, 2]
        close_enough = await session.scalars(select(Item).filter(Item.embedding.l2_distance([3, 1, 2]) < 5))
        for item in close_enough:
            print(item.embedding)

        # Calculate average of all vectors
        avg_embedding = (await session.scalars(select(func.avg(Item.embedding)))).first()
        print(avg_embedding)


async def async_main() -> None:
    # Azure hosted, refresh token that becomes password.
    azure_credential = DefaultAzureCredential()
    # Get token for Azure Database for PostgreSQL
    print("Get password token.")
    token = azure_credential.get_token("https://ossrdbms-aad.database.windows.net/.default")
    # Connect to the database based on environment variables
    load_dotenv(".env", override=True)
    DBUSER = os.environ["DBUSER"]
    DBPASS = token.token
    DBHOST = os.environ["DBHOST"]
    DBNAME = os.environ["DBNAME"]
    DATABASE_URI = f"postgresql+asyncpg://{DBUSER}:{DBPASS}@{DBHOST}/{DBNAME}"
    # Use SSL if not connecting to localhost
    if DBHOST != "localhost":
        DATABASE_URI += "?ssl=require"

    engine = create_async_engine(
        DATABASE_URI,
        echo=False,
    )

    # async_sessionmaker: a factory for new AsyncSession objects.
    # expire_on_commit - don't expire objects after transaction commit
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        # run sql create extension vector
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    await insert_objects(async_session)
    await select_and_update_objects(async_session)

    # for AsyncEngine created in function scope, close and
    # clean-up pooled connections
    await engine.dispose()


asyncio.run(async_main())
