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

"""Load module for auto instrumentation."""

import logging

from opentelemetry.instrumentation.dependencies import (
    DependencyConflict,
    get_dist_dependency_conflicts,
)
from opentelemetry.instrumentation.distro import BaseDistro, DefaultDistro
from opentelemetry.instrumentation.environment_variables import (
    OTEL_PYTHON_CONFIGURATOR,
    OTEL_PYTHON_DISABLED_INSTRUMENTATIONS,
    OTEL_PYTHON_DISTRO,
)
from opentelemetry.instrumentation.version import __version__
from opentelemetry.util._importlib_metadata import entry_points

_logger = logging.getLogger(__name__)


class _EntryPointDistFinder:
    """Entry point distribution finder."""

    def __init__(self):
        self._mapping = {}
        raise NotImplementedError

    def dist_for(self, entry_point):
        """Find the distribution for an entry point."""
        raise NotImplementedError


def _load_configurators():
    """Load configurators from entry points."""
    raise NotImplementedError


def _load_distro():
    """Load the distribution."""
    raise NotImplementedError


def _load_instrumentors(distro):
    """Load instrumentors from entry points."""
    raise NotImplementedError
