# Building NFS2Forge — Standalone .exe

This guide creates a single-folder distributable using **PyInstaller**.

---

## Prerequisites

```bash
pip install pyinstaller
pip install -r requirements.txt
```

---

## Option A — Quick build (one command)

```bash
pyinstaller --noconfirm --onedir --windowed ^
  --name "NFS2Forge" ^
  --icon "img/app.ico" ^
  --add-data "assets;assets" ^
  --add-data "presets;presets" ^
  --add-data "img;img" ^
  main.py
```

Output: `dist\NFS2Forge\NFS2Forge.exe`

---

## Option B — Using the .spec file (recommended for releases)

A `build.spec` is included in the repo. Run:

```bash
pyinstaller build.spec
```

Then zip the contents of `dist\NFS2Forge\` for distribution.

---

## Notes

- Use `--onedir` (not `--onefile`) — PySide6 loads DLLs at runtime; onefile is very slow to start.
- The `--windowed` flag suppresses the console window.
- Make sure `img/app.ico` exists before building.
- Test the built exe on a machine **without Python** before releasing.

---

## Release Checklist

- [ ] Run `pyinstaller build.spec` with no errors
- [ ] Test `dist\NFS2Forge\NFS2Forge.exe` — opens GlobalB.lzc, edits a car, writes successfully
- [ ] Zip `dist\NFS2Forge\` → `NFS2Forge-v1.0.0-win64.zip`
- [ ] Upload to GitHub Releases
