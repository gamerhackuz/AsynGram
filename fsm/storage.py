from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseStorage(ABC):
    """
    FSM storage interfeysi.
    MemoryStorage, RedisStorage shu klassdan meros oladi.
    """

    @abstractmethod
    async def get_state(self, user_id: int) -> Optional[str]:
        ...

    @abstractmethod
    async def set_state(self, user_id: int, state: str) -> None:
        ...

    @abstractmethod
    async def get_data(self, user_id: int) -> Dict[str, Any]:
        ...

    @abstractmethod
    async def update_data(self, user_id: int, data: Dict[str, Any]) -> None:
        ...

    @abstractmethod
    async def clear(self, user_id: int) -> None:
        """State va datani tozalaydi (finish)."""
        ...

    async def close(self) -> None:
        """Storage ulanishini yopadi (Redis uchun)."""
        pass