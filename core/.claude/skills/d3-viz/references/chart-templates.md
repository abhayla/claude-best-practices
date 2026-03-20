# STEP 3: Chart Templates

### 3.1 Bar Chart

```javascript
function barChart(data, { container, width = 800, height = 500 } = {}) {
  const margin = { top: 20, right: 20, bottom: 40, left: 60 };
  const w = width - margin.left - margin.right;
  const h = height - margin.top - margin.bottom;

  const svg = d3.select(container).append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  const x = d3.scaleBand()
    .domain(data.map(d => d.label))
    .range([0, w])
    .padding(0.2);

  const y = d3.scaleLinear()
    .domain([0, d3.max(data, d => d.value) * 1.1])
    .range([h, 0]);

  svg.append("g").attr("transform", `translate(0,${h})`).call(d3.axisBottom(x));
  svg.append("g").call(d3.axisLeft(y));

  svg.selectAll(".bar")
    .data(data)
    .join("rect")
    .attr("class", "bar")
    .attr("x", d => x(d.label))
    .attr("width", x.bandwidth())
    .attr("y", d => y(d.value))
    .attr("height", d => h - y(d.value))
    .attr("fill", "steelblue");
}
```

### 3.2 Line Chart

```javascript
function lineChart(data, { container, width = 800, height = 500 } = {}) {
  const margin = { top: 20, right: 20, bottom: 40, left: 60 };
  const w = width - margin.left - margin.right;
  const h = height - margin.top - margin.bottom;

  const svg = d3.select(container).append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  const x = d3.scaleTime()
    .domain(d3.extent(data, d => d.date))
    .range([0, w]);

  const y = d3.scaleLinear()
    .domain([0, d3.max(data, d => d.value) * 1.1])
    .range([h, 0]);

  svg.append("g").attr("transform", `translate(0,${h})`).call(d3.axisBottom(x));
  svg.append("g").call(d3.axisLeft(y));

  const line = d3.line()
    .x(d => x(d.date))
    .y(d => y(d.value))
    .curve(d3.curveMonotoneX);  // Smooth curve that passes through points

  // Line path
  svg.append("path")
    .datum(data)
    .attr("fill", "none")
    .attr("stroke", "steelblue")
    .attr("stroke-width", 2)
    .attr("d", line);

  // Data points
  svg.selectAll(".dot")
    .data(data)
    .join("circle")
    .attr("class", "dot")
    .attr("cx", d => x(d.date))
    .attr("cy", d => y(d.value))
    .attr("r", 4)
    .attr("fill", "steelblue");
}
```

**Curve options:**

| Curve | Use Case |
|-------|----------|
| `curveLinear` | Default, straight segments |
| `curveMonotoneX` | Smooth, monotone (no overshoot) — best for time series |
| `curveBasis` | Smooth, may not pass through points |
| `curveStep` | Stair-step (before/after transitions) |
| `curveCardinal` | Smooth with tension parameter |
| `curveCatmullRom` | Smooth, passes through all points |

### 3.3 Scatter Plot

```javascript
function scatterPlot(data, { container, width = 800, height = 500 } = {}) {
  const margin = { top: 20, right: 20, bottom: 40, left: 60 };
  const w = width - margin.left - margin.right;
  const h = height - margin.top - margin.bottom;

  const svg = d3.select(container).append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  const x = d3.scaleLinear().domain(d3.extent(data, d => d.x)).nice().range([0, w]);
  const y = d3.scaleLinear().domain(d3.extent(data, d => d.y)).nice().range([h, 0]);
  const r = d3.scaleSqrt().domain([0, d3.max(data, d => d.size)]).range([3, 20]);
  const color = d3.scaleOrdinal(d3.schemeTableau10);

  svg.append("g").attr("transform", `translate(0,${h})`).call(d3.axisBottom(x));
  svg.append("g").call(d3.axisLeft(y));

  svg.selectAll(".dot")
    .data(data)
    .join("circle")
    .attr("class", "dot")
    .attr("cx", d => x(d.x))
    .attr("cy", d => y(d.y))
    .attr("r", d => r(d.size))
    .attr("fill", d => color(d.group))
    .attr("opacity", 0.7)
    .attr("stroke", "white")
    .attr("stroke-width", 1);
}
```

### 3.4 Pie / Donut Chart

```javascript
function pieChart(data, { container, width = 500, height = 500, innerRadius = 0 } = {}) {
  const radius = Math.min(width, height) / 2 - 20;

  const svg = d3.select(container).append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .append("g")
    .attr("transform", `translate(${width / 2},${height / 2})`);

  const pie = d3.pie()
    .value(d => d.value)
    .sort(null);  // Preserve data order

  const arc = d3.arc()
    .innerRadius(innerRadius)  // 0 = pie, >0 = donut
    .outerRadius(radius);

  const arcLabel = d3.arc()
    .innerRadius(radius * 0.6)
    .outerRadius(radius * 0.6);

  const color = d3.scaleOrdinal(d3.schemeTableau10);

  const arcs = svg.selectAll(".arc")
    .data(pie(data))
    .join("g")
    .attr("class", "arc");

  arcs.append("path")
    .attr("d", arc)
    .attr("fill", (d, i) => color(i))
    .attr("stroke", "white")
    .attr("stroke-width", 2);

  arcs.append("text")
    .attr("transform", d => `translate(${arcLabel.centroid(d)})`)
    .attr("text-anchor", "middle")
    .attr("font-size", 12)
    .text(d => d.data.label);
}

// Donut: pieChart(data, { innerRadius: 80 })
```

### 3.5 Force-Directed Graph

```javascript
function forceGraph(nodes, links, { container, width = 800, height = 600 } = {}) {
  const svg = d3.select(container).append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`);

  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(80))
    .force("charge", d3.forceManyBody().strength(-200))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(20));

  const link = svg.selectAll(".link")
    .data(links)
    .join("line")
    .attr("class", "link")
    .attr("stroke", "#999")
    .attr("stroke-opacity", 0.6)
    .attr("stroke-width", d => Math.sqrt(d.value));

  const node = svg.selectAll(".node")
    .data(nodes)
    .join("circle")
    .attr("class", "node")
    .attr("r", 8)
    .attr("fill", d => d3.scaleOrdinal(d3.schemeTableau10)(d.group))
    .call(drag(simulation));  // Enable dragging

  // Labels
  const label = svg.selectAll(".label")
    .data(nodes)
    .join("text")
    .attr("class", "label")
    .attr("font-size", 10)
    .attr("dx", 12)
    .text(d => d.name);

  simulation.on("tick", () => {
    link
      .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
    node
      .attr("cx", d => d.x).attr("cy", d => d.y);
    label
      .attr("x", d => d.x).attr("y", d => d.y);
  });

  // Drag behavior
  function drag(simulation) {
    return d3.drag()
      .on("start", (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x; d.fy = d.y;
      })
      .on("drag", (event, d) => {
        d.fx = event.x; d.fy = event.y;
      })
      .on("end", (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null; d.fy = null;
      });
  }
}
```

**Force options:**

| Force | Purpose | Key Parameters |
|-------|---------|---------------|
| `forceLink` | Connect nodes via edges | `distance`, `strength` |
| `forceManyBody` | Repulsion/attraction | `strength` (negative = repel) |
| `forceCenter` | Pull toward center | `x`, `y` |
| `forceCollide` | Prevent overlap | `radius` |
| `forceX` / `forceY` | Pull toward axis | `x`/`y`, `strength` |

### 3.6 Treemap

```javascript
function treemap(data, { container, width = 800, height = 500 } = {}) {
  const svg = d3.select(container).append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`);

  const root = d3.hierarchy(data)
    .sum(d => d.value)
    .sort((a, b) => b.value - a.value);

  d3.treemap()
    .size([width, height])
    .padding(2)
    .round(true)(root);

  const color = d3.scaleOrdinal(d3.schemeTableau10);

  const cell = svg.selectAll(".cell")
    .data(root.leaves())
    .join("g")
    .attr("class", "cell")
    .attr("transform", d => `translate(${d.x0},${d.y0})`);

  cell.append("rect")
    .attr("width", d => d.x1 - d.x0)
    .attr("height", d => d.y1 - d.y0)
    .attr("fill", d => color(d.parent.data.name))
    .attr("stroke", "white");

  cell.append("text")
    .attr("x", 4).attr("y", 14)
    .attr("font-size", 11)
    .text(d => d.data.name);
}

// Data format:
// { name: "root", children: [
//   { name: "A", children: [{ name: "A1", value: 100 }, { name: "A2", value: 80 }] },
//   { name: "B", value: 200 }
// ]}
```

### 3.7 Choropleth Map

```javascript
async function choropleth(data, { container, width = 960, height = 600 } = {}) {
  const svg = d3.select(container).append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`);

  // Load GeoJSON (example: US states)
  const geo = await d3.json("https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json");
  const states = topojson.feature(geo, geo.objects.states);

  const projection = d3.geoAlbersUsa().fitSize([width, height], states);
  const path = d3.geoPath(projection);

  const dataMap = new Map(data.map(d => [d.id, d.value]));
  const color = d3.scaleSequential(d3.interpolateBlues)
    .domain([0, d3.max(data, d => d.value)]);

  svg.selectAll(".state")
    .data(states.features)
    .join("path")
    .attr("class", "state")
    .attr("d", path)
    .attr("fill", d => {
      const val = dataMap.get(d.id);
      return val != null ? color(val) : "#ccc";
    })
    .attr("stroke", "white")
    .attr("stroke-width", 0.5);
}
```

**Common projections:**

| Projection | Use Case |
|------------|----------|
| `geoAlbersUsa` | US (includes Alaska, Hawaii) |
| `geoMercator` | Web maps, navigation |
| `geoNaturalEarth1` | World maps (minimal distortion) |
| `geoOrthographic` | Globe view |
| `geoEqualEarth` | Equal-area world maps |

---

