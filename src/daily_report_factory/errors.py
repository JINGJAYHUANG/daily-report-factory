class DailyReportFactoryError(Exception):
    """Base exception for Daily Report Factory."""


class CatalogError(DailyReportFactoryError):
    """Raised when a publication catalog is invalid."""


class ContractError(DailyReportFactoryError):
    """Raised when an issue document violates its publication contract."""


class RenderValidationError(DailyReportFactoryError):
    """Raised when rendered HTML fails static acceptance checks."""


class ArchiveSafetyError(DailyReportFactoryError):
    """Raised when an archive operation violates safety constraints."""
