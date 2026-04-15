from __future__ import annotations

from typing import Any, Dict, List, Optional

from .storage import BaseStorage


class StateManager:
    """
    FSM state boshqaruvchi.
    ctx.state orqali ishlatiladi — to'g'ridan-to'g'ri ishlatilmaydi.

    await ctx.state.set("waiting_name")
    await ctx.state.get()
    await ctx.state.finish()
    await ctx.state.update(name="Ali")
    data = await ctx.state.get_data()
    """

    def __init__(self, storage: BaseStorage, user_id: int):
        self._storage = storage
        self._user_id = user_id

    async def set(self, state: str) -> None:
        await self._storage.set_state(self._user_id, state)

    async def get(self) -> Optional[str]:
        return await self._storage.get_state(self._user_id)

    async def finish(self) -> None:
        await self._storage.clear(self._user_id)

    async def update(self, **kwargs: Any) -> None:
        await self._storage.update_data(self._user_id, kwargs)

    async def get_data(self) -> Dict[str, Any]:
        return await self._storage.get_data(self._user_id)

    async def set_data(self, **kwargs: Any) -> None:
        """Oldingi datani o'chirib, yangi data saqlaydi."""
        await self._storage.clear(self._user_id)
        current = await self._storage.get_state(self._user_id)
        if current:
            await self._storage.set_state(self._user_id, current)
        await self._storage.update_data(self._user_id, kwargs)


# ─────────────────────────────────────────
# State Groups — aiogramdan ustun
# ─────────────────────────────────────────
class State:
    """
    StatesGroup ichida ishlatiladi.

    class Form(StatesGroup):
        name = State()   →  str(Form.name) == "Form:name"
    """

    def __init__(self):
        self._name: Optional[str] = None

    def __str__(self) -> str:
        return self._name or ""

    def __repr__(self) -> str:
        return f"State({self._name!r})"

    def __eq__(self, other) -> bool:
        if isinstance(other, State):
            return self._name == other._name
        if isinstance(other, str):
            return self._name == other
        return False

    def __hash__(self) -> int:
        return hash(self._name)
    
class StateGroupMeta(type):
    """
    StatesGroup uchun metaclass.
    Har bir class attributeni to'liq nom bilan almashtiradi.

    class Form(StatesGroup):
        name = State()       → "Form:name"
        age  = State()       → "Form:age"
        city = State()       → "Form:city"
    """

    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        states = {}
        for key, value in namespace.items():
            if isinstance(value, State):
                full_name = f"{name}:{key}"
                value._name = full_name
                states[key] = value
        namespace["_states"] = states
        return super().__new__(mcs, name, bases, namespace)


class StatesGroup(metaclass=StateGroupMeta):
    """
    State guruhlarini yaratish uchun:

    class Registration(StatesGroup):
        name = State()
        phone = State()
        confirm = State()

    # Ishlatish:
    await ctx.state.set(Registration.name)
    @bot.on.message.state(Registration.name)
    """

    _states: Dict[str, "State"] = {}

    @classmethod
    def all(cls) -> List[str]:
        """Guruhning barcha state nomlarini qaytaradi."""
        return [s._name for s in cls._states.values()]


