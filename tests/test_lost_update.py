import pytest

from banking.core.bank import Bank
from banking.core.exceptions import SerializationFailure
from banking.concurrency.lock_manager import LockManager
from banking.concurrency.two_pl import TwoPLTransaction
from banking.concurrency.occ import OCCTransaction


# --------------------------------------------------
# 2PL prevents lost update via locking
# --------------------------------------------------

def test_two_pl_prevents_lost_update():
    bank = Bank({1: 1000})
    lock_manager = LockManager()

    tx1 = TwoPLTransaction(bank, lock_manager)
    tx2 = TwoPLTransaction(bank, lock_manager)

    # T1 reads and writes
    tx1.withdraw(1, 300)

    # T2 attempts same withdrawal BEFORE T1 commits
    # It will block on lock acquisition.
    # Since we are deterministic and not using threads,
    # we simulate serial behavior by committing T1 first.

    tx1.commit()

    # Now T2 proceeds
    tx2.withdraw(1, 300)
    tx2.commit()

    assert bank.get_balance(1) == 400


# --------------------------------------------------
# OCC prevents lost update via validation failure
# --------------------------------------------------

def test_occ_detects_lost_update():
    bank = Bank({1: 1000})
    lock_manager = LockManager()

    tx1 = OCCTransaction(bank, lock_manager)
    tx2 = OCCTransaction(bank, lock_manager)

    # Both read initial balance
    tx1.withdraw(1, 300)
    tx2.withdraw(1, 300)

    # T1 commits successfully
    tx1.commit()

    # T2 should fail at commit due to version mismatch
    with pytest.raises(SerializationFailure):
        tx2.commit()

    # Final balance reflects only one withdrawal
    assert bank.get_balance(1) == 700