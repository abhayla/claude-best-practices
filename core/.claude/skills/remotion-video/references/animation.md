# STEP 4: Animation

### 4.1 interpolate() — Value Mapping

Map frame ranges to output values for smooth animations:

```tsx
import { interpolate, useCurrentFrame } from "remotion";

const frame = useCurrentFrame();

// Fade in over first 30 frames (0→1)
const opacity = interpolate(frame, [0, 30], [0, 1], {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
});

// Slide in from left (frames 0-20)
const translateX = interpolate(frame, [0, 20], [-200, 0], {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
});

// Scale with easing
import { Easing } from "remotion";

const scale = interpolate(frame, [0, 30], [0.5, 1], {
  easing: Easing.bezier(0.25, 0.1, 0.25, 1),
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
});
```

**Rules:**
- ALWAYS set `extrapolateLeft: "clamp"` and `extrapolateRight: "clamp"` unless you specifically want values outside the range
- Input array MUST be monotonically increasing
- Input and output arrays MUST have the same length

### 4.2 spring() — Physics-Based Animation

Natural-feeling motion that animates from 0 to 1:

```tsx
import { spring, useCurrentFrame, useVideoConfig } from "remotion";

const frame = useCurrentFrame();
const { fps } = useVideoConfig();

// Default spring (bouncy entrance)
const scale = spring({
  frame,
  fps,
  config: {
    damping: 200,    // Higher = less bounce (default: 10)
    stiffness: 100,  // Higher = faster (default: 100)
    mass: 1,         // Higher = slower (default: 1)
  },
});

// Delayed spring (starts at frame 20)
const delayed = spring({
  frame: frame - 20,  // Subtract delay frames
  fps,
  config: { damping: 12 },
});

// Spring from custom value
const rotate = spring({
  frame,
  fps,
  from: 45,   // Start at 45 degrees
  to: 0,      // End at 0 degrees
});
```

**Common spring configs:**

| Effect | damping | stiffness | mass |
|--------|---------|-----------|------|
| Snappy | 200 | 200 | 0.5 |
| Bouncy | 8 | 100 | 1 |
| Gentle | 20 | 50 | 1.5 |
| Heavy | 15 | 100 | 3 |

### 4.3 Sequences — Timing & Layering

```tsx
import { Sequence, AbsoluteFill } from "remotion";

export const MyVideo: React.FC = () => {
  return (
    <AbsoluteFill>
      {/* Plays from frame 0, lasts 60 frames */}
      <Sequence durationInFrames={60}>
        <TitleSlide />
      </Sequence>

      {/* Starts at frame 45 (15-frame overlap), lasts 90 frames */}
      <Sequence from={45} durationInFrames={90}>
        <ContentSlide />
      </Sequence>

      {/* Starts at frame 120, plays until end */}
      <Sequence from={120}>
        <OutroSlide />
      </Sequence>
    </AbsoluteFill>
  );
};
```

**Rules:**
- Inside a `<Sequence>`, `useCurrentFrame()` resets to 0 (local time)
- Sequences can overlap for crossfade effects
- Omit `durationInFrames` to play until composition end

### 4.4 Transitions

```tsx
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { slide } from "@remotion/transitions/slide";
import { fade } from "@remotion/transitions/fade";
import { wipe } from "@remotion/transitions/wipe";

export const MyVideo: React.FC = () => {
  return (
    <TransitionSeries>
      <TransitionSeries.Sequence durationInFrames={90}>
        <SlideA />
      </TransitionSeries.Sequence>

      <TransitionSeries.Transition
        presentation={slide({ direction: "from-left" })}
        timing={linearTiming({ durationInFrames: 30 })}
      />

      <TransitionSeries.Sequence durationInFrames={90}>
        <SlideB />
      </TransitionSeries.Sequence>

      <TransitionSeries.Transition
        presentation={fade()}
        timing={linearTiming({ durationInFrames: 20 })}
      />

      <TransitionSeries.Sequence durationInFrames={90}>
        <SlideC />
      </TransitionSeries.Sequence>
    </TransitionSeries>
  );
};
```

Built-in transitions: `slide`, `fade`, `wipe`, `flip`, `clockWipe`, `none`

### 4.5 Text Animation

```tsx
// Word-by-word reveal
const text = "Hello World";
const words = text.split(" ");

return (
  <div style={{ display: "flex", gap: 8 }}>
    {words.map((word, i) => {
      const delay = i * 10; // 10 frames between each word
      const wordOpacity = interpolate(frame - delay, [0, 15], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
      const wordY = interpolate(frame - delay, [0, 15], [20, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
      return (
        <span
          key={i}
          style={{
            opacity: wordOpacity,
            transform: `translateY(${wordY}px)`,
          }}
        >
          {word}
        </span>
      );
    })}
  </div>
);
```

---

