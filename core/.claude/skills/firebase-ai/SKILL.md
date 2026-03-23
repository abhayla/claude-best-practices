---
name: firebase-ai
description: >
  Integrate Firebase AI Logic (Gemini API) including setup, text generation, multimodal
  input, chat sessions, streaming, image generation, structured JSON output,
  on-device hybrid AI, and App Check security. Use when adding AI features to
  Firebase web or mobile apps.
allowed-tools: "Read Grep Glob"
argument-hint: "<what to implement — e.g. 'add text generation' or 'set up multimodal chat with images'>"
version: "1.0.1"
type: reference
---

# Firebase AI Logic (Gemini API)

Reference for integrating Gemini AI into Firebase applications via Firebase AI Logic.

**Request:** $ARGUMENTS

---

## Overview

Firebase AI Logic provides client-side SDKs to call Gemini models directly from web and mobile apps without a dedicated backend. Formerly known as "Vertex AI for Firebase."

### API Providers

| Provider | Use Case | Pricing |
|----------|----------|---------|
| Gemini Developer API | Default for prototyping and production | Free tier + pay-as-you-go |
| Vertex AI Gemini API | Enterprise-grade, scale requirements | Requires Blaze plan |

Use the Gemini Developer API as the default. Only use Vertex AI if the application requires enterprise features.

---

## Setup & Initialization

### Prerequisites

- Node.js 16+ and npm
- Firebase project with a web app configured
- Platform: Web, Android, iOS, or Flutter

### Installation

```bash
npm install firebase@latest
```

### Initialization

```javascript
import { initializeApp } from "firebase/app";
import { getAI, getGenerativeModel, GoogleAIBackend } from "firebase/ai";

// If running in Firebase App Hosting, skip config:
// const app = initializeApp();

const firebaseConfig = {
  // ... your firebase config
};

const app = initializeApp(firebaseConfig);

// Initialize AI Logic (defaults to Gemini Developer API)
const ai = getAI(app, { backend: new GoogleAIBackend() });

const generationConfig = {
  maxOutputTokens: 2048,
  temperature: 0.7,
  topP: 0.95,
  topK: 40,
};

const model = getGenerativeModel(ai, {
  model: "gemini-2.5-flash-lite",
  generationConfig
});
```

### For Vertex AI Backend

```javascript
import { getAI, getGenerativeModel, VertexAIBackend } from "firebase/ai";

const ai = getAI(app, { backend: new VertexAIBackend() });
const model = getGenerativeModel(ai, { model: "gemini-2.5-flash" });
```

---

## Text Generation

### Basic Text

```javascript
async function generateText(prompt) {
  const result = await model.generateContent(prompt);
  const response = result.response;
  return response.text();
}
```

### With System Instructions

```javascript
const model = getGenerativeModel(ai, {
  model: "gemini-2.5-flash-lite",
  systemInstruction: "You are a helpful cooking assistant. Always suggest healthy alternatives.",
});

const result = await model.generateContent("Suggest a dinner recipe");
console.log(result.response.text());
```

---

## Multimodal Input

Firebase AI Logic accepts base64-encoded data or file references for images, audio, video, and PDFs.

### Image Input

```javascript
async function analyzeImage(base64ImageData) {
  const result = await model.generateContent([
    "Describe what you see in this image",
    {
      inlineData: {
        mimeType: "image/jpeg",
        data: base64ImageData
      }
    }
  ]);
  return result.response.text();
}
```

### Multiple Images

```javascript
const result = await model.generateContent([
  "Compare these two images",
  { inlineData: { mimeType: "image/png", data: image1Base64 } },
  { inlineData: { mimeType: "image/png", data: image2Base64 } }
]);
```

### Audio Input

```javascript
const result = await model.generateContent([
  "Transcribe this audio",
  { inlineData: { mimeType: "audio/mp3", data: audioBase64 } }
]);
```

### Video Input

```javascript
const result = await model.generateContent([
  "Summarize this video",
  { inlineData: { mimeType: "video/mp4", data: videoBase64 } }
]);
```

### PDF Input

```javascript
const result = await model.generateContent([
  "Summarize this document",
  { inlineData: { mimeType: "application/pdf", data: pdfBase64 } }
]);
```

---

## Chat Sessions

Maintain conversational context across multiple turns.

```javascript
const chat = model.startChat({
  history: [
    { role: "user", parts: [{ text: "Hello, I'm looking for a recipe" }] },
    { role: "model", parts: [{ text: "I'd love to help! What ingredients do you have?" }] }
  ]
});

// Send messages in the ongoing conversation
const result1 = await chat.sendMessage("I have chicken and rice");
console.log(result1.response.text());

const result2 = await chat.sendMessage("Can you make it spicy?");
console.log(result2.response.text());
```

### Chat with Multimodal

```javascript
const chat = model.startChat();

const result = await chat.sendMessage([
  "What dish can I make with these ingredients?",
  { inlineData: { mimeType: "image/jpeg", data: fridgePhotoBase64 } }
]);
```

---

## Streaming

Receive partial results as they are generated for better UX.

### Streaming Text

```javascript
async function streamText(prompt) {
  const result = await model.generateContentStream(prompt);

  for await (const chunk of result.stream) {
    const text = chunk.text();
    process.stdout.write(text); // Or update UI incrementally
  }

  // Get the complete aggregated response
  const finalResponse = await result.response;
  console.log("\nFull response:", finalResponse.text());
}
```

### Streaming Chat

```javascript
const chat = model.startChat();

const result = await chat.sendMessageStream("Tell me a story about a robot");

for await (const chunk of result.stream) {
  const text = chunk.text();
  // Update UI with each chunk
  updateUI(text);
}
```

---

## Image Generation

Using the Imagen model (Nano Banana) for image creation.

```javascript
import { getImagenModel } from "firebase/ai";

const imagenModel = getImagenModel(ai, {
  model: "imagen-3.0-generate-002"
});

const result = await imagenModel.generateImages("A serene mountain landscape at sunset");

// Access generated images
for (const image of result.images) {
  const base64Data = image.bytesBase64Encoded;
  const mimeType = image.mimeType;
  // Display or save the image
}
```

### Image Generation Options

```javascript
const result = await imagenModel.generateImages("A cute robot", {
  numberOfImages: 4,
  aspectRatio: "16:9",
  // Other options as supported by the model
});
```

---

## Structured JSON Output

Get responses in a specific JSON format using response schemas.

```javascript
import { SchemaType } from "firebase/ai";

const model = getGenerativeModel(ai, {
  model: "gemini-2.5-flash-lite",
  generationConfig: {
    responseMimeType: "application/json",
    responseSchema: {
      type: SchemaType.OBJECT,
      properties: {
        recipes: {
          type: SchemaType.ARRAY,
          items: {
            type: SchemaType.OBJECT,
            properties: {
              name: { type: SchemaType.STRING },
              ingredients: {
                type: SchemaType.ARRAY,
                items: { type: SchemaType.STRING }
              },
              cookTimeMinutes: { type: SchemaType.INTEGER },
              difficulty: { type: SchemaType.STRING }
            },
            required: ["name", "ingredients"]
          }
        }
      }
    }
  }
});

const result = await model.generateContent("Suggest 3 pasta recipes");
const recipes = JSON.parse(result.response.text());
```

---

## On-Device Hybrid AI

Run smaller models on-device and fall back to cloud for complex tasks.

```javascript
import { getGenerativeModel, HybridParams } from "firebase/ai";

// Create a model that tries on-device first, falls back to cloud
const hybridModel = getGenerativeModel(ai, {
  model: "gemini-2.5-flash-lite",
  hybridParams: new HybridParams({
    onDeviceModel: "gemini-nano",
    // Falls back to cloud model if on-device is unavailable
  })
});

const result = await hybridModel.generateContent("Quick translation: Hello in Spanish");
console.log(result.response.text());
```

---

## App Check Security

Protect your AI endpoints from abuse using Firebase App Check.

### Setup

```javascript
import { initializeAppCheck, ReCaptchaV3Provider } from "firebase/app-check";

const appCheck = initializeAppCheck(app, {
  provider: new ReCaptchaV3Provider('YOUR_RECAPTCHA_SITE_KEY'),
  isTokenAutoRefreshEnabled: true
});
```

App Check automatically attaches tokens to Firebase AI Logic requests. No additional code is needed after initialization.

### Enforcing App Check

Enable enforcement in the Firebase Console under App Check settings. Once enforced, requests without valid App Check tokens are rejected.

---

## Remote Config for Model Names

Use Firebase Remote Config to change models without redeploying.

```javascript
import { getRemoteConfig, getValue, fetchAndActivate } from "firebase/remote-config";

const remoteConfig = getRemoteConfig(app);
remoteConfig.settings.minimumFetchIntervalMillis = 3600000; // 1 hour

await fetchAndActivate(remoteConfig);
const modelName = getValue(remoteConfig, "gemini_model_name").asString()
  || "gemini-2.5-flash-lite";

const model = getGenerativeModel(ai, { model: modelName });
```

---

## Generation Parameters

| Parameter | Description | Typical Range |
|-----------|-------------|---------------|
| `temperature` | Creativity vs. focus | 0.0-2.0 (default: 0.7) |
| `topP` | Nucleus sampling threshold | 0.0-1.0 (default: 0.95) |
| `topK` | Number of top tokens to consider | 1-100 (default: 40) |
| `maxOutputTokens` | Maximum response length | Model-dependent (default: 2048) |
| `stopSequences` | Strings that halt generation | Array of strings |
| `candidateCount` | Number of response candidates | 1 (usually) |

---

## Security Best Practices

1. **Always enable App Check** -- Prevents unauthorized API usage and abuse
2. **Use Remote Config for model names** -- Change models without code deploys
3. **Set appropriate rate limits** -- Prevent excessive API calls from clients
4. **Validate inputs client-side** -- Sanitize user prompts before sending to the model
5. **Handle errors gracefully** -- Network failures, quota limits, and safety filters
6. **Use Gemini Developer API by default** -- Only upgrade to Vertex AI when enterprise features are needed

## Common Patterns

| Pattern | Implementation |
|---------|---------------|
| Loading indicator | Use streaming and show partial results |
| Retry on failure | Exponential backoff with max 3 retries |
| Context window management | Track token usage, truncate history when needed |
| Safety filtering | Check `response.promptFeedback` for blocked content |
| Cost control | Set `maxOutputTokens`, use lighter models for simple tasks |

## Anti-Patterns

| Anti-Pattern | Use Instead |
|-------------|-------------|
| Hardcoded model names | Remote Config for model selection |
| No App Check | Always initialize App Check |
| Unbounded chat history | Limit history length, summarize older messages |
| Synchronous-only generation | Use streaming for better UX |
| No error handling for safety filters | Check `promptFeedback.blockReason` |
| Using Vertex AI for simple prototypes | Start with Gemini Developer API (free tier) |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Model not found | Verify model name; check `gemini-2.5-flash-lite` is available |
| App Check token error | Verify reCAPTCHA site key and domain registration |
| Empty response | Check `response.promptFeedback` for safety blocks |
| Quota exceeded | Implement rate limiting; upgrade billing plan |
| Streaming not working | Ensure `generateContentStream` is used, not `generateContent` |
| Large response truncated | Increase `maxOutputTokens` in generation config |
| On-device model unavailable | Hybrid mode auto-falls back to cloud; check device compatibility |

## References

- Firebase AI Logic: https://firebase.google.com/docs/ai-logic
- Gemini API: https://ai.google.dev/gemini-api/docs
- App Check: https://firebase.google.com/docs/app-check
- Remote Config: https://firebase.google.com/docs/remote-config
- Imagen: https://cloud.google.com/vertex-ai/generative-ai/docs/image/overview
