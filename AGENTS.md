# MAC // Spoofer

Canonical existing checkout: this folder, `D:\01 GITHUB Library\MAC-SPOOFER`.
Keep the original `Ringmast4r/MAC-SPOOFER` repository and its visibility/history.
The similarly named Projects Library folder was empty at the 1.6 refactor.

Read the Desktop app and versioning memoranda before desktop/release changes.
Use Python 3.11 and the checked-in build script. Version source is `VERSION`.
Use the SANS-derived shell, a single instance and one tray icon. Close hides;
Exit really exits. Do not replace the user's running binary during an adapter operation.
Run background commands with hidden windows; Patrick explicitly requested no PowerShell
windows on October 7. Only the requested app window should appear.

Patrick selected Blade (Sin City 14) for the shortcut and tray on October 7, 2026.
He then requested its white background; keep shortcut-blade-white.ico on the shortcuts.
The Net Works globe stays on the application/window. Honor saved theme settings;
the owner has used both light and dark. A new installation follows the memo's light default.

Do not change a real adapter during routine UI tests. Use `tests/` and the synthetic
engine in `scripts/check_ui.py`. Real reads are allowed. Do not conflate a registry
write with an observed MAC change, or a local address with a vendor identity.
Keep the legacy vendor-to-local generation as the default, with exact registered prefixes
an explicit option. Preserve the clear/reset/apply sequence and its settling delays.

Huginn-Muninn integration uses the offline, filtered `data/huginn.sqlite3` index.
Preserve its source manifest and the distinction between known sequences, partial
rule matches and observed devices. Never label weights as confidence percentages,
local MACs as vendor identities, or corpus references as live captures. The source
Huginn-Muninn databases and the separate portal/container services stay read-only.

Runtime data is under LocalAppData, never the public repo. `data/` here contains
only the public offline OUI and Huginn-Muninn snapshots and their provenance. Keep owner network data
and local screenshots out of Git. The legacy 1.5 source remains for history.
