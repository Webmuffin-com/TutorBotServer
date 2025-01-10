from pydantic import BaseModel


# Define a Pydantic model for the request body
class PyMessage(BaseModel):
    text: str
    classSelection: str
    lesson: str
    actionPlan: str
