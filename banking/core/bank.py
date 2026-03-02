from typing import Dict
from threading import RLock

from .exceptions import AccountNotFound, InsufficientFunds


class Bank:
    """
    Committed state of the banking system.

    - Balances are stored in integer cents.
    - Each account has a version number for OCC validation.
    - Internal lock protects structural integrity of the store.
    """

    def __init__(self, initial_balances: Dict[int, int]):
        """
        initial_balances: {account_id: balance_in_cents}
        """
        self._balances: Dict[int, int] = dict(initial_balances)
        self._versions: Dict[int, int] = {
            account_id: 0 for account_id in initial_balances
        }

        self._lock = RLock()

    # -----------------------
    # Read operations
    # -----------------------

    def get_balance(self, account_id: int) -> int:
        with self._lock:
            if account_id not in self._balances:
                raise AccountNotFound(f"Account {account_id} does not exist")
            return self._balances[account_id]

    def get_version(self, account_id: int) -> int:
        with self._lock:
            if account_id not in self._versions:
                raise AccountNotFound(f"Account {account_id} does not exist")
            return self._versions[account_id]

    # -----------------------
    # Write operations (internal use only)
    # -----------------------

    def _apply_delta(self, account_id: int, delta: int) -> None:
        """
        Apply delta to balance without version validation.
        Caller must ensure correctness (e.g., locking or OCC validation).
        """
        with self._lock:
            if account_id not in self._balances:
                raise AccountNotFound(f"Account {account_id} does not exist")

            new_balance = self._balances[account_id] + delta

            if new_balance < 0:
                raise InsufficientFunds(
                    f"Insufficient funds in account {account_id}"
                )

            self._balances[account_id] = new_balance
            self._versions[account_id] += 1

    def _set_balance(self, account_id: int, new_balance: int) -> None:
        """
        Used by OCC to write validated balances.
        """
        with self._lock:
            if account_id not in self._balances:
                raise AccountNotFound(f"Account {account_id} does not exist")

            if new_balance < 0:
                raise InsufficientFunds(
                    f"Insufficient funds in account {account_id}"
                )

            self._balances[account_id] = new_balance
            self._versions[account_id] += 1

    # -----------------------
    # Introspection (for tests)
    # -----------------------

    def snapshot(self) -> Dict[int, int]:
        """
        Returns a copy of balances (for deterministic testing).
        """
        with self._lock:
            return dict(self._balances)