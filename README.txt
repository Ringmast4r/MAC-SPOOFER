MAC ADDRESS SPOOFER - GUI VERSION
==================================

FEATURES:
---------
✓ Easy-to-use graphical interface
✓ 11 Beautiful color themes (press 'T' to cycle)
✓ Themes: Dark, Flash Bang, Cyberpunk, Matrix, Ocean, Sunset, Hacker Green,
  Purple Haze, Nord, Dracula, and Skittles (random rainbow!)
✓ One-click MAC spoofing toggle (ON/OFF)
✓ 45+ vendor MAC address presets (Apple, Dell, HP, Cisco, etc.)
✓ Custom MAC address input
✓ Random MAC generation
✓ Restore original MAC address
✓ Real-time status indicator
✓ Activity log

HOW TO USE:
-----------
1. Run "Run_MAC_Spoofer.bat" as Administrator
   - Right-click → "Run as administrator"

2. Select your network interface from the dropdown

3. Choose spoofing method:

   METHOD A - Quick Toggle:
   - Click "⚫ SPOOF ON" (grey indicator) to instantly spoof with random MAC
   - Button changes to "🟢 SPOOF OFF" (green indicator) when actively spoofing
   - Click "🟢 SPOOF OFF" to restore original MAC

   METHOD B - Vendor MAC:
   - Select a vendor (e.g., Apple, Samsung, Cisco)
   - Click "Use Random from Vendor"

   METHOD C - Custom MAC:
   - Enter your desired MAC (format: 00:11:22:33:44:55)
   - Click "Use Custom MAC"

   METHOD D - Random MAC:
   - Click "Generate Random MAC" for completely random address

4. To restore your original MAC:
   - Click "Restore Original" button
   - Or click "SPOOF OFF" if spoofing is active

5. To change themes:
   - Press 'T' key anytime to cycle through 11 color themes
   - Press 'S' key to randomize Skittles theme (endless variations!)
   - Skittles theme generates new random colors each time!

REQUIREMENTS:
-------------
- Python 3.x installed
- Administrator/Root privileges (Windows/Linux)
- Network interface that supports MAC changes

WINDOWS NOTES:
--------------
- Some network adapters may require manual MAC change via Device Manager
- The application will provide instructions in the log window
- You may need to disable/enable the adapter after changing MAC
- Some WiFi adapters don't support MAC spoofing

VENDOR MAC ADDRESSES INCLUDED:
-------------------------------
3Com, Acer, Apple, Asus, Belkin, Cisco, D-Link, Dell, Fujitsu,
HP, Huawei, IBM, Intel, Lenovo, LG, Linksys, Microsoft, Motorola,
Netgear, Nokia, Samsung, Sony, Toshiba, TP-Link, Ubiquiti, Xerox, ZTE

Each vendor has 5-8 authentic MAC address prefixes from IEEE OUI database.

TROUBLESHOOTING:
----------------
Q: Application won't start?
A: Make sure Python is installed and run as administrator

Q: MAC address won't change?
A: Some adapters require manual change via Device Manager (see log for instructions)

Q: Interface not showing?
A: Click "Refresh" button or restart the application

Q: How to verify MAC changed?
A: Run "ipconfig /all" in Command Prompt and check "Physical Address"

FUTURE FEATURES & ROADMAP:
---------------------------
Planned enhancements for future versions:

HIGH PRIORITY:
* MAC History & Session Tracking
  - Track previously used MAC addresses with timestamps
  - Quick reuse dropdown for recent MACs
  - View when each MAC was used (date/time)
  - Optional session notes and duration tracking
  - Privacy-focused: OFF by default, auto-delete, encryption option
  - One-click "Clear All History" button
  - Session-only mode (clears on exit)

THEME ENHANCEMENTS:
* Save/load favorite themes
* Custom theme creator
* Theme import/export
* Animated transitions

MAC MANAGEMENT:
* Per-interface MAC profiles
* Scheduled MAC rotation
* Expanded vendor database (100+)
* MAC groups and profiles
* Backup/restore settings

VERSION HISTORY:
----------------
Version 1.3.0:
- Added 11 beautiful color themes (Dark, Flash Bang, Cyberpunk, Matrix, Ocean,
  Sunset, Hacker Green, Purple Haze, Nord, Dracula, Skittles)
- Press 'T' key to cycle through themes instantly
- Press 'S' key for Skittles-only randomization (endless variations!)
- Skittles theme generates 16 random bright rainbow colors
- Theme indicator discreetly placed at bottom of window

Version 1.2.0:
- Improved visual indicator: ⚫ (grey) = Original MAC, 🟢 (green) = Spoofed
- Added comprehensive MIT License with liability protection
- Enhanced clarity for spoofing status

DISCLAIMER & LICENSE:
---------------------
This tool is for legitimate network testing, privacy, and educational purposes only.

Licensed under MIT License with additional disclaimers:
- NO WARRANTY - Use at your own risk
- Authors NOT LIABLE for any damages, misuse, or legal consequences
- Users accept FULL RESPONSIBILITY for their use
- Must comply with all applicable laws and network policies
- Unauthorized network access is ILLEGAL

See LICENSE file for complete terms and conditions.
Use responsibly and legally.
