---
name: web-scraper
description: >
  Web scraping patterns with Puppeteer, Cheerio, and data extraction pipelines.
  Use when building scrapers, crawlers, or data extraction workflows.
allowed-tools: "Read Grep Glob"
argument-hint: "[cheerio|puppeteer|pipeline|anti-detection]"
version: "1.0.0"
type: reference
triggers: scraper, scraping, puppeteer, cheerio, crawl, crawler
---

# Web Scraper Reference

Web scraping with Cheerio (HTML parsing), Puppeteer (headless browser), and pipeline orchestration.

## Cheerio (Static HTML Parsing)

Best for: server-rendered pages, RSS feeds, simple HTML extraction. Fast and lightweight.

### Basic Usage

```typescript
import axios from "axios";
import * as cheerio from "cheerio";

async function scrape(url: string) {
  const { data: html } = await axios.get(url, {
    headers: { "User-Agent": "Mozilla/5.0 (compatible; YourBot/1.0)" },
    timeout: 10000,
  });

  const $ = cheerio.load(html);

  const items = $(".item-card").map((_, el) => ({
    title: $(el).find("h2").text().trim(),
    price: $(el).find(".price").text().trim(),
    link: $(el).find("a").attr("href"),
  })).get();

  return items;
}
```

### Common Selectors

```typescript
const $ = cheerio.load(html);

// Text content
$("h1").text();                    // inner text
$("h1").first().text();            // first match only

// Attributes
$("a").attr("href");               // attribute value
$("img").attr("src");

// Multiple elements → array
$("li").map((_, el) => $(el).text()).get();

// Nested selection
$("table tbody tr").each((_, row) => {
  const cols = $(row).find("td").map((_, td) => $(td).text().trim()).get();
});

// Filter
$("div").filter(".active");

// HTML content
$(".content").html();              // inner HTML
```

### Handling Tables

```typescript
function parseTable($: cheerio.CheerioAPI, selector: string) {
  const headers = $(`${selector} thead th`)
    .map((_, th) => $(th).text().trim().toLowerCase().replace(/\s+/g, "_"))
    .get();

  const rows = $(`${selector} tbody tr`).map((_, tr) => {
    const cells = $(tr).find("td").map((_, td) => $(td).text().trim()).get();
    return Object.fromEntries(headers.map((h, i) => [h, cells[i] ?? ""]));
  }).get();

  return rows;
}
```

## Puppeteer (Headless Browser)

Best for: JavaScript-rendered pages (SPAs), pages requiring login, infinite scroll, complex interactions.

### Basic Usage

```typescript
import puppeteer from "puppeteer";

async function scrape(url: string) {
  const browser = await puppeteer.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  try {
    const page = await browser.newPage();
    await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64)...");
    await page.setViewport({ width: 1280, height: 800 });

    await page.goto(url, { waitUntil: "networkidle2", timeout: 30000 });

    // Wait for specific element
    await page.waitForSelector(".data-table", { timeout: 10000 });

    // Extract data
    const data = await page.evaluate(() => {
      return Array.from(document.querySelectorAll(".item")).map((el) => ({
        title: el.querySelector("h2")?.textContent?.trim() ?? "",
        price: el.querySelector(".price")?.textContent?.trim() ?? "",
      }));
    });

    return data;
  } finally {
    await browser.close();
  }
}
```

### Handling Infinite Scroll

```typescript
async function scrollToBottom(page: puppeteer.Page, maxScrolls = 20) {
  let previousHeight = 0;
  let scrollCount = 0;

  while (scrollCount < maxScrolls) {
    const currentHeight = await page.evaluate(() => document.body.scrollHeight);
    if (currentHeight === previousHeight) break;

    previousHeight = currentHeight;
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForFunction(
      (prev) => document.body.scrollHeight > prev,
      { timeout: 5000 },
      previousHeight,
    ).catch(() => {}); // timeout = no more content
    scrollCount++;
  }
}
```

### Form Submission and Login

```typescript
async function login(page: puppeteer.Page, email: string, password: string) {
  await page.goto("https://example.com/login", { waitUntil: "networkidle2" });
  await page.type("#email", email, { delay: 50 });
  await page.type("#password", password, { delay: 50 });
  await Promise.all([
    page.waitForNavigation({ waitUntil: "networkidle2" }),
    page.click("#login-button"),
  ]);
}
```

### Intercepting Network Requests

```typescript
// Block images/fonts/CSS for faster scraping
await page.setRequestInterception(true);
page.on("request", (req) => {
  if (["image", "stylesheet", "font"].includes(req.resourceType())) {
    req.abort();
  } else {
    req.continue();
  }
});
```

## PDF Extraction

```typescript
import pdfParse from "pdf-parse";
import fs from "fs";

async function extractPdf(filePath: string) {
  const buffer = fs.readFileSync(filePath);
  const data = await pdfParse(buffer);
  return {
    text: data.text,
    pages: data.numpages,
    info: data.info,
  };
}

// From URL
async function extractPdfFromUrl(url: string) {
  const response = await axios.get(url, { responseType: "arraybuffer" });
  const data = await pdfParse(Buffer.from(response.data));
  return data.text;
}
```

## RSS Feed Parsing

```typescript
import Parser from "rss-parser";

const parser = new Parser({
  customFields: { item: ["media:content", "dc:creator"] },
});

async function parseFeed(url: string) {
  const feed = await parser.parseURL(url);
  return feed.items.map((item) => ({
    title: item.title,
    link: item.link,
    date: item.pubDate,
    content: item.contentSnippet,
  }));
}
```

## Scraping Pipeline Architecture

```typescript
interface ScrapeResult<T> {
  source: string;
  data: T[];
  scrapedAt: Date;
  errors: string[];
}

abstract class BaseScraper<T> {
  abstract name: string;
  abstract scrape(): Promise<T[]>;

  async run(): Promise<ScrapeResult<T>> {
    const errors: string[] = [];
    let data: T[] = [];

    try {
      data = await this.scrape();
    } catch (err) {
      errors.push(`${this.name}: ${err instanceof Error ? err.message : String(err)}`);
    }

    return { source: this.name, data, scrapedAt: new Date(), errors };
  }
}

// Orchestrator
async function runPipeline(scrapers: BaseScraper<unknown>[]) {
  const results = await Promise.allSettled(
    scrapers.map((s) => s.run()),
  );

  const successful = results
    .filter((r): r is PromiseFulfilledResult<ScrapeResult<unknown>> => r.status === "fulfilled")
    .map((r) => r.value);

  const failed = results
    .filter((r): r is PromiseRejectedResult => r.status === "rejected")
    .map((r) => r.reason);

  return { successful, failed };
}
```

## Scheduling with node-cron

```typescript
import cron from "node-cron";

// Run every 6 hours
cron.schedule("0 */6 * * *", async () => {
  console.log("Starting scheduled scrape...");
  try {
    await runPipeline(scrapers);
  } catch (err) {
    console.error("Pipeline failed:", err);
  }
});
```

## Rate Limiting and Politeness

```typescript
class RateLimiter {
  private queue: Array<() => Promise<void>> = [];
  private running = 0;

  constructor(
    private concurrency: number = 2,
    private delayMs: number = 1000,
  ) {}

  async add<T>(fn: () => Promise<T>): Promise<T> {
    while (this.running >= this.concurrency) {
      await new Promise((r) => setTimeout(r, 100));
    }
    this.running++;
    try {
      const result = await fn();
      await new Promise((r) => setTimeout(r, this.delayMs));
      return result;
    } finally {
      this.running--;
    }
  }
}

// Usage
const limiter = new RateLimiter(2, 1500); // 2 concurrent, 1.5s delay
const results = await Promise.all(
  urls.map((url) => limiter.add(() => scrape(url))),
);
```

## Error Handling and Retry

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  retries = 3,
  delay = 1000,
): Promise<T> {
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (err) {
      if (i === retries - 1) throw err;
      const backoff = delay * Math.pow(2, i) + Math.random() * 1000;
      console.warn(`Retry ${i + 1}/${retries} after ${backoff}ms`);
      await new Promise((r) => setTimeout(r, backoff));
    }
  }
  throw new Error("Unreachable");
}
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Empty results with Cheerio | Page is JavaScript-rendered | Switch to Puppeteer |
| Puppeteer timeout | Slow page load | Increase timeout, block images/CSS |
| `net::ERR_ABORTED` | Request blocked by site | Add proper User-Agent, use delays |
| Memory leak with Puppeteer | Browser not closed | Always `browser.close()` in `finally` |
| Stale data | Page structure changed | Add selector validation, alert on empty results |
| IP blocked | Too many requests | Add delays, use rate limiter |
| CAPTCHA encountered | Anti-bot detection | Reduce request rate, add human-like delays |

## CRITICAL RULES

### MUST DO
- Always close Puppeteer browser instances in a `finally` block
- Always set a User-Agent header that identifies your scraper
- Always implement rate limiting — minimum 1s delay between requests to same domain
- Always handle errors per-source so one failure doesn't crash the pipeline
- Always validate extracted data (check for empty results, unexpected formats)
- Always respect `robots.txt` and site terms of service
- Use Cheerio for static HTML (faster, lighter) — only use Puppeteer when JavaScript rendering is required

### MUST NOT DO
- NEVER scrape without rate limiting — it can get your IP banned or cause DoS
- NEVER store scraped credentials or personal data without authorization
- NEVER hardcode selectors without validation — sites change their HTML structure
- NEVER run Puppeteer with `--disable-web-security` in production
- NEVER ignore `robots.txt` disallow rules without explicit permission
