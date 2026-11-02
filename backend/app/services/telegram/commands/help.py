from __future__ import annotations

from .base import BaseCommand, CommandContext


class HelpCommand(BaseCommand):
    name = "help"
    requires_account = False

    def __init__(self, commands: list[BaseCommand], website_url: str):
        self._commands = commands
        self._website = website_url

    def run(self, context: CommandContext) -> str:
        lines = [f"/{command.name} — {command.description(context.locale)}" for command in self._commands]
        lines.append(context.t("tg.help.footer", url=self._website))
        return "\n".join(lines)
