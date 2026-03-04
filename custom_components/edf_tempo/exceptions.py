"""Custom exceptions for the EDF Tempo integration."""


class EDFTempoError(Exception):
    """Base exception for all EDF Tempo errors."""


class CannotConnect(EDFTempoError):
    """Raised when the integration cannot connect to an API endpoint."""


class InvalidAuth(EDFTempoError):
    """Raised when API credentials are rejected (HTTP 401)."""


class RateLimitExceeded(EDFTempoError):
    """Raised when the API rate limit is hit (HTTP 429)."""


class ParseError(EDFTempoError):
    """Raised when API response or CSV data cannot be parsed."""


class InvalidCredentials(EDFTempoError):
    """Raised when credentials fail format/content validation before any request."""
