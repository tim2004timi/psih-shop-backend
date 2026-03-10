from typing import Optional

from fastapi import HTTPException, status

from src.models.orders import Order


def ensure_admin(current_user: Optional[dict]) -> None:
    if not current_user or not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )


def can_access_order(
    order: Order,
    current_user: Optional[dict] = None,
    access_token: Optional[str] = None,
) -> bool:
    if current_user and current_user.get("is_admin", False):
        return True

    if current_user and order.user_id and order.user_id == current_user.get("id"):
        return True

    if order.user_id is None and access_token and access_token == order.access_token:
        return True

    return False


def ensure_order_access(
    order: Order,
    current_user: Optional[dict] = None,
    access_token: Optional[str] = None,
) -> None:
    if can_access_order(order, current_user=current_user, access_token=access_token):
        return

    if order.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guest orders require a valid access token",
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can only access your own orders",
    )
