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

from typing import Collection, Optional, Union, List

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


def _format_requirement_for_dist(req: Requirement) -> str:
    """Format a requirement string with correct spacing for dist conflicts.

    Removes spaces around version specifier operators but preserves spaces in markers.
    """
    result = req.name
    if req.specifier:
        # Join specifier without spaces
        result += str(req.specifier).replace(" ", "")
    if req.marker:
        result += f"; {req.marker}"
    return result


def _check_requirement(req: Requirement, original_str: Optional[str] = None) -> Optional[DependencyConflict]:
    """Check if a single requirement is satisfied.

    Returns DependencyConflict if not satisfied, None otherwise.
    """
    try:
        installed_version = version(req.name)
        # Check if the installed version satisfies the requirement
        if req.specifier and not req.specifier.contains(installed_version):
            # Use original string if provided, otherwise format
            req_str = original_str if original_str else str(req)
            return DependencyConflict(
                req_str, f"{req.name} {installed_version}"
            )
        return None
    except PackageNotFoundError:
        req_str = original_str if original_str else str(req)
        return DependencyConflict(req_str, None)


def get_dependency_conflicts(
    deps: Collection[Union[str, Requirement]],
) -> Optional[DependencyConflict]:
    """Check if there are any dependency conflicts.

    Args:
        deps: A collection of dependencies to check.

    Returns:
        A DependencyConflict if there is a conflict, None otherwise.
    """
    if not deps:
        return None

    for dep in deps:
        original_str = None
        if isinstance(dep, str):
            original_str = dep
            dep = Requirement(dep)

        conflict = _check_requirement(dep, original_str)
        if conflict is not None:
            return conflict

    return None


class _AnyDependencyConflict(DependencyConflict):
    """DependencyConflict for 'any of the following' requirements."""

    def __str__(self) -> str:
        return f'DependencyConflict: requested any of the following: "{self.required}" but found: "{self.found}"'


def get_dist_dependency_conflicts(
    dist: Distribution,
) -> Optional[DependencyConflict]:
    """Check for dependency conflicts in a distribution.

    Args:
        dist: A distribution to check.

    Returns:
        A DependencyConflict if there is a conflict, None otherwise.
    """
    requires = dist.requires
    if requires is None:
        return None

    # Separate "instruments" (AND) dependencies from "instruments-any" (OR) dependencies
    and_deps: List[Requirement] = []
    any_deps: List[Requirement] = []

    for req_str in requires:
        req = Requirement(req_str)
        # Check if this is an instrumentation dependency
        if req.marker is not None:
            marker_str = str(req.marker)
            if 'extra == "instruments-any"' in marker_str:
                any_deps.append(req)
            elif 'extra == "instruments"' in marker_str:
                and_deps.append(req)

    # Check AND dependencies (all must be satisfied)
    for req in and_deps:
        try:
            installed_version = version(req.name)
            # Check if the installed version satisfies the requirement
            if req.specifier and not req.specifier.contains(installed_version):
                return DependencyConflict(
                    _format_requirement_for_dist(req),
                    f"{req.name} {installed_version}"
                )
        except PackageNotFoundError:
            return DependencyConflict(_format_requirement_for_dist(req), None)

    # Check OR dependencies (at least one must be satisfied)
    if any_deps:
        any_satisfied = False
        found_versions: List[str] = []

        for req in any_deps:
            try:
                installed_version = version(req.name)
                # Check if the installed version satisfies the requirement
                if req.specifier and not req.specifier.contains(installed_version):
                    continue
                any_satisfied = True
                found_versions.append(f"{req.name} {installed_version}")
                break
            except PackageNotFoundError:
                continue

        if not any_satisfied:
            # Format the requirement strings
            req_strs = [_format_requirement_for_dist(req) for req in any_deps]
            return _AnyDependencyConflict(req_strs, found_versions)

    return None
