from __future__ import annotations

from travel_agency.exceptions import TravelAgencyError


class ReferenceServiceUnavailableError(TravelAgencyError):
    """Raised when the reference microservice cannot be reached."""
