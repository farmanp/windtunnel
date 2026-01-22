"""Data extraction utilities."""

import logging
from typing import Any

from jsonpath_ng import parse
from jsonpath_ng.exceptions import JsonPathParserError

logger = logging.getLogger(__name__)


def extract_values(
    data: Any,
    extraction_map: dict[str, str],
) -> dict[str, Any]:
    """Extract values from a data structure using JSONPath expressions.

    Args:
        data: The source data (usually a dictionary or list from JSON).
        extraction_map: A mapping of variable names to JSONPath expressions.

    Returns:
        A dictionary containing the extracted values.
    """
    extracted = {}
    
    if not data or not isinstance(data, (dict, list)):
        return extracted

    for var_name, jpath_expr in extraction_map.items():
        try:
            jsonpath_expr = parse(jpath_expr)
            matches = jsonpath_expr.find(data)
            
            if matches:
                # If multiple matches, take the first one (standard behavior for Turbulence)
                extracted[var_name] = matches[0].value
            else:
                logger.debug(f"JSONPath '{jpath_expr}' found no matches for variable '{var_name}'")
        except JsonPathParserError as e:
            logger.warning(f"Malformed JSONPath expression '{jpath_expr}': {e}")
        except Exception as e:
            logger.error(f"Unexpected error extracting '{jpath_expr}': {e}")

    return extracted
