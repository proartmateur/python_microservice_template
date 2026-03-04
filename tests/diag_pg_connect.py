import asyncio

import asyncpg

from src.config import get_settings


async def main() -> None:
    s = get_settings()
    ssl = None if s.PG_SSLMODE == "disable" else s.PG_SSLMODE

    print(f"host={s.PG_HOST} port={s.PG_PORT} db={s.PG_DB} sslmode={s.PG_SSLMODE}")

    conn = await asyncpg.connect(
        user=s.PG_USER,
        password=s.PG_PASSWORD,
        host=s.PG_HOST,
        port=s.PG_PORT,
        database=s.PG_DB,
        timeout=float(s.PG_CONNECT_TIMEOUT),
        ssl=ssl,
    )
    print("db_connect_ok")
    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

