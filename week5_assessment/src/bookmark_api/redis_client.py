import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL= os.getenv("REDIS_URL", "dummy-url")
REDIS_PASSWORD= os.getenv("REDIS_PASSWORD", "dummy-password")
REDIS_PORT= int(os.getenv("REDIS_PORT", "1000"))
REDIS_USER= os.getenv("REDIS_USER", "dummy-user")
from redis import Redis


redis_client = Redis(
    host= REDIS_URL,
    port=REDIS_PORT,
    decode_responses=True,
    username=REDIS_USER,
    password=REDIS_PASSWORD,
)

def get_redis_client():
    return redis_client
