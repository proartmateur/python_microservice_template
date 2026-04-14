"""
Diagnóstico de conectividad a SQL Server via aioodbc.
Uso:
    python tests/diag_ms_connect.py
"""
import asyncio

import aioodbc
import pyodbc

from src.config import get_settings

# Drivers de SQL Server en orden de preferencia (del más moderno al más antiguo)
_PREFERRED_DRIVERS = [
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 13 for SQL Server",
    "SQL Server Native Client 11.0",
    "SQL Server",
]


def _resolve_driver(preferred: str) -> str:
    """Devuelve el driver a usar: el del .env si está disponible, si no el mejor instalado."""
    available = pyodbc.drivers()
    print(f"🔎 Drivers ODBC disponibles: {available}")

    if preferred in available:
        return preferred

    print(f"⚠️  Driver '{preferred}' no encontrado. Buscando alternativa...")
    for driver in _PREFERRED_DRIVERS:
        if driver in available:
            print(f"   ↳ Usando driver alternativo: '{driver}'")
            return driver

    raise RuntimeError(
        f"No se encontró ningún driver ODBC para SQL Server. "
        f"Disponibles: {available}\n"
        f"Descarga el driver en: https://aka.ms/downloadmsodbcsql"
    )


async def main() -> None:
    s = get_settings()
    driver = _resolve_driver(s.DB_DRIVER)

    dsn = (
        f"DRIVER={{{driver}}};"
        f"SERVER={s.MS_HOST},{s.MS_PORT};"
        f"DATABASE={s.MS_DB};"
        f"UID={s.MS_USER};"
        f"PWD={s.MS_PASSWORD};"
        f"TrustServerCertificate=yes;"
    )

    print(f"\n🔌 Intentando conectar a SQL Server...")
    print(f"   host={s.MS_HOST}  port={s.MS_PORT}  db={s.MS_DB}  user={s.MS_USER}")
    print(f"   driver={driver}")

    async with await aioodbc.connect(dsn=dsn) as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT @@VERSION")
            row = await cur.fetchone()
            print(f"\n✅ Conexión exitosa!")
            print(f"   SQL Server: {row[0][:100]}...")


if __name__ == "__main__":
    asyncio.run(main())
