# Offline Print Sheet (Python)

This is a **pure offline** desktop application. It does not use any web
server, browser, or network connection. The form and the print sheet are two
windows in a single Tkinter app and update in real time.

## Run

```bash
python offline_app/app.py
```

## Notes

- The app uses Tkinter from the Python standard library.
- If Tkinter is missing on your system, install the OS package for it.
- Business rules and formulas are in `offline_app/formulas.py`.

## Printing

Use **Save to file** to export a text version. The **Print** button tries to
use the OS print command when it is available.
