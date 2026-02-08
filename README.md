# Live Print Sheet (Python)

This project provides two pages:

- `/form` for entering data
- `/print` for a print-friendly sheet that updates in real time

The backend uses WebSockets to broadcast updates to all connected clients.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

## Usage

1. Open `http://localhost:8000/form` and enter data.
2. Open `http://localhost:8000/print` in another tab.
3. Updates appear immediately on the print page.

## Formulas

Business rules are implemented in `app/formulas.py`. Update the conditions and
fees there to match your real calculation logic.
