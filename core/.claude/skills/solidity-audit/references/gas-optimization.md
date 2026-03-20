# Gas Optimization


```solidity
// Pack variables into single storage slot (32 bytes)
// BAD: 3 storage slots
uint256 amount;    // slot 0 (32 bytes)
address user;      // slot 1 (20 bytes, wastes 12)
bool active;       // slot 2 (1 byte, wastes 31)

// GOOD: 2 storage slots
uint256 amount;    // slot 0 (32 bytes)
address user;      // slot 1 (20 bytes)
bool active;       // slot 1 (1 byte, packed with user)

// Use uint96 when full uint256 not needed
uint96 amount;     // slot 0 (12 bytes)
address user;      // slot 0 (20 bytes, packed!)
```

### 7.2 Common Optimizations

```solidity
// Use custom errors instead of require strings
// BAD: stores string in bytecode
require(amount > 0, "Amount must be greater than zero");
// GOOD: 4-byte selector only
error InsufficientAmount();
if (amount == 0) revert InsufficientAmount();

// Cache storage reads
// BAD: reads s_balance from storage 3 times
if (s_balance > 0 && s_balance >= amount && s_balance - amount >= minBalance) { ... }
// GOOD: one SLOAD
uint256 balance = s_balance;
if (balance > 0 && balance >= amount && balance - amount >= minBalance) { ... }

// Use unchecked for safe arithmetic
// When you've already validated bounds
unchecked {
    s_balances[msg.sender] = balance - amount; // Already checked balance >= amount
}

// Use calldata instead of memory for read-only arrays
function process(uint256[] calldata ids) external { // calldata = cheaper
    // ...
}

// Use ++i instead of i++ in loops
for (uint256 i; i < length; ++i) { // Saves ~5 gas per iteration
    // ...
}

// Use immutable for constructor-set values
address public immutable i_owner; // One-time CODECOPY vs repeated SLOAD
```

### 7.3 Measure Gas

```bash
# Gas snapshot (saves baseline)
forge snapshot

# Compare against baseline
forge snapshot --diff

# Gas report for specific test
forge test --gas-report --match-contract MyContractTest
```
