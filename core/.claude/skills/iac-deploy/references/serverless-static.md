# Serverless and Static Site Deployment

Serverless functions (Lambda/Cloud Functions/Azure Functions), static site deployment (Vercel/Netlify/Cloudflare Pages/Firebase Hosting), SSR deployment, and command cheat sheets.

---

## Serverless & Static Site Deployment

### 14.1 Serverless Functions (AWS Lambda / GCP Cloud Functions / Azure Functions)

```hcl
# Terraform: AWS Lambda function
resource "aws_lambda_function" "api" {
  function_name = "${local.name_prefix}-api"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "index.handler"
  runtime       = "nodejs20.x"
  timeout       = 30
  memory_size   = 256

  filename         = "lambda.zip"
  source_code_hash = filebase64sha256("lambda.zip")

  environment {
    variables = {
      NODE_ENV     = var.environment
      DATABASE_URL = aws_secretsmanager_secret_version.db_url.secret_string
    }
  }

  tracing_config {
    mode = "Active"  # X-Ray tracing
  }
}

resource "aws_lambda_function_url" "api" {
  function_name      = aws_lambda_function.api.function_name
  authorization_type = "NONE"  # Or "AWS_IAM" for authenticated
}

# API Gateway integration
resource "aws_apigatewayv2_api" "api" {
  name          = "${local.name_prefix}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}
```

```python
# Pulumi: GCP Cloud Function
import pulumi_gcp as gcp

function = gcp.cloudfunctions.Function(
    "api-function",
    runtime="python312",
    entry_point="handler",
    source_archive_bucket=source_bucket.name,
    source_archive_object=source_archive.name,
    trigger_http=True,
    available_memory_mb=256,
    timeout=60,
    environment_variables={
        "ENV": pulumi.get_stack(),
    },
)
```

### 14.2 Static Site / SSR Deployment

| Platform | Best For | Deploy Method |
|----------|---------|-------------|
| Vercel | Next.js, SSR, edge functions | `vercel --prod` or Git integration |
| Netlify | Static sites, Jamstack, forms | `netlify deploy --prod` or Git integration |
| Cloudflare Pages | Static + Workers, global edge | `wrangler pages deploy` or Git integration |
| AWS S3 + CloudFront | Full control, AWS-native | Terraform + `aws s3 sync` |
| Firebase Hosting | Google ecosystem, preview channels | `firebase deploy --only hosting` |

```bash
# Vercel: deploy from CI
npx vercel --prod --token=$VERCEL_TOKEN

# Netlify: deploy from CI
npx netlify deploy --prod --dir=dist --auth=$NETLIFY_AUTH_TOKEN --site=$NETLIFY_SITE_ID

# Cloudflare Pages: deploy from CI
npx wrangler pages deploy dist --project-name=my-site

# AWS S3 + CloudFront: deploy from CI
aws s3 sync dist/ s3://$BUCKET_NAME --delete
aws cloudfront create-invalidation --distribution-id $CF_DIST_ID --paths "/*"

# Firebase Hosting
firebase deploy --only hosting --token=$FIREBASE_TOKEN
```

### 14.3 SSR Deployment (Next.js / Nuxt)

```yaml
# GitHub Actions: Vercel deployment
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run build
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

### 14.4 Preview Deployments

Every PR gets its own preview URL for stakeholder review:

| Platform | Preview URL Pattern | Setup |
|----------|-------------------|-------|
| Vercel | `<branch>.vercel.app` | Automatic with Git integration |
| Netlify | `deploy-preview-<N>.netlify.app` | Automatic with Git integration |
| Firebase | `<channel>--<project>.web.app` | `firebase hosting:channel:deploy pr-<N>` |
| Cloudflare Pages | `<hash>.<project>.pages.dev` | Automatic with Git integration |

---

## Quick Reference

### Terraform Command Cheat Sheet

```bash
terraform init                          # Initialize, download providers
terraform validate                      # Syntax and config validation
terraform fmt -recursive                # Format all .tf files
terraform plan -var-file=env.tfvars     # Preview changes
terraform plan -out=tfplan              # Save plan to file
terraform apply tfplan                  # Apply saved plan
terraform apply -target=module.vpc      # Apply specific resource/module
terraform destroy                       # Destroy all managed resources
terraform state list                    # List resources in state
terraform state show aws_vpc.main       # Show resource details
terraform output                        # Show all outputs
terraform import TYPE.NAME ID           # Import existing resource
terraform force-unlock LOCK_ID          # Release stuck lock
terraform providers                     # List required providers
```

### Pulumi Command Cheat Sheet

```bash
pulumi new aws-python                   # Create new project
pulumi stack init dev                   # Create new stack
pulumi stack select prod                # Switch stack
pulumi config set key value             # Set config
pulumi config set --secret key value    # Set secret config
pulumi preview                          # Preview changes
pulumi up                               # Deploy changes
pulumi destroy                          # Tear down stack
pulumi stack export                     # Export stack state
pulumi import TYPE NAME ID              # Import existing resource
pulumi refresh                          # Sync state with cloud
```

### File Organization Convention

```
infrastructure/
  main.tf              # Root module — module calls
  variables.tf         # Root input variables
  outputs.tf           # Root outputs
  versions.tf          # Terraform and provider versions
  backend.tf           # Remote state configuration
  locals.tf            # Computed values and common tags
  environments/
    dev.tfvars
    staging.tfvars
    prod.tfvars
  modules/
    vpc/
    compute/
    database/
    storage/
    dns/
```

---
