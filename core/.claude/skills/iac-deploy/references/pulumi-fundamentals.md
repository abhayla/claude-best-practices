# Pulumi Fundamentals

## Project Structure

```yaml
# Pulumi.yaml
name: my-infra
runtime: python  # or nodejs, go, dotnet
description: Core infrastructure for my-project
```

## Stack Configuration

```bash
# Create stacks
pulumi stack init dev
pulumi stack init staging
pulumi stack init prod

# Set config values
pulumi config set aws:region us-east-1
pulumi config set instanceType t3.micro
pulumi config set --secret dbPassword 'supersecret'

# Stack-specific config
pulumi stack select prod
pulumi config set instanceType t3.large
```

## Resource Creation (Python)

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()
environment = pulumi.get_stack()
project_name = config.require("projectName")

# Common tags applied to all resources
common_tags = {
    "Environment": environment,
    "ManagedBy": "pulumi",
    "Project": project_name,
}

# S3 bucket
data_bucket = aws.s3.Bucket(
    "data-lake",
    bucket=f"{project_name}-{environment}-data-lake",
    versioning=aws.s3.BucketVersioningArgs(enabled=True),
    server_side_encryption_configuration=aws.s3.BucketServerSideEncryptionConfigurationArgs(
        rule=aws.s3.BucketServerSideEncryptionConfigurationRuleArgs(
            apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                sse_algorithm="aws:kms",
            ),
        ),
    ),
    tags={**common_tags, "Purpose": "Data lake storage"},
)

pulumi.export("bucket_name", data_bucket.bucket)
pulumi.export("bucket_arn", data_bucket.arn)
```
