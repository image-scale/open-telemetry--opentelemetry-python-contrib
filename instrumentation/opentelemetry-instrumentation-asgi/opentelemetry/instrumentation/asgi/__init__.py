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

"""OpenTelemetry ASGI Instrumentation."""

from typing import Dict, Optional, Callable


def collect_request_attributes(scope: Dict, sem_conv_opt_in_mode=None) -> Dict:
    """Collect request attributes from ASGI scope."""
    raise NotImplementedError


class OpenTelemetryMiddleware:
    """ASGI middleware for OpenTelemetry."""

    def __init__(
        self,
        app,
        default_span_details=None,
        server_request_hook=None,
        client_request_hook=None,
        client_response_hook=None,
        tracer_provider=None,
        meter_provider=None,
        excluded_urls=None,
    ):
        self.app = app
        raise NotImplementedError

    async def __call__(self, scope, receive, send):
        raise NotImplementedError
