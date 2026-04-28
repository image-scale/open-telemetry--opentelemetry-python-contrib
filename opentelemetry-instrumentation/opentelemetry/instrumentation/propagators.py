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

"""Propagators module for response propagation."""

from typing import Optional, Dict

from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.trace.propagation import get_current_span


_RESPONSE_PROPAGATOR = None


class DictHeaderSetter:
    """Setter for dict headers."""

    def set(self, carrier: Dict, key: str, value: str) -> None:
        """Set a header value."""
        raise NotImplementedError


class TraceResponsePropagator:
    """Propagator for trace response headers."""

    def inject(
        self,
        carrier: Dict,
        context: Optional[Context] = None,
    ) -> None:
        """Inject trace context into response headers."""
        raise NotImplementedError


def get_global_response_propagator():
    """Get the global response propagator."""
    raise NotImplementedError


def set_global_response_propagator(propagator):
    """Set the global response propagator."""
    raise NotImplementedError
