---
name: remotion-video
description: >
  Programmatic video creation with React/Remotion. Compositions, sequences,
  frame-based animations, audio sync, captions, 3D (Three.js), charts,
  transitions, server-side rendering. Data-driven batch video generation.
triggers:
  - remotion
  - video
  - programmatic video
  - create video
  - render video
  - animation
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<action: create|animate|render|caption|3d|chart|batch> <description>"
version: "1.0.0"
type: workflow
---

# Remotion Video — Programmatic Video with React

Create, animate, and render videos using React components with Remotion.

**Input:** $ARGUMENTS

---

## STEP 1: Detect Action

| Action | Trigger | Description |
|--------|---------|-------------|
| `create` | "create video", "new composition" | Scaffold a new video composition |
| `animate` | "animate", "transition", "motion" | Add animations to existing composition |
| `render` | "render", "export", "MP4" | Render composition to video file |
| `caption` | "captions", "subtitles", "SRT" | Add captions/subtitles overlay |
| `3d` | "3D", "three.js", "3d scene" | Add 3D content via @remotion/three |
| `chart` | "chart", "visualization", "data viz" | Create animated data visualizations |
| `batch` | "batch", "personalize", "variations" | Generate multiple video variants from data |

---

## STEP 2: Project Setup

### 2.1 Check Existing Project

```bash
# Check if Remotion is already set up
test -f remotion.config.ts && echo "Remotion project found" || echo "No Remotion project"
ls src/Root.tsx 2>/dev/null || ls app/remotion/Root.tsx 2>/dev/null
```

### 2.2 New Project (if needed)

```bash
npx create-video@latest my-video --template blank --tailwind --skills
cd my-video
npm install
```

### 2.3 Key Files

```
my-video/
  src/
    Root.tsx              # Register all compositions here
    MyComposition.tsx     # Video components
  remotion.config.ts      # Remotion configuration
  package.json
```

---

## STEP 3: Core Patterns

### 3.1 Composition Structure

Every video is a React component registered as a `<Composition>`:

```tsx
// src/Root.tsx
import { Composition } from "remotion";
import { MyVideo } from "./MyVideo";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="MyVideo"
      component={MyVideo}
      durationInFrames={300}   // 10 seconds at 30fps
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        title: "Hello World",
        color: "#0066ff",
      }}
    />
  );
};
```

```tsx
// src/MyVideo.tsx
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";

export const MyVideo: React.FC<{ title: string; color: string }> = ({
  title,
  color,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width, height } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: color }}>
      <h1>{title}</h1>
    </AbsoluteFill>
  );
};
```

**Rules:**
- `useCurrentFrame()` returns the current frame (0-indexed)
- `useVideoConfig()` returns `{ fps, durationInFrames, width, height, id, defaultProps }`
- `<AbsoluteFill>` is the standard full-frame container
- Props MUST be serializable (no functions, no DOM elements)

### 3.2 Dynamic Metadata

Use `calculateMetadata()` for variable duration/resolution based on input data:

```tsx
export const calculateMetadata: CalculateMetadataFunction<MyProps> = async ({
  props,
}) => {
  const data = await fetch(props.dataUrl).then((r) => r.json());
  return {
    durationInFrames: data.items.length * 90, // 3 sec per item
    props: { ...props, data },
  };
};

// In Root.tsx
<Composition
  id="DataVideo"
  component={DataVideo}
  calculateMetadata={calculateMetadata}
  // durationInFrames, width, height can be overridden by calculateMetadata
  durationInFrames={300}
  fps={30}
  width={1920}
  height={1080}
  defaultProps={{ dataUrl: "https://api.example.com/items" }}
/>
```

---

## STEP 4: Animation


**Read:** `references/animation.md` for detailed step 4: animation reference material.

## STEP 5: Media


**Read:** `references/media.md` for detailed step 5: media reference material.

## STEP 6: Advanced Features


**Read:** `references/advanced-features.md` for detailed step 6: advanced features reference material.

## STEP 7: Rendering

### 7.1 CLI Render

```bash
# Render to MP4
npx remotion render MyVideo out/video.mp4

# With custom props
npx remotion render MyVideo out/video.mp4 --props='{"title":"Custom Title"}'

# Render specific frame range
npx remotion render MyVideo out/video.mp4 --frames=0-90

# Render as GIF
npx remotion render MyVideo out/animation.gif

# Render still image
npx remotion still MyVideo out/thumbnail.png --frame=45
```

### 7.2 Programmatic Render

```tsx
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";

const bundled = await bundle({
  entryPoint: "./src/index.ts",
});

const composition = await selectComposition({
  serveUrl: bundled,
  id: "MyVideo",
  inputProps: { title: "Hello" },
});

await renderMedia({
  composition,
  serveUrl: bundled,
  codec: "h264",
  outputLocation: "out/video.mp4",
  onProgress: ({ progress }) => {
    console.log(`Rendering: ${Math.round(progress * 100)}%`);
  },
});
```

### 7.3 Batch Rendering from Dataset

```tsx
import fs from "fs";

const users = JSON.parse(fs.readFileSync("users.json", "utf8"));

for (const user of users) {
  const composition = await selectComposition({
    serveUrl: bundled,
    id: "Personalized",
    inputProps: {
      name: user.name,
      avatarUrl: user.avatar,
      message: `Welcome, ${user.name}!`,
      brandColor: user.brandColor,
    },
  });

  await renderMedia({
    composition,
    serveUrl: bundled,
    codec: "h264",
    outputLocation: `out/${user.id}.mp4`,
  });

  console.log(`Rendered video for ${user.name}`);
}
```

---

## STEP 8: Fonts & Styling

### 8.1 Google Fonts

```tsx
import { loadFont } from "@remotion/google-fonts/Inter";

const { fontFamily } = loadFont();

// Use in component
<div style={{ fontFamily }}>Text with Inter font</div>
```

### 8.2 Local Fonts

```tsx
import { staticFile } from "remotion";

const fontFace = new FontFace("CustomFont", `url(${staticFile("fonts/Custom.woff2")})`);
document.fonts.add(fontFace);
await fontFace.load();
```

### 8.3 TailwindCSS

Remotion supports TailwindCSS out of the box when initialized with `--tailwind`:

```tsx
export const MyVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill className="bg-slate-900 flex items-center justify-center">
      <h1
        className="text-6xl font-bold text-white"
        style={{ opacity }}
      >
        Hello World
      </h1>
    </AbsoluteFill>
  );
};
```

**Rule:** Use inline `style` for animated properties (driven by frame). Use Tailwind classes for static styling.

---

## STEP 9: Preview & Debug

```bash
# Start preview server
npm run dev
# or
npx remotion preview

# Preview opens at http://localhost:3000
# Use timeline scrubber to inspect frame-by-frame
```

### Debug Tips
- Use React DevTools in the preview browser
- `console.log(frame)` to trace animation values
- Use `--log=verbose` for detailed render output
- Check `useVideoConfig()` values match your expectations

---

## STEP 10: Verify

After creating or modifying a composition:

1. **Type check:** `npx tsc --noEmit`
2. **Preview renders:** `npx remotion preview` — scrub through timeline
3. **Render test:** `npx remotion render CompositionId out/test.mp4 --frames=0-30` (first 1 second)
4. **Check file size:** Ensure output is reasonable for duration

```
Video operation complete:
  Action: {{action}}
  Composition: {{id}}
  Duration: {{seconds}}s ({{frames}} frames @ {{fps}}fps)
  Resolution: {{width}}x{{height}}
  Output: {{output path}} ({{file size}})
```

---

## RULES

- ALWAYS use `extrapolateLeft: "clamp"` and `extrapolateRight: "clamp"` with `interpolate()` unless unbounded values are intentional
- ALWAYS use `<OffthreadVideo>` instead of `<Video>` for imported video clips
- ALWAYS use `staticFile()` for assets in the `/public` directory — never import directly
- ALWAYS use `useCurrentFrame()` for animations — NEVER use `requestAnimationFrame` or `setInterval`
- ALWAYS use `<ThreeCanvas>` from `@remotion/three` — NOT `<Canvas>` from `@react-three/fiber`
- Input arrays in `interpolate()` MUST be monotonically increasing
- Props passed to compositions MUST be JSON-serializable (no functions, no React elements)
- Use `spring()` for natural motion, `interpolate()` for precise control
- Use `<Sequence>` for timing — `useCurrentFrame()` inside a Sequence resets to 0
- Render a short frame range first (`--frames=0-30`) to verify before full render
- Use Zod schemas for parametrized/batch videos to validate input props
