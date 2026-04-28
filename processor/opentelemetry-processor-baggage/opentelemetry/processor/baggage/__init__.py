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

"""Baggage Span Processor."""

import re
from typing import Callable, Optional, Pattern, Union

from opentelemetry.baggage import get_all as get_all_baggage
from opentelemetry.context import Context
from opentelemetry.sdk.trace import ReadableSpan, Span, SpanProcessor


ALLOW_ALL_BAGGAGE_KEYS = re.compile(".*")


class BaggageSpanProcessor(SpanProcessor):
    """Baggage span processor.

    Copies baggage entries to span attributes on span start,
    filtered by a predicate function or regex pattern.
    """

    def __init__(
        self,
        baggage_key_predicate: Union[Callable[[str], bool], Pattern],
    ):
        """Initialize the BaggageSpanProcessor.

        Args:
            baggage_key_predicate: Either a callable that takes a baggage key
                and returns True if it should be added to span attributes,
                or a regex Pattern that matches keys to include.
        """
        self._baggage_key_predicate = baggage_key_predicate

    def _matches_predicate(self, key: str) -> bool:
        """Check if a baggage key matches the predicate."""
        if callable(self._baggage_key_predicate) and not isinstance(
            self._baggage_key_predicate, Pattern
        ):
            return self._baggage_key_predicate(key)
        # It's a Pattern
        return self._baggage_key_predicate.match(key) is not None

    def on_start(
        self, span: Span, parent_context: Optional[Context] = None
    ) -> None:
        """Copy matching baggage entries to span attributes.

        Args:
            span: The span being started.
            parent_context: The parent context.
        """
        baggage = get_all_baggage(parent_context)
        for key, value in baggage.items():
            if self._matches_predicate(key):
                span.set_attribute(key, value)

    def on_end(self, span: ReadableSpan) -> None:
        """Called when a span ends. No-op for this processor."""
        pass

    def shutdown(self) -> None:
        """Shut down the processor. No-op for this processor."""
        pass

    def force_flush(self, timeout_millis: Optional[int] = None) -> bool:
        """Force flush. No-op for this processor.

        Returns:
            True always.
        """
        return True
