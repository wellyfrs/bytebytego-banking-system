class TransactionError(Exception):
    """Base class for transaction-related errors."""
    pass


class TransactionAbort(TransactionError):
    """Raised when a transaction must be aborted."""
    pass


class AccountNotFound(TransactionError):
    """Raised when an account does not exist."""
    pass


class InsufficientFunds(TransactionError):
    """Raised when withdrawal would cause negative balance."""
    pass


class SerializationFailure(TransactionAbort):
    """Raised when OCC validation fails."""
    pass


class DeadlockDetected(TransactionAbort):
    """Raised when lock acquisition times out."""
    pass