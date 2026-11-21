import subprocess

import pytest

import probe_compass


@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv("BASE_URL", "http://compass.test:8080/")
    monkeypatch.setenv("EXPECTED_RELEASE", "test-compass")
    monkeypatch.setenv("CHECK_TIMEOUT", "1.75")


def test_success_uses_environment(settings, monkeypatch, capsys):
    def completed(args, **options):
        assert args[-1] == "http://compass.test:8080/"
        assert args[:3] == ["curl", "-q", "-fsS"]
        assert options == {"capture_output": True, "text": True, "timeout": 1.75}
        return subprocess.CompletedProcess(args, 0, "<h1>test-compass</h1>", "")

    monkeypatch.setattr(probe_compass.subprocess, "run", completed)
    assert probe_compass.main() == 0
    assert "VERIFIED | test-compass" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("code", "body", "message"),
    [(22, "", "CURL ERROR | exit 22"), (0, "other release", "RELEASE MISMATCH")],
)
def test_probe_rejects_bad_response(settings, monkeypatch, capsys, code, body, message):
    def completed(args, **options):
        return subprocess.CompletedProcess(args, code, body, "unavailable")

    monkeypatch.setattr(probe_compass.subprocess, "run", completed)
    assert probe_compass.main() == 1
    assert message in capsys.readouterr().out


def test_timeout_signal(settings, monkeypatch, capsys):
    def stalled(args, *, timeout, **options):
        raise subprocess.TimeoutExpired(args, timeout)

    monkeypatch.setattr(probe_compass.subprocess, "run", stalled)
    assert probe_compass.main() == 2
    assert "TIME LIMIT | 1.75s" in capsys.readouterr().out


@pytest.mark.parametrize("variable", ["EXPECTED_RELEASE", "CHECK_TIMEOUT"])
def test_invalid_configuration(settings, variable, monkeypatch, capsys):
    monkeypatch.setenv(variable, "" if variable == "EXPECTED_RELEASE" else "0")
    assert probe_compass.main() == 1
    assert f"CONFIG ERROR | {variable}" in capsys.readouterr().out
