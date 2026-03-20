# Common Actions

### Common Actions

| Action | Syntax | Use For |
|--------|--------|---------|
| `tapOn` | `- tapOn: "Button Text"` | Tap buttons, links, elements |
| `inputText` | `- inputText: "value"` | Type into focused field |
| `assertVisible` | `- assertVisible: "Text"` | Verify element is displayed |
| `assertNotVisible` | `- assertNotVisible: "Error"` | Verify element is NOT shown |
| `scrollUntilVisible` | `- scrollUntilVisible: {element: "Text", direction: DOWN}` | Scroll to find element |
| `back` | `- back` | Press back button |
| `swipe` | `- swipe: {direction: LEFT, duration: 400}` | Swipe gesture |
| `waitForAnimationToEnd` | `- waitForAnimationToEnd` | Wait for transitions |
| `takeScreenshot` | `- takeScreenshot: "screenshot_name"` | Capture for visual regression |
| `runFlow` | `- runFlow: auth/login.yaml` | Reuse another flow |
| `repeat` | `- repeat: {times: 3, commands: [...]}` | Loop actions |
| `evalScript` | `- evalScript: \${output.field}` | Access JavaScript expressions |
| `assertScreenshot` | `- assertScreenshot: {path: "baseline.png", thresholdPercentage: 95}` | Visual regression assertion (autonomous pass/fail) |

