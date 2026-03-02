from typing import Dict, Iterable, List
from threading import Lock
import time

from banking.core.exceptions import DeadlockDetected


class LockManager:
    """
    Manages row-level exclusive locks.

    - Locks are per-account.
    - Lock acquisition is ordered to reduce deadlock risk.
    - Lock release is explicit and must be called by the transaction.
    - Does NOT mutate transaction state.
    """

    def __init__(self):
        self._locks: Dict[int, Lock] = {}
        self._global_lock = Lock()

    # -----------------------
    # Internal helpers
    # -----------------------

    def _get_lock(self, account_id: int) -> Lock:
        """
        Lazily create a lock per account.
        """
        with self._global_lock:
            if account_id not in self._locks:
                self._locks[account_id] = Lock()
            return self._locks[account_id]

    # -----------------------
    # Public API
    # -----------------------

    def acquire_all(
        self,
        account_ids: Iterable[int],
        timeout: float = 5.0
    ) -> List[int]:
        """
        Acquire locks for all account_ids.

        Returns list of acquired account_ids (sorted order).

        Raises DeadlockDetected if timeout occurs.
        """

        # Deterministic ordering prevents circular wait
        ordered_ids = sorted(set(account_ids))

        acquired: List[int] = []
        start_time = time.monotonic()

        for account_id in ordered_ids:
            lock = self._get_lock(account_id)

            remaining = timeout - (time.monotonic() - start_time)
            if remaining <= 0:
                self._release_partial(acquired)
                raise DeadlockDetected(
                    f"Timeout acquiring lock for account {account_id}"
                )

            success = lock.acquire(timeout=remaining)
            if not success:
                self._release_partial(acquired)
                raise DeadlockDetected(
                    f"Timeout acquiring lock for account {account_id}"
                )

            acquired.append(account_id)

        return acquired

    def release_all(self, account_ids: Iterable[int]) -> None:
        """
        Release locks for given account_ids.
        """
        for account_id in account_ids:
            lock = self._get_lock(account_id)
            lock.release()

    # -----------------------
    # Private cleanup
    # -----------------------

    def _release_partial(self, account_ids: Iterable[int]) -> None:
        """
        Release already-acquired locks in case of failure.
        """
        for account_id in reversed(list(account_ids)):
            lock = self._get_lock(account_id)
            lock.release()