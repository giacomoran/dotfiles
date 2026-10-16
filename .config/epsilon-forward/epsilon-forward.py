#!/usr/bin/python3
# Forward every port a server listens on at epsilon to the same port on this Mac, so a
# server an agent starts there opens here at http://localhost:<port>, without --host and
# without running anything by hand.
#
# One SSH connection to epsilon carries every forward (an SSH control master). Every few
# seconds the script lists epsilon's listening ports, forwards the new ones and cancels the
# ones that closed. A port this Mac already uses is left alone, with a notification.
#
# launchd keeps it running: ~/Library/LaunchAgents/com.giacomoran.epsilon-forward.plist.
# The log is epsilon-forward.log next to this file.

import socket
import subprocess
import time
from pathlib import Path

HOST = "epsilon"
PATH_SOCKET_CONTROL = Path(__file__).parent / "control.sock"
SECONDS_POLL = 2
SECONDS_WAIT_CONNECTION = 30
SECONDS_RETRY_CONNECTION = 10
SECONDS_TIMEOUT_COMMAND = 10

# Ports servers listen on: above the privileged ones and below Linux's ephemeral range
# (32768 and up), where dora's daemon, Tailscale and outgoing connections take ports
PORT_MIN = 1024
PORT_MAX = 32767

# Ports never forwarded: T3 Code's own server on epsilon, and SimMachine's, which the
# Mac's own SimMachine (OrbStack) publishes too
PORTS_EXCLUDED = frozenset(
    [3773, 8000, 10000]
    + list(range(8050, 8100))
    + list(range(9950, 10000))
    + list(range(20001, 20021))
)

# Listener addresses a forward to epsilon's loopback reaches, and the address to forward
# to. Listeners bound to one interface only (Tailscale, systemd-resolved) are skipped.
TARGET_BY_ADDRESS_LISTENER = {
    "127.0.0.1": "127.0.0.1",
    "0.0.0.0": "127.0.0.1",
    "*": "127.0.0.1",
    "[::]": "127.0.0.1",
    "[::1]": "[::1]",
}


def log(message):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}", flush=True)


def notify(message):
    subprocess.run(
        ["osascript", "-e", f'display notification "{message}" with title "epsilon-forward"'],
        check=True,
    )


def run_control(operation, specification_forward):
    return subprocess.run(
        ["ssh", "-S", str(PATH_SOCKET_CONTROL), "-O", operation, "-L", specification_forward, HOST],
        capture_output=True,
        text=True,
        timeout=SECONDS_TIMEOUT_COMMAND,
    )


def start_connection():
    PATH_SOCKET_CONTROL.unlink(missing_ok=True)
    return subprocess.Popen(
        [
            "ssh",
            "-M",
            "-S",
            str(PATH_SOCKET_CONTROL),
            "-N",
            "-o",
            "ControlPersist=no",
            "-o",
            "ConnectTimeout=10",
            "-o",
            "ServerAliveInterval=10",
            "-o",
            "ServerAliveCountMax=3",
            HOST,
        ]
    )


def wait_for_connection(connection):
    # The control socket answers once the connection is up
    time_deadline = time.monotonic() + SECONDS_WAIT_CONNECTION
    while time.monotonic() < time_deadline:
        if connection.poll() is not None:
            raise ConnectionError(f"ssh exited with code {connection.returncode}")
        result = subprocess.run(
            ["ssh", "-S", str(PATH_SOCKET_CONTROL), "-O", "check", HOST],
            capture_output=True,
            timeout=SECONDS_TIMEOUT_COMMAND,
        )
        if result.returncode == 0:
            return
        time.sleep(0.5)
    raise ConnectionError(f"no connection after {SECONDS_WAIT_CONNECTION} s")


def list_listeners_remote():
    result = subprocess.run(
        ["ssh", "-S", str(PATH_SOCKET_CONTROL), HOST, "ss", "-ltnH"],
        capture_output=True,
        text=True,
        timeout=SECONDS_TIMEOUT_COMMAND,
    )
    if result.returncode != 0:
        raise ConnectionError(f"ss failed: {result.stderr.strip()}")

    # Map each forwardable port to its target. A port with an IPv4 listener goes to
    # 127.0.0.1 even if it also listens on [::1].
    target_by_port = {}
    for line in result.stdout.splitlines():
        address, _, text_port = line.split()[3].rpartition(":")
        port = int(text_port)
        if port < PORT_MIN or port > PORT_MAX or port in PORTS_EXCLUDED:
            continue
        if address not in TARGET_BY_ADDRESS_LISTENER:
            continue
        if target_by_port.get(port) == "127.0.0.1":
            continue
        target_by_port[port] = TARGET_BY_ADDRESS_LISTENER[address]
    return target_by_port


def is_port_free_local(port):
    # ssh binds the forward on both loopback addresses, so both must be free, or the
    # browser could reach this Mac's own server on one and epsilon's on the other
    for family, address in [(socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")]:
        with socket.socket(family, socket.SOCK_STREAM) as probe:
            try:
                probe.bind((address, port))
            except OSError:
                return False
    return True


def forward_while_connected(connection):
    target_by_port_forwarded = {}
    ports_notified = set()
    while connection.poll() is None:
        target_by_port_remote = list_listeners_remote()

        # Cancel the forwards whose server closed, which frees the port on this Mac
        for port, target in list(target_by_port_forwarded.items()):
            if target_by_port_remote.get(port) == target:
                continue
            run_control("cancel", f"{port}:{target}:{port}")
            del target_by_port_forwarded[port]
            log(f"Cancelled {port}")
        ports_notified &= set(target_by_port_remote)

        # Forward the new servers, on ports this Mac doesn't use itself. A taken port is
        # tried again at every poll, and notified once.
        for port, target in sorted(target_by_port_remote.items()):
            if port in target_by_port_forwarded:
                continue
            is_free = is_port_free_local(port)
            if not is_free and port not in ports_notified:
                ports_notified.add(port)
                log(f"Skipped {port}: in use on this Mac")
                notify(f"epsilon's server on port {port} isn't forwarded: this Mac uses the port")
                continue
            if not is_free:
                continue
            result = run_control("forward", f"{port}:{target}:{port}")
            if result.returncode != 0:
                log(f"Failed to forward {port}: {result.stderr.strip()}")
                continue
            target_by_port_forwarded[port] = target
            ports_notified.discard(port)
            log(f"Forwarded {port} to {target}")

        time.sleep(SECONDS_POLL)
    raise ConnectionError(f"ssh exited with code {connection.returncode}")


def main():
    # Reconnect for as long as the script runs: forwards end with their connection, for
    # example when the Mac sleeps, and are set up again from scratch
    PATH_SOCKET_CONTROL.parent.mkdir(parents=True, exist_ok=True)
    while True:
        log(f"Connecting to {HOST}")
        connection = start_connection()
        try:
            wait_for_connection(connection)
            log(f"Connected to {HOST}")
            forward_while_connected(connection)
        except (ConnectionError, subprocess.TimeoutExpired) as error:
            log(f"Lost the connection: {error}")
        connection.terminate()
        connection.wait()
        time.sleep(SECONDS_RETRY_CONNECTION)


if __name__ == "__main__":
    main()
