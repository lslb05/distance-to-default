import pytest

from distance_to_default.config import Settings


def test_reads_settings_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISTANCE_TO_DEFAULT_LOG_LEVEL", "DEBUG")

    assert Settings().log_level == "DEBUG"
