"""Sending email. SMTP in production (any provider: Gmail, Brevo, …); a recorder elsewhere."""

from __future__ import annotations

import logging
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.message import EmailMessage

log = logging.getLogger(__name__)

#: Port 465 speaks TLS from the first byte; any other port upgrades with STARTTLS.
IMPLICIT_TLS_PORT = 465


@dataclass(frozen=True)
class Mail:
    to: str
    subject: str
    html: str


class Mailer(ABC):
    #: "unchecked", "ok" or "error (<reason>)" — the last sign-in, safe to publish.
    state = "ok"

    @abstractmethod
    def send(self, mail: Mail) -> bool:
        """Send one message. Return False instead of raising: a lost email must not stop a scan."""

    def check(self) -> str:
        """Sign in without sending anything; the result is kept in ``state``."""
        return self.state


class SmtpMailer(Mailer):
    def __init__(self, host: str, port: int, username: str, password: str, sender: str):
        self._host, self._port = host, port
        self._username, self._password = username, password
        self._sender = sender
        self.state = "unchecked"

    def check(self) -> str:
        try:
            with self._open():
                pass
            self.state = "ok"
        except (OSError, smtplib.SMTPException) as error:
            log.warning("SMTP sign-in failed: %s", error)
            self.state = f"error ({_reason(error)})"
        return self.state

    def _open(self) -> smtplib.SMTP:
        if self._port == IMPLICIT_TLS_PORT:
            server = smtplib.SMTP_SSL(self._host, self._port, timeout=20)
        else:
            server = smtplib.SMTP(self._host, self._port, timeout=20)
            server.starttls()
        if self._username:
            server.login(self._username, self._password)
        return server

    def send(self, mail: Mail) -> bool:
        message = EmailMessage()
        message["From"] = self._sender
        message["To"] = mail.to
        message["Subject"] = mail.subject
        message.set_content("This message is in HTML; open it in a mail app that shows HTML.")
        message.add_alternative(mail.html, subtype="html")
        try:
            with self._open() as server:
                server.send_message(message)
            self.state = "ok"
            return True
        except (OSError, smtplib.SMTPException) as error:
            log.warning("email to %s was not sent: %s", mail.to, error)
            self.state = f"error ({_reason(error)})"
            return False


def _reason(error: Exception) -> str:
    """Why signing in failed, naming no account."""
    if isinstance(error, smtplib.SMTPAuthenticationError):
        text = str(error).lower()
        if "application-specific password" in text:
            return "Gmail wants an app password"
        return "wrong username or password"
    if isinstance(error, OSError) and not isinstance(error, smtplib.SMTPException):
        return "mail host unreachable"
    return type(error).__name__


class RecordingMailer(Mailer):
    """Keeps messages instead of sending them — local runs and tests."""

    def __init__(self):
        self.outbox: list[Mail] = []

    def send(self, mail: Mail) -> bool:
        log.info("email (not sent) to %s: %s", mail.to, mail.subject)
        self.outbox.append(mail)
        return True
