from typing import Callable, Any

def verifies(req_id: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to link tests with formal requirement IDs for RTM traceability."""
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        setattr(fn, "_verifies_req", req_id)
        return fn
    return decorator
