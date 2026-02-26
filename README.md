# Conversion Widget (Desktop)

A desktop utility for:
- live **mm ↔ inch** conversion in either direction
- inch input as decimal, fraction (`1/4`), or mixed fraction (`1 1/4`)
- inch display in both decimal and fraction form
- a quick arithmetic calculator

## Run

```bash
python3 desktop_widget.py
```

No external dependencies are required (uses Python's built-in `tkinter`).

## Display troubleshooting (Linux)

If you run from a non-GUI shell, set a display before launching:

```bash
export DISPLAY=:0
python3 desktop_widget.py
```

The app now exits with a clean message if no GUI display is available instead of showing a long traceback.
