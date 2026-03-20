# Solidity Testing Guide


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
