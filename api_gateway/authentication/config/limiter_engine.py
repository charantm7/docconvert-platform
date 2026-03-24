from redis import Redis
import time

redis_client = Redis(host="redis", port=6379, decode_responses=True)


class TokenBucketEngine:

    def __init__(self, redis, script):
        self.redis = redis
        self.script = script

    async def allow(self, key: str, capacity: int, refill_rate: float):
        now = time.time()

        result = await self.redis.evalsha(
            self.script,
            1,
            key,
            capacity,
            refill_rate,
            now
        )

        return result == 1
