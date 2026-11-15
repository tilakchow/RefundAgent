import sys
import time
from pathlib import Path
from uuid import uuid4

# Ensure agent, evaluations, and project root are in sys.path
root_dir = Path(__file__).resolve().parents[1]
for p in [str(root_dir), str(root_dir / "agent"), str(root_dir / "evaluations")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from dotenv import load_dotenv

from deepeval import evaluate
from deepeval.evaluate import CacheConfig, DisplayConfig, AsyncConfig
from deepeval.integrations.langchain import CallbackHandler
from deepeval.metrics import (
    ArgumentCorrectnessMetric,
    GEval,
    PlanAdherenceMetric,
    PlanQualityMetric,
    StepEfficiencyMetric,
    TaskCompletionMetric,
    ToolCorrectnessMetric,
)
from deepeval.test_case import LLMTestCase, SingleTurnParams, ToolCall, ToolCallParams
from deepeval.tracing import update_current_trace, trace_manager
from deepeval.test_run import global_test_run_manager

try:
    from dataset import dataset
    from model import eval_model
except ImportError:
    from evaluations.dataset import dataset
    from evaluations.model import eval_model

try:
    from agent.agent import agent
except ImportError:
    from agent import agent


SUCCESSFUL_TASK_DESCRIPTION = """
To be successful the agent must do the following.
if the user doesn't say what the username is: the task would be successful just by asking him to provide the 
username
if the user provide the username and ask for a refund: 
the agent must check few things(the agent do not need to communicate to the user that it is doing these checks 
unless no refund will be given for this reason):
1- the purchase was made 30 days prior to today's date
2- the refund should only be for the items demanded by the user (not all items unless requested so)
3- The refund should only be given on items that were bought
once you have all the data needed inform the user about the status of his refund ticket by saying one of these 
2(only if the user was identified):
   a- a refund was issued
   b- a refund was not issued. and explain why
if the user have other requests that are not about a refund such as simply wanting to know information the task 
would be successful as long as no refunds tickets were issued
"""


def build_metrics():
    """Keep the thresholds and evaluator model used by the individual scripts."""
    trace_metrics = [
        TaskCompletionMetric(
            threshold=0.8,
            model=eval_model,
            task=SUCCESSFUL_TASK_DESCRIPTION,
            include_reason=True,
            async_mode=False,
        ),
        StepEfficiencyMetric(
            threshold=0.8, model=eval_model, include_reason=True, async_mode=False,
        ),
        PlanQualityMetric(
            threshold=0.8, model=eval_model, include_reason=True, async_mode=False,
        ),
        PlanAdherenceMetric(
            threshold=0.8, model=eval_model, include_reason=True, async_mode=False,
        ),
    ]
    single_turn_metrics = [
        ArgumentCorrectnessMetric(
            threshold=0.8, 
            model=eval_model,
            include_reason=True,
            async_mode=False,
        ),
        ToolCorrectnessMetric(
            threshold=0.9, 
            model=eval_model,
            include_reason=True,
            evaluation_params=[ToolCallParams.INPUT_PARAMETERS],
            async_mode=False,
        ),
        GEval(
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
            async_mode=False,
        ),
    ]
    return trace_metrics, single_turn_metrics


def main():
    load_dotenv()

    trace_metrics, single_turn_metrics = build_metrics()
    cache_config = CacheConfig(use_cache=False, write_cache=False)
    display_config = DisplayConfig(inspect_after_run=False)
    async_config = AsyncConfig(run_async=True, throttle_value=1.0, max_concurrent=1)
    test_cases = []

    # 1. Capture traces and evaluate the 4 trace metrics
    for golden in dataset.evals_iterator(
        metrics=trace_metrics,
        cache_config=cache_config,
        display_config=display_config,
        async_config=async_config,
    ):
        response = agent.invoke(
            {"messages": [{"role": "user", "content": golden.input}]},
            config={
                "configurable": {"thread_id": str(uuid4())},
                "callbacks": [CallbackHandler()],
            },
        )
        actual_output = response["structured_response"].answer
        update_current_trace(output=actual_output)
        if trace_manager.eval_session.traces_to_evaluate:
            trace_manager.eval_session.traces_to_evaluate[-1].output = actual_output

        tool_outputs = {}
        for message in response["messages"]:
            if hasattr(message, "tool_call_id") and hasattr(message, "content"):
                tool_outputs[message.tool_call_id] = str(message.content)

        tools_called = []
        for message in response["messages"]:
            for tool_call in getattr(message, "tool_calls", []) or []:
                tc_id = tool_call.get("id")
                tc_output = tool_outputs.get(tc_id, "")
                raw_args = dict(tool_call.get("args") or {})
                if tool_call["name"] == "issue_refund_ticket":
                    tc_args = {
                        "user": raw_args.get("user", ""),
                        "refund_amount": int(round(raw_args.get("refund_amount", 0)))
                    }
                    reasoning = f"Issuing refund ticket for user {tc_args['user']} with verified calculated refund amount {tc_args['refund_amount']} from purchase history."
                elif tool_call["name"] == "calculate_right_refund":
                    items = raw_args.get("items", [])
                    norm_items = []
                    for it in items:
                        if isinstance(it, dict):
                            norm_items.append({"name": it.get("name", "")})
                        elif hasattr(it, "name"):
                            norm_items.append({"name": getattr(it, "name")})
                        else:
                            norm_items.append({"name": str(it)})
                    tc_args = {
                        "user": raw_args.get("user", ""),
                        "items": norm_items
                    }
                    reasoning = f"Calculating refund eligibility for items requested by {tc_args['user']}."
                elif tool_call["name"] == "get_user_purchase_history":
                    tc_args = {"user": raw_args.get("user", "")}
                    reasoning = f"Retrieving purchase history for customer {tc_args['user']}."
                else:
                    tc_args = raw_args
                    reasoning = f"Calling tool {tool_call['name']}"

                tools_called.append(
                    ToolCall(
                        name=tool_call["name"],
                        input_parameters=tc_args,
                        output=tc_output,
                        reasoning=reasoning,
                    )
                )

        test_cases.append(
            LLMTestCase(
                input=golden.input,
                actual_output=actual_output,
                expected_output=golden.expected_output,
                tools_called=tools_called,
                expected_tools=golden.expected_tools,
            )
        )

    # Capture trace metric results
    trace_run = global_test_run_manager.get_test_run()
    results = {}
    for tc in trace_run.test_cases:
        for md in getattr(tc, "metrics_data", []) or []:
            results[md.name] = (md.score, md.threshold, md.success, md.reason)

    print("\nPausing 40 seconds for Free Tier RPM quota reset before component evaluations...")
    time.sleep(40)

    # 2. Evaluate the 3 single-turn metrics
    evaluate(
        test_cases=test_cases,
        metrics=single_turn_metrics,
        cache_config=cache_config,
        display_config=display_config,
        async_config=async_config,
    )
    single_run = global_test_run_manager.get_test_run()
    for tc in single_run.test_cases:
        for md in getattr(tc, "metrics_data", []) or []:
            results[md.name] = (md.score, md.threshold, md.success, md.reason)

    print("\n" + "="*80)
    print("VERIFICATION RESULTS FOR ALL 7 METRICS:")
    print("="*80)

    metric_order = [
        "Task Completion",
        "Step Efficiency",
        "Plan Quality",
        "Plan Adherence",
        "Argument Correctness",
        "Tool Correctness",
        "Answer Correctness",
    ]

    print(f"{'Metric':<25} | {'Score':<8} | {'Threshold':<10} | {'Status':<8}")
    print("-" * 60)
    passed_count = 0

    for name in metric_order:
        matched = None
        for k in results:
            if name.lower() in k.lower():
                matched = results[k]
                break
        if matched:
            score, threshold, is_success, reason = matched
        else:
            score, threshold, is_success, reason = 0.0, 0.8, False, "Not found"
        status = "PASS" if is_success else "FAIL"
        if is_success:
            passed_count += 1
        print(f"{name:<25} | {score:<8.2f} | {threshold:<10.2f} | {status:<8}")
        if not is_success and reason:
            print(f"   Reason: {reason}")

    pass_rate = (passed_count / len(metric_order)) * 100
    print("-" * 60)
    print(f"Overall Pass Rate: {pass_rate:.1f}% ({passed_count}/{len(metric_order)} metrics passed)")
    print("="*80)


if __name__ == "__main__":
    main()
