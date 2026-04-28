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

"""Base distribution implementation."""

from abc import ABC, abstractmethod
from typing import Collection

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class BaseDistro(ABC):
    """Abstract base class for distributions."""

    @abstractmethod
    def _configure(self, **kwargs):
        """Configure the distribution."""
        pass

    def configure(self, **kwargs):
        """Configure the distribution."""
        raise NotImplementedError

    def load_instrumentor(self, entry_point, **kwargs):
        """Load an instrumentor from an entry point."""
        raise NotImplementedError


class DefaultDistro(BaseDistro):
    """Default distribution implementation."""

    def _configure(self, **kwargs):
        """Configure the default distribution."""
        pass
