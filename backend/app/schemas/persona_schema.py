from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime

class PersonaCreate(BaseModel):
    name: str
    relationship: Optional[str] = None
    birthday: Optional[datetime] = None
    personality: Optional[str] = None
    preferences_json: Optional[Any] = None 

class PersonaResponse(BaseModel):
    persona_id: str
    name: str
    relationship: Optional[str] = None
    birthday: Optional[datetime] = None
    personality: Optional[str] = None
    preferences_json: Optional[Any] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PersonaListResponse(BaseModel):
    personas: List[PersonaResponse]
    total: int