from __future__ import annotations

import logging
from typing import Any, Callable, Optional, Type

logger = logging.getLogger("telegrampy.contrib.database")


class DatabaseMiddleware:
    """
    SQLAlchemy async session ni har bir handlerga inject qiladi.

    bot.provide(db=DatabaseMiddleware(engine))

    @bot.on.message.command("start")
    async def handler(ctx, db):
        user = await db.get(User, ctx.user.id)
    """

    def __init__(self, engine: Any, session_factory: Optional[Callable] = None):
        self._engine = engine
        self._session_factory = session_factory or self._make_factory(engine)

    def _make_factory(self, engine: Any) -> Callable:
        try:
            from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
            return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        except ImportError:
            raise ImportError("SQLAlchemy kerak: pip install sqlalchemy[asyncio]")

    async def __call__(self) -> Any:
        """
        Factory sifatida ishlaydi — har chaqiriqda yangi session.
        bot.provide(db=db_middleware) deb qo'shiladi.
        """
        async with self._session_factory() as session:
            return session


class BaseRepository:
    """
    Asosiy repository klass.
    Har bir model uchun shu klassdan meros olinadi.

    class UserRepo(BaseRepository):
        model = User

        async def get_by_telegram_id(self, tg_id: int):
            return await self.get_by(telegram_id=tg_id)
    """

    model: Any = None

    def __init__(self, session: Any):
        self.session = session

    async def get(self, id: Any) -> Optional[Any]:
        return await self.session.get(self.model, id)

    async def get_by(self, **kwargs) -> Optional[Any]:
        try:
            from sqlalchemy import select
            stmt = select(self.model).filter_by(**kwargs)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except ImportError:
            raise ImportError("SQLAlchemy kerak: pip install sqlalchemy[asyncio]")

    async def get_all(self, **kwargs) -> list:
        try:
            from sqlalchemy import select
            stmt = select(self.model).filter_by(**kwargs)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except ImportError:
            raise ImportError("SQLAlchemy kerak: pip install sqlalchemy[asyncio]")

    async def create(self, **kwargs) -> Any:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: Any, **kwargs) -> Any:
        for key, value in kwargs.items():
            setattr(obj, key, value)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: Any) -> None:
        await self.session.delete(obj)
        await self.session.commit()

    async def get_or_create(self, defaults: dict = None, **kwargs) -> tuple[Any, bool]:
        """
        Topsa qaytaradi, bo'lmasa yaratadi.
        (obj, created) tuple qaytaradi.
        """
        obj = await self.get_by(**kwargs)
        if obj:
            return obj, False
        data = {**kwargs, **(defaults or {})}
        obj = await self.create(**data)
        return obj, True