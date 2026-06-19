from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Any

import chess

from boss_chess.types import MultiplayerConfig


@dataclass(slots=True)
class NetworkHandshake:
    username: str
    mode: str
    variant: str
    color: str


class MultiplayerSession:
    def __init__(self, config: MultiplayerConfig, variant: str, local_color: chess.Color) -> None:
        self.config = config
        self.variant = variant
        self.local_color = local_color
        self.peer_color = chess.BLACK if local_color == chess.WHITE else chess.WHITE
        self.peer_name = "Remote"
        self.sock: socket.socket | None = None
        self.file_r = None
        self.file_w = None

    @property
    def active(self) -> bool:
        return self.config.mode in {"host", "join"} and self.sock is not None

    def start(self) -> None:
        if self.config.mode == "host":
            self._host()
        elif self.config.mode == "join":
            self._join()

    def close(self) -> None:
        for stream in (self.file_r, self.file_w):
            try:
                if stream is not None:
                    stream.close()
            except Exception:
                pass
        try:
            if self.sock is not None:
                self.sock.close()
        finally:
            self.sock = None
            self.file_r = None
            self.file_w = None

    def send_json(self, payload: dict[str, Any]) -> None:
        if self.file_w is None:
            return
        self.file_w.write((json.dumps(payload) + "\n").encode("utf-8"))
        self.file_w.flush()

    def recv_json(self) -> dict[str, Any]:
        if self.file_r is None:
            raise ConnectionError("Network session not started")
        line = self.file_r.readline()
        if not line:
            raise ConnectionError("Remote player disconnected")
        return json.loads(line.decode("utf-8"))

    def send_move(self, move: chess.Move) -> None:
        self.send_json({"type": "move", "uci": move.uci()})

    def recv_move(self) -> chess.Move:
        payload = self.recv_json()
        if payload.get("type") != "move":
            raise ConnectionError(f"Unexpected network payload: {payload}")
        return chess.Move.from_uci(str(payload.get("uci", "")))

    def send_message(self, text: str) -> None:
        self.send_json({"type": "message", "text": text})

    def receive_message(self) -> str:
        payload = self.recv_json()
        if payload.get("type") != "message":
            raise ConnectionError(f"Unexpected network payload: {payload}")
        return str(payload.get("text", ""))

    def _host(self) -> None:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", self.config.port))
        server.listen(1)
        self.sock, address = server.accept()
        server.close()
        self.file_r = self.sock.makefile("rb")
        self.file_w = self.sock.makefile("wb")
        self.send_json(NetworkHandshake(self.config.username, self.config.mode, self.variant, "white" if self.local_color == chess.WHITE else "black").__dict__)
        handshake = self.recv_json()
        self.peer_name = str(handshake.get("username", "Remote"))

    def _join(self) -> None:
        self.sock = socket.create_connection((self.config.host, self.config.port), timeout=20)
        self.file_r = self.sock.makefile("rb")
        self.file_w = self.sock.makefile("wb")
        handshake = self.recv_json()
        self.peer_name = str(handshake.get("username", "Remote"))
        self.send_json(NetworkHandshake(self.config.username, self.config.mode, self.variant, "white" if self.local_color == chess.WHITE else "black").__dict__)
