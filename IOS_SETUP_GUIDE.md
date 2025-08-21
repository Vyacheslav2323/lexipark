# iOS Setup Guide - Lexipark Mobile App

This guide focuses specifically on setting up and building your iOS app using Capacitor.

## 🍎 Prerequisites Check

✅ **Xcode**: Installed and accessible  
✅ **Capacitor**: Project initialized with iOS platform  
✅ **Web Assets**: Synced from Django static files  

## 🚀 Quick Start

### 1. **Xcode Project is Now Open**
- Your iOS project should be open in Xcode
- Project name: `App` (in the `ios/App/` directory)
- Target: `App` with bundle ID `com.lexipark.app`

### 2. **Configure Signing & Capabilities**

#### Step 1: Select Your Project
1. In Xcode's left sidebar, click on the `App` project (blue icon)
2. Select the `App` target
3. Go to the **Signing & Capabilities** tab

#### Step 2: Configure Team
1. **Team**: Select your Apple Developer account
2. **Bundle Identifier**: Should be `com.lexipark.app`
3. **Automatically manage signing**: ✅ Check this box
4. **Provisioning Profile**: Should auto-generate

#### Step 3: Add Capabilities
1. Click **+ Capability** button
2. Add these capabilities:
   - **Associated Domains** (for Universal Links)
   - **Background Modes** (if needed for offline functionality)

### 3. **Customize App Appearance**

#### App Icon
1. In Xcode, go to `App > Assets.xcassets > AppIcon`
2. Replace placeholder icons with your brand icons
3. Required sizes: 1024x1024 (App Store), 180x180 (iPhone), etc.

#### Launch Screen
1. Open `LaunchScreen.storyboard`
2. Customize with your app name and logo
3. Ensure it looks good on all device sizes

### 4. **Build and Test**

#### Build for Simulator
1. Select a simulator (e.g., iPhone 15 Pro)
2. Click **Product > Build** (⌘B)
3. Wait for build to complete

#### Run on Simulator
1. Click **Product > Run** (⌘R)
2. App should launch in simulator
3. Test navigation and functionality

#### Build for Device (Optional)
1. Connect your iPhone via USB
2. Select your device in the device dropdown
3. **Product > Build** then **Product > Run**

## 🔗 Test Deep Links

### Universal Links (https://lexipark.onrender.com)
```bash
# In simulator terminal
xcrun simctl openurl booted "https://lexipark.onrender.com/analysis/"
xcrun simctl openurl booted "https://lexipark.onrender.com/users/profile/"
```

### Custom URL Scheme (lexipark://)
```bash
# Test custom scheme
xcrun simctl openurl booted "lexipark://analysis"
xcrun simctl openurl booted "lexipark://vocab"
```

## 📱 iOS-Specific Features

### 1. **Safe Area Support**
- Your app automatically supports iPhone notches and Dynamic Island
- Content respects safe areas on all devices

### 2. **iOS Gestures**
- Swipe back navigation works automatically
- Pull-to-refresh can be added if needed

### 3. **iOS App Store Requirements**
- [ ] App icon in all required sizes
- [ ] Launch screen configured
- [ ] Privacy policy URL ready
- [ ] App description and screenshots
- [ ] Age rating configured

## 🚨 Common iOS Issues & Fixes

### Build Errors

#### "Signing for 'App' requires a development team"
- **Fix**: Select your team in Signing & Capabilities
- **Fix**: Ensure you're signed into Xcode with your Apple ID

#### "No provisioning profile found"
- **Fix**: Check "Automatically manage signing"
- **Fix**: Ensure your Apple Developer account is active

#### "Bundle identifier conflicts"
- **Fix**: Change bundle ID to something unique
- **Fix**: Use reverse domain notation (e.g., `com.yourname.lexipark`)

### Runtime Issues

#### App crashes on launch
- **Fix**: Check Xcode console for error messages
- **Fix**: Verify web assets are properly synced (`npx cap copy`)

#### Deep links not working
- **Fix**: Verify Associated Domains capability is added
- **Fix**: Check Info.plist URL schemes configuration

## 🔧 Development Workflow

### 1. **Make Web Changes**
```bash
# Edit Django templates/static files
python manage.py collectstatic
```

### 2. **Sync to iOS**
```bash
npx cap copy
npx cap sync ios
```

### 3. **Test in Xcode**
- Build and run on simulator
- Test deep links
- Verify functionality

## 📋 iOS App Store Checklist

### Before Submission
- [ ] App builds successfully
- [ ] App runs on device/simulator
- [ ] Deep links work correctly
- [ ] App icon in all sizes
- [ ] Launch screen configured
- [ ] Privacy policy URL ready
- [ ] Screenshots for all device sizes
- [ ] App description written
- [ ] Keywords selected
- [ ] Age rating determined

### Submission Process
1. **Archive App**: Product > Archive
2. **Upload to App Store Connect**
3. **Create App Store Listing**
4. **Submit for Review**

## 🎯 Next Steps After iOS Setup

1. **Test Deep Links**: Verify all your app routes work
2. **Customize Icons**: Replace placeholder icons with your brand
3. **Test on Device**: Build and test on physical iPhone
4. **Prepare Store Listing**: Create screenshots and descriptions
5. **Submit for Review**: Archive and upload to App Store Connect

## 📞 iOS Development Resources

- **Apple Developer Documentation**: [developer.apple.com](https://developer.apple.com/)
- **Xcode Help**: Help menu in Xcode
- **iOS Human Interface Guidelines**: [HIG](https://developer.apple.com/design/human-interface-guidelines/)
- **Capacitor iOS Documentation**: [capacitorjs.com/docs/ios](https://capacitorjs.com/docs/ios)

## 🚀 Success Indicators

✅ **iOS project opens in Xcode**  
✅ **App builds without errors**  
✅ **App runs on simulator**  
✅ **Deep links work correctly**  
✅ **App icon displays properly**  
✅ **Launch screen shows correctly**  

---

**Your iOS app is now ready for development and testing!** 🎉

Follow this guide step by step, and you'll have a fully functional iOS app that loads your Django web app with native iOS capabilities.
