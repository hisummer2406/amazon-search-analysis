import logging
from typing import Any, Dict

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/login")
async def login() -> Dict[str, Any]:
    pass
