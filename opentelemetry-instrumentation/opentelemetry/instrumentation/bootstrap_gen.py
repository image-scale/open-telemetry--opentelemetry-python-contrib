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

"""Generated bootstrap configuration."""

# Default instrumentations to install
default_instrumentations = [
    "opentelemetry-instrumentation-logging",
]

# Library mappings
libraries = [
    {"library": "flask", "instrumentation": "opentelemetry-instrumentation-flask"},
    {"library": "requests", "instrumentation": "opentelemetry-instrumentation-requests"},
    {"library": "jinja2", "instrumentation": "opentelemetry-instrumentation-jinja2"},
    {"library": "urllib3", "instrumentation": "opentelemetry-instrumentation-urllib3"},
]
