# Upgrade Patterns


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
