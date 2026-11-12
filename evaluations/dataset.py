from deepeval.dataset import EvaluationsDataset, Golden
from deepeval.test_case import ToolCall

dataset = EvaluationsDataset(
    Goldens=[
        Golden(
            input = "I am user123, I would like a refund for the book and the pen ",
            expected_output="A refund ticket for 30$ has been issued !! ",
            expected_tools=[
                ToolCall(name= "get_user_purchase_history"),
                ToolCall(name= "calculate_right_refund"),
                ToolCall(name= "issue_refund_ticket"),
                ToolCall(name= "get_today_date")
            ]
        ),
        Golden(
            input = "I am user123, I would like a refund for the book",
            expected_output="A refund ticket for 23$ has been issued !! ",
            expected_tools=[
                ToolCall(name= "get_user_purchase_history"),
                ToolCall(name= "calculate_right_refund"),
                ToolCall(name= "issue_refund_ticket"),
                ToolCall(name= "get_today_date")
            ]
        ),
        Golden(
            input = "I am user123, I'm not her for refund,I just want to know what I purchased",
            expected_output="No refund tickets were issued only a list of what they brought",
            expected_tools=[
                ToolCall(name= "get_user_purchase_history"),
            ]
        ),
    ]
)