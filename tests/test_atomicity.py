import pytest

from banking.core.bank import Bank
from banking.concurrency.lock_manager import LockManager
from banking.concurrency.two_pl import TwoPLTransaction
from banking.concurrency.occ import OCCTransaction


def test_two_pl_commit_applies_changes():
    bank = Bank({1: 1000})
    lock_manager = LockManager()

    tx = TwoPLTransaction(bank, lock_manager)

    tx.deposit(1, 500)
    tx.commit()

    assert bank.get_balance(1) == 1500


def test_two_pl_abort_discards_changes():
    bank = Bank({1: 1000})
    lock_manager = LockManager()

    tx = TwoPLTransaction(bank, lock_manager)

    tx.deposit(1, 500)
    tx.abort()

    assert bank.get_balance(1) == 1000


def test_occ_commit_applies_changes():
    bank = Bank({1: 1000})
    lock_manager = LockManager()

    tx = OCCTransaction(bank, lock_manager)

    tx.withdraw(1, 300)
    tx.commit()

    assert bank.get_balance(1) == 700


def test_occ_abort_discards_changes():
    bank = Bank({1: 1000})
    lock_manager = LockManager()

    tx = OCCTransaction(bank, lock_manager)

    tx.withdraw(1, 300)
    tx.abort()

    assert bank.get_balance(1) == 1000


def test_withdraw_insufficient_funds():
    bank = Bank({1: 1000})
    lock_manager = LockManager()

    tx = TwoPLTransaction(bank, lock_manager)

    with pytest.raises(Exception):
        tx.withdraw(1, 2000)