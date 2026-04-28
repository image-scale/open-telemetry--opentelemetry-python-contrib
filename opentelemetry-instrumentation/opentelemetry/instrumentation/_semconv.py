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

from enum import Enum
from typing import Dict, List, Optional, Sequence

OTEL_SEMCONV_STABILITY_OPT_IN = "OTEL_SEMCONV_STABILITY_OPT_IN"
_LEGACY_SCHEMA_VERSION = "1.11.0"

HTTP_DURATION_HISTOGRAM_BUCKETS_NEW = []


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
        """Initialize the stability manager."""
        raise NotImplementedError

    @classmethod
    def _get_opentelemetry_stability_opt_in_mode(
        cls,
        signal_type: _OpenTelemetryStabilitySignalType,
    ) -> _StabilityMode:
        """Get the opt-in mode for a signal type."""
        raise NotImplementedError


def _get_schema_version_for_opt_in_mode(
    signal_type: _OpenTelemetryStabilitySignalType,
    mode: _StabilityMode,
) -> str:
    """Get the schema version for an opt-in mode."""
    raise NotImplementedError


def _get_schema_url_for_signal_types(
    signal_types: Sequence[_OpenTelemetryStabilitySignalType],
) -> str:
    """Get the schema URL for signal types."""
    raise NotImplementedError


def _set_status(
    span,
    metrics_attributes: Dict,
    status_code: int,
    status_code_str: str,
    server_span: bool = False,
    sem_conv_opt_in_mode: _StabilityMode = _StabilityMode.DEFAULT,
):
    """Set status on span and metrics attributes."""
    raise NotImplementedError


def _set_db_system(
    result: Dict,
    value: Optional[str],
    sem_conv_opt_in_mode: _StabilityMode = _StabilityMode.DEFAULT,
):
    """Set db.system attribute."""
    raise NotImplementedError


def _set_db_name(
    result: Dict,
    value: Optional[str],
    sem_conv_opt_in_mode: _StabilityMode = _StabilityMode.DEFAULT,
):
    """Set db.name attribute."""
    raise NotImplementedError


def _set_db_statement(
    result: Dict,
    value: Optional[str],
    sem_conv_opt_in_mode: _StabilityMode = _StabilityMode.DEFAULT,
):
    """Set db.statement attribute."""
    raise NotImplementedError


def _set_db_user(
    result: Dict,
    value: Optional[str],
    sem_conv_opt_in_mode: _StabilityMode = _StabilityMode.DEFAULT,
):
    """Set db.user attribute."""
    raise NotImplementedError


def _set_db_operation(
    result: Dict,
    value: Optional[str],
    sem_conv_opt_in_mode: _StabilityMode = _StabilityMode.DEFAULT,
):
    """Set db.operation attribute."""
    raise NotImplementedError


def _server_active_requests_count_attrs_old(*args, **kwargs):
    """Old server active requests count attributes."""
    raise NotImplementedError


def _server_active_requests_count_attrs_new(*args, **kwargs):
    """New server active requests count attributes."""
    raise NotImplementedError
