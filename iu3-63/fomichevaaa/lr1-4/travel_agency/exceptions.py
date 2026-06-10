"""Custom exception hierarchy for the travel agency system."""


class TravelAgencyError(Exception):
    """Base exception for the whole application."""


class ValidationError(TravelAgencyError):
    """Raised when input or entity state is invalid."""


class InputError(ValidationError):
    """Raised when user input cannot be parsed or validated."""


class EntityNotFoundError(TravelAgencyError):
    """Raised when an entity cannot be found in storage."""


class DuplicateEntityError(TravelAgencyError):
    """Raised when an entity with the same identifier already exists."""


class AvailabilityError(TravelAgencyError):
    """Raised when there are not enough seats for a booking."""


class PricingError(TravelAgencyError):
    """Raised when price calculation fails."""


class BookingError(TravelAgencyError):
    """Raised when booking creation cannot be completed safely."""


class StateTransitionError(BookingError):
    """Raised when a booking cannot move to the requested state."""


class PaymentError(TravelAgencyError):
    """Raised when payment processing is invalid."""


class UnitOfWorkError(TravelAgencyError):
    """Raised when a transaction rollback cannot be completed safely."""
