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

"""AWS X-Ray Propagator."""

import logging
import os
import re
from typing import Optional, Set

from opentelemetry import trace
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
    NonRecordingSpan,
    SpanContext,
    TraceFlags,
    TraceState,
    set_span_in_context,
)

_logger = logging.getLogger(__name__)

TRACE_HEADER_KEY = "X-Amzn-Trace-Id"
_AWS_XRAY_LAMBDA_ENV_KEY = "_X_AMZN_TRACE_ID"

# X-Ray trace ID format:
# Root=1-{8 hex timestamp}-{24 hex random}
# Parent={16 hex span id}
# Sampled={0|1}
_TRACE_ID_VERSION = "1"
_TRACE_ID_DELIMITER = "-"

# Regex to parse X-Ray trace header
_XRAY_TRACE_ID_REGEX = re.compile(
    r"^1-([0-9a-f]{8})-([0-9a-f]{24})$", re.IGNORECASE
)


class AwsXRayPropagator(TextMapPropagator):
    """AWS X-Ray propagator.

    Propagates span context in AWS X-Ray format via the X-Amzn-Trace-Id header.
    """

    def extract(
        self,
        carrier: CarrierT,
        context: Optional[Context] = None,
        getter: Getter = default_getter,
    ) -> Context:
        """Extract span context from X-Ray trace header.

        Args:
            carrier: The carrier to extract from.
            context: The context to update, or None for current context.
            getter: The getter to use for extracting values.

        Returns:
            Updated context with extracted span context, or original context
            if extraction fails.
        """
        if context is None:
            context = Context()

        trace_header = self._get_header(carrier, getter)
        if not trace_header:
            return context

        trace_id, span_id, sampled = self._parse_trace_header(trace_header)
        if trace_id is None or span_id is None or sampled is None:
            return context

        # Get trace state from existing span context if present
        existing_span = trace.get_current_span(context)
        existing_span_context = existing_span.get_span_context()
        trace_state = existing_span_context.trace_state if existing_span_context.is_valid else TraceState()

        span_context = SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            is_remote=True,
            trace_flags=TraceFlags(sampled),
            trace_state=trace_state,
        )

        return set_span_in_context(NonRecordingSpan(span_context), context)

    def inject(
        self,
        carrier: CarrierT,
        context: Optional[Context] = None,
        setter: Setter = default_setter,
    ) -> None:
        """Inject span context into X-Ray trace header.

        Args:
            carrier: The carrier to inject into.
            context: The context to get span from, or None for current context.
            setter: The setter to use for injecting values.
        """
        span = trace.get_current_span(context)
        span_context = span.get_span_context()

        if not span_context.is_valid:
            return

        # Format trace ID: 1-{8 hex timestamp}-{24 hex random}
        trace_id_hex = format(span_context.trace_id, "032x")
        xray_trace_id = f"1-{trace_id_hex[:8]}-{trace_id_hex[8:]}"

        # Format span ID
        span_id_hex = format(span_context.span_id, "016x")

        # Format sampled flag
        try:
            sampled = "1" if span_context.trace_flags & TraceFlags.SAMPLED else "0"
        except TypeError:
            sampled = "0"

        trace_header = f"Root={xray_trace_id};Parent={span_id_hex};Sampled={sampled}"

        setter.set(carrier, TRACE_HEADER_KEY, trace_header)

    @property
    def fields(self) -> Set[str]:
        """Return the fields used by this propagator."""
        return {TRACE_HEADER_KEY}

    def _get_header(
        self, carrier: CarrierT, getter: Getter
    ) -> Optional[str]:
        """Get the X-Ray trace header from the carrier."""
        header = getter.get(carrier, TRACE_HEADER_KEY)
        if not header:
            return None
        if isinstance(header, list):
            return header[0] if header else None
        return header

    def _parse_trace_header(
        self, trace_header: str
    ) -> tuple:
        """Parse the X-Ray trace header.

        Returns:
            Tuple of (trace_id, span_id, sampled) or (None, None, None) on error.
        """
        trace_id = None
        span_id = None
        sampled = None

        # Split by semicolon and parse each part
        parts = trace_header.split(";")
        for part in parts:
            part = part.strip()
            if "=" not in part:
                continue

            key, value = part.split("=", 1)
            key = key.strip()
            value = value.strip()

            if key.lower() == "root":
                trace_id = self._parse_trace_id(value)
            elif key.lower() == "parent":
                span_id = self._parse_span_id(value)
            elif key.lower() == "sampled":
                sampled = self._parse_sampled(value)

        return trace_id, span_id, sampled

    def _parse_trace_id(self, value: str) -> Optional[int]:
        """Parse X-Ray trace ID to OpenTelemetry trace ID."""
        match = _XRAY_TRACE_ID_REGEX.match(value)
        if not match:
            return None

        timestamp = match.group(1)
        random_part = match.group(2)

        try:
            return int(timestamp + random_part, 16)
        except ValueError:
            return None

    def _parse_span_id(self, value: str) -> Optional[int]:
        """Parse X-Ray parent (span) ID."""
        if len(value) != 16:
            return None

        try:
            return int(value, 16)
        except ValueError:
            return None

    def _parse_sampled(self, value: str) -> Optional[int]:
        """Parse X-Ray sampled flag."""
        if len(value) != 1:
            return None

        try:
            sampled = int(value)
            if sampled not in (0, 1):
                return None
            return sampled
        except ValueError:
            return None


class AwsXRayLambdaPropagator(AwsXRayPropagator):
    """AWS X-Ray Lambda propagator.

    Extends AwsXRayPropagator to also check the _X_AMZN_TRACE_ID environment
    variable, which is set by AWS Lambda when propagating trace context.
    """

    def extract(
        self,
        carrier: CarrierT,
        context: Optional[Context] = None,
        getter: Getter = default_getter,
    ) -> Context:
        """Extract span context from X-Ray trace header.

        If the context already has a valid span, extracts from the carrier
        (for linking purposes). Otherwise, checks the _X_AMZN_TRACE_ID
        environment variable first, then falls back to the carrier header.

        Args:
            carrier: The carrier to extract from.
            context: The context to update, or None for current context.
            getter: The getter to use for extracting values.

        Returns:
            Updated context with extracted span context.
        """
        if context is None:
            context = Context()

        # Check if there's already a valid span in context
        existing_span = trace.get_current_span(context)
        existing_span_context = existing_span.get_span_context()

        # If we already have a valid span, extract from carrier (for linking)
        if existing_span_context.is_valid:
            trace_header = self._get_header(carrier, getter)
            if trace_header:
                return super().extract(carrier, context, getter)
            return context

        # No valid span - try the Lambda environment variable first
        env_trace_header = os.environ.get(_AWS_XRAY_LAMBDA_ENV_KEY)
        if env_trace_header:
            trace_id, span_id, sampled = self._parse_trace_header(env_trace_header)
            if trace_id is not None and span_id is not None and sampled is not None:
                span_context = SpanContext(
                    trace_id=trace_id,
                    span_id=span_id,
                    is_remote=True,
                    trace_flags=TraceFlags(sampled),
                    trace_state=TraceState(),
                )

                return set_span_in_context(NonRecordingSpan(span_context), context)

        # Fall back to carrier
        trace_header = self._get_header(carrier, getter)
        if trace_header:
            return super().extract(carrier, context, getter)

        # No trace header found - return context
        return context
