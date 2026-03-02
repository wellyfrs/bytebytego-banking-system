# Banking System With Transactions

This repository contains a deterministic, correctness-focused reference implementation of the “Banking System With Transactions” chapter.

The goal of this implementation is not to expand scope, but to:

- Make isolation guarantees explicit  
- Eliminate implicit concurrency invariants  
- Use version-based validation (instead of value comparison)  
- Provide deterministic tests that prove anomaly prevention  
- Clarify what is covered and what is intentionally out of scope  

---

# Scope and Design Intent

This implementation models:

- In-memory bank
- Integer balances (cents, not float)
- Strict Two-Phase Locking (2PL)
- Version-based Optimistic Concurrency Control (OCC)
- Serializable isolation
- Deterministic anomaly simulation
- Deadlock detection via timeout

This implementation explicitly does **not** cover:

- Account lifecycle inside transactions
- Predicate/range locking
- Snapshot Isolation (SI)
- Serializable Snapshot Isolation (SSI)
- MVCC with multiple physical versions
- Distributed transactions (2PC, Saga, TCC)
- Replication or durability

The scope is intentionally focused on **single-node concurrency control** and **isolation semantics**.

---

# Isolation Guarantees

The three logical stages correspond to the chapter’s progression:

## 1. Naive (not implemented here)

Allows:

- Dirty writes
- Lost updates
- Non-repeatable reads
- Write skew

Provides no isolation guarantees.

---

## 2. Strict Two-Phase Locking (2PL)

Properties:

- Exclusive row locks
- Locks acquired on first access
- Locks held until commit
- Deterministic release

Prevents:

- Dirty reads
- Dirty writes
- Lost updates
- Non-repeatable reads
- Write skew

Provides:

**Conflict-serializable execution**

Equivalent to:

**SERIALIZABLE isolation (row-level scope)**

---

## 3. Version-Based OCC

Properties:

- Snapshots version numbers on read
- Tracks read_set and write_set explicitly
- Locks read ∪ write set at commit
- Validates versions before applying writes

Prevents:

- Lost updates
- Write skew
- Read skew
- Serialization anomalies

Provides:

**Serializable isolation**

Important distinction:

This implementation uses version-based validation, not value equality.  
Value equality can miss intermediate modifications.

---

# Snapshot Isolation vs Serializable

This implementation achieves serializable behavior.

It does not implement Snapshot Isolation (SI).

Write skew is explicitly prevented.

If the chapter discusses MVCC, it would be valuable to clarify:

- Snapshot Isolation allows write skew.
- Serializable Snapshot Isolation (SSI) prevents it.
- Many engineers conflate SI with serializable isolation.

This distinction is important for conceptual accuracy.

---

# Why Deterministic Tests

Concurrency anomalies are timing-dependent.

Using real threads to simulate anomalies typically results in:

- Flaky tests
- Nondeterministic behavior
- Platform-sensitive race conditions

Instead, tests simulate explicit interleavings step-by-step.

This ensures:

- Reproducibility
- Stable CI behavior
- Clear reasoning about isolation guarantees

This mirrors how database systems are formally validated — by reasoning about interleavings rather than OS scheduling randomness.

---

# Test Coverage

## Atomicity Tests

Verify:

- Commit applies writes
- Abort discards writes
- No partial mutation

---

## Lost Update

Scenario:

Two transactions withdraw from same account concurrently.

Expected behavior:

- 2PL → serial execution (no lost update)
- OCC → one transaction aborts (version mismatch)

---

## Write Skew

Scenario:

Two accounts must not both become zero.

Both transactions:

- Read both accounts
- Withdraw from one based on condition

Expected behavior:

- 2PL → one blocks or serializes
- OCC → one aborts
- Invariant preserved

This test distinguishes serializable from snapshot isolation.

---

## Deadlock Detection

Simulates circular wait using opposing lock acquisition order.

Verifies:

- Timeout-based deadlock detection
- Proper lock release
- No lock leakage

---

# Design Improvements Over Chapter Draft

This implementation intentionally removes several fragilities observed in the draft:

### 1. Explicit Read/Write Sets

No implicit coupling between helper methods.  
Concurrency invariants are structurally enforced.

### 2. Version-Based OCC

Validation is based on version numbers, not value equality.

### 3. LockManager Separation

Lock manager does not mutate transaction state.  
Transactions handle abort logic explicitly.

### 4. Integer Money

Balances stored in cents, not float.

### 5. Deterministic Validation

Concurrency correctness proven via explicit interleaving tests.

---

# What This Implementation Does Not Model

To keep scope aligned with the chapter’s focus:

- No account creation/deletion inside transactions
- No nested transactions or savepoints
- No phantom read modeling (no predicate queries)
- No multi-version physical storage
- No distributed coordination (2PC/Saga)

Those belong to separate conceptual layers.

---

# Recommended Additions to the Chapter

Based on this implementation, the chapter could be strengthened by:

1. Explicitly naming anomalies (lost update, write skew).
2. Stating which isolation level each solution achieves.
3. Clarifying that strict 2PL and proper OCC aim for serializable isolation.
4. Briefly distinguishing Snapshot Isolation from Serializable.
5. Including at least minimal deterministic test scenarios.
6. Clarifying that mutable balances are a simplification versus ledger-based systems.

---

# Conceptual Mapping

| Approach           | Lost Update | Write Skew | Serializable |
|--------------------|-------------|------------|--------------|
| Naive              | Yes         | Yes        | No           |
| 2PL                | No          | No         | Yes          |
| OCC                | No          | No         | Yes          |
| Snapshot Isolation | No          | Yes        | No           |
| SSI                | No          | No         | Yes          |

---

# Intended Use

This repository is:

- A correctness reference
- A teaching companion
- A deterministic isolation demonstration

It is not:

- A production banking engine
- A distributed system
- A durable storage layer

---

# Final Note

The primary purpose of this implementation is to make isolation semantics explicit and verifiable.

Concurrency discussions are most valuable when:

- Anomalies are named
- Guarantees are stated
- Trade-offs are clear
- Tests demonstrate behavior

This code aims to reinforce those properties.