from __future__ import annotations

from html import escape

from ...searches.service import SearchService
from ...users.service import UserService
from ..link_service import TelegramLinkService
from .base import BaseCommand, CommandContext


class StatusCommand(BaseCommand):
    name = "status"
    description = "your plan, searches and whether this chat is paused"

    def __init__(self, users: UserService, searches: SearchService, links: TelegramLinkService):
        self._users = users
        self._searches = searches
        self._links = links

    def run(self, context: CommandContext) -> str:
        plan = self._users.plan_of(context.user)
        chat = self._links.chat(context.chat_id)
        searches = self._searches.list(context.user)
        lines = [
            f"Account: <b>{escape(context.user.email)}</b> · plan <b>{plan.name}</b>",
            f"Scans every {plan.scan_interval_minutes} min · this chat is {'⏸ paused' if chat.paused else '▶️ active'}",
            "",
        ]
        lines += [
            f"{'🟢' if s.enabled else '⚪️'} {escape(s.name)} — {s.deal_type.value} {s.property_type.value}, "
            f"{s.city}, ≤ {s.max_price:,} zł, ≥ {s.min_area:g} m²".replace(",", " ")
            for s in searches
        ] or ["No searches yet — add one on the website."]
        return "\n".join(lines)
