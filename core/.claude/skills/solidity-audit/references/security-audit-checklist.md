# Security Audit Checklist (Cyfrin Methodology)


Run through these categories systematically:

#### Category 1: Access Control
- [ ] All external/public functions have appropriate access modifiers
- [ ] `onlyOwner` / role checks on sensitive functions
- [ ] No unprotected `selfdestruct`
- [ ] No unprotected initializer (for upgradeable contracts)
- [ ] Ownership transfer is two-step (`Ownable2Step`)

#### Category 2: Reentrancy
- [ ] CEI pattern followed on all state-changing + external-call functions
- [ ] `nonReentrant` modifier on all functions that send ETH or call external contracts
- [ ] No cross-function reentrancy (function A calls B, B re-enters A via callback)
- [ ] Read-only reentrancy considered (view functions returning stale state during callback)

#### Category 3: Input Validation
- [ ] All address parameters checked for `address(0)`
- [ ] All amounts checked for zero or overflow
- [ ] Array length limits enforced (prevent gas DoS)
- [ ] Enum values validated (Solidity doesn't auto-check in older versions)

#### Category 4: Arithmetic
- [ ] Using Solidity 0.8+ (built-in overflow/underflow protection)
- [ ] Division before multiplication avoided (precision loss)
- [ ] Rounding direction is correct for the protocol
- [ ] Fee calculations won't round to zero for small amounts

#### Category 5: Oracle & External Data
- [ ] Chainlink price feed has staleness check
- [ ] Fallback oracle if primary fails
- [ ] Price manipulation resistance (TWAP vs spot price)
- [ ] Decimal handling correct (different tokens have different decimals)

```solidity
// Example: Safe Chainlink usage
function getLatestPrice() public view returns (uint256) {
    (, int256 price, , uint256 updatedAt, ) = priceFeed.latestRoundData();
    if (price <= 0) revert StalePrice();
    if (block.timestamp - updatedAt > STALENESS_THRESHOLD) revert StalePrice();
    return uint256(price);
}
```

#### Category 6: Token Handling
- [ ] ERC-20 return values checked (use SafeERC20)
- [ ] Fee-on-transfer tokens handled
- [ ] Rebasing tokens handled (or explicitly excluded)
- [ ] Token decimals not hardcoded to 18

```solidity
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

using SafeERC20 for IERC20;

// Instead of: token.transfer(to, amount)
token.safeTransfer(to, amount); // Reverts on failure
```

#### Category 7: Front-Running / MEV
- [ ] Commit-reveal scheme for sensitive operations
- [ ] Slippage protection on swaps
- [ ] Deadline parameter on time-sensitive transactions
- [ ] No block.timestamp dependency for critical logic

#### Category 8: Denial of Service
- [ ] No unbounded loops over user-controlled arrays
- [ ] Pull over push pattern for payments
- [ ] No reliance on `transfer()` / `send()` (2300 gas limit)
- [ ] Fallback functions don't revert unconditionally

### 5.2 Static Analysis

```bash
# Aderyn (Cyfrin's tool — recommended)
aderyn .
# Outputs markdown report with findings

# Slither (Trail of Bits)
slither .
# Outputs vulnerability findings with severity levels

# Both tools complement each other — run both
```

### 5.3 Common Vulnerability Patterns

| Vulnerability | Risk | Prevention |
|--------------|------|------------|
| Reentrancy | Critical | CEI pattern + `nonReentrant` |
| Access control missing | Critical | `onlyOwner` / `AccessControl` |
| Unchecked return values | High | `SafeERC20` |
| Oracle manipulation | High | Staleness check + TWAP |
| Front-running | High | Commit-reveal + slippage |
| Integer overflow (< 0.8) | High | Use Solidity 0.8+ |
| Unbounded loops | Medium | Array length limits |
| Timestamp dependency | Medium | Use block numbers instead |
| Centralization risk | Medium | Multisig + timelock |
| Floating pragma | Low | Pin exact version |
