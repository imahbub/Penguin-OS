"""Unix domain socket IPC for PenguinOS Voice Assistant daemon and UI/CLI."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Callable, Set, Optional, Dict, Any


def get_socket_path() -> str:
    """Get the standard user runtime socket path."""
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if not runtime_dir:
        runtime_dir = f"/run/user/{os.getuid()}"
    return os.path.join(runtime_dir, "penguin-assistant.sock")


class IPCServer:
    """Unix Domain Socket server for commands and event broadcasting."""

    def __init__(self, command_handler: Callable[[Dict[str, Any]], Dict[str, Any]]):
        self.socket_path = get_socket_path()
        self.command_handler = command_handler
        self.subscribers: Set[asyncio.StreamWriter] = set()
        self.server: Optional[asyncio.AbstractServer] = None

    async def start(self):
        """Bind socket and listen."""
        # Unlink existing socket if orphaned
        if os.path.exists(self.socket_path):
            try:
                os.unlink(self.socket_path)
            except OSError:
                pass

        self.server = await asyncio.start_unix_server(self._handle_client, path=self.socket_path)

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming client connection."""
        is_subscriber = False
        try:
            while not reader.at_eof():
                line = await reader.readline()
                if not line:
                    break

                try:
                    data = json.loads(line.decode("utf-8").strip())
                except Exception:
                    continue

                cmd = data.get("cmd")
                if cmd == "subscribe":
                    is_subscriber = True
                    self.subscribers.add(writer)
                    writer.write(b'{"status":"subscribed"}\n')
                    await writer.drain()
                    continue

                # Normal command dispatch
                res = self.command_handler(data)
                writer.write((json.dumps(res) + "\n").encode("utf-8"))
                await writer.drain()

                # If this client is not subscribing to events, close after request/response
                if not is_subscriber:
                    break

        except Exception:
            pass
        finally:
            if is_subscriber and writer in self.subscribers:
                self.subscribers.remove(writer)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    def broadcast(self, event_data: Dict[str, Any]):
        """Broadcast an event notification to all UI subscribers."""
        if not self.subscribers:
            return

        payload = (json.dumps(event_data) + "\n").encode("utf-8")
        stale = set()
        for writer in self.subscribers:
            try:
                writer.write(payload)
            except Exception:
                stale.add(writer)

        for s in stale:
            self.subscribers.discard(s)

    async def stop(self):
        """Stop server and clean up socket file."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        if os.path.exists(self.socket_path):
            try:
                os.unlink(self.socket_path)
            except OSError:
                pass


def send_ipc_command(data: Dict[str, Any], timeout: float = 3.0) -> Optional[Dict[str, Any]]:
    """Synchronous helper for CLI to communicate with daemon."""
    import socket

    sock_path = get_socket_path()
    if not os.path.exists(sock_path):
        return None

    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(timeout)
        client.connect(sock_path)
        payload = (json.dumps(data) + "\n").encode("utf-8")
        client.sendall(payload)

        resp = b""
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            resp += chunk
            if b"\n" in chunk:
                break

        client.close()
        if resp:
            return json.loads(resp.decode("utf-8").strip())
    except Exception:
        return None
    return None
