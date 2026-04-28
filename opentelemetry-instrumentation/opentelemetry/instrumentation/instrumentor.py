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
        raise NotImplementedError

    def instrument(self, **kwargs):
        """Instrument the library."""
        raise NotImplementedError

    def uninstrument(self, **kwargs):
        """Uninstrument the library."""
        raise NotImplementedError
