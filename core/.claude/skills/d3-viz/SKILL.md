---
name: d3-viz
description: >
  Build D3.js data visualizations including bar, line, scatter, pie, heatmap, chord,
  force graph, treemap, and choropleth charts with responsive SVG and interactions.
  Use when creating or modifying data visualizations with D3.
triggers:
  - d3
  - d3.js
  - data visualization
  - chart
  - scatter plot
  - force graph
  - choropleth
  - treemap
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<chart-type: bar|line|scatter|pie|heatmap|chord|force|treemap|choropleth> <description>"
version: "1.0.0"
type: workflow
---

# D3.js — Interactive Data Visualization

Create publication-quality, interactive data visualizations with D3.js.

**Input:** $ARGUMENTS

---

## STEP 1: Detect Chart Type

| Type | When to Use | D3 Generators |
|------|-------------|---------------|
| `bar` | Categorical comparisons | `scaleBand`, `scaleLinear` |
| `line` | Time series, trends | `d3.line()`, `d3.curveMonotoneX` |
| `scatter` | Correlations, distributions | `scaleLinear` x2, optional size/color |
| `pie` | Part-to-whole (≤7 slices) | `d3.pie()`, `d3.arc()` |
| `heatmap` | Matrix data, density | `scaleBand` x2, `scaleSequential` |
| `chord` | Entity relationships, flows | `d3.chord()`, `d3.ribbon()` |
| `force` | Networks, graphs | `d3.forceSimulation()` |
| `treemap` | Hierarchical proportions | `d3.treemap()`, `d3.hierarchy()` |
| `choropleth` | Geographic data | `d3.geoPath()`, projections |

---

## STEP 2: Standard Workflow

Every D3 visualization follows this structure:


**Read:** `references/standard-workflow.md` for detailed step 2: standard workflow reference material.

## STEP 3: Chart Templates


**Read:** `references/chart-templates.md` for detailed step 3: chart templates reference material.

## STEP 4: Interactions

### 4.1 Tooltips

```javascript
// Create tooltip div (outside SVG)
const tooltip = d3.select("body").append("div")
  .attr("class", "tooltip")
  .style("position", "absolute")
  .style("background", "rgba(0,0,0,0.8)")
  .style("color", "white")
  .style("padding", "8px 12px")
  .style("border-radius", "4px")
  .style("font-size", "13px")
  .style("pointer-events", "none")
  .style("opacity", 0);

// Attach to elements
svg.selectAll(".bar")
  .on("mouseover", (event, d) => {
    tooltip.transition().duration(200).style("opacity", 1);
    tooltip.html(`<strong>${d.label}</strong><br/>Value: ${d.value}`)
      .style("left", (event.pageX + 10) + "px")
      .style("top", (event.pageY - 28) + "px");
  })
  .on("mouseout", () => {
    tooltip.transition().duration(300).style("opacity", 0);
  });
```

### 4.2 Zoom & Pan

```javascript
const zoom = d3.zoom()
  .scaleExtent([0.5, 10])
  .on("zoom", (event) => {
    g.attr("transform", event.transform);
  });

svg.call(zoom);

// Reset zoom button
d3.select("#reset-zoom").on("click", () => {
  svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity);
});
```

### 4.3 Brush (Range Selection)

```javascript
const brush = d3.brushX()
  .extent([[0, 0], [width, height]])
  .on("end", (event) => {
    if (!event.selection) return;
    const [x0, x1] = event.selection.map(x.invert);
    // Filter data to selected range
    const filtered = data.filter(d => d.date >= x0 && d.date <= x1);
    updateChart(filtered);
  });

svg.append("g").attr("class", "brush").call(brush);
```

---

## STEP 5: Transitions & Animation

```javascript
// Basic transition
svg.selectAll(".bar")
  .transition()
  .duration(750)
  .ease(d3.easeCubicInOut)
  .attr("y", d => y(d.value))
  .attr("height", d => height - y(d.value));

// Staggered entrance
svg.selectAll(".bar")
  .transition()
  .duration(500)
  .delay((d, i) => i * 50)  // 50ms between each bar
  .attr("y", d => y(d.value))
  .attr("height", d => height - y(d.value));

// Chained transitions
svg.selectAll(".dot")
  .transition().duration(300)
    .attr("r", 10)
  .transition().duration(300)
    .attr("fill", "red")
  .transition().duration(300)
    .attr("r", 5);

// Line draw animation
const totalLength = path.node().getTotalLength();
path
  .attr("stroke-dasharray", totalLength)
  .attr("stroke-dashoffset", totalLength)
  .transition()
  .duration(2000)
  .ease(d3.easeLinear)
  .attr("stroke-dashoffset", 0);
```

**Easing options:**

| Easing | Effect |
|--------|--------|
| `easeLinear` | Constant speed |
| `easeCubicInOut` | Smooth start and end (default) |
| `easeElasticOut` | Springy overshoot |
| `easeBounceOut` | Bouncing finish |
| `easeBackOut` | Slight overshoot then settle |

---

## STEP 6: Responsive Design

```javascript
function makeResponsive(container, renderFn, data) {
  const observer = new ResizeObserver(entries => {
    for (const entry of entries) {
      const { width, height } = entry.contentRect;
      d3.select(container).select("svg").remove(); // Clear
      renderFn(data, { container, width, height });
    }
  });
  observer.observe(d3.select(container).node());
  return observer; // Return to disconnect later
}

// Usage
makeResponsive("#chart", barChart, data);
```

**Mobile breakpoints:**
```javascript
const isMobile = width < 600;
const margin = isMobile
  ? { top: 10, right: 10, bottom: 30, left: 40 }
  : { top: 20, right: 30, bottom: 50, left: 60 };

// Reduce tick count on mobile
axis.ticks(isMobile ? 4 : 8);

// Rotate labels on mobile
if (isMobile) {
  xAxis.selectAll("text").attr("transform", "rotate(-45)").style("text-anchor", "end");
}
```

---

## STEP 7: Framework Integration

### 7.1 React

```tsx
import { useEffect, useRef } from "react";
import * as d3 from "d3";

function BarChart({ data }) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || !data.length) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // Clear previous render

    // ... D3 rendering code using svg ...
  }, [data]);

  return <svg ref={svgRef} />;
}
```

**Rules for React:**
- Use `useRef` to get the SVG element — NEVER use `d3.select("#id")` in React
- Clear previous render with `svg.selectAll("*").remove()` in `useEffect`
- Put D3 code in `useEffect` with data as dependency
- Let D3 handle the SVG internals, React handles the container

### 7.2 Vanilla HTML

```html
<div id="chart"></div>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
  // D3 code using d3.select("#chart")
</script>
```

---

## STEP 8: Data Loading & Formatting

```javascript
// CSV
const data = await d3.csv("data.csv", d => ({
  date: d3.timeParse("%Y-%m-%d")(d.date),
  value: +d.value,  // Convert string to number
  label: d.label,
}));

// JSON
const data = await d3.json("data.json");

// TSV
const data = await d3.tsv("data.tsv", d3.autoType);  // Auto-detect types

// Number formatting
d3.format(",.0f")(1234567)    // "1,234,567"
d3.format("$.2f")(42.5)       // "$42.50"
d3.format(".1%")(0.853)       // "85.3%"
d3.format(".2s")(1500000)     // "1.5M"

// Date formatting
d3.timeFormat("%b %d, %Y")(new Date())  // "Mar 12, 2026"
d3.timeFormat("%H:%M")(new Date())      // "14:30"
```

---

## STEP 9: Color & Design

### Color Schemes

```javascript
// Categorical (up to 10 distinct colors)
d3.schemeTableau10      // Recommended default
d3.schemeCategory10     // Classic D3
d3.schemePaired         // 12 paired colors

// Sequential (gradients)
d3.interpolateBlues     // Single hue
d3.interpolateViridis   // Perceptually uniform (colorblind safe)
d3.interpolateInferno   // Dark-to-light (colorblind safe)
d3.interpolatePlasma    // Purple-to-yellow

// Diverging (two-directional)
d3.interpolateRdBu      // Red-Blue
d3.interpolateRdYlGn    // Red-Yellow-Green
d3.interpolateBrBG      // Brown-BlueGreen
```

### Legend

```javascript
function addLegend(svg, categories, color, { x = 20, y = 20 } = {}) {
  const legend = svg.append("g")
    .attr("transform", `translate(${x},${y})`);

  categories.forEach((cat, i) => {
    const row = legend.append("g").attr("transform", `translate(0,${i * 22})`);
    row.append("rect").attr("width", 16).attr("height", 16).attr("fill", color(cat));
    row.append("text").attr("x", 22).attr("y", 13).attr("font-size", 13).text(cat);
  });
}
```

---

## STEP 10: Verify

After creating a visualization:

1. **Data binding:** Verify element count matches data length
   ```javascript
   console.log("Data:", data.length, "Elements:", svg.selectAll(".bar").size());
   ```

2. **Scale domains:** Ensure no data falls outside scale domains
   ```javascript
   console.log("X domain:", x.domain(), "Y domain:", y.domain());
   ```

3. **Responsiveness:** Resize browser window — chart should scale proportionally

4. **Accessibility:** Add `role="img"` and `aria-label` to SVG
   ```javascript
   svg.attr("role", "img").attr("aria-label", "Bar chart showing quarterly revenue");
   ```

```
Visualization complete:
  Type: {{chart type}}
  Data points: {{count}}
  Dimensions: {{width}}x{{height}}
  Interactions: {{tooltips, zoom, brush, drag}}
  Framework: {{vanilla | React | Vue}}
```

---

## RULES

- ALWAYS use the margin convention — `{ top, right, bottom, left }` with inner `g` transform
- ALWAYS use `viewBox` for responsive SVGs — NEVER set fixed width/height attributes
- ALWAYS use `.join()` (D3 v6+) — NEVER use the old `.enter().append()` pattern
- ALWAYS provide a key function in `.data(data, d => d.id)` for update animations
- ALWAYS set `extrapolateLeft`/`extrapolateRight` to `"clamp"` when using `interpolate` outside D3
- Use `scaleSqrt` for encoding values as circle radius — `scaleLinear` distorts perceived area
- Use `curveMonotoneX` for time series lines — it prevents overshoot between data points
- Use `d3.schemeTableau10` as the default categorical color scheme — it is colorblind-friendly
- Tooltips MUST be HTML divs positioned with `position: absolute` — NOT SVG elements
- Force simulations MUST clean up: call `simulation.stop()` on component unmount
- In React, use `useRef` for SVG access — NEVER use `d3.select("#id")` (breaks with multiple instances)
- ALWAYS add `role="img"` and `aria-label` to SVG root for screen reader accessibility
