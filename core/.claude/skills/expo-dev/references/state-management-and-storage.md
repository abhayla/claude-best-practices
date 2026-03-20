# STEP 4: State Management and Storage

### Key-Value Storage (localStorage Polyfill)

```tsx
import "expo-sqlite/localStorage/install";

localStorage.setItem("theme", "dark");
const theme = localStorage.getItem("theme");
```

### SecureStore (Tokens, Passwords)

```tsx
import * as SecureStore from "expo-secure-store";

await SecureStore.setItemAsync("token", "abc123");
const token = await SecureStore.getItemAsync("token");
```

### SQLite (Complex Data)

```tsx
import * as SQLite from "expo-sqlite";

const db = await SQLite.openDatabaseAsync("app.db");
await db.execAsync(`
  CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL
  )
`);
await db.runAsync("INSERT INTO items (title) VALUES (?)", ["New Item"]);
const items = await db.getAllAsync("SELECT * FROM items");
```

### Storage Decision Table

| Use Case | Solution |
|---|---|
| Settings, preferences, small data | `localStorage` polyfill (`expo-sqlite/localStorage/install`) |
| Large datasets, relational queries | `expo-sqlite` directly |
| Sensitive data (tokens, passwords) | `expo-secure-store` |

### React Hook for Storage

```tsx
import { useSyncExternalStore } from "react";
import { storage } from "@/utils/storage";

export function useStorage<T>(key: string, defaultValue: T): [T, (v: T) => void] {
  const value = useSyncExternalStore(
    (cb) => storage.subscribe(key, cb),
    () => storage.get(key, defaultValue)
  );
  return [value, (newValue: T) => storage.set(key, newValue)];
}
```

---

