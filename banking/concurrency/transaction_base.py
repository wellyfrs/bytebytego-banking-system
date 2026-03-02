from abc import ABC, abstractmethod
from typing import Dict, Set

from banking.core.bank import Bank
from banking.core.exceptions import (
    AccountNotFound,
    InsufficientFunds,
    TransactionAbort,
)


class Transaction(ABC):
    """
    Base class for transactions.

    Tracks:
    - read_set: accounts read
    - write_set: accounts written
    - local_changes: account_id -> delta
    """

    def __init__(self, bank: Bank):
        self.bank = bank

        self._read_set: Set[int] = set()
        self._write_set: Set[int] = set()
        self._local_changes: Dict[int, int] = {}

        self._active: bool = True

    # -----------------------
    # Public operations
    # -----------------------

    def get_balance(self, account_id: int) -> int:
        self._ensure_active()

        # Record read
        self._read(account_id)

        # If written locally, return adjusted value
        if account_id in self._local_changes:
            base = self.bank.get_balance(account_id)
            return base + self._local_changes[account_id]

        return self.bank.get_balance(account_id)

    def deposit(self, account_id: int, amount: int) -> None:
        self._ensure_active()

        if amount < 0:
            raise ValueError("Deposit amount must be non-negative")

        self._write(account_id, amount)

    def withdraw(self, account_id: int, amount: int) -> None:
        self._ensure_active()

        if amount < 0:
            raise ValueError("Withdraw amount must be non-negative")

        # Ensure sufficient funds at transaction view
        current_balance = self.get_balance(account_id)
        if current_balance < amount:
            raise InsufficientFunds(
                f"Insufficient funds in account {account_id}"
            )

        self._write(account_id, -amount)

    # -----------------------
    # Read / Write tracking
    # -----------------------

    def _read(self, account_id: int) -> None:
        if not self._account_exists(account_id):
            raise AccountNotFound(f"Account {account_id} does not exist")

        self._read_set.add(account_id)

    def _write(self, account_id: int, delta: int) -> None:
        if not self._account_exists(account_id):
            raise AccountNotFound(f"Account {account_id} does not exist")

        self._read_set.add(account_id)
        self._write_set.add(account_id)

        self._local_changes[account_id] = (
            self._local_changes.get(account_id, 0) + delta
        )

    # -----------------------
    # Utilities
    # -----------------------

    def _account_exists(self, account_id: int) -> bool:
        try:
            self.bank.get_balance(account_id)
            return True
        except AccountNotFound:
            return False

    def _ensure_active(self) -> None:
        if not self._active:
            raise TransactionAbort("Transaction is no longer active")

    def abort(self) -> None:
        self._active = False
        self._local_changes.clear()
        self._read_set.clear()
        self._write_set.clear()

    # -----------------------
    # Abstract commit
    # -----------------------

    @abstractmethod
    def commit(self) -> None:
        """
        Must:
        - Enforce concurrency strategy
        - Apply writes atomically
        - Raise TransactionAbort on failure
        """
        pass

    # -----------------------
    # Introspection (for tests)
    # -----------------------

    @property
    def read_set(self) -> Set[int]:
        return set(self._read_set)

    @property
    def write_set(self) -> Set[int]:
        return set(self._write_set)

    @property
    def local_changes(self) -> Dict[int, int]:
        return dict(self._local_changes)