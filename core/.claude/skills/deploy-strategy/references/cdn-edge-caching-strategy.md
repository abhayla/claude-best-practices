# STEP 8: CDN & Edge Caching Strategy

### 8.1 CDN Provider Setup

| Provider | Best For | IaC Resource |
|----------|---------|-------------|
| CloudFront | AWS-native, S3 origins | `aws_cloudfront_distribution` |
| Cloudflare | Multi-cloud, DDoS protection, Workers | `cloudflare_zone` + `cloudflare_record` |
| Fastly | Real-time purge, VCL customization | `fastly_service_vcl` |
| Cloud CDN (GCP) | GCP-native, Cloud Storage origins | `google_compute_backend_bucket` |

### 8.2 Cache-Control Strategy

| Content Type | Cache-Control Header | TTL | Rationale |
|-------------|---------------------|-----|-----------|
| Static assets (JS/CSS with hash) | `public, max-age=31536000, immutable` | 1 year | Content-hash in filename = safe to cache forever |
| Static assets (no hash) | `public, max-age=86400` | 1 day | May change, moderate cache |
| HTML pages | `public, max-age=0, must-revalidate` | 0 (ETag) | Always check freshness |
| API responses (public) | `public, max-age=60, stale-while-revalidate=300` | 1 min + 5 min stale | Fresh data with fallback |
| API responses (private) | `private, no-store` | None | User-specific, never cache |
| Images/media | `public, max-age=604800` | 7 days | Rarely change |
| Fonts | `public, max-age=31536000, immutable` | 1 year | Never change |

### 8.3 Cache Invalidation

| Strategy | When to Use | How |
|----------|------------|-----|
| **Content-hash filenames** | JS/CSS bundles | Webpack/Vite adds hash to filename — new deploy = new URL |
| **Purge on deploy** | HTML, API responses | CI/CD step: `aws cloudfront create-invalidation --paths "/*"` |
| **Stale-while-revalidate** | API data that tolerates brief staleness | `Cache-Control: max-age=60, stale-while-revalidate=300` |
| **Tag-based purge** | Granular invalidation (Fastly, Cloudflare) | Surrogate-Key header + purge by tag |

```yaml
