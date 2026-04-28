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

import os
import re
from typing import List, Optional, Sequence
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SANITIZE_FIELDS = "OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SANITIZE_FIELDS"
OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST = "OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST"
OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE = "OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE"
OTEL_PYTHON_INSTRUMENTATION_HTTP_CAPTURE_ALL_METHODS = "OTEL_PYTHON_INSTRUMENTATION_HTTP_CAPTURE_ALL_METHODS"

# Standard HTTP methods
_STANDARD_HTTP_METHODS = frozenset([
    "GET", "HEAD", "POST", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH"
])

# Sensitive query parameter names to redact
_SENSITIVE_QUERY_PARAMS = frozenset([
    "AWSAccessKeyId", "Signature", "X-Goog-Signature", "sig"
])


def sanitize_method(method: str) -> str:
    """Sanitize HTTP method.

    Returns the uppercase version of standard HTTP methods, or "_OTHER"
    for non-standard methods unless OTEL_PYTHON_INSTRUMENTATION_HTTP_CAPTURE_ALL_METHODS
    is set.
    """
    upper_method = method.upper()
    if upper_method in _STANDARD_HTTP_METHODS:
        return upper_method

    # Check if we should capture all methods
    capture_all = os.environ.get(OTEL_PYTHON_INSTRUMENTATION_HTTP_CAPTURE_ALL_METHODS, "")
    if capture_all.lower() in ("1", "true"):
        return upper_method

    return "_OTHER"


class ExcludeList:
    """List of URL patterns to exclude from instrumentation."""

    def __init__(self, patterns: List[str]):
        self._patterns = [re.compile(p) for p in patterns] if patterns else []

    def url_disabled(self, url: str) -> bool:
        """Check if a URL should be excluded."""
        for pattern in self._patterns:
            if pattern.search(url):
                return True
        return False


def get_excluded_urls(instrumentation_name: str) -> ExcludeList:
    """Get excluded URLs from environment variable.

    First checks for OTEL_PYTHON_{name}_EXCLUDED_URLS, then falls back to
    OTEL_PYTHON_EXCLUDED_URLS.
    """
    name_upper = instrumentation_name.upper()
    specific_env = f"OTEL_PYTHON_{name_upper}_EXCLUDED_URLS"
    generic_env = "OTEL_PYTHON_EXCLUDED_URLS"

    # Check specific env first
    if specific_env in os.environ:
        urls_str = os.environ.get(specific_env, "")
    else:
        urls_str = os.environ.get(generic_env, "")

    if not urls_str:
        return ExcludeList([])

    patterns = [p.strip() for p in urls_str.split(",") if p.strip()]
    return ExcludeList(patterns)


def remove_url_credentials(url: str) -> str:
    """Remove credentials from URL.

    Replaces username:password with REDACTED:REDACTED.
    """
    parsed = urlparse(url)
    if parsed.username or parsed.password:
        # Reconstruct the netloc with redacted credentials
        # Preserve IPv6 brackets if present in the original URL
        hostname = parsed.hostname
        if "[" in parsed.netloc:
            # IPv6 address, add brackets
            hostname = f"[{hostname}]"

        if parsed.port:
            netloc = f"REDACTED:REDACTED@{hostname}:{parsed.port}"
        else:
            netloc = f"REDACTED:REDACTED@{hostname}"
        return urlunparse((
            parsed.scheme,
            netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
    return url


def redact_query_parameters(url: str, query_params_to_redact: Optional[Sequence[str]] = None) -> str:
    """Redact sensitive query parameters from URL.

    Args:
        url: The URL to redact.
        query_params_to_redact: List of query parameter names to redact.
            Defaults to common sensitive parameter names.
    """
    if not url:
        return url

    parsed = urlparse(url)
    if not parsed.query:
        return url

    params_to_redact = set(query_params_to_redact) if query_params_to_redact else _SENSITIVE_QUERY_PARAMS

    # Parse query parameters
    query_params = parse_qsl(parsed.query, keep_blank_values=True)

    # Redact sensitive parameters
    redacted_params = []
    for key, value in query_params:
        if key in params_to_redact:
            redacted_params.append((key, "REDACTED"))
        else:
            redacted_params.append((key, value))

    # Reconstruct the query string manually to preserve special chars like @
    new_query = "&".join(f"{k}={v}" for k, v in redacted_params)
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))


def redact_url(url: str) -> str:
    """Redact both credentials and sensitive query parameters from URL."""
    url = remove_url_credentials(url)
    url = redact_query_parameters(url)
    return url


def get_custom_headers(env_var: str) -> List[str]:
    """Get custom headers from environment variable.

    Returns a list of header names parsed from the comma-separated environment variable.
    """
    headers_str = os.environ.get(env_var, "")
    if not headers_str:
        return []
    return [h.strip() for h in headers_str.split(",") if h.strip()]


class SanitizeValue:
    """Class for sanitizing header values based on a list of sensitive header names."""

    def __init__(self, sanitized_fields: Optional[List[str]] = None):
        self._sanitized_fields = set(
            f.lower() for f in (sanitized_fields or [])
        )

    def sanitize(self, header_name: str, value: str) -> str:
        """Sanitize a header value if the header name is in the sensitive list."""
        if header_name.lower() in self._sanitized_fields:
            return "[REDACTED]"
        return value

    def sanitize_header_value(self, header: str, value: str) -> str:
        """Sanitize a header value if the header name is in the sensitive list."""
        return self.sanitize(header, value)


def normalise_request_header_name(header: str) -> str:
    """Normalize a request header name to OpenTelemetry attribute format."""
    # Convert to lowercase and replace dashes with underscores
    normalized = header.lower().replace("-", "_")
    return f"http.request.header.{normalized}"


def normalise_response_header_name(header: str) -> str:
    """Normalize a response header name to OpenTelemetry attribute format."""
    # Convert to lowercase and replace dashes with underscores
    normalized = header.lower().replace("-", "_")
    return f"http.response.header.{normalized}"


# Bot patterns for synthetic user agent detection
_BOT_PATTERNS = [
    "googlebot", "bingbot", "yandexbot", "duckduckbot", "slurp", "baiduspider",
    "facebot", "facebookexternalhit", "ia_archiver", "spider", "crawler"
]

# Test patterns for synthetic user agent detection
_TEST_PATTERNS = [
    "alwayson", "synthetics", "pingdom", "gtmetrix", "newrelic"
]


def normalize_user_agent(user_agent) -> Optional[str]:
    """Normalize a user agent to a string.

    Handles bytes, bytearray, memoryview, and string inputs.
    Returns None if input is None.
    """
    if user_agent is None:
        return None
    if isinstance(user_agent, (bytes, bytearray, memoryview)):
        return bytes(user_agent).decode("utf-8", errors="replace")
    return str(user_agent)


def detect_synthetic_user_agent(user_agent: Optional[str]) -> Optional[str]:
    """Detect if a user agent is synthetic (bot or test).

    Returns 'test' for test patterns, 'bot' for bot patterns, or None.
    Test patterns take priority over bot patterns.
    """
    if not user_agent:
        return None

    user_agent_lower = user_agent.lower()

    # Check test patterns first (higher priority)
    for pattern in _TEST_PATTERNS:
        if pattern in user_agent_lower:
            return "test"

    # Check bot patterns
    for pattern in _BOT_PATTERNS:
        if pattern in user_agent_lower:
            return "bot"

    return None
