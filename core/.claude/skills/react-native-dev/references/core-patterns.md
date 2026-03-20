# STEP 2: Core Patterns

### Functional Component Template

```tsx
import React, { useCallback, useMemo } from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';

interface ItemCardProps {
  title: string;
  subtitle: string;
  onPress?: () => void;
}

export const ItemCard: React.FC<ItemCardProps> = React.memo(({ title, subtitle, onPress }) => {
  const handlePress = useCallback(() => {
    onPress?.();
  }, [onPress]);

  return (
    <Pressable onPress={handlePress} style={styles.container}>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.subtitle}>{subtitle}</Text>
    </Pressable>
  );
});

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: '#fff',
    borderRadius: 8,
    marginVertical: 4,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
});
```

### Hooks Reference

| Hook | Use Case | Performance Note |
|------|----------|------------------|
| `useState` | Local component state | Triggers re-render on change |
| `useEffect` | Side effects (API calls, subscriptions) | Always specify dependency array |
| `useCallback` | Memoize event handlers | Use when passing callbacks as props |
| `useMemo` | Memoize expensive computations | Use for derived data, not simple values |
| `useRef` | Mutable values, DOM refs | Does NOT trigger re-render |
| `useReducer` | Complex local state logic | Alternative to multiple `useState` |

### Optimized List Rendering

```tsx
import { FlatList, ListRenderItem } from 'react-native';

// GOOD: Extract renderItem with proper typing
const renderItem: ListRenderItem<Item> = useCallback(({ item }) => (
  <ItemCard
    key={item.id}
    title={item.title}
    subtitle={item.subtitle}
    onPress={() => onItemSelect(item.id)}
  />
), [onItemSelect]);

// GOOD: Extract keyExtractor
const keyExtractor = useCallback((item: Item) => item.id, []);

<FlatList
  data={items}
  renderItem={renderItem}
  keyExtractor={keyExtractor}
  initialNumToRender={10}
  maxToRenderPerBatch={10}
  windowSize={5}
  removeClippedSubviews={true}
  getItemLayout={(_, index) => ({    // If fixed height, improves scroll perf
    length: ITEM_HEIGHT,
    offset: ITEM_HEIGHT * index,
    index,
  })}
/>

// For large lists (1000+ items), prefer FlashList from Shopify
// yarn add @shopify/flash-list
import { FlashList } from '@shopify/flash-list';

<FlashList
  data={items}
  renderItem={renderItem}
  keyExtractor={keyExtractor}
  estimatedItemSize={80}
/>
```

### StyleSheet Best Practices

```tsx
// GOOD: Define styles outside component (created once)
const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  row: { flexDirection: 'row', alignItems: 'center' },
});

// BAD: Inline styles (new object every render)
// <View style={{ flex: 1, padding: 16 }}>

// Dynamic styles: use a factory or useMemo
const dynamicStyles = useMemo(() => ({
  container: { backgroundColor: isActive ? '#e0f0ff' : '#fff' },
}), [isActive]);
```

---

