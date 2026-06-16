#!/bin/bash
# package.sh - Package Chrome Extension for distribution

set -e

echo "🔨 Packaging Pater Chrome Extension..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get version from manifest
VERSION=$(grep -o '"version": "[^"]*"' manifest.json | cut -d'"' -f4)
echo "📦 Extension version: $VERSION"

# Clean up old packages
echo "🧹 Cleaning old packages..."
rm -f ../pater-extension-*.zip

# Check for required files
echo "🔍 Checking required files..."
REQUIRED_FILES=(
    "manifest.json"
    "background.js"
    "content-script.js"
    "popup.html"
    "popup.js"
    "popup.css"
    "sidepanel.html"
    "sidepanel.js"
    "sidepanel.css"
    "onboarding.html"
    "options.html"
    "options.js"
    "privacy-policy.html"
    "terms-of-service.html"
    "icons/icon-16.png"
    "icons/icon-48.png"
    "icons/icon-128.png"
    "icons/icon-256.png"
    "utils/api-client.js"
    "utils/storage.js"
    "utils/logger.js"
    "styles/variables.css"
    "styles/common.css"
)

MISSING_FILES=()
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -ne 0 ]; then
    echo -e "${RED}❌ Missing required files:${NC}"
    for file in "${MISSING_FILES[@]}"; do
        echo "   - $file"
    done
    exit 1
fi

echo -e "${GREEN}✅ All required files present${NC}"

# Check icon dimensions using Python
echo "🖼️  Verifying icons..."
python3 -c "
from PIL import Image
import sys

sizes = [16, 48, 128, 256]
for size in sizes:
    try:
        img = Image.open(f'icons/icon-{size}.png')
        if img.size == (size, size):
            print(f'   ✅ icon-{size}.png is valid ({size}x{size})')
        else:
            print(f'   ❌ icon-{size}.png has wrong size: {img.size}')
            sys.exit(1)
    except Exception as e:
        print(f'   ❌ icon-{size}.png error: {e}')
        sys.exit(1)
"

# Create ZIP package
echo "📦 Creating ZIP package..."
zip -r "../pater-extension-v${VERSION}.zip" . \
    -x "*.DS_Store" \
    -x "*/.DS_Store" \
    -x "*.txt" \
    -x "*/txt/*" \
    -x "package.sh" \
    -x "__MACOSX/*"

# Verify ZIP contents
echo "🔍 Verifying package contents..."
FILE_COUNT=$(unzip -l "../pater-extension-v${VERSION}.zip" 2>/dev/null | grep -c -E "\.png$|\.js$|\.html$|\.css$" || echo "0")
echo "   📁 Package contains $FILE_COUNT asset files"

# Get package size
PACKAGE_SIZE=$(du -h "../pater-extension-v${VERSION}.zip" | cut -f1)
echo -e "${GREEN}✅ Package created: pater-extension-v${VERSION}.zip (${PACKAGE_SIZE})${NC}"

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Package Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Version:  $VERSION"
echo "   File:     pater-extension-v${VERSION}.zip"
echo "   Size:     $PACKAGE_SIZE"
echo "   Location: $(realpath ../pater-extension-v${VERSION}.zip)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Next steps:"
echo "   1. Upload to Chrome Web Store Developer Dashboard"
echo "   2. Add store listing details"
echo "   3. Upload screenshots (1280x800)"
echo "   4. Add privacy policy URL"
echo "   5. Submit for review"
echo ""
echo -e "${GREEN}🎉 Packaging complete!${NC}"