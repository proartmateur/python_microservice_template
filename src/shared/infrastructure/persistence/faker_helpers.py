"""Utilidades para adaptadores de persistencia faker.

Mapea tipos Python básicos a generadores de Faker para sembrar entidades
sintéticas en modo desarrollo. Faker se restringe a esta capa de infraestructura
y nunca se usa en dominio ni casos de uso.
"""

from __future__ import annotations

from typing import Any

from faker import Faker

_faker = Faker()


def fake_value(prop_type: str, *, seen: set[Any] | None = None) -> Any:
    """Genera un valor sintético según el tipo declarado de la propiedad.

    Args:
        prop_type: nombre del tipo Python (str, int, float, bool, datetime, UUID).
        seen: conjunto de valores ya usados para forzar unicidad cuando aplique
            (p. ej. emails únicos). Opcional.
    """
    if prop_type == "str":
        if seen is not None:
            while True:
                value = _faker.unique.user_name()
                if value not in seen:
                    seen.add(value)
                    return value
        return _faker.user_name()
    if prop_type == "int":
        return _faker.random_int(min=1, max=999999)
    if prop_type == "float":
        return round(_faker.pyfloat(left_digits=4, right_digits=2), 2)
    if prop_type == "bool":
        return _faker.boolean()
    if prop_type == "datetime":
        return _faker.date_time_this_year()
    if prop_type == "UUID":
        return _faker.uuid4(cast_to=None)
    # Fallback: string genérico.
    return _faker.word()