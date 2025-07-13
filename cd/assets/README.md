# Distribution Assets

This directory contains assets used for building platform-specific distributions.

## 📁 Directory Structure

```
assets/
├── icons/              # Application icons
│   ├── app.icns           # macOS icon format
│   ├── app.ico            # Windows icon format
│   └── app.png            # Base PNG icon (512x512 recommended)
├── macos/              # macOS-specific assets
│   ├── background.png     # DMG background image
│   └── Info.plist.template # App bundle info template
└── windows/            # Windows-specific assets
    ├── version_info.txt   # Version information
    └── installer_banner.bmp # Installer banner image
```

## 🎨 Icon Guidelines

### macOS Icons (`.icns`)
- **Format**: Apple Icon Image format
- **Sizes**: Multiple sizes embedded (16x16 to 1024x1024)
- **Tools**: Use `iconutil` or third-party tools to convert PNG to ICNS

### Windows Icons (`.ico`)
- **Format**: Windows Icon format
- **Sizes**: Multiple sizes embedded (16x16 to 256x256)
- **Tools**: Use online converters or ImageMagick

### Base Icon (`.png`)
- **Size**: 512x512 pixels minimum
- **Format**: PNG with transparency
- **Style**: Clean, scalable design that works at small sizes

## 🛠️ Creating Icons

### From PNG to ICNS (macOS)
```bash
# Create iconset directory
mkdir app.iconset

# Generate different sizes
sips -z 16 16     app.png --out app.iconset/icon_16x16.png
sips -z 32 32     app.png --out app.iconset/icon_16x16@2x.png
sips -z 32 32     app.png --out app.iconset/icon_32x32.png
sips -z 64 64     app.png --out app.iconset/icon_32x32@2x.png
sips -z 128 128   app.png --out app.iconset/icon_128x128.png
sips -z 256 256   app.png --out app.iconset/icon_128x128@2x.png
sips -z 256 256   app.png --out app.iconset/icon_256x256.png
sips -z 512 512   app.png --out app.iconset/icon_256x256@2x.png
sips -z 512 512   app.png --out app.iconset/icon_512x512.png
sips -z 1024 1024 app.png --out app.iconset/icon_512x512@2x.png

# Convert to ICNS
iconutil -c icns app.iconset
```

### From PNG to ICO (Windows)
```bash
# Using ImageMagick
convert app.png -resize 256x256 -colors 256 app.ico

# Or create multi-size ICO
convert app.png \
  \( -clone 0 -resize 16x16 \) \
  \( -clone 0 -resize 24x24 \) \
  \( -clone 0 -resize 32x32 \) \
  \( -clone 0 -resize 48x48 \) \
  \( -clone 0 -resize 64x64 \) \
  \( -clone 0 -resize 128x128 \) \
  \( -clone 0 -resize 256x256 \) \
  -delete 0 app.ico
```

## 🎭 Default Icons

If no custom icons are provided, the build scripts will automatically generate default icons with the "IP" text on a colored background.

## 📱 Design Recommendations

1. **Simple & Recognizable**: Icons should be clear at small sizes
2. **Consistent Branding**: Use consistent colors and style
3. **Platform Guidelines**: Follow macOS and Windows design guidelines
4. **High Resolution**: Provide high-resolution sources for scaling
5. **Transparency**: Use transparency where appropriate

## 🔧 Custom Assets

To customize the application appearance:

1. Replace `app.png` with your custom icon
2. Run the conversion scripts above
3. Rebuild the distributions
4. Test on both platforms

For advanced customization, edit the DMG background or Windows installer graphics.