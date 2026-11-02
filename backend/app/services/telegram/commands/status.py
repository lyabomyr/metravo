from __future__ import annotations

from html import escape

from ...searches.models import Search, describe_interval
from ...searches.service import SearchService
from ...users.service import UserService
from ..formatter import zloty
from ..link_service import TelegramLinkService
from .base import BaseCommand, CommandContext


class StatusCommand(BaseCommand):
    name = "status"

    def __init__(self, users: UserService, searches: SearchService, links: TelegramLinkService):
        self._users = users
        self._searches = searches
        self._links = links

    def run(self, context: CommandContext) -> str:
        plan = self._users.plan_of(context.user)
        chat = self._links.chat(context.chat_id)
        searches = self._searches.list(context.user)
        lines = [
            context.t("tg.status.account", email=escape(context.user.email), plan=plan.name),
            context.t("tg.status.paused" if chat.paused else "tg.status.active"),
            "",
        ]
        lines += [self._line(search, context) for search in searches] or [context.t("tg.status.none")]
        return "\n".join(lines)

    @staticmethod
    def _line(search: Search, context: CommandContext) -> str:
        what = f"{context.t('deal.' + search.deal_type.value)} · {context.t('property.' + search.property_type.value)}"
        return (
            f"{'🟢' if search.enabled else '⚪️'} {escape(search.name)} — {what}, {search.city}, "
            f"≤ {zloty(search.max_price)} zł, ≥ {search.min_area:g} m², {describe_interval(search.interval_minutes, context.locale)}"
        )
