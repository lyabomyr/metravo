import smtplib

import pytest

from app.services.email import mailer as mailer_module
from app.services.email.mailer import Mail, SmtpMailer


class FakeSmtp:
    """smtplib.SMTP without a network: accepts one username/password pair."""

    accepted = ("me@gmail.com", "abcdefghijklmnop")
    sent: list = []

    def __init__(self, host, port, timeout):
        self.host = host

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def starttls(self):
        pass

    def login(self, username, password):
        if (username, password) != self.accepted:
            raise smtplib.SMTPAuthenticationError(535, b"5.7.8 Username and Password not accepted.")

    def send_message(self, message):
        FakeSmtp.sent.append(message["To"])


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    FakeSmtp.sent = []
    monkeypatch.setattr(mailer_module.smtplib, "SMTP", FakeSmtp)


def test_a_working_account_signs_in_without_sending_anything():
    mailer = SmtpMailer("smtp.gmail.com", 587, "me@gmail.com", "abcdefghijklmnop", "me@gmail.com")
    assert mailer.state == "unchecked"
    assert mailer.check() == "ok" and FakeSmtp.sent == []


def test_a_refused_sign_in_is_named_without_the_account():
    mailer = SmtpMailer("smtp.gmail.com", 587, "me@gmail.com", "wrong", "me@gmail.com")
    assert mailer.check() == "error (wrong username or password)"
    assert not mailer.send(Mail("a@b.pl", "s", "<p>x</p>"))
    assert "me@gmail.com" not in mailer.state


def test_a_send_that_works_marks_the_account_ok():
    mailer = SmtpMailer("smtp.gmail.com", 587, "me@gmail.com", "abcdefghijklmnop", "me@gmail.com")
    assert mailer.send(Mail("a@b.pl", "s", "<p>x</p>")) and mailer.state == "ok" and FakeSmtp.sent == ["a@b.pl"]


def test_a_pasted_secret_with_a_newline_still_signs_in(settings):
    from dataclasses import replace

    from app.core.container import Container

    smtp = replace(settings, smtp_host="smtp.gmail.com", smtp_username="me@gmail.com\n", smtp_password="abcd efgh ijkl mnop\n")
    container = Container(smtp)
    assert smtp.alert_mailbox == ("imap.gmail.com", 993, "me@gmail.com", "abcdefghijklmnop")
    assert container.mailer.check() == "ok"
