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

"""SQL Commenter utilities."""

from urllib.parse import quote


def _url_encode(value: str) -> str:
    """URL encode a value, then escape percent signs for SQL.

    This encodes the value for URL safety, then replaces % with %%
    to escape it for SQL comments.
    """
    # URL encode (safe='' ensures all special chars are encoded)
    encoded = quote(str(value), safe='')
    # Escape % as %% for SQL
    return encoded.replace('%', '%%')


def _add_sql_comment(sql: str, **comments) -> str:
    """Add SQL comments to a query.

    Args:
        sql: The SQL query.
        **comments: Key-value pairs to add as comments.

    Returns:
        The SQL query with comments added.
    """
    if not comments:
        return sql

    # Build the comment string with sorted keys
    comment_parts = []
    for key in sorted(comments.keys()):
        encoded_key = _url_encode(key)
        encoded_value = _url_encode(comments[key])
        comment_parts.append(f"{encoded_key}='{encoded_value}'")

    comment_str = ",".join(comment_parts)
    comment = f"/*{comment_str}*/"

    # Handle trailing semicolon
    if sql.endswith(";"):
        return f"{sql[:-1]} {comment};"
    else:
        return f"{sql} {comment}"
