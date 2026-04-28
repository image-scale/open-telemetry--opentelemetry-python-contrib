"""Parse pytest log output (possibly multiple sessions) into per-test results."""

import re
import sys
from typing import Optional


def parse_log(log: str) -> dict[str, str]:
    """Parse pytest log output and return {test_id: status} mapping.

    Handles:
    - Multiple pytest sessions in one log file
    - Inline test results: ``test_id STATUS [XX%]``
    - Split test results (live log output): test ID on its own line, then log
      content, then ``STATUS [XX%]`` alone on a line
    - ANSI escape code stripping
    - Parametrized test IDs with ``[params]``

    Returns a dict mapping full test IDs to one of: PASSED, FAILED, SKIPPED,
    ERROR.
    """
    # Strip ANSI escape codes
    log = re.sub(r'\x1b\[[0-9;]*[mK]', '', log)

    results: dict[str, str] = {}

    # Inline result: ``test_id STATUS [XX%]``
    # Uses non-greedy match on the test_id part so the status keyword isn't
    # consumed, but guarantees the status keyword is at the right position.
    inline_re = re.compile(
        r'^(.+?)\s+(PASSED|FAILED|SKIPPED|ERROR)\s+\[\s*\d+%\]\s*$'
    )

    # Standalone status on its own line (follows live log output)
    status_only_re = re.compile(
        r'^(PASSED|FAILED|SKIPPED|ERROR)\s+\[\s*\d+%\]\s*$'
    )

    # Test ID alone on a line (no trailing status keyword).
    # Test IDs use ``::`` as separators and contain no whitespace.
    test_id_only_re = re.compile(r'^(\S+::\S+(?:::\S+)*)\s*$')

    # Section headers are lines bounded by runs of ``=`` signs.
    section_header_re = re.compile(r'^={3,}[^=].*[^=]={3,}\s*$')

    current_test_id: Optional[str] = None
    # True while inside a FAILURES/ERRORS or short test summary section
    skip_section: bool = False

    for raw_line in log.splitlines():
        line = raw_line.rstrip()

        # ---- Section header detection ----
        if section_header_re.match(line):
            if re.search(r'\b(FAILURES|ERRORS)\b', line):
                skip_section = True
                current_test_id = None
            elif 'short test summary info' in line:
                skip_section = True
                current_test_id = None
            else:
                # All other headers (test session starts, warnings summary,
                # session result summary, etc.) end any skip zone.
                skip_section = False
                current_test_id = None
            continue

        if skip_section:
            continue

        # ---- Inline test result ----
        m = inline_re.match(line)
        if m:
            candidate_id = m.group(1).strip()
            status = m.group(2)
            if '::' in candidate_id:
                results[candidate_id] = status
                current_test_id = None
                continue

        # ---- Standalone status (after live log output) ----
        m = status_only_re.match(line)
        if m:
            if current_test_id:
                results[current_test_id] = m.group(1)
                current_test_id = None
            continue

        # ---- Test ID only line (precedes live log output) ----
        m = test_id_only_re.match(line)
        if m:
            candidate = m.group(1)
            if '::' in candidate:
                current_test_id = candidate
            continue

    return results


if __name__ == '__main__':
    log_path = sys.argv[1] if len(sys.argv) > 1 else 'test_output.log'
    with open(log_path) as f:
        log_content = f.read()

    results = parse_log(log_content)

    counts: dict[str, int] = {}
    for status in results.values():
        counts[status] = counts.get(status, 0) + 1

    print(f'Total: {len(results)}')
    for status in ('PASSED', 'FAILED', 'SKIPPED', 'ERROR'):
        if counts.get(status):
            print(f'  {status}: {counts[status]}')

    failed = [(tid, st) for tid, st in results.items() if st in ('FAILED', 'ERROR')]
    if failed:
        print(f'\nFailed/Error ({len(failed)}):')
        for tid, st in sorted(failed):
            print(f'  [{st}] {tid}')

