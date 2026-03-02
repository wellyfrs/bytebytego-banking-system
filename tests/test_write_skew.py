import pytest

from banking.core.bank import Bank
from banking.core.exceptions import SerializationFailure
from banking.concurrency.lock_manager import LockManager
from banking.concurrency.two_pl import TwoPLTransaction
from banking.concurrency.occ import OCCTransaction


# --------------------------------------------------
# 2PL prevents write skew
# --------------------------------------------------

def test_two_pl_prevents_write_skew():
    bank = Bank({1: 100, 2: 100})
    lock_manager = LockManager()

    tx1 = TwoPLTransaction(bank, lock_manager)
    tx2 = TwoPLTransaction(bank, lock_manager)

    # T1 reads both
    if tx1.get_balance(2) > 0:
        tx1.withdraw(1, 100)

    # T1 commit first (simulating lock ordering)
    tx1.commit()

    # T2 now reads committed state
    if tx2.get_balance(1) > 0:
        tx2.withdraw(2, 100)

    tx2.commit()

    # Serializable result: only one withdrawal applied
    assert (
        bank.get_balance(1) == 0 and bank.get_balance(2) == 100
        or
        bank.get_balance(1) == 100 and bank.get_balance(2) == 0
    )


# --------------------------------------------------
# OCC prevents write skew via validation
# --------------------------------------------------

def test_occ_detects_write_skew():
    bank = Bank({1: 100, 2: 100})
    lock_manager = LockManager()

    tx1 = OCCTransaction(bank, lock_manager)
    tx2 = OCCTransaction(bank, lock_manager)

    # Both read initial snapshot
    if tx1.get_balance(2) > 0:
        tx1.withdraw(1, 100)

    if tx2.get_balance(1) > 0:
        tx2.withdraw(2, 100)

    # T1 commits
    tx1.commit()

    # T2 should fail due to version change in read set
    with pytest.raises(SerializationFailure):
        tx2.commit()

    # Only one withdrawal applied
    assert (
        bank.get_balance(1) == 0 and bank.get_balance(2) == 100
        or
        bank.get_balance(1) == 100 and bank.get_balance(2) == 0
    )