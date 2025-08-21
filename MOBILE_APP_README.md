# Lexipark Mobile App

This document covers building and publishing the Lexipark mobile app using Capacitor.

## Prerequisites

- Node.js 18+ and npm
- Android Studio (for Android builds)
- Xcode 15+ (for iOS builds, macOS only)
- Capacitor CLI: `npm i -g @capacitor/cli`

## Project Structure

```
jorp/
├── static/                 # Web assets (served by Django)
├── android/               # Android native project
├── ios/                   # iOS native project
├── capacitor.config.json  # Capacitor configuration
└── package.json          # Node dependencies
```

## Building the App

### 1. Update Web Assets

```bash
# After making changes to Django templates/static
python manage.py collectstatic
npx cap copy
```

### 2. Android Build

```bash
# Open Android Studio
npx cap open android

# In Android Studio:
# 1. Wait for Gradle sync
# 2. Build > Build Bundle(s) / APK(s) > Build APK(s)
# 3. APK will be in android/app/build/outputs/apk/debug/
```

### 3. iOS Build

```bash
# Open Xcode
npx cap open ios

# In Xcode:
# 1. Select target device/simulator
# 2. Product > Build
# 3. Product > Archive (for App Store)
```

## Store Readiness Checklist

### Android (Google Play Store)

- [ ] **App Icon**: 512x512 PNG in `android/app/src/main/res/mipmap-hdpi/`
- [ ] **Package Name**: `com.lexipark.app` (already set)
- [ ] **Version Code**: Increment in `android/app/build.gradle`
- [ ] **Target SDK**: 34 (Android 14)
- [ ] **Min SDK**: 24 (Android 7.0)
- [ ] **64-bit Support**: Enable in `android/app/build.gradle`
- [ ] **Signing**: Generate release keystore
- [ ] **Privacy Policy**: Required URL in store listing

### iOS (App Store)

- [ ] **App Icon**: 1024x1024 PNG in `ios/App/App/Assets.xcassets/AppIcon.appiconset/`
- [ ] **Bundle ID**: `com.lexipark.app` (already set)
- [ ] **Version**: Increment in Xcode project settings
- [ ] **Launch Screen**: Customize in `ios/App/App/Base.lproj/LaunchScreen.storyboard`
- [ ] **Signing**: Configure in Xcode > Signing & Capabilities
- [ ] **Privacy Policy**: Required URL in store listing

## Deep Links Configuration

### Android App Links
- Domain: `lexipark.onrender.com`
- Auto-verification enabled
- Custom scheme: `lexipark://`

### iOS Universal Links
- Domain: `lexipark.onrender.com`
- Custom scheme: `lexipark://`
- Associated domains configured

### Testing Deep Links

```bash
# Android
adb shell am start -W -a android.intent.action.VIEW -d "https://lexipark.onrender.com/analysis/" com.lexipark.app

# iOS Simulator
xcrun simctl openurl booted "lexipark://analysis"
```

## Development Workflow

### 1. Make Web Changes
```bash
# Edit Django templates/static files
python manage.py collectstatic
```

### 2. Sync to Native
```bash
npx cap copy
npx cap sync
```

### 3. Test Changes
```bash
# Android
npx cap run android

# iOS
npx cap run ios
```

## Troubleshooting

### Common Issues

1. **iOS Build Fails**
   - Ensure Xcode 15+ is installed
   - Check signing certificates in Xcode
   - Verify iOS deployment target

2. **Android Build Fails**
   - Update Android Studio and SDK tools
   - Check Gradle version compatibility
   - Verify Android SDK installation

3. **Deep Links Not Working**
   - Check manifest/Info.plist configuration
   - Verify domain verification (Android)
   - Test with adb/xcrun commands

### Performance Tips

- Use `npx cap copy` instead of `npx cap sync` for faster builds
- Keep `webDir` pointing to `static/` for Django integration
- Use production URLs in `capacitor.config.json` for testing

## Publishing

### Google Play Store
1. Generate signed APK/Bundle
2. Create store listing with screenshots
3. Set privacy policy URL
4. Submit for review

### App Store
1. Archive app in Xcode
2. Upload via App Store Connect
3. Create store listing with screenshots
4. Set privacy policy URL
5. Submit for review

## Support

For issues related to:
- **Capacitor**: Check [Capacitor documentation](https://capacitorjs.com/docs)
- **Android**: Check [Android developer docs](https://developer.android.com/)
- **iOS**: Check [Apple developer docs](https://developer.apple.com/)
- **Django**: Check [Django documentation](https://docs.djangoproject.com/)
