"""Command-line entry points for jobs that run outside a web request.

    python -m app.cli scan           # one scan run by hand (the API schedules its own)
    python -m app.cli scan-remote    # the REMOTE_PORTALS only — .github/workflows/portal-scan.yml
    python -m app.cli set-webhook    # point the Telegram bot at this API
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict

from .core.config import Settings
from .core.container import Container


def scan(container: Container) -> int:
    report = container.scanner.run()
    print(json.dumps(asdict(report), indent=2))
    return 0


def scan_remote(container: Container) -> int:
    if not container.settings.remote_portals:
        print("REMOTE_PORTALS is empty: nothing to fetch here", file=sys.stderr)
        return 1
    report = container.scanner.run_remote()
    print(json.dumps(asdict(report), indent=2))
    return 0


def set_webhook(container: Container) -> int:
    settings = container.settings
    url = f"{settings.public_api_url}/api/telegram/webhook"
    container.telegram_client.set_webhook(url, settings.telegram_webhook_secret)
    print(f"Telegram webhook → {url}")
    return 0


COMMANDS = {"scan": scan, "scan-remote": scan_remote, "set-webhook": set_webhook}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    parser.add_argument("command", choices=sorted(COMMANDS))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = Settings.from_env()
    settings.validate(serving=False)
    return COMMANDS[args.command](Container(settings))


if __name__ == "__main__":
    sys.exit(main())
