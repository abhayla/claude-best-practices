# STEP 2: Standard Workflow

### 2.1 Setup Dimensions

```javascript
// Responsive container with margin convention
const margin = { top: 40, right: 30, bottom: 50, left: 60 };
const width = 800 - margin.left - margin.right;
const height = 500 - margin.top - margin.bottom;

const svg = d3.select("#chart")
  .append("svg")
  .attr("viewBox", `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`)
  .attr("preserveAspectRatio", "xMidYMid meet")
  .append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);
```

**Rules:**
- ALWAYS use the margin convention — it prevents clipping of axes and labels
- ALWAYS use `viewBox` instead of fixed `width`/`height` for responsive SVGs
- Use `preserveAspectRatio="xMidYMid meet"` for proportional scaling

### 2.2 Create Scales

```javascript
// Continuous scales
const x = d3.scaleLinear().domain([0, d3.max(data, d => d.value)]).range([0, width]);
const y = d3.scaleLinear().domain([0, 100]).range([height, 0]); // Inverted for SVG coords

// Time scale
const xTime = d3.scaleTime()
  .domain(d3.extent(data, d => d.date))
  .range([0, width]);

// Categorical scale
const xBand = d3.scaleBand()
  .domain(data.map(d => d.category))
  .range([0, width])
  .padding(0.2);

// Color scales
const color = d3.scaleOrdinal(d3.schemeTableau10);                    // Categorical
const colorSeq = d3.scaleSequential(d3.interpolateViridis).domain([0, max]); // Sequential
const colorDiv = d3.scaleDiverging(d3.interpolateRdBu).domain([-1, 0, 1]);   // Diverging

// Log / Power scales
const logScale = d3.scaleLog().domain([1, 1000]).range([0, width]);
const sqrtScale = d3.scaleSqrt().domain([0, max]).range([0, 30]); // Common for bubble radius
```

**Scale selection guide:**

| Data Type | Scale | Notes |
|-----------|-------|-------|
| Continuous numeric | `scaleLinear` | Default for most axes |
| Time/Date | `scaleTime` | Handles date objects |
| Categories | `scaleBand` | For bar charts (with width) |
| Categories (points) | `scalePoint` | For dot plots |
| Exponential range | `scaleLog` | Domain must not include 0 |
| Area/radius encoding | `scaleSqrt` | Preserves perceived area |
| Color (sequential) | `scaleSequential` | Single-hue gradients |
| Color (diverging) | `scaleDiverging` | Two-hue around midpoint |
| Color (categorical) | `scaleOrdinal` | Distinct colors per group |

### 2.3 Create Axes

```javascript
// Add axes
svg.append("g")
  .attr("class", "x-axis")
  .attr("transform", `translate(0,${height})`)
  .call(d3.axisBottom(x))
  .selectAll("text")
  .attr("transform", "rotate(-45)")
  .style("text-anchor", "end");

svg.append("g")
  .attr("class", "y-axis")
  .call(d3.axisLeft(y).ticks(5).tickFormat(d3.format(",.0f")));

// Axis labels
svg.append("text")
  .attr("x", width / 2)
  .attr("y", height + margin.bottom - 5)
  .attr("text-anchor", "middle")
  .text("X Axis Label");

svg.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -height / 2)
  .attr("y", -margin.left + 15)
  .attr("text-anchor", "middle")
  .text("Y Axis Label");
```

### 2.4 Bind Data & Render

```javascript
// Modern join pattern (D3 v6+)
svg.selectAll(".bar")
  .data(data, d => d.id)   // Key function for object constancy
  .join(
    enter => enter.append("rect")
      .attr("class", "bar")
      .attr("x", d => xBand(d.category))
      .attr("width", xBand.bandwidth())
      .attr("y", height)           // Start from bottom
      .attr("height", 0)           // Start with no height
      .attr("fill", d => color(d.category))
      .call(enter => enter.transition().duration(750)
        .attr("y", d => y(d.value))
        .attr("height", d => height - y(d.value))
      ),
    update => update
      .call(update => update.transition().duration(750)
        .attr("y", d => y(d.value))
        .attr("height", d => height - y(d.value))
      ),
    exit => exit
      .call(exit => exit.transition().duration(300)
        .attr("height", 0)
        .attr("y", height)
        .remove()
      )
  );
```

**Rules:**
- ALWAYS use `.join()` (D3 v6+) instead of the old `.enter().append()` pattern
- ALWAYS provide a key function (`d => d.id`) for object constancy during updates
- Enter: animate from invisible state → visible
- Exit: animate from visible → invisible, then `.remove()`

---

