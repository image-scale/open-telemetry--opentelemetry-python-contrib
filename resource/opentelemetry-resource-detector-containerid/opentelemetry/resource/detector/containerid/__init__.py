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

"""Container ID Resource Detector."""

import logging
import re
from typing import Optional

from opentelemetry.sdk.resources import Resource, ResourceDetector
from opentelemetry.semconv.resource import ResourceAttributes

_logger = logging.getLogger(__name__)

# Container ID is a 64-character hex string
_CONTAINER_ID_PATTERN = re.compile(r'[a-f0-9]{64}')

# Path to cgroup file (cgroup v1)
_CGROUP_PATH = "/proc/self/cgroup"

# Path to mountinfo file (cgroup v2)
_MOUNTINFO_PATH = "/proc/self/mountinfo"


def _get_container_id_v1() -> Optional[str]:
    """Extract container ID from cgroup v1 file (/proc/self/cgroup).

    Returns the first 64-character hex string found in docker paths.
    """
    try:
        with open(_CGROUP_PATH, "r") as f:
            for line in f:
                # Look for docker or container paths
                if "/docker/" in line or "/docker-" in line:
                    match = _CONTAINER_ID_PATTERN.search(line)
                    if match:
                        return match.group(0)
        return None
    except Exception as e:
        _logger.debug("Failed to get container id. Exception: %s", e)
        return None


def _get_container_id_v2() -> Optional[str]:
    """Extract container ID from mountinfo file (/proc/self/mountinfo).

    Returns the first 64-character hex string found in docker paths.
    """
    try:
        with open(_MOUNTINFO_PATH, "r") as f:
            for line in f:
                # Look for docker paths
                if "/docker/containers/" in line or "/docker-" in line:
                    match = _CONTAINER_ID_PATTERN.search(line)
                    if match:
                        return match.group(0)
        return None
    except Exception as e:
        _logger.debug("Failed to get container id. Exception: %s", e)
        return None


def _get_container_id() -> Optional[str]:
    """Get the container ID.

    First tries cgroup v1, then falls back to cgroup v2 (mountinfo).
    """
    container_id = _get_container_id_v1()
    if container_id is None:
        container_id = _get_container_id_v2()
    return container_id


class ContainerResourceDetector(ResourceDetector):
    """Container ID resource detector."""

    def detect(self) -> Resource:
        """Detect the container ID and return it as a Resource.

        Returns:
            A Resource with container.id attribute, or empty Resource if
            container ID cannot be detected.
        """
        container_id = _get_container_id()
        if container_id:
            return Resource({ResourceAttributes.CONTAINER_ID: container_id})
        return Resource({})
