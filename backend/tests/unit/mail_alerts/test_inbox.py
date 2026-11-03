from pathlib import Path

from app.services.mail_alerts.inbox import FolderInbox, ImapInbox

MAIL = Path(__file__).parents[2] / "fixtures" / "mail"
RAW = (MAIL / "olx-krakow.eml").read_bytes()


class FakeImap:
    """Just enough of imaplib for ImapInbox: two unread emails, one of them from OLX."""

    instances: list["FakeImap"] = []

    def __init__(self, host, port, timeout):
        self.host, self.port, self.calls = host, port, []
        FakeImap.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.calls.append(("logout",))

    def login(self, user, password):
        self.calls.append(("login", user))

    def select(self, folder):
        self.calls.append(("select", folder))

    def uid(self, command, *args):
        self.calls.append((command, *args))
        if command == "SEARCH":
            return "OK", [b"7" if '"olx.pl"' in args else b""]
        if command == "FETCH":
            return "OK", [(b"7 (BODY[] {123}", RAW), b")"]
        return "OK", [b""]


def test_imap_reads_unread_alert_emails_without_marking_them():
    FakeImap.instances.clear()
    inbox = ImapInbox("imap.example.com", 993, "alerts@example.com", "secret", connect=FakeImap)
    mails = inbox.unread_from(("olx.pl", "otodom.pl"))
    assert [(mail.uid, mail.sender) for mail in mails] == [("7", "powiadomienia@olx.pl")]
    calls = FakeImap.instances[0].calls
    assert ("SEARCH", None, "UNSEEN", "FROM", '"olx.pl"') in calls
    assert ("FETCH", b"7", "(BODY.PEEK[])") in calls  # PEEK: reading does not mark it read
    assert not any(call[0] == "STORE" for call in calls)


def test_imap_marks_only_the_processed_emails_read():
    FakeImap.instances.clear()
    ImapInbox("imap.example.com", 993, "u", "p", connect=FakeImap).mark_read(["7"])
    assert ("STORE", "7", "+FLAGS", "(\\Seen)") in FakeImap.instances[0].calls
    ImapInbox("imap.example.com", 993, "u", "p", connect=FakeImap).mark_read([])
    assert len(FakeImap.instances) == 1  # nothing to mark: no connection at all


def test_a_folder_of_saved_emails_stands_in_for_the_mailbox():
    inbox = FolderInbox(str(MAIL))
    assert {mail.uid for mail in inbox.unread_from(("olx.pl", "otodom.pl"))} == {"olx-krakow.eml", "otodom-krakow.eml"}
    assert [mail.uid for mail in inbox.unread_from(("otodom.pl",))] == ["otodom-krakow.eml"]
    inbox.mark_read(["olx-krakow.eml"])
    assert len(inbox.unread_from(("olx.pl", "otodom.pl"))) == 2  # a stand-in: every check sees every file
