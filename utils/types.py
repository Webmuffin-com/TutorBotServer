from pydantic import BaseModel
from typing import Optional


class PyMessage(BaseModel):
    text: str
    classSelection: str
    lesson: str
    actionPlan: str
    accessKey: str
    userTimestamp: Optional[str] = None  # ISO timestamp from client
