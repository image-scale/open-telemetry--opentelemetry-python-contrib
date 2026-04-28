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

"""Bootstrap module for auto-instrumentation."""

from typing import Collection, Optional

from opentelemetry.instrumentation.bootstrap_gen import (
    default_instrumentations,
    libraries,
)


def run(
    libraries: Optional[Collection] = None,
    default_instrumentations: Optional[Collection] = None,
):
    """Run the bootstrap process."""
    raise NotImplementedError


def _find_installed_libraries() -> Collection:
    """Find installed libraries that can be instrumented."""
    raise NotImplementedError


def _sys_pip_install(package: str):
    """Install a package using pip."""
    raise NotImplementedError


def _pip_check():
    """Check pip packages."""
    raise NotImplementedError


def _is_installed(package: str) -> bool:
    """Check if a package is installed."""
    raise NotImplementedError
