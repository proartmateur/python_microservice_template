from typing import Annotated

from fastapi import APIRouter, Depends

# gencli:router-imports


router = APIRouter(prefix="/<snake_name>s", tags=["<ent>s"])

# gencli:routes
