# STEP 4: Write Compose UI Tests

### 4.1 Screen Test Pattern

```kotlin
@RunWith(AndroidJUnit4::class)
class FeatureScreenTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun `loading state shows progress indicator`() {
        composeTestRule.setContent {
            FeatureScreen(state = FeatureState.Loading, onIntent = {})
        }

        composeTestRule.onNodeWithTag("loading_indicator").assertIsDisplayed()
    }

    @Test
    fun `content state shows data`() {
        val data = FeatureData(id = "1", name = "Test Feature")
        composeTestRule.setContent {
            FeatureScreen(
                state = FeatureState.Content(data),
                onIntent = {}
            )
        }

        composeTestRule.onNodeWithText("Test Feature").assertIsDisplayed()
    }

    @Test
    fun `clicking action button sends intent`() {
        var receivedIntent: FeatureIntent? = null
        composeTestRule.setContent {
            FeatureScreen(
                state = FeatureState.Content(testData),
                onIntent = { receivedIntent = it }
            )
        }

        composeTestRule.onNodeWithContentDescription("Action").performClick()

        assertThat(receivedIntent).isEqualTo(FeatureIntent.ActionClicked)
    }

    @Test
    fun `error state shows retry button`() {
        composeTestRule.setContent {
            FeatureScreen(
                state = FeatureState.Error("Something went wrong"),
                onIntent = {}
            )
        }

        composeTestRule.onNodeWithText("Retry").assertIsDisplayed()
        composeTestRule.onNodeWithText("Something went wrong").assertIsDisplayed()
    }
}
```

### 4.2 Compose Test Finders Reference

| Finder | Usage |
|--------|-------|
| `onNodeWithText("label")` | Find by visible text |
| `onNodeWithContentDescription("desc")` | Find by a11y description |
| `onNodeWithTag("tag")` | Find by `Modifier.testTag("tag")` |
| `onAllNodesWithText("item")` | Find multiple matches |
| `onNodeWithTag("list").onChildren()` | Navigate child nodes |

### 4.3 Compose Test Actions Reference

| Action | Usage |
|--------|-------|
| `.performClick()` | Tap |
| `.performTextInput("text")` | Type text |
| `.performScrollTo()` | Scroll to node |
| `.performTouchInput { swipeUp() }` | Gesture |
| `.performImeAction()` | Submit keyboard action |

