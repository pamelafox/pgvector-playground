import asyncio
import os

import asyncpg
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from pgvector.asyncpg import register_vector


async def async_main():
    # Establish a connection to an existing database
    load_dotenv(".env", override=True)
    POSTGRES_HOST = os.environ["POSTGRES_HOST"]
    POSTGRES_USERNAME = os.environ["POSTGRES_USERNAME"]
    POSTGRES_DATABASE = os.environ["POSTGRES_DATABASE"]

    if POSTGRES_HOST.endswith(".database.azure.com"):
        print("Authenticating to Azure Database for PostgreSQL using Azure Identity...")
        azure_credential = DefaultAzureCredential()
        token = azure_credential.get_token("https://ossrdbms-aad.database.windows.net/.default")
        POSTGRES_PASSWORD = token.token
    else:
        POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]

    DATABASE_URI = f"postgresql://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DATABASE}"
    # Specify SSL mode if needed
    if POSTGRES_SSL := os.environ.get("POSTGRES_SSL"):
        DATABASE_URI += f"?ssl={POSTGRES_SSL}"

    conn = await asyncpg.connect(DATABASE_URI)

    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    await register_vector(conn)

    await conn.execute("DROP TABLE IF EXISTS items")
    await conn.execute("CREATE TABLE items (id bigserial PRIMARY KEY, embedding vector(3))")
    await conn.execute("CREATE INDEX ON items USING hnsw (embedding vector_l2_ops)")

    await conn.execute("INSERT INTO items (embedding) VALUES ($1)", [1, 2, 3])
    await conn.execute("INSERT INTO items (embedding) VALUES ($1)", [-1, 1, 3])
    await conn.execute("INSERT INTO items (embedding) VALUES ($1)", [0, -1, -2])

    # Find 2 closest vectors to [3, 1, 2]
    row = await conn.fetch("SELECT * FROM items ORDER BY embedding <-> $1 LIMIT 2", [3, 1, 2])
    for row in row:
        print(row["embedding"])

    # Calculate distance between [3, 1, 2] and the first vector
    row = await conn.fetch(
        "SELECT embedding <-> $1 AS distance FROM items ORDER BY embedding <-> $1 LIMIT 1", [3, 1, 2]
    )
    print(row[0]["distance"])

    # Find vectors within distance 5 from [3, 1, 2]
    row = await conn.fetch("SELECT * FROM items WHERE embedding <-> $1 < 5", [3, 1, 2])
    for row in row:
        print(row["embedding"])

    # Calculate average of all vectors
    row = await conn.fetch("SELECT avg(embedding) FROM items")
    print(row[0]["avg"])

    # Close the connection.
    await conn.close()


asyncio.run(async_main())
