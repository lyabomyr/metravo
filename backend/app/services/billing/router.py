from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.container import Container
from ..auth.dependencies import current_user, get_container
from ..users.models import User
from .schemas import CheckoutRequest, PlanOut, RedirectOut, SubscriptionOut

router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.get("/plans", response_model=list[PlanOut])
def plans(container: Container = Depends(get_container)):
    return [PlanOut.of(plan) for plan in container.billing.plans()]


@router.get("/subscription", response_model=SubscriptionOut | None)
def subscription(user: User = Depends(current_user), container: Container = Depends(get_container)):
    sub = container.billing.subscription(user)
    return SubscriptionOut.of(sub) if sub else None


@router.post("/checkout", response_model=RedirectOut)
def checkout(body: CheckoutRequest, user: User = Depends(current_user), container: Container = Depends(get_container)):
    return RedirectOut(url=container.billing.checkout_url(user, body.plan))


@router.post("/portal", response_model=RedirectOut)
def portal(user: User = Depends(current_user), container: Container = Depends(get_container)):
    return RedirectOut(url=container.billing.portal_url(user))


@router.post("/webhook")
async def webhook(request: Request, container: Container = Depends(get_container)) -> dict:
    container.billing.handle_webhook(await request.body(), {k.lower(): v for k, v in request.headers.items()})
    return {"received": True}
