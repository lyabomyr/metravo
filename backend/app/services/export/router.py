from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from ...core.container import Container
from ..auth.dependencies import current_user, get_container
from ..users.models import User

router = APIRouter(prefix="/api/export", tags=["export"])


def _download(content: str, filename: str, media_type: str) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/listings.csv")
def listings(user: User = Depends(current_user), container: Container = Depends(get_container)) -> Response:
    return _download(container.export.listings_csv(user), "metravo-listings.csv", "text/csv; charset=utf-8")
