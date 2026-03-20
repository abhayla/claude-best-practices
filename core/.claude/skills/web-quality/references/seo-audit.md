# STEP 4: SEO Audit

### 4.1 Meta Tags

- [ ] `<title>` is present, unique per page, 50-60 characters
- [ ] `<meta name="description">` is present, unique per page, 150-160 characters
- [ ] `<meta name="viewport" content="width=device-width, initial-scale=1">` is set
- [ ] `<link rel="canonical">` points to the preferred URL for each page
- [ ] `<meta name="robots">` is set appropriately (index,follow for public pages)
- [ ] `<html lang="en">` (or appropriate language) is set
- [ ] `<meta charset="utf-8">` is present

### 4.2 Open Graph and Twitter Cards

- [ ] `og:title` — page title for social sharing
- [ ] `og:description` — page description for social sharing
- [ ] `og:image` — social sharing image (1200x630px recommended)
- [ ] `og:url` — canonical URL
- [ ] `og:type` — website, article, product, etc.
- [ ] `og:site_name` — site name
- [ ] `twitter:card` — summary, summary_large_image, etc.
- [ ] `twitter:title`, `twitter:description`, `twitter:image` (falls back to OG if missing)

### 4.3 Structured Data (JSON-LD)

Add structured data to help search engines understand page content:

```html
<!-- Organization (site-wide) -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Company Name",
  "url": "https://example.com",
  "logo": "https://example.com/logo.png",
  "sameAs": ["https://twitter.com/example", "https://linkedin.com/company/example"]
}
</script>

<!-- Article -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Article Title",
  "author": { "@type": "Person", "name": "Author Name" },
  "datePublished": "2024-01-15",
  "dateModified": "2024-01-20",
  "image": "https://example.com/article-image.jpg"
}
</script>

<!-- BreadcrumbList -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://example.com" },
    { "@type": "ListItem", "position": 2, "name": "Blog", "item": "https://example.com/blog" },
    { "@type": "ListItem", "position": 3, "name": "Article Title" }
  ]
}
</script>

<!-- FAQ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is the question?",
      "acceptedAnswer": { "@type": "Answer", "text": "The answer." }
    }
  ]
}
</script>

<!-- Product -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Product Name",
  "image": "https://example.com/product.jpg",
  "offers": {
    "@type": "Offer",
    "price": "29.99",
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock"
  }
}
</script>
```

Checklist:
- [ ] At least one structured data type per page
- [ ] JSON-LD format used (not Microdata or RDFa)
- [ ] No validation errors in Google's Rich Results Test
- [ ] `@context` and `@type` are present
- [ ] Required fields for each type are populated

### 4.4 Technical SEO

- [ ] XML sitemap exists at `/sitemap.xml`
- [ ] `robots.txt` exists and doesn't block important pages
- [ ] Sitemap is referenced in `robots.txt`
- [ ] Clean, descriptive URLs (no query parameter soup)
- [ ] Heading hierarchy is logical (`h1` > `h2` > `h3`)
- [ ] Internal links use descriptive anchor text (not "click here")
- [ ] Broken links are identified and fixed (404s)
- [ ] 301 redirects are in place for moved pages
- [ ] HTTPS is enforced (HTTP redirects to HTTPS)
- [ ] `hreflang` tags for multi-language sites
- [ ] Page load time under 3 seconds

---

