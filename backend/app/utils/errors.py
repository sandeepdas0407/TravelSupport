class UpstreamServiceError(Exception):
    """Raised when a required upstream API (geocoding/routing) fails and there is no fallback."""

    def __init__(self, service: str, message: str) -> None:
        super().__init__(f"{service}: {message}")
        self.service = service
        self.message = message


class SynthesisError(Exception):
    """Raised when the Claude synthesis call fails after retries."""
