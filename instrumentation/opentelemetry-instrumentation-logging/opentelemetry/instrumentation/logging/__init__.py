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
import os
from typing import Callable, Collection, Optional

from opentelemetry import trace
from opentelemetry._logs import get_logger_provider
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.logging.handler import LoggingHandler
from opentelemetry.sdk.resources import Resource

_logger = logging.getLogger(__name__)

DEFAULT_LOGGING_FORMAT = (
    "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] "
    "[trace_id=%(otelTraceID)s span_id=%(otelSpanID)s "
    "resource.service.name=%(otelServiceName)s "
    "trace_sampled=%(otelTraceSampled)s] - %(message)s"
)

# Environment variables
OTEL_PYTHON_LOG_CORRELATION = "OTEL_PYTHON_LOG_CORRELATION"
OTEL_PYTHON_LOG_FORMAT = "OTEL_PYTHON_LOG_FORMAT"
OTEL_PYTHON_LOG_LEVEL = "OTEL_PYTHON_LOG_LEVEL"
OTEL_PYTHON_LOG_CODE_ATTRIBUTES = "OTEL_PYTHON_LOG_CODE_ATTRIBUTES"
OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED = (
    "OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED"
)
OTEL_PYTHON_LOG_AUTO_INSTRUMENTATION = "OTEL_PYTHON_LOG_AUTO_INSTRUMENTATION"


def _setup_logging_handler(
    logger_provider=None,
    log_code_attributes: bool = False,
):
    """Set up the LoggingHandler on the root logger.

    Args:
        logger_provider: The OTel logger provider to use.
        log_code_attributes: Whether to include code location attributes.
    """
    handler = LoggingHandler(
        logger_provider=logger_provider,
        log_code_attributes=log_code_attributes,
    )
    logging.getLogger().addHandler(handler)


class _OTelLoggingFilter(logging.Filter):
    """Filter that injects trace context into log records."""

    def __init__(
        self,
        tracer_provider: Optional[trace.TracerProvider] = None,
        log_hook: Optional[Callable] = None,
    ):
        super().__init__()
        self._tracer_provider = tracer_provider
        self._log_hook = log_hook
        self._service_name = self._get_service_name()

    def _get_service_name(self) -> str:
        """Get the service name from the tracer provider's resource."""
        try:
            if self._tracer_provider and hasattr(
                self._tracer_provider, "resource"
            ):
                resource = self._tracer_provider.resource
                if hasattr(resource, "attributes"):
                    return resource.attributes.get(
                        "service.name", "unknown_service"
                    )
            # Try getting from global tracer provider
            provider = trace.get_tracer_provider()
            if hasattr(provider, "resource"):
                resource = provider.resource
                if hasattr(resource, "attributes"):
                    return resource.attributes.get(
                        "service.name", "unknown_service"
                    )
        except Exception:
            pass
        return "unknown_service"

    def filter(self, record: logging.LogRecord) -> bool:
        """Inject trace context into the log record.

        Args:
            record: The log record to filter.

        Returns:
            True to allow the record to be logged.
        """
        # Get the current span context
        span = trace.get_current_span()
        span_context = span.get_span_context()

        # Inject trace context
        if span_context.is_valid:
            record.otelTraceID = format(span_context.trace_id, "032x")
            record.otelSpanID = format(span_context.span_id, "016x")
            record.otelTraceSampled = span_context.trace_flags.sampled
        else:
            record.otelTraceID = "0"
            record.otelSpanID = "0"
            record.otelTraceSampled = False

        # Get service name
        if self._tracer_provider and hasattr(self._tracer_provider, "resource"):
            try:
                resource = self._tracer_provider.resource
                if hasattr(resource, "attributes"):
                    record.otelServiceName = resource.attributes.get(
                        "service.name", ""
                    )
                else:
                    record.otelServiceName = ""
            except Exception:
                record.otelServiceName = ""
        else:
            record.otelServiceName = self._service_name

        # Call log hook if provided
        if self._log_hook:
            try:
                self._log_hook(span, record)
            except Exception:
                pass

        return True


class LoggingInstrumentor(BaseInstrumentor):
    """Logging instrumentor.

    Instruments Python logging to inject trace context into log records
    and optionally export logs to OpenTelemetry.
    """

    _filter: Optional[_OTelLoggingFilter] = None
    _handler: Optional[LoggingHandler] = None

    def instrumentation_dependencies(self) -> Collection[str]:
        """Return the instrumentation dependencies."""
        return []

    def _instrument(self, **kwargs):
        """Instrument Python logging.

        Args:
            tracer_provider: The tracer provider to use for trace context.
            set_logging_format: If True, set the logging format to include
                trace context.
            logging_format: Custom logging format to use.
            log_level: The logging level to use.
            log_hook: A callable to be called for each log record.
            enable_log_auto_instrumentation: If False, skip setting up the
                LoggingHandler for exporting logs.
            log_code_attributes: If True, include code location attributes.
        """
        tracer_provider = kwargs.get("tracer_provider")
        set_logging_format = kwargs.get("set_logging_format", False)
        logging_format = kwargs.get("logging_format")
        log_level = kwargs.get("log_level")
        log_hook = kwargs.get("log_hook")
        enable_log_auto_instrumentation = kwargs.get(
            "enable_log_auto_instrumentation", True
        )
        log_code_attributes = kwargs.get("log_code_attributes", False)

        # Check environment variables for log correlation
        env_set_logging_format = (
            os.environ.get(OTEL_PYTHON_LOG_CORRELATION, "").lower() == "true"
        )
        if env_set_logging_format:
            set_logging_format = True

        # Check environment variable for log code attributes
        env_log_code_attributes = (
            os.environ.get(OTEL_PYTHON_LOG_CODE_ATTRIBUTES, "").lower()
            == "true"
        )
        if env_log_code_attributes:
            log_code_attributes = True

        # Get format and level from environment variables if not provided
        if logging_format is None:
            logging_format = os.environ.get(
                OTEL_PYTHON_LOG_FORMAT, DEFAULT_LOGGING_FORMAT
            )
        if log_level is None:
            env_log_level = os.environ.get(OTEL_PYTHON_LOG_LEVEL, "info")
            log_level = getattr(logging, env_log_level.upper(), logging.INFO)

        # Set up logging format if requested
        if set_logging_format:
            logging.basicConfig(format=logging_format, level=log_level)

            # Create and add the filter for trace context injection
            self._filter = _OTelLoggingFilter(
                tracer_provider=tracer_provider,
                log_hook=log_hook,
            )
            logging.getLogger().addFilter(self._filter)
        elif log_hook:
            # Even without format, we can add a filter for the hook
            self._filter = _OTelLoggingFilter(
                tracer_provider=tracer_provider,
                log_hook=log_hook,
            )
            logging.getLogger().addFilter(self._filter)

        # Check if SDK auto-instrumentation is enabled (deprecated)
        sdk_auto_enabled = (
            os.environ.get(
                OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED, ""
            ).lower()
            == "true"
        )
        if sdk_auto_enabled:
            _logger.warning(
                "Skipping installation of LoggingHandler from "
                "`opentelemetry-instrumentation-logging` to avoid duplicate "
                "logs. The SDK's deprecated LoggingHandler is already active "
                "(OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true). "
                "To migrate, unset this environment variable. The SDK's "
                "handler will be removed in a future release."
            )
            return

        # Check if auto-instrumentation is disabled
        auto_instrumentation_disabled = (
            os.environ.get(OTEL_PYTHON_LOG_AUTO_INSTRUMENTATION, "").lower()
            == "false"
        )
        if auto_instrumentation_disabled or not enable_log_auto_instrumentation:
            return

        # Set up logging handler
        logger_provider = get_logger_provider()
        _setup_logging_handler(
            logger_provider=logger_provider,
            log_code_attributes=log_code_attributes,
        )

    def _uninstrument(self, **kwargs):
        """Uninstrument Python logging."""
        root_logger = logging.getLogger()

        # Remove our filter
        if self._filter is not None:
            root_logger.removeFilter(self._filter)
            self._filter = None

        # Remove LoggingHandler instances
        handlers_to_remove = [
            h for h in root_logger.handlers if isinstance(h, LoggingHandler)
        ]
        for handler in handlers_to_remove:
            root_logger.removeHandler(handler)
