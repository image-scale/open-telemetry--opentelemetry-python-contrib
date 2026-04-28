#!/bin/bash
set -eo pipefail

cd /workspace/opentelemetry-python-contrib
PROJ_ROOT="$(pwd)"

export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
export CI=true

rm -rf .pytest_cache

PYTEST_ARGS="-v --tb=short --no-cov -p no:cacheprovider"
EXIT_CODE=0

# Base instrumentation package path
BASE_INSTR="${PROJ_ROOT}/opentelemetry-instrumentation"
UTIL_HTTP="${PROJ_ROOT}/util/opentelemetry-util-http"

run_tests() {
    local pkg_dir="$1"
    PYTHONPATH="${PROJ_ROOT}/${pkg_dir}" pytest ${PYTEST_ARGS} "${pkg_dir}/tests" || EXIT_CODE=$?
}

run_tests_with_deps() {
    local pkg_dir="$1"
    PYTHONPATH="${PROJ_ROOT}/${pkg_dir}:${BASE_INSTR}:${UTIL_HTTP}" pytest ${PYTEST_ARGS} "${pkg_dir}/tests" || EXIT_CODE=$?
}

run_tests opentelemetry-instrumentation
run_tests opentelemetry-distro
run_tests_with_deps instrumentation/opentelemetry-instrumentation-logging
run_tests_with_deps instrumentation/opentelemetry-instrumentation-wsgi
run_tests_with_deps instrumentation/opentelemetry-instrumentation-asgi
run_tests_with_deps instrumentation/opentelemetry-instrumentation-threading
run_tests_with_deps instrumentation/opentelemetry-instrumentation-asyncio
run_tests_with_deps instrumentation/opentelemetry-instrumentation-urllib
run_tests_with_deps instrumentation/opentelemetry-instrumentation-urllib3
run_tests_with_deps instrumentation/opentelemetry-instrumentation-dbapi
run_tests_with_deps instrumentation/opentelemetry-instrumentation-sqlite3
run_tests_with_deps instrumentation/opentelemetry-instrumentation-jinja2
run_tests_with_deps instrumentation/opentelemetry-instrumentation-requests
run_tests_with_deps instrumentation/opentelemetry-instrumentation-flask
run_tests_with_deps instrumentation/opentelemetry-instrumentation-fastapi
run_tests_with_deps instrumentation/opentelemetry-instrumentation-starlette
run_tests util/opentelemetry-util-http
run_tests util/opentelemetry-util-genai
run_tests propagator/opentelemetry-propagator-aws-xray
run_tests propagator/opentelemetry-propagator-ot-trace
run_tests processor/opentelemetry-processor-baggage
run_tests resource/opentelemetry-resource-detector-containerid

exit $EXIT_CODE

