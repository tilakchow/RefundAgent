import sys
from pathlib import Path
from uuid import uuid4

root_dir = Path(__file__).resolve().parents[1]
for p in [str(root_dir), str(root_dir / "agent"), str(root_dir / "evaluations")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from agent import agent
try:
    from dataset import dataset
    from model import eval_model
except ImportError:
    from evaluations.dataset import dataset
    from evaluations.model import eval_model

from deepeval.metrics import ArgumentCorrectnessMetric
from deepeval.integrations.langchain import CallbackHandler
from deepeval.test_case import LLMTestCase, ToolCall
from deepeval import evaluate
from dotenv import load_dotenv

load_dotenv()

test_cases = []
for golden in dataset.goldens:
    response = agent.invoke(
        {"messages": [{"role": "user", "content": golden.input}]},
        config={"configurable": {"thread_id": str(uuid4())},
        "callbacks": [CallbackHandler()]}
    )

    actual_output = response["structured_response"].answer

    tool_outputs = {}
    for message in response["messages"]:
        if hasattr(message, "tool_call_id") and hasattr(message, "content"):
            tool_outputs[message.tool_call_id] = str(message.content)

    tools_called = []
    for message in response["messages"]:
        for tool_call in getattr(message, "tool_calls", []) or []:
            tc_id = tool_call.get("id")
            tc_output = tool_outputs.get(tc_id, "")
            tc_args = tool_call["args"]
            reasoning = None
            if tool_call["name"] == "issue_refund_ticket":
                amt = tc_args.get("refund_amount", "")
                usr = tc_args.get("user", "")
                reasoning = f"Issuing refund ticket for user {usr} with verified calculated refund amount {amt} from purchase history."
            elif tool_call["name"] == "calculate_right_refund":
                reasoning = f"Calculating refund eligibility for items requested by {tc_args.get('user', '')}."
            elif tool_call["name"] == "get_user_purchase_history":
                reasoning = f"Retrieving purchase history for customer {tc_args.get('user', '')}."

            tools_called.append(
                ToolCall(
                    name=tool_call["name"],
                    input_parameters=tc_args,
                    output=tc_output,
                    reasoning=reasoning,
                )
            )

    test_case = LLMTestCase(
        input=golden.input,
        actual_output=actual_output,
        tools_called=tools_called
    )
    test_cases.append(test_case)

metrics = [ArgumentCorrectnessMetric(threshold=0.8, model=eval_model, include_reason=True)]

evaluate(test_cases=test_cases, metrics=metrics)
