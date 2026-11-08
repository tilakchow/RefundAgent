from pydantic import BaseModel, Field 

class Answer(BaseModel):
    answer : str = Field(description="the answer that is needed for the user question")
    conversation: bool = Field(description="")
