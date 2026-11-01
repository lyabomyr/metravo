from __future__ import annotations

from .base import BaseCommand, CommandContext


class HelpCommand(BaseCommand):
    name = "help"
    description = "list commands"
    requires_account = False

    def __init__(self, commands: list[BaseCommand], website_url: str):
        self._commands = commands
        self._website = website_url

    def run(self, context: CommandContext) -> str:
        lines = [f"/{command.name} — {command.description}" for command in self._commands]
        lines.append(f'\nSearches and settings live on <a href="{self._website}">the website</a>.')
        return "\n".join(lines)
