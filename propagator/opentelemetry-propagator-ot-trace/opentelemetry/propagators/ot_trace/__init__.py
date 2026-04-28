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

"""OT Trace Propagator."""

import re
from typing import Optional, Set

from opentelemetry import trace
from opentelemetry.baggage import get_all as get_all_baggage
from opentelemetry.baggage import set_baggage
from opentelemetry.context import Context
from opentelemetry.propagators.textmap import (
    CarrierT,
    Getter,
    Setter,
    TextMapPropagator,
    default_getter,
    default_setter,
)
from opentelemetry.trace import (
    INVALID_SPAN_ID,
    INVALID_TRACE_ID,
    NonRecordingSpan,
    SpanContext,
    TraceFlags,
    set_span_in_context,
)

# OT-Trace header names
OT_TRACE_ID_HEADER = "ot-tracer-traceid"
OT_SPAN_ID_HEADER = "ot-tracer-spanid"
OT_SAMPLED_HEADER = "ot-tracer-sampled"
OT_BAGGAGE_PREFIX = "ot-baggage-"

# Valid baggage key/value patterns (alphanumeric, dashes, underscores)
_VALID_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
_VALID_VALUE_PATTERN = re.compile(r"^[\x20-\x7E]+$")


class OTTracePropagator(TextMapPropagator):
    """OT Trace propagator.

    Propagates span context using OT-Trace format headers.
    """

    def extract(
        self,
        carrier: CarrierT,
        context: Optional[Context] = None,
        getter: Getter = default_getter,
    ) -> Context:
        """Extract span context from OT-Trace headers.

        Args:
            carrier: The carrier to extract from.
            context: The context to update, or None for current context.
            getter: The getter to use for extracting values.

        Returns:
            Updated context with extracted span context.
        """
        if context is None:
            context = Context()

        trace_id = self._get_header(carrier, getter, OT_TRACE_ID_HEADER)
        span_id = self._get_header(carrier, getter, OT_SPAN_ID_HEADER)
        sampled = self._get_header(carrier, getter, OT_SAMPLED_HEADER)

        if not trace_id or not span_id:
            return context

        # Parse trace ID (can be 16 or 32 hex chars)
        parsed_trace_id = self._parse_trace_id(trace_id)
        if parsed_trace_id is None or parsed_trace_id == INVALID_TRACE_ID:
            return context

        # Parse span ID (16 hex chars)
        parsed_span_id = self._parse_span_id(span_id)
        if parsed_span_id is None or parsed_span_id == INVALID_SPAN_ID:
            return context

        # Parse sampled flag
        trace_flags = TraceFlags.DEFAULT
        if sampled and sampled.lower() == "true":
            trace_flags = TraceFlags.SAMPLED

        span_context = SpanContext(
            trace_id=parsed_trace_id,
            span_id=parsed_span_id,
            is_remote=True,
            trace_flags=trace_flags,
        )

        context = set_span_in_context(NonRecordingSpan(span_context), context)

        # Extract baggage
        context = self._extract_baggage(carrier, getter, context)

        return context

    def inject(
        self,
        carrier: CarrierT,
        context: Optional[Context] = None,
        setter: Setter = default_setter,
    ) -> None:
        """Inject span context into OT-Trace headers.

        Args:
            carrier: The carrier to inject into.
            context: The context to get span from, or None for current context.
            setter: The setter to use for injecting values.
        """
        span = trace.get_current_span(context)
        span_context = span.get_span_context()

        if not span_context.is_valid:
            return

        # Format trace ID (truncate to 64 bits / 16 hex chars)
        trace_id_hex = format(span_context.trace_id, "x")
        # Take the lower 64 bits (last 16 hex chars)
        if len(trace_id_hex) > 16:
            trace_id_hex = trace_id_hex[-16:]

        # Format span ID
        span_id_hex = format(span_context.span_id, "x")

        # Format sampled flag
        sampled = "true" if span_context.trace_flags & TraceFlags.SAMPLED else "false"

        setter.set(carrier, OT_TRACE_ID_HEADER, trace_id_hex)
        setter.set(carrier, OT_SPAN_ID_HEADER, span_id_hex)
        setter.set(carrier, OT_SAMPLED_HEADER, sampled)

        # Inject baggage
        self._inject_baggage(carrier, context, setter)

    @property
    def fields(self) -> Set[str]:
        """Return the fields used by this propagator."""
        return {OT_TRACE_ID_HEADER, OT_SPAN_ID_HEADER, OT_SAMPLED_HEADER}

    def _get_header(
        self, carrier: CarrierT, getter: Getter, key: str
    ) -> Optional[str]:
        """Get a header value from the carrier."""
        header = getter.get(carrier, key)
        if not header:
            return None
        if isinstance(header, list):
            return header[0] if header else None
        return header

    def _parse_trace_id(self, value: str) -> Optional[int]:
        """Parse trace ID (16 or 32 hex chars)."""
        try:
            return int(value, 16)
        except ValueError:
            return None

    def _parse_span_id(self, value: str) -> Optional[int]:
        """Parse span ID (up to 16 hex chars)."""
        try:
            return int(value, 16)
        except ValueError:
            return None

    def _extract_baggage(
        self, carrier: CarrierT, getter: Getter, context: Context
    ) -> Context:
        """Extract baggage from carrier."""
        # Get all keys from carrier
        if hasattr(getter, "keys"):
            keys = getter.keys(carrier)
        elif hasattr(carrier, "keys"):
            keys = carrier.keys()
        else:
            keys = []

        for key in keys:
            if key.lower().startswith(OT_BAGGAGE_PREFIX):
                baggage_key = key[len(OT_BAGGAGE_PREFIX):]
                baggage_value = self._get_header(carrier, getter, key)
                if baggage_value:
                    context = set_baggage(baggage_key, baggage_value, context)

        return context

    def _inject_baggage(
        self, carrier: CarrierT, context: Optional[Context], setter: Setter
    ) -> None:
        """Inject baggage into carrier."""
        baggage = get_all_baggage(context)
        for key, value in baggage.items():
            # Validate key and value
            if self._is_valid_key(key) and self._is_valid_value(value):
                setter.set(carrier, f"{OT_BAGGAGE_PREFIX}{key}", value)

    def _is_valid_key(self, key: str) -> bool:
        """Check if baggage key is valid."""
        return bool(_VALID_KEY_PATTERN.match(key))

    def _is_valid_value(self, value: str) -> bool:
        """Check if baggage value is valid (ASCII printable)."""
        return bool(_VALID_VALUE_PATTERN.match(value))
