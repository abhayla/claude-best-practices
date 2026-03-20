# Deployment Guide


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