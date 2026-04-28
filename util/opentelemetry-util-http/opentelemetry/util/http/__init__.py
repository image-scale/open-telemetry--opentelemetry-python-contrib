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

"""OpenTelemetry HTTP Utilities."""

from typing import Optional

OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SANITIZE_FIELDS = "OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SANITIZE_FIELDS"
OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST = "OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST"
OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE = "OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE"
OTEL_PYTHON_INSTRUMENTATION_HTTP_CAPTURE_ALL_METHODS = "OTEL_PYTHON_INSTRUMENTATION_HTTP_CAPTURE_ALL_METHODS"


def sanitize_method(method: str) -> str:
    """Sanitize HTTP method."""
    raise NotImplementedError


def get_excluded_urls(excluded_urls_env_var: str):
    """Get excluded URLs from environment variable."""
    raise NotImplementedError


def redact_query_parameters(url: str, query_params_to_redact: Optional[list] = None) -> str:
    """Redact query parameters from URL."""
    raise NotImplementedError


def redact_url(url: str) -> str:
    """Redact URL."""
    raise NotImplementedError


def remove_url_credentials(url: str) -> str:
    """Remove credentials from URL."""
    raise NotImplementedError
