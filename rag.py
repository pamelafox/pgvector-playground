import os

import numpy as np
from azure.ai.inference import EmbeddingsClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
import psycopg2
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv

# Set up GitHub models
endpoint = "https://models.inference.ai.azure.com"
model_name = "text-embedding-3-small"
token = os.environ["GITHUB_TOKEN"]

# Set up Postgres
load_dotenv(override=True)
DBUSER = os.environ["DBUSER"]
DBPASS = os.environ["DBPASS"]
DBHOST = os.environ["DBHOST"]
DBNAME = os.environ["DBNAME"]
# Use SSL if not connecting to localhost
DBSSL = "disable"
if DBHOST != "localhost":
    DBSSL = "require"

conn = psycopg2.connect(database=DBNAME, user=DBUSER, password=DBPASS, host=DBHOST, sslmode=DBSSL)
conn.autocommit = True
cur = conn.cursor()
register_vector(conn)
cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

# Get question from user
question = "how do i use postgres inside vs code?"

# Turn the question into an embedding
client = EmbeddingsClient(endpoint=endpoint, credential=AzureKeyCredential(token))
response = client.embed(input=question, model=model_name, dimensions=256)
embedding = np.array(response.data[0].embedding)

cur.execute(
    """
WITH semantic_search AS (
    SELECT id, RANK () OVER (ORDER BY embedding <=> %(embedding)s) AS rank
    FROM videos
    ORDER BY embedding <=> %(embedding)s
    LIMIT 20
),
keyword_search AS (
    SELECT id, RANK () OVER (ORDER BY ts_rank_cd(to_tsvector('english', title || ' ' || description), query) DESC)
    FROM videos, plainto_tsquery('english', %(query)s) query
    WHERE to_tsvector('english', title || ' ' || description) @@ query
    ORDER BY ts_rank_cd(to_tsvector('english', title || ' ' || description), query) DESC
    LIMIT 20
)
SELECT
    COALESCE(semantic_search.id, keyword_search.id) AS id,
    COALESCE(1.0 / (%(k)s + semantic_search.rank), 0.0) +
    COALESCE(1.0 / (%(k)s + keyword_search.rank), 0.0) AS score
FROM semantic_search
FULL OUTER JOIN keyword_search ON semantic_search.id = keyword_search.id
ORDER BY score DESC
LIMIT 20
""",
    {"query": question, "embedding": embedding, "k": 60},
)

results = cur.fetchall()

# Fetch the videos by ID
ids = [result[0] for result in results]
cur.execute("SELECT id, title, description FROM videos WHERE id = ANY(%s)", (ids,))
results = cur.fetchall()
for result in results:
    print(result[1])

# Format the results for the LLM
formatted_results = ""
for result in results:
    formatted_results += f"## {result[1]}\n\n{result[2]}\n"

client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(token),
)

response = client.complete(
    messages=[
        SystemMessage(
            content="You must answer user question according to sources. Say you dont know if you cant find answer in sources. Cite the title of each video inside square brackets. The title of each video which will be a markdown heading."
        ),
        UserMessage(content=question + "\n\nSources:\n\n" + formatted_results),
    ],
    model="gpt-4o",
    temperature=0.3,
    max_tokens=1000
)

print("Answer:\n\n")
print(response.choices[0].message.content)