from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict

from formulas import DEFAULT_DATA, compute_results, normalize_data


def format_money(value: float) -> str:
    return f"{value:.2f}"


def format_percent(value: float) -> str:
    return f"{value * 100:.0f}%"


def format_quantity(value: float) -> str:
    if int(value) == value:
        return str(int(value))
    return f"{value:.2f}"


def format_text(value: Any) -> str:
    text = str(value or "").strip()
    return text if text else "-"


class PrintSheetApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Offline Print Sheet")
        self.root.geometry("900x520")

        self.state: Dict[str, Any] = normalize_data(DEFAULT_DATA)
        self.results: Dict[str, Any] = compute_results(self.state)

        self.vars = {
            "customer_name": tk.StringVar(value=self.state["customer_name"]),
            "order_number": tk.StringVar(value=self.state["order_number"]),
            "product": tk.StringVar(value=self.state["product"]),
            "quantity": tk.StringVar(value=format_quantity(self.state["quantity"])),
            "price": tk.StringVar(value=format_money(self.state["price"])),
            "region": tk.StringVar(value=self.state["region"]),
            "delivery": tk.StringVar(value=self.state["delivery"]),
            "urgent": tk.BooleanVar(value=self.state["urgent"]),
            "notes": tk.StringVar(value=self.state["notes"]),
        }

        self.result_labels: Dict[str, ttk.Label] = {}
        self.print_labels: Dict[str, ttk.Label] = {}

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
        ttk.Label(header, text="Live Form", font=("Segoe UI", 14, "bold")).pack(
            side="left"
        )
        ttk.Button(
            header, text="Open print window", command=self._show_print_window
        ).pack(side="right")

        form_frame = ttk.LabelFrame(main, text="Input data", padding=12)
        form_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        result_frame = ttk.LabelFrame(main, text="Calculated results", padding=12)
        result_frame.grid(row=1, column=1, sticky="nsew")

        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(1, weight=1)

        row = 0
        row = self._add_entry(form_frame, row, "Customer name", "customer_name")
        row = self._add_entry(form_frame, row, "Order number", "order_number")
        row = self._add_entry(form_frame, row, "Product", "product")
        row = self._add_entry(form_frame, row, "Quantity", "quantity")
        row = self._add_entry(form_frame, row, "Unit price", "price")
        row = self._add_combo(
            form_frame, row, "Region", "region", ["local", "national", "international"]
        )
        row = self._add_combo(
            form_frame, row, "Delivery", "delivery", ["standard", "express"]
        )
        row = self._add_check(form_frame, row, "Urgent processing", "urgent")
        self._add_entry(form_frame, row, "Notes", "notes")

        results = [
            ("Subtotal", "subtotal", format_money),
            ("Discount rate", "discount_rate", format_percent),
            ("Discount amount", "discount_amount", format_money),
            ("Delivery fee", "delivery_fee", format_money),
            ("Urgent fee", "urgent_fee", format_money),
            ("Tax rate", "tax_rate", format_percent),
            ("Tax amount", "tax_amount", format_money),
            ("Total", "total", format_money),
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
        self.print_window.geometry("720x520")

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

        details_frame = ttk.LabelFrame(container, text="Order details", padding=12)
        details_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        totals_frame = ttk.LabelFrame(container, text="Totals", padding=12)
        totals_frame.grid(row=2, column=0, sticky="ew")

        detail_rows = [
            ("Customer", "customer_name", format_text),
            ("Order number", "order_number", format_text),
            ("Product", "product", format_text),
            ("Quantity", "quantity", format_quantity),
            ("Unit price", "price", format_money),
            ("Region", "region", str),
            ("Delivery", "delivery", str),
            ("Urgent", "urgent", lambda value: "yes" if value else "no"),
            ("Notes", "notes", format_text),
        ]
        for index, (label, key, _) in enumerate(detail_rows):
            ttk.Label(details_frame, text=label).grid(
                row=index, column=0, sticky="w", pady=2
            )
            value_label = ttk.Label(details_frame, text="-")
            value_label.grid(row=index, column=1, sticky="e", pady=2)
            self.print_labels[key] = value_label

        totals_rows = [
            ("Subtotal", "subtotal", format_money),
            ("Discount", "discount_amount", format_money),
            ("Delivery fee", "delivery_fee", format_money),
            ("Urgent fee", "urgent_fee", format_money),
            ("Tax", "tax_amount", format_money),
            ("Total", "total", format_money),
        ]
        for index, (label, key, _) in enumerate(totals_rows):
            ttk.Label(totals_frame, text=label).grid(
                row=index, column=0, sticky="w", pady=2
            )
            value_label = ttk.Label(totals_frame, text="-")
            value_label.grid(row=index, column=1, sticky="e", pady=2)
            self.print_labels[key] = value_label

        for frame in (details_frame, totals_frame):
            frame.columnconfigure(0, weight=1)
            frame.columnconfigure(1, weight=0)

    def _add_entry(self, parent: ttk.LabelFrame, row: int, label: str, key: str) -> int:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        entry = ttk.Entry(parent, textvariable=self.vars[key])
        entry.grid(row=row, column=1, sticky="ew", pady=4, padx=(12, 0))
        parent.columnconfigure(1, weight=1)
        return row + 1

    def _add_combo(
        self,
        parent: ttk.LabelFrame,
        row: int,
        label: str,
        key: str,
        values: list[str],
    ) -> int:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        combo = ttk.Combobox(
            parent, textvariable=self.vars[key], values=values, state="readonly"
        )
        combo.grid(row=row, column=1, sticky="ew", pady=4, padx=(12, 0))
        parent.columnconfigure(1, weight=1)
        return row + 1

    def _add_check(
        self, parent: ttk.LabelFrame, row: int, label: str, key: str
    ) -> int:
        check = ttk.Checkbutton(parent, text=label, variable=self.vars[key])
        check.grid(row=row, column=0, columnspan=2, sticky="w", pady=4)
        return row + 1

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
            "subtotal": format_money,
            "discount_rate": format_percent,
            "discount_amount": format_money,
            "delivery_fee": format_money,
            "urgent_fee": format_money,
            "tax_rate": format_percent,
            "tax_amount": format_money,
            "total": format_money,
            "status": lambda value: str(value),
        }

        for key, label in self.result_labels.items():
            formatter = result_formatters.get(key, lambda value: str(value))
            label.config(text=formatter(self.results.get(key)))

        detail_formatters = {
            "customer_name": format_text,
            "order_number": format_text,
            "product": format_text,
            "quantity": format_quantity,
            "price": format_money,
            "region": str,
            "delivery": str,
            "urgent": lambda value: "yes" if value else "no",
            "notes": format_text,
            "subtotal": format_money,
            "discount_amount": format_money,
            "delivery_fee": format_money,
            "urgent_fee": format_money,
            "tax_amount": format_money,
            "total": format_money,
        }

        for key, label in self.print_labels.items():
            value = self.state.get(key, self.results.get(key, "-"))
            formatter = detail_formatters.get(key, lambda value: str(value))
            label.config(text=formatter(value))

    def _show_print_window(self) -> None:
        self.print_window.deiconify()
        self.print_window.lift()
        self.print_window.focus_force()

    def _build_print_text(self) -> str:
        lines = [
            "PRINT SHEET",
            "",
            "Order details",
            f"Customer: {format_text(self.state['customer_name'])}",
            f"Order number: {format_text(self.state['order_number'])}",
            f"Product: {format_text(self.state['product'])}",
            f"Quantity: {format_quantity(self.state['quantity'])}",
            f"Unit price: {format_money(self.state['price'])}",
            f"Region: {self.state['region']}",
            f"Delivery: {self.state['delivery']}",
            f"Urgent: {'yes' if self.state['urgent'] else 'no'}",
            f"Notes: {format_text(self.state['notes'])}",
            "",
            "Totals",
            f"Subtotal: {format_money(self.results['subtotal'])}",
            f"Discount: {format_money(self.results['discount_amount'])}",
            f"Delivery fee: {format_money(self.results['delivery_fee'])}",
            f"Urgent fee: {format_money(self.results['urgent_fee'])}",
            f"Tax: {format_money(self.results['tax_amount'])}",
            f"Total: {format_money(self.results['total'])}",
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
