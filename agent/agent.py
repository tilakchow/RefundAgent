from uuid import uuid4
from dotenv import load_dotenv
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import HumanMessage
from deepeval.tracing import observe

from models import model
from tools import calculate_right_refund, get_user_purchase_history, issue_refund_ticket
from prompts import agent_system_prompt
from objects import Answer

load_dotenv()

agent = create_agent(
    model=model,
    system_prompt=agent_system_prompt,
    tools=[get_user_purchase_history, calculate_right_refund, issue_refund_ticket],
    response_format=Answer,
    checkpointer=InMemorySaver()
)

@observe(type="agent")
def invoke_agent(user_input: str, thread_id: str = None, callbacks=None):
    """Wrapper function to invoke the agent with full trace observation."""
    tid = thread_id or str(uuid4())
    config = {"configurable": {"thread_id": tid}}
    if callbacks:
        config["callbacks"] = callbacks
    return agent.invoke(
        {"messages": [{"role": "user", "content": user_input}]},
        config=config
    )

def run_conversation():
    config = {"configurable": {"thread_id": str(uuid4())}}
    text = "I would like to request a refund"
    print(text)
    
    question = HumanMessage(content=text)
    conversation = True

    while conversation:
        response = agent.invoke({"messages": question}, config=config)
        structured_response = response["structured_response"]
        print(structured_response.answer)
        conversation = structured_response.conversation

        if conversation:
            user_input = input("reply: \n")
            question = HumanMessage(content=user_input)

    print("the job is done!")

if __name__ == "__main__":
    run_conversation()
