from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from requests import Response

load_dotenv( )
model = init_chat_model(model="openai/gpt-oss-120b" ,model_provider = "groq")

##print(Response.content)

