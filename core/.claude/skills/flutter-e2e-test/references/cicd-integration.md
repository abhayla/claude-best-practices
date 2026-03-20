# STEP 7: CI/CD Integration

### GitHub Actions Example

```yaml
name: Flutter E2E Tests

on: [push, pull_request]

jobs:
  e2e-android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.24.x'
          channel: stable

      - name: Install dependencies
        run: flutter pub get

      - name: Enable KVM
        run: |
          echo 'KERNEL=="kvm", GROUP="kvm", MODE="0666"' | sudo tee /etc/udev/rules.d/99-kvm4all.rules
          sudo udevadm control --reload-rules
          sudo udevadm trigger --name-match=kvm

      - name: Run E2E tests on Android
        uses: reactivecircus/android-emulator-runner@v2
        with:
          api-level: 34
          arch: x86_64
          script: flutter test integration_test/ --reporter github

      - name: Upload screenshots
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: e2e-screenshots
          path: build/screenshots/

  e2e-web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.24.x'
      - uses: browser-actions/setup-chrome@v1
      - uses: nanasess/setup-chromedriver@v2

      - run: flutter pub get

      - name: Run E2E tests on Web
        run: |
          chromedriver --port=4444 &
          flutter drive \
            --driver=test_driver/integration_test.dart \
            --target=integration_test/app_test.dart \
            -d web-server \
            --browser-name=chrome \
            --headless
```

### Generating Reports

```bash
