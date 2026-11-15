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

from deepeval.metrics import GEval
from deepeval.integrations.langchain import CallbackHandler
from deepeval.test_case import LLMTestCase, SingleTurnParams
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

    test_case = LLMTestCase(
        input=golden.input,
        actual_output=actual_output,
        expected_output=golden.expected_output,
    )

    test_cases.append(test_case)

answer_correctness_metric = GEval(
    name="Answer Correctness",
    evaluation_params=[
        SingleTurnParams.INPUT,
        SingleTurnParams.ACTUAL_OUTPUT,
        SingleTurnParams.EXPECTED_OUTPUT,
    ],
    evaluation_steps=[
        "Check that the actual output and expected output have the same "
        "logical conclusion about the user's request.",
    ],
    threshold=0.8,
    model=eval_model,
    verbose_mode=True,
)

evaluate(test_cases=test_cases, metrics=[answer_correctness_metric])
