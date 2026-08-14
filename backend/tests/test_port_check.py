"""端口占用预检的单元测试：复现启动时端口被占用的场景。"""

import socket

import pytest

from app.main import _port_in_use_message, check_port_available


def _listen_on_free_port() -> socket.socket:
    """绑定并监听一个临时端口，返回处于 LISTEN 状态的 socket。"""
    blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    blocker.bind(("127.0.0.1", 0))
    blocker.listen(1)
    return blocker


def test_check_port_available_exits_with_hint_when_port_in_use(caplog) -> None:
    blocker = _listen_on_free_port()
    port = blocker.getsockname()[1]
    try:
        with pytest.raises(SystemExit) as exc_info:
            check_port_available("127.0.0.1", port)
        assert exc_info.value.code == 1
        message = caplog.text
        assert f"端口 {port} 已被其他进程占用" in message
        assert f"lsof -nP -iTCP:{port} -sTCP:LISTEN" in message
        assert "kill <PID>" in message
        assert f"--port {port + 1}" in message
    finally:
        blocker.close()


def test_check_port_available_passes_when_port_free() -> None:
    # 先占用再释放一个临时端口，验证预检对空闲端口正常返回、不抛异常
    blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    blocker.bind(("127.0.0.1", 0))
    port = blocker.getsockname()[1]
    blocker.close()
    check_port_available("127.0.0.1", port)


def test_port_in_use_message_contains_required_sections() -> None:
    message = _port_in_use_message("127.0.0.1", 8000)
    assert "端口 8000 已被其他进程占用" in message
    assert "lsof -nP -iTCP:8000 -sTCP:LISTEN" in message
    assert "kill <PID>" in message
    assert message.startswith("=") and message.endswith("=")  # 分隔线包裹
