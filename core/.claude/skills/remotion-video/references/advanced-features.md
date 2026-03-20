# STEP 6: Advanced Features

### 6.1 3D with @remotion/three

```tsx
import { ThreeCanvas } from "@remotion/three";
import { useCurrentFrame } from "remotion";

export const My3DScene: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <ThreeCanvas width={1920} height={1080}>
      <ambientLight intensity={0.5} />
      <directionalLight position={[5, 5, 5]} />
      <mesh rotation={[0, frame * 0.02, 0]}>
        <boxGeometry args={[2, 2, 2]} />
        <meshStandardMaterial color="#0066ff" />
      </mesh>
    </ThreeCanvas>
  );
};
```

**Rules:**
- Use `<ThreeCanvas>` (NOT regular `<Canvas>` from @react-three/fiber)
- `width` and `height` props are REQUIRED on `<ThreeCanvas>`
- Drive animations with `useCurrentFrame()` — NOT `useFrame()` from R3F
- `requestAnimationFrame`-based animations will NOT work — use frame-based math

### 6.2 Charts & Data Visualization

```tsx
// Animated bar chart
const data = [
  { label: "Q1", value: 120 },
  { label: "Q2", value: 180 },
  { label: "Q3", value: 95 },
  { label: "Q4", value: 210 },
];

const maxValue = Math.max(...data.map((d) => d.value));

return (
  <div style={{ display: "flex", alignItems: "flex-end", gap: 20, height: 400 }}>
    {data.map((d, i) => {
      const barHeight = spring({
        frame: frame - i * 8,
        fps,
        config: { damping: 15 },
      });
      return (
        <div key={i} style={{ textAlign: "center" }}>
          <div
            style={{
              width: 80,
              height: (d.value / maxValue) * 350 * barHeight,
              backgroundColor: "#0066ff",
              borderRadius: 8,
            }}
          />
          <div style={{ marginTop: 8 }}>{d.label}</div>
        </div>
      );
    })}
  </div>
);
```

### 6.3 Parametrized Videos with Zod

```tsx
import { z } from "zod";

// Define schema for video props
export const videoSchema = z.object({
  name: z.string(),
  avatarUrl: z.string().url(),
  message: z.string(),
  brandColor: z.string().regex(/^#[0-9a-f]{6}$/i),
});

type VideoProps = z.infer<typeof videoSchema>;

// Register with schema
<Composition
  id="Personalized"
  component={PersonalizedVideo}
  schema={videoSchema}
  defaultProps={{
    name: "John",
    avatarUrl: "https://example.com/avatar.jpg",
    message: "Welcome!",
    brandColor: "#0066ff",
  }}
  durationInFrames={150}
  fps={30}
  width={1080}
  height={1080}
/>
```

---

