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

"""Logging handler for OpenTelemetry."""

import logging
from typing import Optional

from opentelemetry._logs import LoggerProvider, get_logger_provider
from opentelemetry._logs import SeverityNumber


def _get_severity_number(level: int) -> SeverityNumber:
    """Map Python logging level to OTel severity number."""
    if level >= logging.CRITICAL:
        return SeverityNumber.FATAL
    if level >= logging.ERROR:
        return SeverityNumber.ERROR
    if level >= logging.WARNING:
        return SeverityNumber.WARN
    if level >= logging.INFO:
        return SeverityNumber.INFO
    if level >= logging.DEBUG:
        return SeverityNumber.DEBUG
    return SeverityNumber.TRACE


class LoggingHandler(logging.Handler):
    """Logging handler that exports logs to OpenTelemetry.

    This handler converts Python log records to OpenTelemetry logs
    and exports them using the configured logger provider.
    """

    def __init__(
        self,
        level: int = logging.NOTSET,
        logger_provider: Optional[LoggerProvider] = None,
        log_code_attributes: bool = False,
    ):
        """Initialize the handler.

        Args:
            level: The logging level threshold.
            logger_provider: The OTel logger provider to use.
            log_code_attributes: Whether to include code location attributes.
        """
        super().__init__(level)
        self._logger_provider = logger_provider or get_logger_provider()
        self._log_code_attributes = log_code_attributes
        self._otel_logger = None
        if self._logger_provider:
            self._otel_logger = self._logger_provider.get_logger(
                __name__,
            )

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record.

        Args:
            record: The Python log record to emit.
        """
        if self._otel_logger is None:
            return

        try:
            # Get attributes from the record
            attributes = {}

            if self._log_code_attributes:
                attributes["code.filepath"] = record.pathname
                attributes["code.lineno"] = record.lineno
                attributes["code.function"] = record.funcName

            # Emit the log
            self._otel_logger.emit(
                self.format(record),
                severity_number=_get_severity_number(record.levelno),
                attributes=attributes,
            )
        except Exception:  # pylint: disable=broad-except
            self.handleError(record)
