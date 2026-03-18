# Shared helpers and data structures for diagnostics

class Status:
    GOOD = "good"
    WARNING = "warning"
    BAD = "bad"
    ERROR = "error"

def format_result(status: str, value: str, details: str = "") -> dict:
    """Format a diagnostic result consistently."""
    return {
        "status": status,
        "value": value,
        "details": details
    }
