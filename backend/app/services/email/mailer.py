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
    @abstractmethod
    def send(self, mail: Mail) -> bool:
        """Send one message. Return False instead of raising: a lost email must not stop a scan."""


class SmtpMailer(Mailer):
    def __init__(self, host: str, port: int, username: str, password: str, sender: str):
        self._host, self._port = host, port
        self._username, self._password = username, password
        self._sender = sender

    def send(self, mail: Mail) -> bool:
        message = EmailMessage()
        message["From"] = self._sender
        message["To"] = mail.to
        message["Subject"] = mail.subject
        message.set_content("This message is in HTML; open it in a mail app that shows HTML.")
        message.add_alternative(mail.html, subtype="html")
        try:
            if self._port == IMPLICIT_TLS_PORT:
                server = smtplib.SMTP_SSL(self._host, self._port, timeout=20)
            else:
                server = smtplib.SMTP(self._host, self._port, timeout=20)
                server.starttls()
            with server:
                if self._username:
                    server.login(self._username, self._password)
                server.send_message(message)
            return True
        except (OSError, smtplib.SMTPException) as error:
            log.warning("email to %s was not sent: %s", mail.to, error)
            return False


class RecordingMailer(Mailer):
    """Keeps messages instead of sending them — local runs and tests."""

    def __init__(self):
        self.outbox: list[Mail] = []

    def send(self, mail: Mail) -> bool:
        log.info("email (not sent) to %s: %s", mail.to, mail.subject)
        self.outbox.append(mail)
        return True
