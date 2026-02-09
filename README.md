# Offline Print Sheet (Python)

This is a **pure offline** desktop application. It does not use any web
server, browser, or network connection. It shows a single echo sheet template
that mirrors the provided image layout. Every value on the sheet is rendered as
a variable name placeholder.

## Run

```bash
python offline_app/app.py
```

## Notes

- The app uses Tkinter from the Python standard library.
- If Tkinter is missing on your system, install the OS package for it.
- Business rules and formulas should be implemented in `offline_app/formulas.py`.

## Workflow

Edit `compute_values()` in `offline_app/formulas.py` to return a dictionary of
variable names and their values. Click **Refresh values** in the UI to redraw
the sheet with your computed results.

## A4 PDF export (ready for print)

The **Save A4 PDF** button generates a PDF in A4 size. For this feature install
`reportlab`:

```bash
pip install reportlab
```

If Cyrillic text does not render in the PDF, install a system font such as
DejaVu Sans or Arial (the app tries to auto-detect them).
