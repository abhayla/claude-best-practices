# Solidity Development Patterns


```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title MyContract
 * @author Developer Name
 * @notice Brief description of what this contract does
 * @dev Implementation details and design decisions
 */
contract MyContract is Ownable, ReentrancyGuard {
    // ============ Errors ============
    error MyContract__InsufficientBalance(uint256 requested, uint256 available);
    error MyContract__ZeroAddress();
    error MyContract__TransferFailed();

    // ============ Events ============
    event Deposited(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);

    // ============ State Variables ============
    // Constants (UPPER_SNAKE_CASE)
    uint256 public constant MIN_DEPOSIT = 1e18; // 1 token (18 decimals)
    uint256 public constant FEE_BASIS_POINTS = 30; // 0.3%
    uint256 private constant BASIS_POINTS_DENOMINATOR = 10_000;

    // Immutables (set once in constructor)
    IERC20 public immutable i_token;

    // Storage variables (s_ prefix for clarity)
    mapping(address => uint256) private s_balances;
    uint256 private s_totalDeposits;
    bool private s_paused;

    // ============ Modifiers ============
    modifier whenNotPaused() {
        require(!s_paused, "Contract is paused");
        _;
    }

    // ============ Constructor ============
    constructor(address tokenAddress) Ownable(msg.sender) {
        if (tokenAddress == address(0)) revert MyContract__ZeroAddress();
        i_token = IERC20(tokenAddress);
    }

    // ============ External Functions ============
    // ============ Public Functions ============
    // ============ Internal Functions ============
    // ============ View / Pure Functions ============
}
```

**Naming conventions:**
- Custom errors: `ContractName__ErrorDescription`
- Constants: `UPPER_SNAKE_CASE`
- Immutables: `i_variableName`
- Storage variables: `s_variableName`
- Function parameters: `_paramName` (optional but common)
- No magic numbers — use named constants

### 3.2 Check-Effects-Interactions Pattern (CEI)

The #1 rule for preventing reentrancy:

```solidity
function withdraw(uint256 amount) external nonReentrant whenNotPaused {
    // 1. CHECKS — validate inputs and state
    if (amount == 0) revert MyContract__InsufficientBalance(amount, 0);
    uint256 balance = s_balances[msg.sender];
    if (balance < amount) revert MyContract__InsufficientBalance(amount, balance);

    // 2. EFFECTS — update state BEFORE external calls
    s_balances[msg.sender] = balance - amount;
    s_totalDeposits -= amount;

    // 3. INTERACTIONS — external calls LAST
    emit Withdrawn(msg.sender, amount);
    bool success = i_token.transfer(msg.sender, amount);
    if (!success) revert MyContract__TransferFailed();
}
```

**Rules:**
- ALWAYS update state before external calls
- ALWAYS use `nonReentrant` modifier on functions that make external calls
- ALWAYS use custom errors instead of `require` strings (saves gas)
- ALWAYS emit events for state changes

### 3.3 Access Control Patterns

```solidity
// Simple: Ownable (single admin)
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

// Role-based: AccessControl (multiple roles)
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

contract MyContract is AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
    }

    function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) {
        // ...
    }

    function pause() external onlyRole(PAUSER_ROLE) {
        s_paused = true;
    }
}
```

### 3.4 Emergency Pause

```solidity
import {Pausable} from "@openzeppelin/contracts/utils/Pausable.sol";

contract MyContract is Ownable, Pausable {
    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }

    function deposit(uint256 amount) external whenNotPaused {
        // Only callable when not paused
    }

    // Emergency withdrawal should work even when paused
    function emergencyWithdraw() external {
        uint256 balance = s_balances[msg.sender];
        s_balances[msg.sender] = 0;
        i_token.transfer(msg.sender, balance);
    }
}
```
