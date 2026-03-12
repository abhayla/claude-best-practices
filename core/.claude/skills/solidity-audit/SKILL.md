---
name: solidity-audit
description: >
  Production Solidity development and security auditing. Foundry/Hardhat testing,
  reentrancy protection, access control, gas optimization, upgrade patterns (UUPS,
  Transparent), oracle security, ERC standards, Aderyn/Slither static analysis,
  Cyfrin audit methodology. Private key safety guardrails.
triggers:
  - solidity
  - smart contract
  - web3
  - foundry
  - hardhat
  - solidity audit
  - reentrancy
  - ERC-20
  - ERC-721
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<action: audit|develop|test|deploy|upgrade|optimize> <contract or description>"
---

# Solidity Audit — Smart Contract Development & Security

Production-grade Solidity development with security-first practices and audit methodology.

**Input:** $ARGUMENTS

---

## STEP 0: Private Key Safety Gate

**Before ANY operation**, check for exposed secrets:

```bash
# Scan for private keys, mnemonics, and API keys in the project
grep -rn "PRIVATE_KEY\|MNEMONIC\|0x[0-9a-fA-F]\{64\}\|secret\|api.key" \
  --include="*.sol" --include="*.js" --include="*.ts" --include="*.json" \
  --include="*.env" --include="*.toml" . 2>/dev/null | \
  grep -v "node_modules\|\.git\|artifacts\|cache"
```

**If ANY private key or mnemonic is found in source code:**
1. STOP immediately
2. Alert the user: `CRITICAL: Private key found in <file>:<line>. Move to .env and add to .gitignore.`
3. Do NOT proceed until resolved

**Verify .gitignore includes:**
```
.env
.env.local
broadcast/
cache/
out/
```

---

## STEP 1: Detect Action

| Action | Trigger | Description |
|--------|---------|-------------|
| `audit` | "audit", "security review" | Full security audit of contracts |
| `develop` | "create", "build", "implement" | Write new smart contracts |
| `test` | "test", "coverage", "fuzz" | Write and run tests |
| `deploy` | "deploy", "script" | Deployment scripts and verification |
| `upgrade` | "upgrade", "proxy", "UUPS" | Upgradeable contract patterns |
| `optimize` | "gas", "optimize", "efficient" | Gas optimization |

---

## STEP 2: Project Setup

### 2.1 Detect Framework

```bash
# Foundry project
test -f foundry.toml && echo "Foundry project"

# Hardhat project
test -f hardhat.config.js -o -f hardhat.config.ts && echo "Hardhat project"

# Neither
echo "No framework detected"
```

### 2.2 New Foundry Project (recommended)

```bash
forge init my-project
cd my-project

# Install OpenZeppelin
forge install OpenZeppelin/openzeppelin-contracts --no-commit

# Install Chainlink (for oracles)
forge install smartcontractkit/chainlink --no-commit

# Update remappings
echo '@openzeppelin/=lib/openzeppelin-contracts/
@chainlink/=lib/chainlink/' > remappings.txt
```

### 2.3 Project Structure

```
project/
  src/              # Contract source files
  test/             # Test files (.t.sol for Foundry)
  script/           # Deployment scripts (.s.sol)
  lib/              # Dependencies (git submodules)
  foundry.toml      # Foundry config
  .env              # Secrets (NEVER commit)
  .gitignore
```

---

## STEP 3: Development Patterns

### 3.1 Contract Structure

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

---

## STEP 4: Testing (Foundry)

### 4.1 Unit Tests

```solidity
// test/MyContract.t.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test, console} from "forge-std/Test.sol";
import {MyContract} from "../src/MyContract.sol";
import {MockERC20} from "./mocks/MockERC20.sol";

contract MyContractTest is Test {
    MyContract public myContract;
    MockERC20 public token;

    address public USER = makeAddr("user");
    address public OWNER = makeAddr("owner");
    uint256 public constant STARTING_BALANCE = 100e18;

    function setUp() public {
        // Runs before each test
        vm.startPrank(OWNER);
        token = new MockERC20("Test", "TST", 18);
        myContract = new MyContract(address(token));
        vm.stopPrank();

        // Fund test user
        token.mint(USER, STARTING_BALANCE);
        vm.prank(USER);
        token.approve(address(myContract), type(uint256).max);
    }

    function test_DepositUpdatesBalance() public {
        uint256 amount = 10e18;

        vm.prank(USER);
        myContract.deposit(amount);

        assertEq(myContract.getBalance(USER), amount);
    }

    function test_RevertWhen_DepositZeroAmount() public {
        vm.prank(USER);
        vm.expectRevert(
            abi.encodeWithSelector(
                MyContract.MyContract__InsufficientBalance.selector,
                0,
                0
            )
        );
        myContract.deposit(0);
    }

    function test_RevertWhen_WithdrawMoreThanBalance() public {
        vm.prank(USER);
        vm.expectRevert();
        myContract.withdraw(1e18);
    }

    function test_EmitsEventOnDeposit() public {
        uint256 amount = 10e18;

        vm.expectEmit(true, false, false, true);
        emit MyContract.Deposited(USER, amount);

        vm.prank(USER);
        myContract.deposit(amount);
    }

    function test_OnlyOwnerCanPause() public {
        vm.prank(USER); // Not owner
        vm.expectRevert();
        myContract.pause();
    }
}
```

### 4.2 Fuzz Testing

```solidity
function testFuzz_DepositAndWithdraw(uint256 amount) public {
    // Bound amount to valid range
    amount = bound(amount, myContract.MIN_DEPOSIT(), token.balanceOf(USER));

    vm.startPrank(USER);
    myContract.deposit(amount);
    myContract.withdraw(amount);
    vm.stopPrank();

    assertEq(myContract.getBalance(USER), 0);
    assertEq(token.balanceOf(USER), STARTING_BALANCE);
}

function testFuzz_FeeCalculation(uint256 amount) public {
    amount = bound(amount, 1e18, 1_000_000e18);

    uint256 fee = myContract.calculateFee(amount);
    uint256 expectedFee = (amount * 30) / 10_000; // 0.3%

    assertEq(fee, expectedFee);
}
```

### 4.3 Invariant Testing

```solidity
// test/invariants/Handler.t.sol
contract Handler is Test {
    MyContract public myContract;

    constructor(MyContract _myContract) {
        myContract = _myContract;
    }

    function deposit(uint256 amount) external {
        amount = bound(amount, 1e18, 100e18);
        // ... setup and call
    }

    function withdraw(uint256 amount) external {
        amount = bound(amount, 0, myContract.getBalance(msg.sender));
        // ... setup and call
    }
}

// test/invariants/Invariants.t.sol
contract InvariantsTest is Test {
    function setUp() public {
        // Setup handler
        targetContract(address(handler));
    }

    function invariant_TotalDepositsSolvency() public view {
        // Total deposits should never exceed token balance
        assertLe(
            myContract.totalDeposits(),
            token.balanceOf(address(myContract))
        );
    }

    function invariant_UserBalancesNeverNegative() public view {
        // Individual balances are uint256, so this is guaranteed,
        // but verify the accounting is correct
        assertGe(myContract.getBalance(USER), 0);
    }
}
```

### 4.4 Running Tests

```bash
# Run all tests
forge test

# Run with verbosity (show logs)
forge test -vvv

# Run specific test
forge test --match-test test_DepositUpdatesBalance -vvv

# Run specific contract
forge test --match-contract MyContractTest

# Fuzz with more runs
forge test --fuzz-runs 10000

# Coverage report
forge coverage

# Coverage with report file
forge coverage --report lcov

# Gas snapshot
forge snapshot

# Compare gas changes
forge snapshot --diff
```

### 4.5 Hardhat Tests (alternative)

```javascript
const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("MyContract", function () {
  let myContract, token, owner, user;

  beforeEach(async function () {
    [owner, user] = await ethers.getSigners();
    const Token = await ethers.getContractFactory("MockERC20");
    token = await Token.deploy("Test", "TST", 18);
    const MyContract = await ethers.getContractFactory("MyContract");
    myContract = await MyContract.deploy(token.address);
  });

  it("should deposit tokens", async function () {
    const amount = ethers.parseEther("10");
    await token.connect(user).approve(myContract.address, amount);
    await myContract.connect(user).deposit(amount);
    expect(await myContract.getBalance(user.address)).to.equal(amount);
  });

  it("should revert on zero deposit", async function () {
    await expect(
      myContract.connect(user).deposit(0)
    ).to.be.revertedWithCustomError(myContract, "MyContract__InsufficientBalance");
  });
});
```

```bash
# Hardhat commands
npx hardhat test
npx hardhat test --grep "should deposit"
npx hardhat coverage
```

---

## STEP 5: Security Audit (Cyfrin Methodology)

### 5.1 Audit Checklist

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

---

## STEP 6: Upgrade Patterns

### 6.1 UUPS (Recommended)

```solidity
// Implementation contract
import {UUPSUpgradeable} from "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import {Initializable} from "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import {OwnableUpgradeable} from "@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";

contract MyContractV1 is Initializable, UUPSUpgradeable, OwnableUpgradeable {
    uint256 public value;

    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() {
        _disableInitializers(); // Prevent implementation from being initialized
    }

    function initialize(address initialOwner) public initializer {
        __Ownable_init(initialOwner);
        __UUPSUpgradeable_init();
        value = 0;
    }

    function setValue(uint256 newValue) external onlyOwner {
        value = newValue;
    }

    function _authorizeUpgrade(address newImplementation) internal override onlyOwner {}
}

// V2 — add new storage at the END (never reorder existing variables)
contract MyContractV2 is MyContractV1 {
    uint256 public newVariable; // Added at end of storage layout

    function newFunction() external view returns (uint256) {
        return value + newVariable;
    }
}
```

### 6.2 Deployment Script (Foundry)

```solidity
// script/Deploy.s.sol
import {Script} from "forge-std/Script.sol";
import {ERC1967Proxy} from "@openzeppelin/contracts/proxy/ERC1967/ERC1967Proxy.sol";
import {MyContractV1} from "../src/MyContractV1.sol";

contract DeployScript is Script {
    function run() external returns (address proxy) {
        vm.startBroadcast();

        // Deploy implementation
        MyContractV1 implementation = new MyContractV1();

        // Deploy proxy pointing to implementation
        bytes memory initData = abi.encodeCall(
            MyContractV1.initialize,
            (msg.sender)
        );
        ERC1967Proxy proxyContract = new ERC1967Proxy(
            address(implementation),
            initData
        );

        vm.stopBroadcast();
        return address(proxyContract);
    }
}
```

**Upgrade rules:**
- NEVER reorder or remove existing storage variables
- ALWAYS add new variables at the END of storage layout
- NEVER change variable types (uint256 → uint128)
- ALWAYS use `_disableInitializers()` in constructor
- ALWAYS test upgrade path: deploy V1 → upgrade to V2 → verify state preserved
- Use storage gaps in base contracts for future expansion:
  ```solidity
  uint256[50] private __gap; // Reserve 50 storage slots
  ```

---

## STEP 7: Gas Optimization

### 7.1 Storage Patterns

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

---

## STEP 8: Deployment

### 8.1 Foundry Deploy Script

```solidity
// script/Deploy.s.sol
import {Script, console} from "forge-std/Script.sol";
import {MyContract} from "../src/MyContract.sol";

contract DeployScript is Script {
    function run() external returns (MyContract) {
        // Load from .env
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address tokenAddress = vm.envAddress("TOKEN_ADDRESS");

        vm.startBroadcast(deployerPrivateKey);
        MyContract myContract = new MyContract(tokenAddress);
        vm.stopBroadcast();

        console.log("Deployed to:", address(myContract));
        return myContract;
    }
}
```

### 8.2 Deploy Commands

```bash
# Local (Anvil)
anvil &  # Start local node
forge script script/Deploy.s.sol --rpc-url http://localhost:8545 --broadcast

# Testnet (Sepolia)
forge script script/Deploy.s.sol \
  --rpc-url $SEPOLIA_RPC_URL \
  --broadcast \
  --verify \
  --etherscan-api-key $ETHERSCAN_API_KEY \
  -vvvv

# Mainnet (with confirmation)
forge script script/Deploy.s.sol \
  --rpc-url $MAINNET_RPC_URL \
  --broadcast \
  --verify \
  --etherscan-api-key $ETHERSCAN_API_KEY \
  --slow \
  -vvvv
```

### 8.3 Helper Config Pattern

Eliminate hardcoded addresses across networks:

```solidity
// script/HelperConfig.s.sol
contract HelperConfig is Script {
    struct NetworkConfig {
        address priceFeed;
        address token;
        uint256 deployerKey;
    }

    NetworkConfig public activeConfig;

    constructor() {
        if (block.chainid == 1) {
            activeConfig = getMainnetConfig();
        } else if (block.chainid == 11155111) {
            activeConfig = getSepoliaConfig();
        } else {
            activeConfig = getAnvilConfig();
        }
    }

    function getMainnetConfig() internal view returns (NetworkConfig memory) {
        return NetworkConfig({
            priceFeed: 0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419,
            token: 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48,
            deployerKey: vm.envUint("PRIVATE_KEY")
        });
    }

    function getSepoliaConfig() internal view returns (NetworkConfig memory) {
        return NetworkConfig({
            priceFeed: 0x694AA1769357215DE4FAC081bf1f309aDC325306,
            token: address(0), // Deploy mock
            deployerKey: vm.envUint("PRIVATE_KEY")
        });
    }

    function getAnvilConfig() internal returns (NetworkConfig memory) {
        // Deploy mocks for local testing
        vm.startBroadcast();
        MockPriceFeed mockFeed = new MockPriceFeed();
        MockERC20 mockToken = new MockERC20("Mock", "MCK", 18);
        vm.stopBroadcast();

        return NetworkConfig({
            priceFeed: address(mockFeed),
            token: address(mockToken),
            deployerKey: 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
        });
    }
}
```

---

## STEP 9: ERC Standards Reference

### ERC-20 (Fungible Token)

```solidity
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MyToken is ERC20 {
    constructor() ERC20("My Token", "MTK") {
        _mint(msg.sender, 1_000_000e18);
    }
}
```

### ERC-721 (NFT)

```solidity
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";

contract MyNFT is ERC721 {
    uint256 private s_tokenCounter;

    constructor() ERC721("My NFT", "MNFT") {}

    function mint() external returns (uint256) {
        uint256 tokenId = s_tokenCounter++;
        _safeMint(msg.sender, tokenId);
        return tokenId;
    }
}
```

### ERC-1155 (Multi-Token)

```solidity
import {ERC1155} from "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";

contract GameItems is ERC1155 {
    uint256 public constant GOLD = 0;
    uint256 public constant SWORD = 1;

    constructor() ERC1155("https://api.example.com/items/{id}.json") {
        _mint(msg.sender, GOLD, 1000, "");
        _mint(msg.sender, SWORD, 1, "");
    }
}
```

---

## STEP 10: Verify & Report

### For Development

```bash
# Compile
forge build

# Test
forge test -vvv

# Coverage
forge coverage

# Gas snapshot
forge snapshot
```

### For Audit

```
Security Audit Report:
  Contract: {{name}}
  Solidity: {{version}}
  Framework: {{Foundry | Hardhat}}
  Lines of Code: {{count}}

  Static Analysis:
    Aderyn: {{findings count by severity}}
    Slither: {{findings count by severity}}

  Test Coverage:
    Statements: {{%}}
    Branches: {{%}}
    Functions: {{%}}

  Checklist:
    Access Control: {{PASS | FAIL — details}}
    Reentrancy: {{PASS | FAIL — details}}
    Input Validation: {{PASS | FAIL — details}}
    Oracle Security: {{PASS | FAIL — details}}
    Token Handling: {{PASS | FAIL — details}}
    MEV Protection: {{PASS | FAIL — details}}
    DoS Resistance: {{PASS | FAIL — details}}
    Gas Optimization: {{suggestions}}

  Critical Findings: {{count}}
  High Findings: {{count}}
  Medium Findings: {{count}}
  Low/Info Findings: {{count}}
```

---

## RULES

- NEVER store private keys, mnemonics, or API keys in source code — use `.env` + `.gitignore`
- ALWAYS follow Check-Effects-Interactions pattern on functions with external calls
- ALWAYS use `nonReentrant` modifier on functions that transfer ETH or call external contracts
- ALWAYS use `SafeERC20` for token transfers — bare `transfer()` can silently fail
- ALWAYS use custom errors instead of `require` strings — saves deployment and runtime gas
- ALWAYS check Chainlink oracle staleness — stale prices can drain protocols
- ALWAYS use two-step ownership transfer (`Ownable2Step`) for critical contracts
- ALWAYS add `_disableInitializers()` in constructors of upgradeable contracts
- NEVER reorder or remove storage variables in upgradeable contracts
- NEVER use `tx.origin` for authorization — use `msg.sender`
- NEVER use `transfer()` or `send()` for ETH — use `call{value: amount}("")` with reentrancy guard
- NEVER hardcode addresses — use HelperConfig pattern for multi-network support
- Run both Aderyn AND Slither before any deployment — they catch different issues
- Pin Solidity version (`pragma solidity 0.8.20;`) — never use floating (`^0.8.0`) in production
- Test coverage must include: unit, fuzz, and invariant tests before audit
