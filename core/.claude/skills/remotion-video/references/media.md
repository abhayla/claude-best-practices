# STEP 5: Media

### 5.1 Audio

```tsx
import { Audio, interpolate, useCurrentFrame } from "remotion";
import { staticFile } from "remotion";

// Basic audio
<Audio src={staticFile("music.mp3")} />

// With volume control
<Audio
  src={staticFile("music.mp3")}
  volume={(f) =>
    interpolate(f, [0, 30, 270, 300], [0, 0.8, 0.8, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    })
  }
  startFrom={60}          // Skip first 2 seconds of audio
  endAt={360}             // Stop at 12 seconds
  playbackRate={1.5}      // Speed up
/>
```

### 5.2 Audio Visualization

```tsx
import { getAudioData, useAudioData, visualizeAudio } from "@remotion/media-utils";

const audioData = useAudioData(staticFile("music.mp3"));
if (!audioData) return null;

const visualization = visualizeAudio({
  fps,
  frame,
  audioData,
  numberOfSamples: 256,  // Frequency bands
});

// Render spectrum bars
return (
  <div style={{ display: "flex", alignItems: "flex-end", height: 200 }}>
    {visualization.map((v, i) => (
      <div
        key={i}
        style={{
          width: 4,
          height: v * 200,
          backgroundColor: "#0066ff",
          marginRight: 1,
        }}
      />
    ))}
  </div>
);
```

### 5.3 Video & Images

```tsx
import { Video, Img, staticFile, OffthreadVideo } from "remotion";

// Video (use OffthreadVideo for better performance)
<OffthreadVideo src={staticFile("background.mp4")} />

// With time remapping
<OffthreadVideo
  src={staticFile("clip.mp4")}
  startFrom={90}
  endAt={180}
  volume={0.5}
  playbackRate={0.5}   // Slow motion
/>

// Images
<Img src={staticFile("photo.png")} style={{ width: "100%" }} />

// Remote images (must be CORS-enabled)
<Img src="https://example.com/image.jpg" />
```

**Rules:**
- Use `staticFile()` for files in `/public` directory
- Use `<OffthreadVideo>` over `<Video>` for better rendering performance
- Remote media must be CORS-accessible

### 5.4 Captions & Subtitles

```tsx
import { parseSrt, createTikTokStyleCaptions } from "@remotion/captions";

// Parse SRT file
const srt = `
1
00:00:00,000 --> 00:00:02,500
Hello, welcome to the video.

2
00:00:02,500 --> 00:00:05,000
Let me show you something cool.
`;

const parsed = parseSrt({ input: srt });

// TikTok-style word-by-word captions
const { pages } = createTikTokStyleCaptions({
  captions: parsed,
  combineTokensWithinMilliseconds: 800,
});

// Render current caption
const currentPage = pages.find(
  (p) =>
    p.startMs <= (frame / fps) * 1000 &&
    p.endMs >= (frame / fps) * 1000
);

return (
  <div style={{
    position: "absolute",
    bottom: 100,
    width: "100%",
    textAlign: "center",
    fontSize: 48,
    fontWeight: "bold",
    color: "white",
    textShadow: "2px 2px 4px rgba(0,0,0,0.8)",
  }}>
    {currentPage?.tokens.map((token, i) => (
      <span
        key={i}
        style={{
          color: token.startMs <= (frame / fps) * 1000 ? "#FFD700" : "white",
        }}
      >
        {token.text}
      </span>
    ))}
  </div>
);
```

---

