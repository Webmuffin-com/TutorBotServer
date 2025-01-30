from pydantic import BaseModel


class PyMessage(BaseModel):
    text: str
    classSelection: str
    lesson: str
    actionPlan: str
    accessKey: str
