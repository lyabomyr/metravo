from __future__ import annotations

from fastapi import APIRouter, Depends, status

from ...core.container import Container
from ..auth.dependencies import current_user, get_container
from ..users.models import User
from .schemas import SearchIn, SearchOut

router = APIRouter(prefix="/api/searches", tags=["searches"])


@router.get("", response_model=list[SearchOut])
def list_searches(user: User = Depends(current_user), container: Container = Depends(get_container)):
    return [SearchOut.of(search) for search in container.searches.list(user)]


@router.post("", response_model=SearchOut, status_code=status.HTTP_201_CREATED)
def create_search(body: SearchIn, user: User = Depends(current_user), container: Container = Depends(get_container)):
    return SearchOut.of(container.searches.create(user, body.to_search()))


@router.get("/{search_id}", response_model=SearchOut)
def get_search(search_id: str, user: User = Depends(current_user), container: Container = Depends(get_container)):
    return SearchOut.of(container.searches.get(user, search_id))


@router.put("/{search_id}", response_model=SearchOut)
def update_search(
    search_id: str, body: SearchIn, user: User = Depends(current_user), container: Container = Depends(get_container)
):
    return SearchOut.of(container.searches.update(user, search_id, body.to_search()))


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_search(search_id: str, user: User = Depends(current_user), container: Container = Depends(get_container)):
    container.searches.delete(user, search_id)
