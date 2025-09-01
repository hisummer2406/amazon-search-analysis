from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List


class ChunkStartRequest(BaseModel):
    filename: str = Field(..., description="文件名")
    data_type: str = Field(..., description="文件类型")


class Part(BaseModel):
    partNumber: int = Field(..., description="分块编号")


class FinishChunkRequest(BaseModel):
    uploadId: str = Field(..., description="startChunkApi 返回的")
    key: str = Field(..., description="startChunkApi 返回的")
    filename: str = Field(..., description="文件名")
    partList: List[Part] = Field(..., description="每个成员为 分块编号和分块 eTag 信息。")
