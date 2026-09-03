import json

import redis

from app.config import settings
from app.utils.logger import logger

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2
)


def set_cache(key: str, value, expire: int | None = None) -> bool:

    try:

        redis_client.set(key, json.dumps(value), ex=expire)

        return True

    except Exception as error:

        logger.error(f"Redis SET Error: {str(error)}")

        return False


def get_cache(key: str):

    try:

        value = redis_client.get(key)

        return json.loads(value) if value else None

    except Exception as error:

        logger.error(f"Redis GET Error: {str(error)}")

        return None


def delete_cache(key: str) -> bool:

    try:

        redis_client.delete(key)

        return True

    except Exception as error:

        logger.error(f"Redis DELETE Error: {str(error)}")

        return False