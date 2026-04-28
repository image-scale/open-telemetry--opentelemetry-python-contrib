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

"""Semantic conventions module."""

import os
from enum import Enum
from typing import Dict, Optional, Sequence

from opentelemetry.semconv._incubating.attributes.db_attributes import (
    DB_NAME,
    DB_OPERATION,
    DB_STATEMENT,
    DB_SYSTEM,
    DB_USER,
)
from opentelemetry.semconv.attributes.db_attributes import (
    DB_NAMESPACE,
    DB_OPERATION_NAME,
    DB_QUERY_TEXT,
    DB_SYSTEM_NAME,
)
from opentelemetry.trace.status import Status, StatusCode

OTEL_SEMCONV_STABILITY_OPT_IN = "OTEL_SEMCONV_STABILITY_OPT_IN"
_LEGACY_SCHEMA_VERSION = "1.11.0"

# Schema versions for different stability modes
_SCHEMA_VERSION_HTTP_STABLE = "1.21.0"
_SCHEMA_VERSION_DATABASE_STABLE = "1.25.0"
_SCHEMA_VERSION_GEN_AI_STABLE = "1.26.0"

HTTP_DURATION_HISTOGRAM_BUCKETS_NEW = [
    0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75,
    1.0, 2.5, 5.0, 7.5, 10.0,
]


class _StabilityMode(Enum):
    """Stability mode enum."""
    DEFAULT = "default"
    HTTP = "http"
    HTTP_DUP = "http/dup"
    DATABASE = "database"
    DATABASE_DUP = "database/dup"
    GEN_AI_LATEST_EXPERIMENTAL = "gen_ai_latest_experimental"


class _OpenTelemetryStabilitySignalType(Enum):
    """Stability signal type enum."""
    HTTP = "http"
    DATABASE = "database"
    GEN_AI = "gen_ai"


class _OpenTelemetrySemanticConventionStability:
    """Semantic convention stability manager."""

    _initialized = False
    _http_mode = _StabilityMode.DEFAULT
    _database_mode = _StabilityMode.DEFAULT
    _gen_ai_mode = _StabilityMode.DEFAULT

    @classmethod
    def _initialize(cls):
        """Initialize the stability manager from environment variables."""
        opt_in = os.environ.get(OTEL_SEMCONV_STABILITY_OPT_IN, "")

        # Parse comma-separated opt-in modes
        modes = [m.strip() for m in opt_in.split(",") if m.strip()]

        # Reset to defaults
        cls._http_mode = _StabilityMode.DEFAULT
        cls._database_mode = _StabilityMode.DEFAULT
        cls._gen_ai_mode = _StabilityMode.DEFAULT

        for mode in modes:
            if mode == "http":
                cls._http_mode = _StabilityMode.HTTP
            elif mode == "http/dup":
                # http/dup takes precedence over http
                if cls._http_mode != _StabilityMode.HTTP_DUP:
                    cls._http_mode = _StabilityMode.HTTP_DUP
            elif mode == "database":
                cls._database_mode = _StabilityMode.DATABASE
            elif mode == "database/dup":
                # database/dup takes precedence over database
                if cls._database_mode != _StabilityMode.DATABASE_DUP:
                    cls._database_mode = _StabilityMode.DATABASE_DUP
            elif mode == "gen_ai_latest_experimental":
                cls._gen_ai_mode = _StabilityMode.GEN_AI_LATEST_EXPERIMENTAL

        cls._initialized = True

    @classmethod
    def _get_opentelemetry_stability_opt_in_mode(
        cls,
        signal_type: _OpenTelemetryStabilitySignalType,
    ) -> _StabilityMode:
        """Get the opt-in mode for a signal type."""
        if not cls._initialized:
            cls._initialize()

        if signal_type == _OpenTelemetryStabilitySignalType.HTTP:
            return cls._http_mode
        elif signal_type == _OpenTelemetryStabilitySignalType.DATABASE:
            return cls._database_mode
        elif signal_type == _OpenTelemetryStabilitySignalType.GEN_AI:
            return cls._gen_ai_mode

        return _StabilityMode.DEFAULT


def _get_schema_version_for_opt_in_mode(
    signal_type: _OpenTelemetryStabilitySignalType,
    mode: _StabilityMode,
) -> str:
    """Get the schema version for an opt-in mode."""
    if signal_type == _OpenTelemetryStabilitySignalType.HTTP:
        if mode in (_StabilityMode.HTTP, _StabilityMode.HTTP_DUP):
            return _SCHEMA_VERSION_HTTP_STABLE
    elif signal_type == _OpenTelemetryStabilitySignalType.DATABASE:
        if mode in (_StabilityMode.DATABASE, _StabilityMode.DATABASE_DUP):
            return _SCHEMA_VERSION_DATABASE_STABLE
    elif signal_type == _OpenTelemetryStabilitySignalType.GEN_AI:
        if mode == _StabilityMode.GEN_AI_LATEST_EXPERIMENTAL:
            return _SCHEMA_VERSION_GEN_AI_STABLE

    return _LEGACY_SCHEMA_VERSION


def _get_schema_url_for_signal_types(
    signal_types: Sequence[_OpenTelemetryStabilitySignalType],
) -> str:
    """Get the schema URL for signal types.

    Returns the highest version schema URL needed by any of the signal types.
    """
    if not signal_types:
        return f"https://opentelemetry.io/schemas/{_LEGACY_SCHEMA_VERSION}"

    # Get the highest version across all signal types
    versions = []
    for signal_type in signal_types:
        mode = _OpenTelemetrySemanticConventionStability._get_opentelemetry_stability_opt_in_mode(
            signal_type
        )
        version = _get_schema_version_for_opt_in_mode(signal_type, mode)
        versions.append(version)

    # Compare version strings and get the highest
    def version_key(v: str):
        parts = v.split(".")
        return tuple(int(p) for p in parts)

    highest_version = max(versions, key=version_key)
    return f"https://opentelemetry.io/schemas/{highest_version}"


def _set_status(
    span,
    metrics_attributes: Dict,
    status_code: int,
    status_code_str: str,
    server_span: bool = False,
    sem_conv_opt_in_mode: _StabilityMode = _StabilityMode.DEFAULT,
):
    """Set status on span and metrics attributes."""
    is_recording = span.is_recording() if hasattr(span, 'is_recording') else True

    # Handle non-integer status codes
    if status_code < 0:
        if is_recording:
            span.set_status(
                Status(
                    StatusCode.ERROR,
                    f"Non-integer HTTP status: {status_code_str}"
                )
            )
        return

    # Determine if this is an error status
    is_error = status_code >= 500 if server_span else status_code >= 400

    # Set attributes based on mode
    use_old = sem_conv_opt_in_mode in (
        _StabilityMode.DEFAULT, _StabilityMode.HTTP_DUP
    )
    use_new = sem_conv_opt_in_mode in (
        _StabilityMode.HTTP, _StabilityMode.HTTP_DUP
    )

    if use_old:
        if is_recording:
            span.set_attribute("http.status_code", status_code)
        metrics_attributes["http.status_code"] = status_code

    if use_new:
        if is_recording:
            span.set_attribute("http.response.status_code", status_code)
        metrics_attributes["http.response.status_code"] = status_code

        # Set error.type for error status codes in new mode
        if is_error:
            if is_recording:
                span.set_attribute("error.type", status_code_str)
            metrics_attributes["error.type"] = status_code_str

    # Set span status for errors
    if is_error and is_recording:
        span.set_status(Status(StatusCode.ERROR))


def _set_db_system(
    result: Dict,
    value: Optional[str],
    sem_conv_opt_in_mode: _StabilityMode = _StabilityMode.DEFAULT,
):
    """Set db.system attribute."""
    if value is None:
        return

    use_old = sem_conv_opt_in_mode in (
        _StabilityMode.DEFAULT, _StabilityMode.DATABASE_DUP
    )
    use_new = sem_conv_opt_in_mode in (
        _StabilityMode.DATABASE, _StabilityMode.DATABASE_DUP
    )

    if use_old:
        result[DB_SYSTEM] = value
    if use_new:
        result[DB_SYSTEM_NAME] = value


def _set_db_name(
    result: Dict,
    value: Optional[str],
    sem_conv_opt_in_mode: _StabilityMode = _StabilityMode.DEFAULT,
):
    """Set db.name attribute."""
    if value is None:
        return

    use_old = sem_conv_opt_in_mode in (
        _StabilityMode.DEFAULT, _StabilityMode.DATABASE_DUP
    )
    use_new = sem_conv_opt_in_mode in (
        _StabilityMode.DATABASE, _StabilityMode.DATABASE_DUP
    )

    if use_old:
        result[DB_NAME] = value
    if use_new:
        result[DB_NAMESPACE] = value


def _set_db_statement(
    result: Dict,
    value: Optional[str],
    sem_conv_opt_in_mode: _StabilityMode = _StabilityMode.DEFAULT,
):
    """Set db.statement attribute."""
    if value is None:
        return

    use_old = sem_conv_opt_in_mode in (
        _StabilityMode.DEFAULT, _StabilityMode.DATABASE_DUP
    )
    use_new = sem_conv_opt_in_mode in (
        _StabilityMode.DATABASE, _StabilityMode.DATABASE_DUP
    )

    if use_old:
        result[DB_STATEMENT] = value
    if use_new:
        result[DB_QUERY_TEXT] = value


def _set_db_user(
    result: Dict,
    value: Optional[str],
    sem_conv_opt_in_mode: _StabilityMode = _StabilityMode.DEFAULT,
):
    """Set db.user attribute."""
    if value is None:
        return

    use_old = sem_conv_opt_in_mode in (
        _StabilityMode.DEFAULT, _StabilityMode.DATABASE_DUP
    )
    # db.user is deprecated and has no new replacement in stable semconv
    # Only set old attribute
    if use_old:
        result[DB_USER] = value


def _set_db_operation(
    result: Dict,
    value: Optional[str],
    sem_conv_opt_in_mode: _StabilityMode = _StabilityMode.DEFAULT,
):
    """Set db.operation attribute."""
    if value is None:
        return

    use_old = sem_conv_opt_in_mode in (
        _StabilityMode.DEFAULT, _StabilityMode.DATABASE_DUP
    )
    use_new = sem_conv_opt_in_mode in (
        _StabilityMode.DATABASE, _StabilityMode.DATABASE_DUP
    )

    if use_old:
        result[DB_OPERATION] = value
    if use_new:
        result[DB_OPERATION_NAME] = value


def _server_active_requests_count_attrs_old(
    method: str,
    scheme: str,
    host: str,
    port: Optional[int] = None,
    flavor: Optional[str] = None,
):
    """Old server active requests count attributes."""
    attrs = {
        "http.method": method,
        "http.scheme": scheme,
        "http.host": host,
    }
    if port:
        attrs["http.server_name"] = f"{host}:{port}"
    if flavor:
        attrs["http.flavor"] = flavor
    return attrs


def _server_active_requests_count_attrs_new(
    method: str,
    scheme: str,
    host: str,
    port: Optional[int] = None,
):
    """New server active requests count attributes."""
    attrs = {
        "http.request.method": method,
        "url.scheme": scheme,
        "server.address": host,
    }
    if port:
        attrs["server.port"] = port
    return attrs
