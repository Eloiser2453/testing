# Echo Report (PyQt6)

Приложение для заполнения и печати эхокардиографического отчёта.
Слева — форма ввода, справа — A4 лист с предпросмотром. Все изменения
отображаются сразу, без использования веба.

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Qt Designer

Файл интерфейса для Qt Designer: `ui/main_window.ui`.

## Возможности

- Лист формата A4
- Печать через системный диалог
- Обновление в реальном времени
