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

"""Base instrumentor implementation."""

import logging
from abc import ABC, abstractmethod
from typing import Collection, Optional

from opentelemetry.instrumentation.dependencies import (
    DependencyConflict,
    DependencyConflictError,
    get_dependency_conflicts,
)

_LOG = logging.getLogger(__name__)


class BaseInstrumentor(ABC):
    """Abstract base class for instrumentors."""

    _instance = None
    _is_instrumented_by_opentelemetry = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @abstractmethod
    def instrumentation_dependencies(self) -> Collection[str]:
        """Return the instrumentation dependencies."""
        pass

    @abstractmethod
    def _instrument(self, **kwargs):
        """Instrument the library."""
        pass

    @abstractmethod
    def _uninstrument(self, **kwargs):
        """Uninstrument the library."""
        pass

    def _check_dependency_conflicts(self) -> Optional[DependencyConflict]:
        """Check for dependency conflicts."""
        return get_dependency_conflicts(self.instrumentation_dependencies())

    def instrument(self, **kwargs):
        """Instrument the library.

        Args:
            **kwargs: Additional arguments passed to _instrument().
                raise_exception_on_conflict: If True, raise DependencyConflictError
                    when there are dependency conflicts. Default is True.

        Returns:
            The result of _instrument() if successful, None otherwise.

        Raises:
            DependencyConflictError: If raise_exception_on_conflict is True and
                there are dependency conflicts.
        """
        if self._is_instrumented_by_opentelemetry:
            _LOG.warning("Attempting to instrument while already instrumented")
            return None

        # Check for skip_dep_check flag (used in auto instrumentation)
        skip_dep_check = kwargs.pop("skip_dep_check", False)
        raise_exception_on_conflict = kwargs.pop("raise_exception_on_conflict", True)

        if not skip_dep_check:
            conflict = self._check_dependency_conflicts()
            if conflict is not None:
                if raise_exception_on_conflict:
                    raise DependencyConflictError(str(conflict))
                _LOG.error(conflict)
                return None

        result = self._instrument(**kwargs)
        self._is_instrumented_by_opentelemetry = True
        return result

    def uninstrument(self, **kwargs):
        """Uninstrument the library.

        Returns:
            The result of _uninstrument() if successful, None otherwise.
        """
        if not self._is_instrumented_by_opentelemetry:
            _LOG.warning("Attempting to uninstrument while not instrumented")
            return None

        result = self._uninstrument(**kwargs)
        self._is_instrumented_by_opentelemetry = False
        return result
