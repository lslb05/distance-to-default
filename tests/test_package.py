import pytest

from distancia_ao_default.config import Settings


def test_reads_settings_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISTANCIA_AO_DEFAULT_LOG_LEVEL", "DEBUG")

    assert Settings().log_level == "DEBUG"
