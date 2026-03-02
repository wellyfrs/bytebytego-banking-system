from typing import Dict, Set

from banking.core.exceptions import (
    SerializationFailure,
)
from banking.concurrency.transaction_base import Transaction
from banking.concurrency.lock_manager import LockManager


class OCCTransaction(Transaction):
    """
    Optimistic Concurrency Control (OCC) transaction.

    - Snapshots version numbers on read.
    - Tracks read and write sets.
    - Validates read set at commit.
    - Applies writes only if validation succeeds.
    - Guarantees serializable execution if read/write sets are complete.
    """

    def __init__(self, bank, lock_manager: LockManager):
        super().__init__(bank)
        self._lock_manager = lock_manager
        self._snapshot_versions: Dict[int, int] = {}
        self._locks_held: Set[int] = set()

    # -----------------------
    # Override read to snapshot versions
    # -----------------------

    def _read(self, account_id: int) -> None:
        # Record snapshot version on first read
        if account_id not in self._snapshot_versions:
            version = self.bank.get_version(account_id)
            self._snapshot_versions[account_id] = version

        super()._read(account_id)

    # -----------------------
    # Commit / Abort
    # -----------------------

    def commit(self) -> None:
        self._ensure_active()

        # Lock read ∪ write set
        accounts_to_lock = self._read_set.union(self._write_set)

        try:
            acquired = self._lock_manager.acquire_all(accounts_to_lock)
            self._locks_held.update(acquired)

            # Validate read set
            for account_id in self._read_set:
                current_version = self.bank.get_version(account_id)
                snapshot_version = self._snapshot_versions.get(account_id)

                if snapshot_version is None:
                    # Should not happen if reads are tracked properly
                    raise SerializationFailure(
                        f"Missing snapshot for account {account_id}"
                    )

                if current_version != snapshot_version:
                    raise SerializationFailure(
                        f"Serialization conflict on account {account_id}"
                    )

            # Apply writes
            for account_id, delta in self._local_changes.items():
                self.bank._apply_delta(account_id, delta)

            self._active = False

        except SerializationFailure:
            self.abort()
            raise

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