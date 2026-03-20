# Module Composition

## Terraform Module Structure

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

## Module Input/Output Contract

```hcl
# modules/vpc/variables.tf — inputs
variable "cidr_block" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "Must be a valid CIDR block."
  }
}

variable "availability_zones" {
  description = "List of AZs for subnet distribution"
  type        = list(string)
}

variable "enable_nat_gateway" {
  description = "Whether to provision NAT gateways for private subnets"
  type        = bool
  default     = true
}

# modules/vpc/outputs.tf — outputs
output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}
```

## Calling Modules

```hcl
# Root module — main.tf
module "vpc" {
  source = "./modules/vpc"

  cidr_block         = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
  enable_nat_gateway = var.environment == "prod"
}

module "database" {
  source = "./modules/database"

  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnet_ids
  instance_class     = var.environment == "prod" ? "db.r6g.large" : "db.t3.micro"
  master_password    = var.db_password
}
```

## Module Versioning

```hcl
# From Terraform Registry
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
}

# From Git with tag
module "vpc" {
  source = "git::https://github.com/myorg/terraform-modules.git//vpc?ref=v2.1.0"
}
```

## Module Rules

- MUST version-pin all external module sources.
- MUST define clear input/output contracts with descriptions and validations.
- NEVER put provider blocks inside modules — providers are passed from root.
- Modules MUST be stateless — no backend configuration inside modules.
- Keep modules focused: one logical concern per module (networking, compute, database).
