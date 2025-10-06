# MAC Address Spoofer - Version History

**IMPORTANT:** Always update this file when making changes to the project!

---

## Current Version: 1.3.0

---

## Version History

### Version 1.3.0 (Current)
**Release Date:** January 2025

**Major Features:**
- ✨ Added 11 beautiful color themes with instant switching
- 🎨 Theme System:
  - Dark Mode (default)
  - Flash Bang (formerly Light Mode - blinding white)
  - Cyberpunk (neon colors)
  - Matrix (green on black)
  - Ocean (blue tones)
  - Sunset (purple/pink tones)
  - Hacker Green (terminal style)
  - Purple Haze (deep purple)
  - Nord (popular color scheme)
  - Dracula (popular theme)
  - Skittles (16 random bright colors, regenerates each time!)

**Key Bindings:**
- Press **'T'** to cycle through all themes
- Press **'S'** to randomize Skittles theme only (endless variations!)

**UI Updates:**
- Theme indicator moved to bottom of window (discrete placement)
- Shows current theme and keybinds: `(press "t" to change | "s" for skittles)`
- Skittles theme generates 16 unique random bright colors

**Files Updated:**
- `mac_spoofer_gui.py` - Added theme system, keybinds, Skittles randomization
- `README.md` - Updated features, theme list, changelog
- `README.txt` - Updated features, version history
- `version.md` - Created version tracking file (this file)

---

### Version 1.2.0
**Release Date:** January 2025

**Features:**
- Improved visual indicator on SPOOF ON/OFF button
- Button indicator changes: ⚫ (grey/black) = Original MAC, 🟢 (green) = Spoofed MAC
- Added comprehensive MIT License with liability protection
- Enhanced user clarity for spoofing status

**Files Updated:**
- `mac_spoofer_gui.py` - Updated button indicators
- `LICENSE` - Created MIT License with disclaimers
- `README.md` - Added license section, updated changelog
- `README.txt` - Added license info

---

### Version 1.1.0

**Features:**
- Expanded to 45+ vendor presets with country information
- Added major vendors: Xiaomi, Espressif, OPPO, Vivo, Google, Nintendo, Amazon, Broadcom, Qualcomm, Nvidia, and more
- Country-based vendor organization (USA, China, Korea, Japan, Taiwan, Hong Kong, Finland)
- Extracted comprehensive MAC prefixes from official IEEE OUI database files
- Each vendor now has 7-10 authentic MAC address prefixes

**Files Updated:**
- `mac_spoofer_gui.py` - Expanded vendor MAC dictionary
- `README.md` - Updated vendor list and features

---

### Version 1.0.0 (Initial Release)

**Core Features:**
- GUI and CLI versions
- Cross-platform support (Windows, Linux, macOS)
- Dark mode theme
- One-click toggle functionality
- Original MAC restoration
- Vendor MAC presets (initial set)
- Custom MAC address input
- Random MAC generation
- Activity logging
- Real-time status indicator

**Files Created:**
- `mac_spoofer.py` - CLI version
- `mac_spoofer_gui.py` - GUI version
- `Run_MAC_Spoofer.bat` - Windows launcher
- `MAC_Spoofer.spec` - PyInstaller specification
- `README.md` - Main documentation
- `README.txt` - Text documentation

---

## Version Numbering Convention

**Format:** MAJOR.MINOR.PATCH

- **MAJOR** (X.0.0): Breaking changes, major new features, complete redesign
- **MINOR** (1.X.0): New features, theme additions, significant UI changes
- **PATCH** (1.0.X): Bug fixes, minor tweaks, documentation updates

---

## Update Checklist

When updating the project, **ALWAYS** update these files:

### Version Bump:
1. ✅ `version.md` - Add new version section with details
2. ✅ `README.md` - Update Changelog section
3. ✅ `README.txt` - Update VERSION HISTORY section
4. ✅ `mac_spoofer_gui.py` - Update version in code if applicable

### Documentation:
5. ✅ `README.md` - Update Features section if applicable
6. ✅ `README.txt` - Update FEATURES section if applicable

### Build:
7. ✅ Rebuild executable: `pyinstaller MAC_Spoofer.spec --clean`
8. ✅ Test the executable
9. ✅ Update `dist/` folder

---

## Theme System (v1.3.0+)

**Themes List:**
1. Dark Mode
2. Flash Bang
3. Cyberpunk
4. Matrix
5. Ocean
6. Sunset
7. Hacker Green
8. Purple Haze
9. Nord
10. Dracula
11. Skittles (randomized)

**Keybindings:**
- `T` key: Cycle through all themes
- `S` key: Randomize Skittles theme only

**Adding New Themes:**
1. Add theme dictionary to `setup_themes()` in `mac_spoofer_gui.py`
2. Update theme count in README files
3. Update this version.md file
4. Increment MINOR version (e.g., 1.3.0 → 1.4.0)

---

## Future Roadmap Ideas

### High Priority
- [ ] **MAC History & Session Tracking**
  - Track previously used MAC addresses with timestamps
  - Quick reuse dropdown for recent MACs
  - Session management (start/end times, duration, notes)
  - Privacy-focused: OFF by default, encrypted storage option
  - Auto-delete old entries (configurable: 7/30/90 days)
  - "Clear All History" button for instant wipe
  - Session-only mode (clear on app exit)
  - Limit: Last 20-50 MACs (configurable)

### Theme Enhancements
- [ ] Save/load favorite themes
- [ ] Custom theme creator
- [ ] Theme import/export
- [ ] Animated theme transitions

### MAC Management
- [ ] Per-interface MAC saving
- [ ] Scheduled MAC rotation
- [ ] More vendor presets (100+)
- [ ] MAC address groups/profiles
- [ ] Backup/restore MAC settings

---

**Last Updated:** Version 1.3.0 - January 2025
