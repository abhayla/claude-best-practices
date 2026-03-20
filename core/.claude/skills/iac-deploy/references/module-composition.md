# STEP 5: Module Composition

### 5.1 Terraform Module Structure

```
modules/
  vpc/
    main.tf          # Resource definitions
    variables.tf     # Input variables
    outputs.tf       # Output values
    versions.tf      # Provider requirements
    README.md        # Usage documentation
  database/
    main.tf
    variables.tf
    outputs.tf
    versions.tf
```

### 5.2 Module Input/Output Contract

```hcl
