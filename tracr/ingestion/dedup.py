import hashlib
import math
import struct

import redis.asyncio as aioredis

from tracr.config import settings


class BloomFilter:
    """Redis-backed bloom filter for URL deduplication."""

    def __init__(self, name: str = "tracr:dedup:bloom"):
        self.name = name
        self.size = 10_000_000
        self.hash_count = self._optimal_hash_count(10_000_000, 0.001)

    @staticmethod
    def _optimal_hash_count(size: int, fp_rate: float) -> int:
        return max(1, round((size / 10_000_000) * math.log(1 / fp_rate)))

    def _get_client(self) -> aioredis.Redis:
        return aioredis.from_url(settings.REDIS_URL)

    def _positions(self, value: str) -> list[int]:
        positions = []
        for i in range(self.hash_count):
            digest = hashlib.sha256(f"{i}:{value}".encode()).digest()
            position = struct.unpack(">Q", digest[:8])[0] % self.size
            positions.append(position)
        return positions

    async def exists(self, url_hash: str) -> bool:
        client = self._get_client()
        try:
            pipe = client.pipeline()
            for pos in self._positions(url_hash):
                pipe.getbit(self.name, pos)
            results = await pipe.execute()
            return all(results)
        finally:
            await client.aclose()

    async def add(self, url_hash: str) -> None:
        client = self._get_client()
        try:
            pipe = client.pipeline()
            for pos in self._positions(url_hash):
                pipe.setbit(self.name, pos, 1)
            await pipe.execute()
        finally:
            await client.aclose()


bloom = BloomFilter()
