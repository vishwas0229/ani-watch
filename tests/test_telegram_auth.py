from pathlib import Path

import pytest

from ani_watch.auth.telegram import TelegramAccountService, TelegramCredentialStore
from ani_watch.config.settings import AppSettings
from ani_watch.domain.errors import AuthenticationError


def test_telegram_credentials_use_keyring(monkeypatch) -> None:
    saved = {}

    monkeypatch.setattr(
        "ani_watch.auth.telegram.keyring.set_password",
        lambda service, key, value: saved.__setitem__((service, key), value),
    )
    monkeypatch.setattr(
        "ani_watch.auth.telegram.keyring.get_password",
        lambda service, key: saved.get((service, key)),
    )

    store = TelegramCredentialStore()
    store.save_api_hash(" secret ")
    assert store.get_api_hash() == "secret"


def test_telegram_account_requires_api_credentials(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "ani_watch.auth.telegram.keyring.get_password",
        lambda service, key: None,
    )
    service = TelegramAccountService(
        AppSettings(telegram_api_id=None),
        session_path=tmp_path / "telegram",
    )

    with pytest.raises(AuthenticationError, match="API ID"):
        service._validate_configuration()
