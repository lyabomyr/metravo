"""Where alert emails are read from: an IMAP mailbox, or saved ``.eml`` files in local and e2e runs."""

from __future__ import annotations

import email
import imaplib
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from email.message import EmailMessage
from email.policy import default as default_policy
from email.utils import parseaddr
from pathlib import Path

log = logging.getLogger(__name__)

#: Read at most this many alert emails per check; the rest wait for the next one.
MAX_PER_CHECK = 50


@dataclass(frozen=True)
class AlertMail:
    uid: str
    sender: str
    subject: str
    html: str
    text: str


def read_mail(uid: str, raw: bytes) -> AlertMail:
    message: EmailMessage = email.message_from_bytes(raw, policy=default_policy)  # type: ignore[assignment]
    html = message.get_body(preferencelist=("html",))
    text = message.get_body(preferencelist=("plain",))
    return AlertMail(
        uid=uid,
        sender=parseaddr(str(message.get("From", "")))[1].lower(),
        subject=str(message.get("Subject", "")),
        html=html.get_content() if html else "",
        text=text.get_content() if text else "",
    )


class Inbox(ABC):
    #: Shown on the admin page, the password never.
    address: str = ""

    @abstractmethod
    def unread_from(self, domains: tuple[str, ...]) -> list[AlertMail]:
        """Unread emails whose sender is at one of ``domains``. Reading does not mark them read."""

    @abstractmethod
    def mark_read(self, uids: list[str]) -> None:
        """Done with these: the next check skips them."""


class ImapInbox(Inbox):
    """A real mailbox over IMAP (SSL). Only alert emails are touched; everything else stays as it is."""

    def __init__(self, host: str, port: int, username: str, password: str, folder: str = "INBOX",
                 connect: Callable[..., imaplib.IMAP4] = imaplib.IMAP4_SSL, timeout: int = 30):
        self.address = username
        self._host, self._port, self._username, self._password = host, port, username, password
        self._folder = folder
        self._connect = connect
        self._timeout = timeout

    def unread_from(self, domains: tuple[str, ...]) -> list[AlertMail]:
        with self._session() as imap:
            uids: set[bytes] = set()
            for domain in domains:
                _, data = imap.uid("SEARCH", None, "UNSEEN", "FROM", f'"{domain}"')
                uids.update(data[0].split() if data and data[0] else [])
            mails = []
            for uid in sorted(uids, key=int)[:MAX_PER_CHECK]:
                _, data = imap.uid("FETCH", uid, "(BODY.PEEK[])")
                raw = next((part[1] for part in data if isinstance(part, tuple)), None)
                if raw:
                    mails.append(read_mail(uid.decode(), raw))
            return mails

    def mark_read(self, uids: list[str]) -> None:
        if not uids:
            return
        with self._session() as imap:
            for uid in uids:
                imap.uid("STORE", uid, "+FLAGS", "(\\Seen)")

    def _session(self) -> imaplib.IMAP4:
        imap = self._connect(self._host, self._port, timeout=self._timeout)
        imap.login(self._username, self._password)
        imap.select(self._folder)
        return imap


class FolderInbox(Inbox):
    """Saved ``.eml`` files stand in for the mailbox — local and e2e runs, no network.

    Every check sees every file: nothing marks a file read, and offers already
    recorded are not announced twice anyway.
    """

    def __init__(self, folder: str):
        self.address = f"files in {Path(folder).name}/"
        self._folder = Path(folder)

    def unread_from(self, domains: tuple[str, ...]) -> list[AlertMail]:
        mails = [read_mail(path.name, path.read_bytes()) for path in sorted(self._folder.glob("*.eml"))]
        return [mail for mail in mails if _from(mail.sender, domains)][:MAX_PER_CHECK]

    def mark_read(self, uids: list[str]) -> None:
        pass


def _from(sender: str, domains: tuple[str, ...]) -> bool:
    host = sender.rpartition("@")[2]
    return any(host == domain or host.endswith("." + domain) for domain in domains)
