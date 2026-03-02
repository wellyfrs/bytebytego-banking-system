import pytest
import threading

from banking.core.bank import Bank
from banking.core.exceptions import DeadlockDetected
from banking.concurrency.lock_manager import LockManager
from banking.concurrency.two_pl import TwoPLTransaction


def test_two_pl_deadlock_detection():
    bank = Bank({1: 1000, 2: 1000})
    lock_manager = LockManager()

    tx1 = TwoPLTransaction(bank, lock_manager)
    tx2 = TwoPLTransaction(bank, lock_manager)

    # Step 1: T1 locks account 1
    tx1.get_balance(1)

    # Step 2: T2 locks account 2
    tx2.get_balance(2)

    # Now we simulate opposing lock attempts in separate threads
    # so that both attempt to acquire the other's lock.

    def tx1_attempt():
        with pytest.raises(DeadlockDetected):
            tx1.get_balance(2)

    def tx2_attempt():
        with pytest.raises(DeadlockDetected):
            tx2.get_balance(1)

    t1 = threading.Thread(target=tx1_attempt)
    t2 = threading.Thread(target=tx2_attempt)

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    # Cleanup
    tx1.abort()
    tx2.abort()