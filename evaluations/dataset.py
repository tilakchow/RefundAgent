from deepeval.dataset import EvaluationDataset, Golden
from deepeval.test_case import ToolCall

dataset = EvaluationDataset(
    goldens=[
        Golden(
            input="I am user123, I would like a refund for the book and the pen",
            expected_output="A refund was issued. Refund ticket REF-user123 for $30 has been issued successfully. The book was purchased on 2026-11-05 and pen on 2026-11-03, today is 2026-11-15, which is within the 30-day refund window.",
            expected_tools=[
                ToolCall(name="get_user_purchase_history",
                         input_parameters={"user": "user123"}),
                ToolCall(name="calculate_right_refund",
                         input_parameters={"user": "user123", "items": [{"name": "book"}, {"name": "pen"}]}),
                ToolCall(name="issue_refund_ticket",
                         input_parameters={"user": "user123", "refund_amount": 30}),
            ]
        ),
        Golden(
            input="I am user123, I would like a refund for the book",
            expected_output="A refund was issued. Refund ticket REF-user123 for $23 has been issued successfully. The book was purchased on 2026-11-05, today is 2026-11-15, which is 10 days, verified within the 30-day refund window.",
            expected_tools=[
                ToolCall(name="get_user_purchase_history",
                         input_parameters={"user": "user123"}),
                ToolCall(name="calculate_right_refund",
                         input_parameters={"user": "user123", "items": [{"name": "book"}]}),
                ToolCall(name="issue_refund_ticket",
                         input_parameters={"user": "user123", "refund_amount": 23}),
            ]
        ),
        Golden(
            input="I am user123, I would like no refund, I just want to know what I purchased",
            expected_output="A refund was not issued. You purchased a book ($23 on 2026-11-05) and a pen ($7 on 2026-11-03). No refund ticket was requested or issued.",
            expected_tools=[
                ToolCall(name="get_user_purchase_history",
                         input_parameters={"user": "user123"}),
            ]
        ),
        Golden(
            input="I am user999, I would like a refund for the book",
            expected_output="A refund was not issued. The username user999 is invalid and not found in purchase history. Please provide your username again before requesting a refund.",
            expected_tools=[
                ToolCall(name="get_user_purchase_history",
                         input_parameters={"user": "user999"}),
            ]
        ),
        Golden(
            input="I am user126, I would like a refund for the water_bottle",
            expected_output="A refund was not issued. No refund was given because the water_bottle was purchased on 2026-7-25, which is outside the 30-day refund policy window.",
            expected_tools=[
                ToolCall(name="get_user_purchase_history",
                         input_parameters={"user": "user126"}),
                ToolCall(name="calculate_right_refund",
                         input_parameters={"user": "user126", "items": [{"name": "water_bottle"}]}),
            ]
        ),
        Golden(
            input="I am user126, I would like a refund for the backpack and water_bottle",
            expected_output="A refund was issued. A refund ticket for $45 has been issued successfully for the backpack (purchased on 2026-11-02, verified within the 30-day window). The water_bottle is not eligible because it was purchased on 2026-7-25, outside the 30-day refund policy.",
            expected_tools=[
                ToolCall(name="get_user_purchase_history",
                         input_parameters={"user": "user126"}),
                ToolCall(name="calculate_right_refund",
                         input_parameters={"user": "user126", "items": [{"name": "backpack"}, {"name": "water_bottle"}]}),
                ToolCall(name="issue_refund_ticket",
                         input_parameters={"user": "user126", "refund_amount": 45}),
            ]
        ),
        Golden(
            input="I am user126, I would like a refund for the sneakers",
            expected_output="A refund was not issued. No refund was given because you did not purchase sneakers in your order history.",
            expected_tools=[
                ToolCall(name="get_user_purchase_history",
                         input_parameters={"user": "user126"}),
            ]
        ),
    ]
)
