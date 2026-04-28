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
from typing import Callable, Pattern, Union

from opentelemetry.sdk.trace import SpanProcessor


ALLOW_ALL_BAGGAGE_KEYS = re.compile(".*")


class BaggageSpanProcessor(SpanProcessor):
    """Baggage span processor."""

    def __init__(
        self,
        baggage_key_predicate: Union[Callable[[str], bool], Pattern],
    ):
        self._baggage_key_predicate = baggage_key_predicate
        raise NotImplementedError

    def on_start(self, span, parent_context=None):
        raise NotImplementedError

    def on_end(self, span):
        pass

    def shutdown(self):
        pass

    def force_flush(self, timeout_millis=None):
        return True
