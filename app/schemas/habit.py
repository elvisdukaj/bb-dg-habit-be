from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Frequency(str, Enum):
    daily = "daily"
    weekly = "weekly"


class HabitCreate(BaseModel):
    title: str = Field(min_length=1)
    frequency: Frequency


class HabitUpdate(BaseModel):
    title: str = Field(min_length=1)
    frequency: Frequency


class HabitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    frequency: Frequency
    created_at: datetime
    updated_at: datetime
