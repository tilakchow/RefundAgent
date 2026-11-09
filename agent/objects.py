from operator import truediv
from pydantic import BaseModel, Field 

class Answer(BaseModel):
    answer : str = Field(description="the answer that is needed for the user question")
    conversation: bool = Field(description= "this is an indicator to know if the conversation" \
    "should still continue or not.if the agent has made the decision about the refund this should be false " \
    "if the conversation still need more talk then its true", default=True)

class PurchaseItem(BaseModel):
    name : str = Field(description="the name of the item that the user wants to purchase")
