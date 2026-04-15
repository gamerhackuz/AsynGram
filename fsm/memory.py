from __future__ import annotations

from typing import Any, Dict, Optional

from .storage import BaseStorage


class MemoryStorage(BaseStorage):
    """
    Tezkor in-memory storage.
    Bot o'chsa state yo'qoladi — development uchun ideal.

    bot = Bot("TOKEN", storage=MemoryStorage())
    """

    def __init__(self):
        self._states: Dict[int, str] = {}
        self._data: Dict[int, Dict[str, Any]] = {}

    async def get_state(self, user_id: int) -> Optional[str]:
        return self._states.get(user_id)

    async def set_state(self, user_id: int, state: str) -> None:
        self._states[user_id] = state

    async def get_data(self, user_id: int) -> Dict[str, Any]:
        return dict(self._data.get(user_id, {}))

    async def update_data(self, user_id: int, data: Dict[str, Any]) -> None:
        if user_id not in self._data:
            self._data[user_id] = {}
        self._data[user_id].update(data)

    async def clear(self, user_id: int) -> None:
        self._states.pop(user_id, None)
        self._data.pop(user_id, None)

    def __repr__(self) -> str:
        return f"MemoryStorage(users={len(self._states)})"