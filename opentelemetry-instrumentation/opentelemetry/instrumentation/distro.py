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

import logging
from abc import ABC, abstractmethod

_logger = logging.getLogger(__name__)


class BaseDistro(ABC):
    """Abstract base class for distributions.

    A distribution is a way to configure OpenTelemetry for a specific
    environment or use case. It can configure exporters, set environment
    variables, and load instrumentors.
    """

    @abstractmethod
    def _configure(self, **kwargs):
        """Configure the distribution.

        Subclasses must implement this method to perform the actual
        configuration.
        """
        pass

    def configure(self, **kwargs):
        """Configure the distribution.

        This method calls _configure with the given keyword arguments.
        """
        self._configure(**kwargs)

    def load_instrumentor(self, entry_point, **kwargs):
        """Load an instrumentor from an entry point.

        Args:
            entry_point: The entry point to load the instrumentor from.
            **kwargs: Additional arguments to pass to the instrumentor.

        Returns:
            The loaded instrumentor, or None if loading failed.
        """
        try:
            instrumentor_cls = entry_point.load()
            instrumentor = instrumentor_cls()
            instrumentor.instrument(**kwargs)
            return instrumentor
        except Exception as exc:
            _logger.warning(
                "Failed to load instrumentor %s: %s", entry_point.name, exc
            )
            return None


class DefaultDistro(BaseDistro):
    """Default distribution implementation.

    This distribution does not perform any configuration by default.
    """

    def _configure(self, **kwargs):
        """Configure the default distribution.

        This is a no-op for the default distribution.
        """
        pass
