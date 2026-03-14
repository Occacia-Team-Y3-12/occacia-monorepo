"""
app/schemas/persona_schema.py
"""
from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator

class PersonaCreate(BaseModel):
    name:              str
    relationship:      Optional[str]        = None
    birthday:          Optional[datetime]   = None
    personality:       Optional[str]        = None
    preferences_json:  Optional[Any]        = None 
    food_preferences:  Optional[List[str]]  = None
    color_preferences: Optional[List[str]]  = None
    music_preferences: Optional[List[str]]  = None
    personality_tags:  Optional[List[str]]  = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name must not be empty")
        return v.strip()

class PersonaUpdate(BaseModel):
    name:              Optional[str]        = None
    relationship:      Optional[str]        = None
    birthday:          Optional[datetime]   = None
    personality:       Optional[str]        = None
    preferences_json:  Optional[Any]        = None
    food_preferences:  Optional[List[str]]  = None
    color_preferences: Optional[List[str]]  = None
    music_preferences: Optional[List[str]]  = None
    personality_tags:  Optional[List[str]]  = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("name must not be empty or whitespace")
        return v.strip() if v is not None else v

class PersonaResponse(BaseModel):
    id:                int
    persona_id:        str
    customer_id:       str
    name:              str
    relationship:      Optional[str]      = None
    birthday:          Optional[datetime] = None
    personality:       Optional[str]      = None
    preferences_json:  Optional[Any]      = None
    food_preferences:  List[str]          = []
    color_preferences: List[str]          = []
    music_preferences: List[str]          = []
    personality_tags:  List[str]          = []
    is_confirmed:      bool               = False
    confirmed_at:      Optional[datetime] = None
    created_at:        Optional[datetime] = None
    updated_at:        Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True) 

    # THE FIX: This intercepts 'None' or strings from the DB and turns them into safe lists for the test.
    @field_validator("food_preferences", "color_preferences", "music_preferences", "personality_tags", mode="before")
    @classmethod
    def coerce_to_list(cls, v):
        if v is None: return []
        if isinstance(v, str): return [s.strip() for s in v.split(",") if s.strip()]
        if isinstance(v, list): return v
        return list(v)

class PersonaListResponse(BaseModel):
    personas: List[PersonaResponse]
    total: int