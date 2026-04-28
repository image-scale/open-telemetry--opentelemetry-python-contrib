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

"""Dependencies module for checking instrumentation dependencies."""

from typing import Collection, Optional, Union, Sequence, List

from packaging.requirements import Requirement

from opentelemetry.util._importlib_metadata import (
    Distribution,
    PackageNotFoundError,
    version,
)


class DependencyConflict:
    """Represents a dependency conflict."""

    def __init__(self, required: str, found: Optional[str]):
        self.required = required
        self.found = found

    def __str__(self) -> str:
        return f'DependencyConflict: requested: "{self.required}" but found: "{self.found}"'


class DependencyConflictError(Exception):
    """Exception raised when there is a dependency conflict."""
    pass


def get_dependency_conflicts(
    deps: Collection[Union[str, Requirement]],
) -> Optional[DependencyConflict]:
    """Check if there are any dependency conflicts.

    Args:
        deps: A collection of dependencies to check.

    Returns:
        A DependencyConflict if there is a conflict, None otherwise.
    """
    raise NotImplementedError


def get_dist_dependency_conflicts(
    dist: Distribution,
) -> Optional[DependencyConflict]:
    """Check for dependency conflicts in a distribution.

    Args:
        dist: A distribution to check.

    Returns:
        A DependencyConflict if there is a conflict, None otherwise.
    """
    raise NotImplementedError
