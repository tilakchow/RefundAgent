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

from deepeval.metrics import StepEfficiencyMetric
from deepeval.integrations.langchain import CallbackHandler
from dotenv import load_dotenv

load_dotenv()

metrics = [StepEfficiencyMetric(threshold=0.8, model=eval_model, include_reason=True)]

for golden in dataset.evals_iterator(metrics=metrics):
    response = agent.invoke(
        {"messages": [{"role": "user", "content": golden.input}]},
        config={
            "configurable": {"thread_id": str(uuid4())},
            "callbacks": [CallbackHandler()]
        }
    )
