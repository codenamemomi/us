import asyncio
from collections import defaultdict
import json
import time
from uuid import UUID


class Hub:
    def __init__(self) -> None:
        self.subs: dict[str, set[asyncio.Queue]] = defaultdict(set)
        self.last_seen: dict[str, float] = {}

    async def publish(self, user_id: str | UUID | None, event: dict) -> None:
        if not user_id:
            return
        key = str(user_id)
        queues = list(self.subs.get(key, []))
        for q in queues:
            q.put_nowait(event)

    def is_online(self, user_id: str | UUID | None) -> bool:
        if not user_id:
            return False
        key = str(user_id)
        if len(self.subs.get(key, set())) > 0:
            return True
        last = self.last_seen.get(key)
        if last is not None and (time.time() - last) < 4.0:
            return True
        return False


hub = Hub()

