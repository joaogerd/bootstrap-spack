import subprocess
from types import SimpleNamespace

from bootstrap.shared.command_runner import CommandRunner
from bootstrap.shared.execution_policy import ExecutionPolicy


def test_command_runner_run_captures_command_and_duration(monkeypatch) -> None:
    def fake_run(args, capture_output, text, env, timeout, check):
        return SimpleNamespace(returncode=0, stdout="hello\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    runner = CommandRunner(ExecutionPolicy(timeout_seconds=1, retries=1))
    result = runner.run(["echo", "hello"])

    assert result.returncode == 0
    assert result.stdout == "hello\n"
    assert result.stderr == ""
    assert result.command == "echo hello"
    assert result.timed_out is False
    assert result.duration_seconds >= 0


def test_command_runner_run_marks_timeout(monkeypatch) -> None:
    def fake_run(args, capture_output, text, env, timeout, check):
        raise subprocess.TimeoutExpired(cmd=args, timeout=timeout, output="", stderr="boom")

    monkeypatch.setattr(subprocess, "run", fake_run)

    runner = CommandRunner(ExecutionPolicy(timeout_seconds=1, retries=1))
    result = runner.run(["sleep", "5"])

    assert result.returncode == 124
    assert result.timed_out is True
    assert result.command == "sleep 5"
    assert "timeout" in result.stderr
