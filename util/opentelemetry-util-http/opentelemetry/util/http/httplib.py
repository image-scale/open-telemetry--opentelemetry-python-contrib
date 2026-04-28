# Copyright The OpenTelemetry Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""HTTP library utilities for IP address handling."""

import logging
import threading
from typing import Any, Dict, List, Optional


_state_lock = threading.Lock()
_states: Dict[int, Dict[str, Any]] = {}


def _getstate(connection) -> Dict[str, Any]:
    """Get the state for a connection."""
    conn_id = id(connection)
    with _state_lock:
        if conn_id not in _states:
            _states[conn_id] = {"need_ip": []}
        return _states[conn_id]


def _setstate(connection, state: Dict[str, Any]):
    """Set the state for a connection."""
    conn_id = id(connection)
    with _state_lock:
        _states[conn_id] = state


def _clearstate(connection):
    """Clear the state for a connection."""
    conn_id = id(connection)
    with _state_lock:
        _states.pop(conn_id, None)


_logger = logging.getLogger(__name__)


def trysetip(connection, loglevel: int = logging.WARNING) -> bool:
    """Try to set the IP address on spans that need it.

    Args:
        connection: The HTTP connection to get the peer address from.
        loglevel: The log level to use for warnings.

    Returns:
        True if the operation was successful (or there was nothing to do),
        False if the connection has no socket.
    """
    if connection.sock is None:
        return False

    state = _getstate(connection)
    spans_needing_ip: List = state.get("need_ip", [])

    try:
        peername = connection.sock.getpeername()
        ip = peername[0] if peername else None
        if ip:
            for span in spans_needing_ip:
                span.set_attribute("net.peer.ip", ip)
    except Exception as exc:
        _logger.log(loglevel, "Failed to get peer address: %s", exc)

    # Clear the need_ip list
    state["need_ip"] = []
    return True
