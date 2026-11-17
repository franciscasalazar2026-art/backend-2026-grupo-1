import json

from app.infrastructure.recovery_mail import deliver_recovery_token


def test_local_mailbox_writes_one_complete_message(monkeypatch, tmp_path):
    mailbox = tmp_path / "mail"
    monkeypatch.setenv("RECOVERY_MAIL_DIR", str(mailbox))

    deliver_recovery_token("taller@example.com", "token-sintetico", "mensaje-01")

    messages = list(mailbox.iterdir())
    assert [path.name for path in messages] == ["mensaje-01.json"]
    assert json.loads(messages[0].read_text(encoding="utf-8")) == {
        "email": "taller@example.com",
        "token": "token-sintetico",
    }


def test_disabled_mailbox_never_writes_to_working_directory(monkeypatch, tmp_path):
    monkeypatch.delenv("RECOVERY_MAIL_DIR", raising=False)
    monkeypatch.chdir(tmp_path)

    deliver_recovery_token("taller@example.com", "token-sintetico", "mensaje-01")

    assert not list(tmp_path.iterdir())


def test_broken_mailbox_does_not_log_the_email_or_token(monkeypatch, tmp_path, caplog):
    mailbox = tmp_path / "not-a-directory"
    mailbox.touch()
    monkeypatch.setenv("RECOVERY_MAIL_DIR", str(mailbox))

    deliver_recovery_token("taller@example.com", "token-sintetico", "mensaje-01")

    assert "No se pudo escribir" in caplog.text
    assert "taller@example.com" not in caplog.text
    assert "token-sintetico" not in caplog.text
