# Marketplace Assets

This directory contains visual assets for the Claude Code Marketplace listing.

## Required Assets

### 1. Plugin Icon (`icon.png`)
- **Size**: 128x128 pixels (recommended)
- **Format**: PNG with transparency
- **Design**: Should represent testing/automation
- **Colors**: Consistent with project branding
- **Status**: TODO - Placeholder needed

**Suggested Design Elements**:
- Test tube or beaker icon
- Checkmark or validation symbol
- Gear/automation symbol
- Python logo integration (for Phase 1)
- Professional color palette

### 2. Gallery Banner (Optional)
- **Size**: 1280x640 pixels
- **Format**: PNG or JPG
- **Design**: Hero banner for marketplace listing
- **Status**: Optional for initial release

### 3. Screenshots (Optional but Recommended)
- **Size**: 1280x720 pixels or higher
- **Format**: PNG or JPG
- **Quantity**: 3-5 screenshots
- **Status**: TODO - Should show plugin in action

**Suggested Screenshots**:
1. `/test-analyze` command output showing identified test targets
2. `/test-loop` interactive workflow with approval gates
3. Generated test file with comprehensive tests
4. Test execution results showing pass/fail
5. Example project structure

## Creating the Icon

### Option 1: Use AI Image Generation
```bash
# Prompt for AI image generator:
"A minimalist icon for an automated testing plugin.
Features a test tube with checkmarks, gears, and subtle Python colors.
128x128px, PNG with transparency, professional style."
```

### Option 2: Use Icon Design Tool
- Figma: https://www.figma.com/
- Canva: https://www.canva.com/
- GIMP: https://www.gimp.org/ (free)

### Option 3: Use Free Icon Libraries
- Font Awesome: https://fontawesome.com/
- Material Icons: https://fonts.google.com/icons
- Feather Icons: https://feathericons.com/

**Combine symbols**: Test tube + Checkmark + Automation

## Placeholder Icon

For development/testing purposes, you can use a simple placeholder:

```bash
# Create a simple text-based placeholder (requires ImageMagick)
convert -size 128x128 xc:transparent \
  -font Arial -pointsize 72 -fill '#4A90E2' \
  -gravity center -annotate +0+0 'T' \
  icon.png
```

Or download a free testing icon from:
- https://www.flaticon.com/search?word=testing
- https://icon-icons.com/search/icons/?icontext=test

## Integration

Once created, the icon should be referenced in:
- `.claude-plugin/plugin.json`: `"icon": "assets/icon.png"`
- `MARKETPLACE.md`: Listed in screenshots section

## License Compliance

Ensure all assets are:
- Created by you/your team, OR
- Licensed for commercial use (CC0, MIT, or similar)
- Properly attributed if required

---

**Status**: Assets directory created. Icon and screenshots needed before marketplace submission.
