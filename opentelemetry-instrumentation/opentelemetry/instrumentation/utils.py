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

"""Utility functions for instrumentation."""

import sys
from contextlib import contextmanager
from typing import Optional, Union

from opentelemetry.context import (
    _SUPPRESS_HTTP_INSTRUMENTATION_KEY,
    _SUPPRESS_INSTRUMENTATION_KEY,
    attach,
    detach,
    get_current,
    set_value,
    get_value,
)
from opentelemetry.trace import StatusCode

try:
    # wrapt 2.0.0+
    from wrapt import BaseObjectProxy
except ImportError:
    from wrapt import ObjectProxy as BaseObjectProxy


def http_status_to_status_code(
    status: Optional[int],
    server_span: bool = False,
    allow_redirect: bool = True,
) -> StatusCode:
    """Convert HTTP status code to OpenTelemetry status code.

    Args:
        status: The HTTP status code.
        server_span: If True, treat as server span (4xx are UNSET, 5xx are ERROR).
        allow_redirect: If False, treat 3xx as ERROR.

    Returns:
        The corresponding OpenTelemetry StatusCode.
    """
    if status is None:
        return StatusCode.UNSET

    # Check for out-of-range status codes
    if status < 100 or status >= 600:
        return StatusCode.ERROR

    # 1xx, 2xx are always UNSET
    if status < 300:
        return StatusCode.UNSET

    # 3xx redirects
    if status < 400:
        if allow_redirect:
            return StatusCode.UNSET
        else:
            return StatusCode.ERROR

    # 4xx client errors
    if status < 500:
        if server_span:
            return StatusCode.UNSET
        else:
            return StatusCode.ERROR

    # 5xx server errors
    return StatusCode.ERROR


def _python_path_without_directory(
    python_path: str,
    directory: str,
    path_separator: str,
) -> str:
    """Remove a directory from the Python path.

    Args:
        python_path: The Python path string.
        directory: The directory to remove.
        path_separator: The path separator (e.g., ":" on Linux, ";" on Windows).

    Returns:
        The Python path without the specified directory.
    """
    paths = python_path.split(path_separator)
    filtered = [p for p in paths if p != directory]

    if not filtered:
        # If removing the directory would result in empty path, return original
        return python_path

    return path_separator.join(filtered)


def is_instrumentation_enabled() -> bool:
    """Check if instrumentation is enabled.

    Returns:
        True if instrumentation is enabled, False otherwise.
    """
    return not get_value(_SUPPRESS_INSTRUMENTATION_KEY)


def is_http_instrumentation_enabled() -> bool:
    """Check if HTTP instrumentation is enabled.

    Returns:
        True if HTTP instrumentation is enabled, False otherwise.
    """
    if not is_instrumentation_enabled():
        return False
    return not get_value(_SUPPRESS_HTTP_INSTRUMENTATION_KEY)


@contextmanager
def suppress_instrumentation():
    """Context manager to suppress instrumentation.

    While in this context, all instrumentation is suppressed.
    Sets both the UUID-based key and the simple string key for compatibility.
    """
    # Set both keys for backward compatibility
    ctx = set_value(_SUPPRESS_INSTRUMENTATION_KEY, True)
    ctx = set_value("suppress_instrumentation", True, ctx)
    token = attach(ctx)
    try:
        yield
    finally:
        detach(token)


@contextmanager
def suppress_http_instrumentation():
    """Context manager to suppress HTTP instrumentation.

    While in this context, HTTP instrumentation is suppressed.
    """
    token = attach(set_value(_SUPPRESS_HTTP_INSTRUMENTATION_KEY, True))
    try:
        yield
    finally:
        detach(token)


def unwrap(obj: Union[str, object], attr: str):
    """Unwrap a wrapped attribute.

    Args:
        obj: The object or a dotted import path string.
        attr: The attribute name to unwrap.
    """
    if isinstance(obj, str):
        # Parse the dotted import path
        if not obj:
            raise ImportError("Cannot parse '' as dotted import path")

        parts = obj.rsplit(".", 1)
        if len(parts) == 1:
            raise ImportError(f"Cannot parse '{obj}' as dotted import path")

        module_path, obj_name = parts

        # Check if the module is already imported
        if module_path not in sys.modules:
            # Module not imported, do nothing
            return

        module = sys.modules[module_path]

        if not hasattr(module, obj_name):
            raise ImportError(
                f"Cannot import '{obj_name}' from '{module_path}'"
            )

        obj = getattr(module, obj_name)

    # Check if the attribute exists
    if not hasattr(obj, attr):
        return

    # Check if the attribute is wrapped by wrapt
    wrapped = getattr(obj, attr)
    if not isinstance(wrapped, BaseObjectProxy):
        return

    # Unwrap by restoring the original function
    if hasattr(wrapped, "__wrapped__"):
        setattr(obj, attr, wrapped.__wrapped__)
