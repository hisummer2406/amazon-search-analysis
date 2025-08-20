import logging

from fastapi import APIRouter
from typing import Dict , Any

from fastapi_amis_admin.amis import Page

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/search")
async def search_data()->Dict[str , Any]:
    pass

# 格式数据
def _format_search_data(item)->Dict[str , Any]:
    pass
