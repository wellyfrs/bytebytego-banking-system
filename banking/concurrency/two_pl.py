from typing import Set

from banking.concurrency.transaction_base import Transaction
from banking.concurrency.lock_manager import LockManager


class TwoPLTransaction(Transaction):
    """
    Strict Two-Phase Locking (2PL) transaction.

    - Acquires exclusive row lock on first access.
    - Holds all locks until commit or abort.
    - Guarantees conflict-serializable execution.
    """

    def __init__(self, bank, lock_manager: LockManager):
        super().__init__(bank)
        self._lock_manager = lock_manager
        self._locks_held: Set[int] = set()

    # -----------------------
    # Override read/write to enforce locking
    # -----------------------

    def _read(self, account_id: int) -> None:
        self._acquire_lock(account_id)
        super()._read(account_id)

    def _write(self, account_id: int, delta: int) -> None:
        self._acquire_lock(account_id)
        super()._write(account_id, delta)

    # -----------------------
    # Lock acquisition
    # -----------------------

    def _acquire_lock(self, account_id: int) -> None:
        if account_id in self._locks_held:
            return

        acquired = self._lock_manager.acquire_all([account_id])
        self._locks_held.update(acquired)

    # -----------------------
    # Commit / Abort
    # -----------------------

    def commit(self) -> None:
        self._ensure_active()

        try:
            # Apply all writes under lock
            for account_id, delta in self._local_changes.items():
                self.bank._apply_delta(account_id, delta)

            self._active = False

        except Exception:
            self.abort()
            raise

        finally:
            self._release_locks()

    def abort(self) -> None:
        if not self._active:
            return

        super().abort()
        self._release_locks()

    # -----------------------
    # Cleanup
    # -----------------------

    def _release_locks(self) -> None:
        if self._locks_held:
            self._lock_manager.release_all(self._locks_held)
            self._locks_held.clear()