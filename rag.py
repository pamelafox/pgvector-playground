"""Simple RAG:

1. Get question from user
2. Use answer to search Postgres database
3. Format rows in an LLM-compatible format
4. Send question and formatted rows to LLM
"""

import os

import numpy as np
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference import EmbeddingsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
import psycopg2
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector

# Set up PostgreSQL database
load_dotenv(override=True)
DBUSER = os.environ["DBUSER"]
DBPASS = os.environ["DBPASS"]
DBHOST = os.environ["DBHOST"]
DBNAME = os.environ["DBNAME"]

conn = psycopg2.connect(database=DBNAME, user=DBUSER, password=DBPASS, host=DBHOST)
conn.autocommit = True
register_vector(conn)
cur = conn.cursor()

# Setup Azure AI variables
token = os.environ["GITHUB_TOKEN"]
endpoint = "https://models.inference.ai.azure.com"


# Get question from user
question = "videos sobre extensiones?"

# Convert question to an embedding
client = EmbeddingsClient(endpoint=endpoint, credential=AzureKeyCredential(token))

response = client.embed(
    input=["first phrase", "second phrase", "third phrase"], model="text-embedding-3-small", dimensions=256
)

embedding = response.data[0].embedding

# Search the database for the most similar embeddings
query = """
WITH semantic_search AS (
    SELECT id, RANK () OVER (ORDER BY embedding <=> %(embedding)s) AS rank
    FROM videos
    ORDER BY embedding <=> %(embedding)s
    LIMIT 20
),
keyword_search AS (
    SELECT id, RANK () OVER (ORDER BY ts_rank_cd(to_tsvector('english', description), query) DESC)
    FROM videos, phraseto_tsquery('english', %(query)s) query
    WHERE to_tsvector('english', description) @@ query
    ORDER BY ts_rank_cd(to_tsvector('english', description), query) DESC
    LIMIT 20
)
SELECT
    COALESCE(semantic_search.id, keyword_search.id) AS id,
    COALESCE(1.0 / (%(k)s + semantic_search.rank), 0.0) +
    COALESCE(1.0 / (%(k)s + keyword_search.rank), 0.0) AS score
FROM semantic_search
FULL OUTER JOIN keyword_search ON semantic_search.id = keyword_search.id
ORDER BY score DESC
LIMIT 5
"""
cur.execute(query, {"embedding": np.array(embedding), "query": question, "k": 60})

# Now fetch rows for each ID
rows = []
for row in cur.fetchall():
    cur.execute("SELECT id, title, description FROM videos WHERE id = %s", (row[0],))
    rows.append(cur.fetchone())

# query = """
#     SELECT title, description
#     FROM videos
#     ORDER BY embedding <=> %(embedding)s
#     LIMIT 20
# """
# cur.execute(query, {"embedding": np.array(embedding)})

# Do a full-text search of the database
# cur.execute("""
#     SELECT title, description, RANK () OVER (ORDER BY ts_rank_cd(to_tsvector('english', description), query) DESC)
#         FROM videos, plainto_tsquery('english', %s) query
#         WHERE to_tsvector('english', description) @@ query
#         ORDER BY ts_rank_cd(to_tsvector('english', description), query) DESC
#         LIMIT 20
#     """, (question,))
# cur.execute(
#     "SELECT * FROM videos WHERE to_tsvector(title || ' ' || description) @@ websearch_to_tsquery(%s)", (question,)
# )
# rows = cur.fetchall()

# Format rows in an LLM-compatible format
formatted_rows = ""
for row in rows:
    formatted_rows += f"## {row[1]}\n\n{row[2]}\n\n"
print(formatted_rows)

# Send question and formatted rows to LLM

client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(token),
)

response = client.complete(
    messages=[
        SystemMessage(
            content="You answer questions about VS Code videos. You must answer only according to the sources, which will be described in Markdown starting with ## Video Title "
        ),
        UserMessage(content=question + "\n\nSources:\n\n" + formatted_rows),
    ],
    model="meta-llama-3.1-405b-instruct",
    temperature=1.0,
    max_tokens=1000,
    top_p=1.0,
)

print("Answer:")
print(response.choices[0].message.content)
