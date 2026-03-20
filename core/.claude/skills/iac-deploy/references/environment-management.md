# Environment Management

## Terraform Workspaces

```bash
# Create workspaces
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# Switch workspace
terraform workspace select prod

# List workspaces
terraform workspace list
```

```hcl
# Reference workspace in config
locals {
  environment = terraform.workspace
  is_prod     = terraform.workspace == "prod"
}
```

**Workspace limitations:** Workspaces share the same backend config and code. For significantly different environments, use separate directories or Terragrunt instead.

## Variable Files Per Environment (Preferred Approach)

```hcl
# environments/prod.tfvars
environment    = "prod"
instance_type  = "t3.large"
instance_count = 3
enable_waf     = true
db_multi_az    = true
```

```bash
# Apply with environment-specific vars
terraform plan -var-file=environments/prod.tfvars
terraform apply -var-file=environments/prod.tfvars
```

## Pulumi Stacks

```bash
# Each stack is a separate environment
pulumi stack select dev
pulumi up

pulumi stack select prod
pulumi up
```

```python
# Stack-aware configuration in Pulumi
import pulumi

stack = pulumi.get_stack()
config = pulumi.Config()

# Stack-specific defaults
instance_type = config.get("instanceType") or ("t3.large" if stack == "prod" else "t3.micro")
replicas = config.get_int("replicas") or (3 if stack == "prod" else 1)
```
