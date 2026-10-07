# Windows 1.6.0 verification — October 7, 2026

- 18 pytest cases passed: accepted/rejected address syntax, cryptographic local generation, local/virtual convention attribution, exact /24 /28 /36 prefix handling, vendor search, simulated apply/restore, driver rejection and recovery, privilege checks, session authentication, cross-origin rejection, preview mutation rejection and asset path restrictions.
- Browser workflow passed with a synthetic adapter: private generation, invalid input, exact vendor generation, OUI lookup, cancel versus confirm, simulated apply and restore, light/dark persistence, four viewport sizes, settings, JSON export and no JavaScript errors. A separate browser context verified operation with the production Content Security Policy intact.
- Real Windows adapter enumeration completed read-only. No adapter MAC or override was changed during this task. Registry mutation and restart paths were tested against simulated drivers only.
- PyInstaller one-file Windows EXE built with product/file version 1.6.0 and Net Works Lab LLC company metadata. Root and dist binaries match SHA-256 `834f7a443e81f2692f41983a64772173061b9e39ead40c0c064c1d8714244bad`.
- Desktop, Start Menu and project-folder shortcuts target the actual root EXE and use the owner-selected Blade icon. The Net Works globe is the app/window icon. Nine icon frames were inspected on black and white.
- Installed EXE reported a loaded native renderer, ready page, two visible physical adapters and a successfully registered tray icon. The process was responsive.
- Five additional launches handed their show requests to the existing instance. One PyInstaller parent/child pair remained; no additional app instances remained.
- The authenticated Exit handler removed the processes and released port 8802. The same callback is connected to tray Exit. Relaunch succeeded. Actual tray-menu clicking and native pixel review could not be completed because the Windows Computer Use pipe was unavailable after retries and a reset; browser pixel review and native startup/process evidence are separate checks.
- The owner requested dark mode. The installed app's persisted preference is dark, and its native page-ready callback confirmed dark after a clean relaunch.

The public screenshots use synthetic adapter data. The installed-app read-only screenshot remains in excluded `build/` because it contains owner network addresses. UAC acceptance and physical driver compatibility were not tested. The old root/dist EXEs are preserved locally under `build/` and the previous revision remains in Git history.
