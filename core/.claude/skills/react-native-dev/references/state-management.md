# STEP 4: State Management

### Decision Guide

| Approach | When to Use |
|----------|-------------|
| `useState` / `useReducer` | Local component state only |
| Context API | Lightweight shared state (theme, locale, auth status) |
| Zustand | Medium complexity — most RN apps (recommended default) |
| Redux Toolkit | Large teams, complex state with middleware needs |

### Zustand (Recommended)

```tsx
// store/useAppStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface AppState {
  user: User | null;
  theme: 'light' | 'dark';
  setUser: (user: User | null) => void;
  toggleTheme: () => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      user: null,
      theme: 'light',
      setUser: (user) => set({ user }),
      toggleTheme: () => set((state) => ({
        theme: state.theme === 'light' ? 'dark' : 'light',
      })),
    }),
    {
      name: 'app-storage',
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);

// Usage in component — only subscribes to what it reads
function UserBadge() {
  const user = useAppStore((state) => state.user); // Selective subscription
  if (!user) return null;
  return <Text>{user.name}</Text>;
}
```

### Redux Toolkit Pattern

```tsx
// store/slices/authSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

export const login = createAsyncThunk(
  'auth/login',
  async (credentials: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const response = await api.login(credentials);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState: { user: null, status: 'idle', error: null } as AuthState,
  reducers: {
    logout: (state) => { state.user = null; state.status = 'idle'; },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => { state.status = 'loading'; })
      .addCase(login.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.user = action.payload;
      })
      .addCase(login.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload as string;
      });
  },
});

export const { logout } = authSlice.actions;
export default authSlice.reducer;
```

### Context API (Lightweight)

```tsx
// Use for values that change infrequently (theme, locale, auth status)
const ThemeContext = React.createContext<{ theme: Theme; toggle: () => void } | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>(lightTheme);
  const toggle = useCallback(() => {
    setTheme((prev) => (prev === lightTheme ? darkTheme : lightTheme));
  }, []);

  const value = useMemo(() => ({ theme, toggle }), [theme, toggle]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = React.useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}
```

---

