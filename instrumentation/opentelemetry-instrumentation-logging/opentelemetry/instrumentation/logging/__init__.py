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

"""OpenTelemetry Logging Instrumentation."""

import logging

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor

DEFAULT_LOGGING_FORMAT = "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s resource.service.name=%(otelServiceName)s trace_sampled=%(otelTraceSampled)s] - %(message)s"


def _setup_logging_handler(logger_provider=None, log_code_attributes=False):
    """Set up logging handler."""
    raise NotImplementedError


class LoggingInstrumentor(BaseInstrumentor):
    """Logging instrumentor."""

    def instrumentation_dependencies(self):
        return []

    def _instrument(self, **kwargs):
        raise NotImplementedError

    def _uninstrument(self, **kwargs):
        raise NotImplementedError
