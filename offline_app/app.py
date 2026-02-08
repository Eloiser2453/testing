from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict

from formulas import DEFAULT_DATA, SEGMENT_KEYS, compute_results, normalize_data


def format_score(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    return "-"


def format_text(value: Any) -> str:
    text = str(value or "").strip()
    return text if text else "-"


def format_segment(value: Any) -> str:
    if isinstance(value, int):
        return str(value)
    return "-"


class PrintSheetApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Offline Echo Sheet")
        self.root.geometry("980x640")

        self.state: Dict[str, Any] = normalize_data(DEFAULT_DATA)
        self.results: Dict[str, Any] = compute_results(self.state)

        self.vars = {
            "patient_name": tk.StringVar(value=self.state["patient_name"]),
            "age": tk.StringVar(value=self.state["age"]),
            "diagnosis": tk.StringVar(value=self.state["diagnosis"]),
            "rhythm": tk.StringVar(value=self.state["rhythm"]),
        }
        for key in SEGMENT_KEYS:
            self.vars[key] = tk.StringVar(
                value="" if self.state.get(key) is None else str(self.state.get(key))
            )

        self.result_labels: Dict[str, ttk.Label] = {}
        self.print_labels: Dict[str, ttk.Label] = {}
        self.segment_canvas_items: Dict[str, Dict[str, int]] = {
            "top": {},
            "bottom": {},
        }

        self._build_form()
        self._build_print_window()
        self._bind_traces()
        self._update_views()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.print_window.protocol("WM_DELETE_WINDOW", self._on_print_close)

    def _build_form(self) -> None:
        main = ttk.Frame(self.root, padding=12)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        header = ttk.Frame(main)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        ttk.Label(header, text="Echo Form", font=("Segoe UI", 14, "bold")).pack(
            side="left"
        )
        ttk.Button(
            header, text="Open print window", command=self._show_print_window
        ).pack(side="right")

        left_container = ttk.Frame(main)
        left_container.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(1, weight=1)
        left_container.rowconfigure(1, weight=1)

        form_frame = ttk.LabelFrame(left_container, text="Patient info", padding=12)
        form_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        segments_frame = ttk.LabelFrame(
            left_container, text="LV segments (bottom circles)", padding=12
        )
        segments_frame.grid(row=1, column=0, sticky="nsew")

        result_frame = ttk.LabelFrame(main, text="LV summary", padding=12)
        result_frame.grid(row=1, column=1, sticky="nsew")

        row = 0
        row = self._add_entry(form_frame, row, "Patient name", "patient_name")
        row = self._add_entry(form_frame, row, "Age", "age")
        row = self._add_entry(form_frame, row, "Diagnosis", "diagnosis")
        self._add_entry(form_frame, row, "Rhythm", "rhythm")

        self._build_segment_inputs(segments_frame)

        results = [
            ("LV score", "lv_score", format_score),
            ("Segments filled", "segment_count", lambda value: str(value)),
            ("Status", "status", lambda value: str(value)),
        ]
        for index, (label, key, _) in enumerate(results):
            ttk.Label(result_frame, text=label).grid(
                row=index, column=0, sticky="w", pady=2
            )
            value_label = ttk.Label(result_frame, text="-")
            value_label.grid(row=index, column=1, sticky="e", pady=2)
            self.result_labels[key] = value_label

        result_frame.columnconfigure(0, weight=1)
        result_frame.columnconfigure(1, weight=0)

    def _build_print_window(self) -> None:
        self.print_window = tk.Toplevel(self.root)
        self.print_window.title("Print sheet")
        self.print_window.geometry("820x640")

        container = ttk.Frame(self.print_window, padding=12)
        container.grid(row=0, column=0, sticky="nsew")
        self.print_window.columnconfigure(0, weight=1)
        self.print_window.rowconfigure(0, weight=1)

        header = ttk.Frame(container)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(header, text="Print Sheet", font=("Segoe UI", 14, "bold")).pack(
            side="left"
        )
        ttk.Button(header, text="Save to file", command=self._save_to_file).pack(
            side="right", padx=(6, 0)
        )
        ttk.Button(header, text="Print", command=self._print_to_system).pack(
            side="right"
        )

        details_frame = ttk.LabelFrame(container, text="Patient info", padding=12)
        details_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        lv_frame = ttk.LabelFrame(container, text="LV diagram", padding=12)
        lv_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 12))
        summary_frame = ttk.LabelFrame(container, text="Summary", padding=12)
        summary_frame.grid(row=3, column=0, sticky="ew")

        container.rowconfigure(2, weight=1)

        detail_rows = [
            ("Patient name", "patient_name", format_text),
            ("Age", "age", format_text),
            ("Diagnosis", "diagnosis", format_text),
            ("Rhythm", "rhythm", format_text),
        ]
        for index, (label, key, _) in enumerate(detail_rows):
            ttk.Label(details_frame, text=label).grid(
                row=index, column=0, sticky="w", pady=2
            )
            value_label = ttk.Label(details_frame, text="-")
            value_label.grid(row=index, column=1, sticky="e", pady=2)
            self.print_labels[key] = value_label

        self._build_lv_canvas(lv_frame)

        summary_rows = [
            ("LV score", "lv_score", format_score),
            ("Segments filled", "segment_count", lambda value: str(value)),
            ("Status", "status", lambda value: str(value)),
        ]
        for index, (label, key, _) in enumerate(summary_rows):
            ttk.Label(summary_frame, text=label).grid(
                row=index, column=0, sticky="w", pady=2
            )
            value_label = ttk.Label(summary_frame, text="-")
            value_label.grid(row=index, column=1, sticky="e", pady=2)
            self.print_labels[key] = value_label

        for frame in (details_frame, summary_frame):
            frame.columnconfigure(0, weight=1)
            frame.columnconfigure(1, weight=0)

    def _build_lv_canvas(self, parent: ttk.LabelFrame) -> None:
        canvas = tk.Canvas(
            parent,
            width=420,
            height=300,
            background="white",
            highlightthickness=1,
            highlightbackground="#cfd4dc",
        )
        canvas.grid(row=0, column=0, sticky="nsew")
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        canvas.create_text(210, 16, text="LV top view", font=("Segoe UI", 10, "bold"))
        canvas.create_oval(120, 40, 300, 220, outline="#485767", width=2)

        top_positions = {
            "seg_1": (210, 60),
            "seg_2": (255, 90),
            "seg_3": (255, 160),
            "seg_4": (210, 190),
            "seg_5": (165, 160),
            "seg_6": (165, 90),
        }

        for key, (x, y) in top_positions.items():
            canvas.create_oval(x - 16, y - 16, x + 16, y + 16, outline="#4b5563", width=2)
            text_id = canvas.create_text(x, y, text="-", font=("Segoe UI", 10, "bold"))
            self.segment_canvas_items["top"][key] = text_id

        bottom_y = 255
        start_x = 50
        spacing = 60
        for index, key in enumerate(SEGMENT_KEYS):
            x = start_x + spacing * index
            canvas.create_oval(x - 12, bottom_y - 12, x + 12, bottom_y + 12, outline="#6b7280")
            text_id = canvas.create_text(x, bottom_y, text="-", font=("Segoe UI", 10))
            self.segment_canvas_items["bottom"][key] = text_id
            canvas.create_text(x, bottom_y + 18, text=f"S{index + 1}", font=("Segoe UI", 8))

        self.segment_canvas = canvas

    def _add_entry(self, parent: ttk.LabelFrame, row: int, label: str, key: str) -> int:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        entry = ttk.Entry(parent, textvariable=self.vars[key])
        entry.grid(row=row, column=1, sticky="ew", pady=4, padx=(12, 0))
        parent.columnconfigure(1, weight=1)
        return row + 1

    def _build_segment_inputs(self, parent: ttk.LabelFrame) -> None:
        values = ["", "1", "2", "3", "4"]
        for index, key in enumerate(SEGMENT_KEYS):
            ttk.Label(parent, text=f"S{index + 1}").grid(
                row=0, column=index, pady=(0, 6)
            )
            combo = ttk.Combobox(
                parent,
                textvariable=self.vars[key],
                values=values,
                width=3,
                state="readonly",
            )
            combo.grid(row=1, column=index, padx=4, pady=2)
            parent.columnconfigure(index, weight=1)

    def _bind_traces(self) -> None:
        for var in self.vars.values():
            var.trace_add("write", self._on_change)

    def _collect_state(self) -> Dict[str, Any]:
        return {key: var.get() for key, var in self.vars.items()}

    def _on_change(self, *_: Any) -> None:
        raw_state = self._collect_state()
        self.state = normalize_data(raw_state)
        self.results = compute_results(self.state)
        self._update_views()

    def _update_views(self) -> None:
        result_formatters = {
            "lv_score": format_score,
            "segment_count": lambda value: str(value),
            "status": lambda value: str(value),
        }

        for key, label in self.result_labels.items():
            formatter = result_formatters.get(key, lambda value: str(value))
            label.config(text=formatter(self.results.get(key)))

        detail_formatters = {
            "patient_name": format_text,
            "age": format_text,
            "diagnosis": format_text,
            "rhythm": format_text,
            "lv_score": format_score,
            "segment_count": lambda value: str(value),
            "status": lambda value: str(value),
        }

        for key, label in self.print_labels.items():
            value = self.state.get(key, self.results.get(key, "-"))
            formatter = detail_formatters.get(key, lambda value: str(value))
            label.config(text=formatter(value))

        for key in SEGMENT_KEYS:
            value = self.state.get(key)
            text = format_segment(value)
            top_id = self.segment_canvas_items["top"].get(key)
            bottom_id = self.segment_canvas_items["bottom"].get(key)
            if top_id:
                self.segment_canvas.itemconfigure(top_id, text=text)
            if bottom_id:
                self.segment_canvas.itemconfigure(bottom_id, text=text)

    def _show_print_window(self) -> None:
        self.print_window.deiconify()
        self.print_window.lift()
        self.print_window.focus_force()

    def _build_print_text(self) -> str:
        segment_lines = []
        for index, key in enumerate(SEGMENT_KEYS):
            segment_lines.append(f"S{index + 1}: {format_segment(self.state.get(key))}")

        lines = [
            "ECHO PRINT SHEET",
            "",
            "Patient info",
            f"Patient: {format_text(self.state['patient_name'])}",
            f"Age: {format_text(self.state['age'])}",
            f"Diagnosis: {format_text(self.state['diagnosis'])}",
            f"Rhythm: {format_text(self.state['rhythm'])}",
            "",
            "LV segments",
            *segment_lines,
            "",
            "Summary",
            f"LV score: {format_score(self.results['lv_score'])}",
            f"Segments filled: {self.results['segment_count']}",
            f"Status: {self.results['status']}",
            "",
        ]
        return "\n".join(lines)

    def _save_to_file(self) -> None:
        filename = filedialog.asksaveasfilename(
            title="Save print sheet",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not filename:
            return
        try:
            with open(filename, "w", encoding="utf-8") as handle:
                handle.write(self._build_print_text())
        except OSError as exc:
            messagebox.showerror("Save failed", f"Unable to save file:\n{exc}")

    def _print_to_system(self) -> None:
        text = self._build_print_text()
        try:
            tmp = tempfile.NamedTemporaryFile(
                delete=False, suffix=".txt", mode="w", encoding="utf-8"
            )
            with tmp:
                tmp.write(text)
        except OSError as exc:
            messagebox.showerror("Print failed", f"Unable to create temp file:\n{exc}")
            return

        if sys.platform.startswith("win"):
            try:
                os.startfile(tmp.name, "print")
            except OSError as exc:
                messagebox.showerror("Print failed", f"Unable to print:\n{exc}")
            return

        command = shutil.which("lp") or shutil.which("lpr")
        if not command:
            messagebox.showinfo(
                "Print not available",
                "Printing is not configured on this system. "
                "Use 'Save to file' instead.",
            )
            return

        try:
            subprocess.run([command, tmp.name], check=False)
        except OSError as exc:
            messagebox.showerror("Print failed", f"Unable to print:\n{exc}")

    def _on_print_close(self) -> None:
        self.print_window.withdraw()

    def _on_close(self) -> None:
        self.print_window.destroy()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    ttk.Style().theme_use("clam")
    PrintSheetApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
