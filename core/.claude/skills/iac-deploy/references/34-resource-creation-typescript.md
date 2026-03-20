# 3.4 Resource Creation — TypeScript

### 3.4 Resource Creation — TypeScript

```typescript
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

const config = new pulumi.Config();
const environment = pulumi.getStack();
const projectName = pulumi.getProject();

const commonTags = {
    Environment: environment,
    ManagedBy: "pulumi",
    Project: projectName,
};

const dataBucket = new aws.s3.Bucket("data-lake", {
    bucket: `${projectName}-${environment}-data-lake`,
    versioning: { enabled: true },
    serverSideEncryptionConfiguration: {
        rule: {
            applyServerSideEncryptionByDefault: {
                sseAlgorithm: "aws:kms",
            },
        },
    },
    tags: { ...commonTags, Purpose: "Data lake storage" },
});

export const bucketName = dataBucket.bucket;
export const bucketArn = dataBucket.arn;
```

