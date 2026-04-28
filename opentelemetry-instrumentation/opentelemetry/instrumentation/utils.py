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

from contextlib import contextmanager
from typing import Optional

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


def http_status_to_status_code(
    status: Optional[int],
    server_span: bool = False,
    allow_redirect: bool = True,
) -> StatusCode:
    """Convert HTTP status code to OpenTelemetry status code."""
    raise NotImplementedError


def _python_path_without_directory(
    python_path: str,
    directory: str,
    path_separator: str,
) -> str:
    """Remove a directory from the Python path."""
    raise NotImplementedError


def is_instrumentation_enabled() -> bool:
    """Check if instrumentation is enabled."""
    raise NotImplementedError


def is_http_instrumentation_enabled() -> bool:
    """Check if HTTP instrumentation is enabled."""
    raise NotImplementedError


@contextmanager
def suppress_instrumentation():
    """Context manager to suppress instrumentation."""
    raise NotImplementedError


@contextmanager
def suppress_http_instrumentation():
    """Context manager to suppress HTTP instrumentation."""
    raise NotImplementedError


def unwrap(obj, attr: str):
    """Unwrap a wrapped attribute."""
    raise NotImplementedError
