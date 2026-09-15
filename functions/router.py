import json
from redis_client import redis_client
from datetime import datetime, timezone
import secrets
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from auth.database import get_async_session, User
from auth.manager import current_user, current_user_optional
from models.models import link
from .schemas import LinkCreate, LinkUpdate, LinkStats


router = APIRouter(
    prefix="/links",
    tags=["Links"],
)

#Создание ссылки
@router.post("/shorten")
async def create_link(
    data: LinkCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User | None = Depends(current_user_optional),
):
    if data.custom_alias:
        short_code = data.custom_alias

        result = await session.execute(
            select(link).where(link.c.short_code == short_code)
        )

        if result.first() is not None:
            raise HTTPException(
                status_code=400,
                detail="Такой alias уже существует",
            )

    else:
        while True:
            short_code = secrets.token_urlsafe(6)

            result = await session.execute(
                select(link).where(link.c.short_code == short_code)
            )

            if result.first() is None:
                break

    await session.execute(
        insert(link).values(
            original_url=str(data.original_url),
            short_code=short_code,
            create_date=datetime.utcnow(),
            last_date=data.expires_at,
            clicks=0,
            user_id=user.id if user else None,
        )
    )

    await session.commit()

    return {
        "short_code": short_code,
        "short_url": f"/links/{short_code}",
        "original_url": str(data.original_url),
        "expires_at": data.expires_at,
    }


#Поиск
@router.get("/search")
async def search_link(
    original_url: str,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(link).where(link.c.original_url == original_url)
    )

    return result.mappings().all()

#Статистика
@router.get("/{short_code}/stats", response_model=LinkStats)
async def get_stats(
    short_code: str,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(link).where(link.c.short_code == short_code)
    )

    link_data = result.first()

    if link_data is None:
        raise HTTPException(
            status_code=404,
            detail="Ссылка не найдена",
        )

    link_data = link_data._mapping

    return {
        "short_code": link_data["short_code"],
        "original_url": link_data["original_url"],
        "create_date": link_data["create_date"],
        "clicks": link_data["clicks"],
        "last_used_date": link_data["last_used_date"],
    }



#Изменение
@router.put("/{short_code}")
async def update_link(
    short_code: str,
    data: LinkUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
):
    result = await session.execute(
        select(link).where(
            link.c.short_code == short_code,
            link.c.user_id == user.id,
        )
    )

    if result.first() is None:
        raise HTTPException(
            status_code=404,
            detail="Ссылка не найдена",
        )

    await session.execute(
        update(link)
        .where(
            link.c.short_code == short_code,
            link.c.user_id == user.id,
        )
        .values(
            original_url=str(data.original_url)
        )
    )

    await session.commit()

    await redis_client.delete(f"link:{short_code}")

    return {
        "short_code": short_code,
        "original_url": str(data.original_url),
    }


#Удаление
@router.delete("/{short_code}")
async def delete_link(
    short_code: str,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
):
    result = await session.execute(
        select(link).where(
            link.c.short_code == short_code,
            link.c.user_id == user.id,
        )
    )

    if result.first() is None:
        raise HTTPException(
            status_code=404,
            detail="Ссылка не найдена",
        )

    await session.execute(
        delete(link).where(
            link.c.short_code == short_code,
            link.c.user_id == user.id,
        )
    )

    await session.commit()

    await redis_client.delete(f"link:{short_code}")

    return {
        "message": "Ссылка удалена"
    }


#Переход по ссылке
@router.get("/{short_code}")
async def redirect_link(
    short_code: str,
    session: AsyncSession = Depends(get_async_session),
):
    cache_key = f"link:{short_code}"
    cached = await redis_client.get(cache_key)

    if cached:
        link_data = json.loads(cached)

        if link_data["last_date"] is not None:
            last_date = datetime.fromisoformat(link_data["last_date"])

            if last_date <= datetime.now(timezone.utc):
                await redis_client.delete(cache_key)

                await session.execute(
                    delete(link).where(link.c.short_code == short_code)
                )
                await session.commit()

                raise HTTPException(
                    status_code=404,
                    detail="Срок действия ссылки истёк",
                )

        now = datetime.now(timezone.utc)

        await session.execute(
            update(link)
            .where(link.c.short_code == short_code)
            .values(
                clicks=link.c.clicks + 1,
                last_used_date=now,
            )
        )

        await session.commit()

        return RedirectResponse(
            url=link_data["original_url"],
            status_code=307,
        )

    result = await session.execute(
        select(link).where(link.c.short_code == short_code)
    )

    link_data = result.first()

    if link_data is None:
        raise HTTPException(
            status_code=404,
            detail="Ссылка не найдена",
        )

    link_data = link_data._mapping

    now = datetime.now(timezone.utc)

    if (
        link_data["last_date"] is not None
        and link_data["last_date"] <= now
    ):
        await session.execute(
            delete(link).where(link.c.short_code == short_code)
        )

        await session.commit()

        raise HTTPException(
            status_code=404,
            detail="Срок действия ссылки истёк",
        )
    
    await redis_client.set(
        cache_key,
        json.dumps({
            "original_url": link_data["original_url"],
            "last_date": (
                link_data["last_date"].isoformat()
                if link_data["last_date"] is not None
                else None
            ),
        }),
        ex=300,
    )

    await session.execute(
        update(link)
        .where(link.c.short_code == short_code)
        .values(
            clicks=link.c.clicks + 1,
            last_used_date=now,
        )
    )

    await session.commit()

    return RedirectResponse(
        url=link_data["original_url"],
        status_code=307,
    )