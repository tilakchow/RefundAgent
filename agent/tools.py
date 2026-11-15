from datetime import date, datetime
import logging
from typing import Any
from uuid import uuid4
from data import users_data
from deepeval.tracing import observe
from dotenv import load_dotenv
from langchain.tools import tool
from objects import PurchaseItem

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s "
)

@tool
@observe(type="tool")
def get_user_purchase_history(user: str) -> dict:
    """Retrieves the customer order purchase history given their username."""
    logging.info(f"using get_user_purchase_history tool on user: {user}")
    if users_data.get(user):
        return users_data[user]
    return {"status": "there was no username found"}

@tool
@observe(type="tool")
def calculate_right_refund(user: str, items: list[PurchaseItem]) -> dict:
    """Calculates refund eligibility and amount for the requested items.
    Internally retrieves today's date, checks if each purchase is within the 30-day window
    and not in the future, and returns purchase date, today's date, days elapsed, and eligibility.
    """
    logging.info(f"using calculate_right_refund tool to get user: {user} refund for items: {items}")
    if not users_data.get(user):
        return {
            "status": "there was no username found",
            "purchase_date": "N/A",
            "today_date": date.today().isoformat(),
            "days_since_purchase": 0,
            "within_30_day_window": False,
            "refund_amount": 0.0,
            "eligible": False
        }

    today = date.today()
    today_str = today.isoformat()
    user_orders = users_data[user]

    total_refund = 0.0
    purchase_dates = []
    days_elapsed = []
    eligible_items = []
    ineligible_items = []

    for item in items:
        item_name = item.name
        if item_name in user_orders:
            order_info = user_orders[item_name]
            p_date_raw = order_info["date"]
            try:
                parts = [int(p) for p in p_date_raw.split("-")]
                p_date = date(parts[0], parts[1], parts[2])
            except Exception:
                p_date = datetime.strptime(p_date_raw, "%Y-%m-%d").date()

            p_date_str = p_date.isoformat()
            purchase_dates.append(p_date_str)
            days = (today - p_date).days
            days_elapsed.append(days)

            # Within 30 days and not in the future
            if 0 <= days <= 30:
                total_refund += float(order_info["price"])
                eligible_items.append({
                    "name": item_name,
                    "price": float(order_info["price"]),
                    "purchase_date": p_date_str,
                    "days_since_purchase": days
                })
            else:
                ineligible_items.append({
                    "name": item_name,
                    "price": float(order_info["price"]),
                    "purchase_date": p_date_str,
                    "days_since_purchase": days,
                    "reason": "outside 30-day refund window" if days > 30 else "future purchase date"
                })
        else:
            ineligible_items.append({
                "name": item_name,
                "reason": "item not found in purchase history"
            })

    is_eligible = len(eligible_items) > 0
    p_dates_str = ", ".join(purchase_dates) if purchase_dates else "N/A"
    primary_days = days_elapsed[0] if days_elapsed else 0

    return {
        "purchase_date": p_dates_str,
        "today_date": today_str,
        "days_since_purchase": primary_days,
        "within_30_day_window": is_eligible,
        "refund_amount": total_refund,
        "eligible": is_eligible,
        "eligible_items": eligible_items,
        "ineligible_items": ineligible_items
    }

@tool
@observe(type="tool")
def issue_refund_ticket(user: str, refund_amount: int) -> dict:
    """Issues a refund ticket with a unique ticket ID for the customer.

    Args:
        user: The customer username.
        refund_amount: The total refund amount in dollars as an integer.
    """
    logging.info(f"using issue_refund_ticket for user: {user}, amount: {refund_amount}")
    ticket_id = f"REF-{user}-{uuid4().hex[:6].upper()}"
    return {
        "status": "success",
        "ticket_id": ticket_id,
        "user": user,
        "refund_amount": int(round(refund_amount)),
        "message": f"A refund ticket {ticket_id} has been issued successfully for ${refund_amount}."
    }
