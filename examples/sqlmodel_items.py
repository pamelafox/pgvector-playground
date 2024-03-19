import os

from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column
from sqlmodel import Field, Session, SQLModel, create_engine, func, select


class Item(SQLModel, table=True):
    id: int = Field(primary_key=True, sa_column_kwargs={"autoincrement": True})
    embedding: list[float] = Field(sa_column=Column(Vector(3)))


# Connect to the database
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
    DATABASE_URI += f"?sslmode={POSTGRES_SSL}"

engine = create_engine(DATABASE_URI, echo=False)

SQLModel.metadata.drop_all(engine)
SQLModel.metadata.create_all(engine)

with Session(engine) as session:
    session.add_all(
        [
            Item(embedding=[1, 2, 3]),
            Item(embedding=[-1, 1, 3]),
            Item(embedding=[0, -1, -2]),
        ]
    )

    # Find 2 closest vectors to [3, 1, 2]
    closest_items = session.exec(select(Item).order_by(Item.embedding.l2_distance([3, 1, 2])).limit(2))
    for item in closest_items:
        print(item.embedding)

    # Calculate distance between [3, 1, 2] and the first vector
    distance = session.exec(select(Item.embedding.l2_distance([3, 1, 2]))).first()
    print(distance)

    # Find vectors within distance 5 from [3, 1, 2]
    close_enough_items = session.exec(select(Item).filter(Item.embedding.l2_distance([3, 1, 2]) < 5))
    for item in close_enough_items:
        print(item.embedding)

    # Calculate average of all vectors
    avg_embedding = session.exec(select(func.avg(Item.embedding))).first()
    print(avg_embedding)
