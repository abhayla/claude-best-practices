# 3.5 Resource Creation — Go

### 3.5 Resource Creation — Go

```go
package main

import (
    "fmt"
    "github.com/pulumi/pulumi-aws/sdk/v6/go/aws/s3"
    "github.com/pulumi/pulumi/sdk/v3/go/pulumi"
    "github.com/pulumi/pulumi/sdk/v3/go/pulumi/config"
)

func main() {
    pulumi.Run(func(ctx *pulumi.Context) error {
        env := ctx.Stack()
        project := ctx.Project()
        cfg := config.New(ctx, "")

        bucket, err := s3.NewBucket(ctx, "data-lake", &s3.BucketArgs{
            Bucket: pulumi.Sprintf("%s-%s-data-lake", project, env),
            Tags: pulumi.StringMap{
                "Environment": pulumi.String(env),
                "ManagedBy":   pulumi.String("pulumi"),
            },
        })
        if err != nil {
            return err
        }

        ctx.Export("bucketName", bucket.Bucket)
        return nil
    })
}
```

**Pulumi key rules:**
- MUST use `pulumi.get_stack()` / `getStack()` for environment differentiation — never hardcode.
- MUST use `pulumi config set --secret` for any sensitive values.
- MUST export critical resource attributes (IDs, ARNs, endpoints) for cross-stack references.
- Use component resources (classes extending `pulumi.ComponentResource`) for reusable abstractions.

---

