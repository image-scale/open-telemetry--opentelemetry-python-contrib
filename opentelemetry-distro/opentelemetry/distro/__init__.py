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

"""OpenTelemetry Distro package."""

import os

from opentelemetry.environment_variables import (
    OTEL_METRICS_EXPORTER,
    OTEL_TRACES_EXPORTER,
)
from opentelemetry.instrumentation.distro import BaseDistro
from opentelemetry.sdk.environment_variables import OTEL_EXPORTER_OTLP_PROTOCOL


class OpenTelemetryDistro(BaseDistro):
    """OpenTelemetry distribution.

    Configures OpenTelemetry with default settings for OTLP export
    over gRPC protocol.
    """

    def _configure(self, **kwargs):
        """Configure the distribution.

        Sets default environment variables for traces and metrics export
        using OTLP over gRPC.
        """
        # Set default exporter to OTLP if not already set
        if OTEL_TRACES_EXPORTER not in os.environ:
            os.environ[OTEL_TRACES_EXPORTER] = "otlp"

        if OTEL_METRICS_EXPORTER not in os.environ:
            os.environ[OTEL_METRICS_EXPORTER] = "otlp"

        if OTEL_EXPORTER_OTLP_PROTOCOL not in os.environ:
            os.environ[OTEL_EXPORTER_OTLP_PROTOCOL] = "grpc"
