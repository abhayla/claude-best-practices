# STEP 7: Testing

### Jest + React Native Testing Library

```tsx
// components/ItemCard.test.tsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react-native';
import { ItemCard } from './ItemCard';

describe('ItemCard', () => {
  it('renders title and subtitle', () => {
    render(<ItemCard title="Test Title" subtitle="Test Sub" />);

    expect(screen.getByText('Test Title')).toBeTruthy();
    expect(screen.getByText('Test Sub')).toBeTruthy();
  });

  it('calls onPress when pressed', () => {
    const onPress = jest.fn();
    render(<ItemCard title="Tap Me" subtitle="Sub" onPress={onPress} />);

    fireEvent.press(screen.getByText('Tap Me'));
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it('renders correctly without onPress', () => {
    const { toJSON } = render(<ItemCard title="Static" subtitle="Card" />);
    expect(toJSON()).toMatchSnapshot();
  });
});
```

### Hook Testing

```tsx
import { renderHook, act } from '@testing-library/react-native';
import { useCounter } from './useCounter';

describe('useCounter', () => {
  it('increments count', () => {
    const { result } = renderHook(() => useCounter());

    act(() => { result.current.increment(); });
    expect(result.current.count).toBe(1);
  });
});
```

### Integration Test with Navigation

```tsx
import { NavigationContainer } from '@react-navigation/native';
import { render, fireEvent, waitFor } from '@testing-library/react-native';

function renderWithNavigation(component: React.ReactElement) {
  return render(
    <NavigationContainer>{component}</NavigationContainer>
  );
}

it('navigates to detail screen on item press', async () => {
  renderWithNavigation(<RootNavigator />);

  fireEvent.press(screen.getByText('First Item'));
  await waitFor(() => {
    expect(screen.getByText('Item Detail')).toBeTruthy();
  });
});
```

### Run Tests

```bash
