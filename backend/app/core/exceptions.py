class BarbechAIError(Exception):
    """Base exception for BarbechAI."""


class DiscoveryError(BarbechAIError):
    """Raised when business discovery fails."""


class EnrichmentError(BarbechAIError):
    """Raised when enrichment fails."""


class DatabaseError(BarbechAIError):
    """Raised when a database operation fails."""


class ValidationError(BarbechAIError):
    """Raised when input validation fails."""
