# app/utils/rate_limit.py

from fastapi import HTTPException, Request, status

from app.config import settings
from app.utils.redis_cache import redis_client
from app.utils.logger import logger


def rate_limit(max_requests: int = None, window_seconds: int = None):

    max_requests = max_requests or settings.RATE_LIMIT_MAX_REQUESTS
    window_seconds = window_seconds or settings.RATE_LIMIT_WINDOW_SECONDS

    def dependency(request: Request):

        try:

            client_ip = request.client.host

            key = f"rate_limit:{request.url.path}:{client_ip}"

            current_count = redis_client.get(key)

            if current_count is None:

                redis_client.set(key, 1, ex=window_seconds)

            elif int(current_count) >= max_requests:

                logger.warning(f"Rate limit exceeded : {client_ip} on {request.url.path}")

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later."
                )

            else:

                redis_client.incr(key)

        except HTTPException:

            raise

        except Exception as error:

            logger.error(f"Rate limit check failed, allowing request through : {str(error)}")

    return dependency