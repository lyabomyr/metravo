from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from ...core.container import Container
from ..auth.dependencies import current_user, get_container
from ..users.models import User
from .schemas import ChannelChange, ChannelOut

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/channels", response_model=list[ChannelOut])
def channels(user: User = Depends(current_user), container: Container = Depends(get_container)):
    return [ChannelOut.of(setting) for setting in container.notifications.settings(user)]


@router.put("/channels/{code}", response_model=ChannelOut)
def update_channel(code: str, body: ChannelChange, user: User = Depends(current_user), container: Container = Depends(get_container)):
    return ChannelOut.of(container.notifications.update(user, code, body.enabled, body.address))


@router.post("/channels/{code}/test", status_code=204)
def test_channel(code: str, user: User = Depends(current_user), container: Container = Depends(get_container)) -> Response:
    container.notifier.send_test(user, code)
    return Response(status_code=204)
