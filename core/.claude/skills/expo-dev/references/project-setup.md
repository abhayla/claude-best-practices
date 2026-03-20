# STEP 1: Project Setup

### Create New Project

```bash
npx create-expo-app@latest my-app
cd my-app
npx expo start
```

### Project Structure

```
app/
  _layout.tsx           # Root layout (NativeTabs or Stack)
  index.tsx             # Home route (matches "/")
  +not-found.tsx        # 404 handler
  (tabs)/
    _layout.tsx         # Tab navigator
    (home)/
      _layout.tsx       # Stack inside tab
      index.tsx
    (settings)/
      _layout.tsx
      index.tsx
components/             # Reusable components (NEVER in app/)
  theme.tsx
  cards.tsx
hooks/                  # Custom hooks
  use-storage.ts
utils/                  # Utilities
  storage.ts
modules/                # Custom native modules (if needed)
assets/                 # Images, fonts, static files
```

### app.json / app.config.js Configuration

**Static** (`app.json`):

```json
{
  "expo": {
    "name": "My App",
    "slug": "my-app",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "splash": {
      "image": "./assets/splash-icon.png",
      "resizeMode": "contain",
      "backgroundColor": "#ffffff"
    },
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "com.example.myapp"
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#ffffff"
      },
      "package": "com.example.myapp",
      "softwareKeyboardLayoutMode": "resize"
    },
    "plugins": ["expo-router"],
    "scheme": "myapp"
  }
}
```

**Dynamic** (`app.config.js`) for environment variables:

```js
export default ({ config }) => ({
  ...config,
  name: process.env.APP_NAME || "My App",
  extra: {
    apiUrl: process.env.API_URL,
    eas: {
      projectId: "your-project-id",
    },
  },
});
```

Access values via `expo-constants`:

```tsx
import Constants from "expo-constants";
const apiUrl = Constants.expoConfig?.extra?.apiUrl;
```

### EAS Environment Variables

```bash
