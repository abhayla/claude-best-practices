# ERC Standards Reference

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