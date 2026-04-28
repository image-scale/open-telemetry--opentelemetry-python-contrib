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
        """Set a header value.

        If the key already exists, append the value with ", ".
        """
        if key in carrier:
            carrier[key] = carrier[key] + ", " + value
        else:
            carrier[key] = value


class TraceResponsePropagator:
    """Propagator for trace response headers."""

    def inject(
        self,
        carrier: Dict,
        context: Optional[Context] = None,
    ) -> None:
        """Inject trace context into response headers.

        Injects the traceresponse header in W3C Trace Context format.
        """
        setter = DictHeaderSetter()
        span = get_current_span(context)
        span_context = span.get_span_context()

        # Format trace ID and span ID as hex strings with proper padding
        trace_id = format(span_context.trace_id, "032x")
        span_id = format(span_context.span_id, "016x")
        trace_flags = format(span_context.trace_flags, "02x")

        # W3C Trace Context format: version-traceid-spanid-flags
        traceresponse = f"00-{trace_id}-{span_id}-{trace_flags}"

        setter.set(carrier, "traceresponse", traceresponse)
        setter.set(carrier, "Access-Control-Expose-Headers", "traceresponse")


def get_global_response_propagator():
    """Get the global response propagator."""
    return _RESPONSE_PROPAGATOR


def set_global_response_propagator(propagator):
    """Set the global response propagator."""
    global _RESPONSE_PROPAGATOR
    _RESPONSE_PROPAGATOR = propagator
