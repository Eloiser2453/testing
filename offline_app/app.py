from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Dict

from formulas import DEFAULT_VALUES, SEGMENT_VARS, compute_values


class EchoSheetApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Offline Echo Template")
        self.root.geometry("1120x820")

        toolbar = ttk.Frame(self.root, padding=(12, 8))
        toolbar.pack(side="top", fill="x")
        ttk.Label(
            toolbar, text="Offline Echo Sheet Template", font=("Arial", 12, "bold")
        ).pack(side="left")
        ttk.Button(toolbar, text="Refresh values", command=self.refresh).pack(
            side="right"
        )

        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(container, background="#e9edf2")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        vbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        hbar = ttk.Scrollbar(container, orient="horizontal", command=self.canvas.xview)
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")
        self.canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)

        self.page_left = 30
        self.page_top = 30
        self.page_width = 980
        self.page_height = 1350
        self.text_items: Dict[str, int] = {}

        self._draw_sheet()
        self.refresh()

        self.canvas.configure(
            scrollregion=(
                0,
                0,
                self.page_left + self.page_width + 60,
                self.page_top + self.page_height + 60,
            )
        )

    def refresh(self) -> None:
        values = DEFAULT_VALUES.copy()
        values.update(compute_values())
        self.apply_values(values)

    def apply_values(self, values: Dict[str, str]) -> None:
        for key, item_id in self.text_items.items():
            if key in values:
                self.canvas.itemconfigure(item_id, text=str(values[key]))

    def _draw_sheet(self) -> None:
        left = self.page_left
        top = self.page_top
        right = left + self.page_width
        bottom = top + self.page_height

        self.canvas.create_rectangle(left, top, right, bottom, fill="white", outline="#333")

        header_bottom = top + 90
        self.canvas.create_rectangle(left, top, right, header_bottom, fill="#e0e6f0", outline="#333")
        self.canvas.create_text(
            left + 20,
            top + 25,
            text="ЭХОТЕКА",
            anchor="w",
            font=("Arial", 16, "bold"),
        )
        self.canvas.create_text(
            right - 20,
            top + 25,
            text="Трансторакальная эхокг",
            anchor="e",
            font=("Arial", 12, "bold"),
        )

        title_y = header_bottom + 30
        self.canvas.create_text(
            (left + right) / 2,
            title_y,
            text="ЭХОКАРДИОГРАММА от",
            anchor="e",
            font=("Arial", 12, "bold"),
        )
        self._add_value("EXAM_DATE", (left + right) / 2 + 10, title_y, anchor="w")

        info_top = title_y + 20
        info_bottom = info_top + 80
        self._draw_info_block(left + 10, info_top, right - 10, info_bottom)

        section_top = info_bottom + 20
        box_height = 120
        box_width = (self.page_width - 40) / 2

        self._draw_measure_box(
            left + 10,
            section_top,
            box_width,
            box_height,
            "Левый желудочек",
            [
                ("КДР", "LV_KDR"),
                ("КСР", "LV_KSR"),
                ("КДО", "LV_EDV"),
                ("КСО", "LV_ESV"),
                ("ФВ", "LV_EF"),
                ("МЖП", "LV_IVS"),
                ("ЗСЛЖ", "LV_PW"),
            ],
        )
        self._draw_measure_box(
            left + 20 + box_width,
            section_top,
            box_width,
            box_height,
            "Правый желудочек",
            [
                ("База", "RV_BASE"),
                ("Средний", "RV_MID"),
                ("TAPSE", "RV_TAPSE"),
            ],
        )

        next_row = section_top + box_height + 20
        self._draw_measure_box(
            left + 10,
            next_row,
            box_width,
            box_height,
            "Левое предсердие",
            [
                ("АП", "LA_AP"),
                ("Объём", "LA_VOL"),
            ],
        )
        self._draw_measure_box(
            left + 20 + box_width,
            next_row,
            box_width,
            box_height,
            "Правое предсердие",
            [
                ("АП", "RA_AP"),
                ("Объём", "RA_VOL"),
            ],
        )

        next_row += box_height + 20
        self._draw_measure_box(
            left + 10,
            next_row,
            box_width,
            box_height,
            "Аорта и ЛА",
            [
                ("Корень аорты", "AO_ROOT"),
                ("Восход.", "AO_ASC"),
                ("ЛА", "PA_DIAMETER"),
                ("НПВ", "IVC_DIAMETER"),
            ],
        )
        self._draw_measure_box(
            left + 20 + box_width,
            next_row,
            box_width,
            box_height,
            "Миокард",
            [
                ("Масса ЛЖ", "LV_MASS"),
                ("Отн. толщина", "LV_REL_WALL"),
            ],
        )

        valves_top = next_row + box_height + 20
        self._draw_valve_table(left + 10, valves_top, self.page_width - 20)

        segments_top = valves_top + 190
        self._draw_segments(left + 10, segments_top, self.page_width - 20)

        report_top = segments_top + 260
        self._draw_text_block(
            left + 10,
            report_top,
            self.page_width - 20,
            130,
            "Описание",
            "REPORT_TEXT",
        )
        conclusion_top = report_top + 150
        self._draw_text_block(
            left + 10,
            conclusion_top,
            self.page_width - 20,
            110,
            "Заключение",
            "CONCLUSION_TEXT",
        )

        footer_y = conclusion_top + 140
        self.canvas.create_line(left + 10, footer_y, right - 10, footer_y, fill="#333")
        self.canvas.create_text(
            left + 20,
            footer_y + 20,
            text="Врач:",
            anchor="w",
            font=("Arial", 10, "bold"),
        )
        self._add_value("DOCTOR_NAME", left + 80, footer_y + 20, anchor="w")

    def _draw_info_block(self, left: float, top: float, right: float, bottom: float) -> None:
        self.canvas.create_rectangle(left, top, right, bottom, outline="#333")

        mid_x = (left + right) / 2
        self.canvas.create_line(mid_x, top, mid_x, bottom, fill="#333")

        self._add_label_value(left + 10, top + 15, "Пациент:", "PATIENT_NAME", left + 130)
        self._add_label_value(left + 10, top + 40, "Возраст:", "PATIENT_AGE", left + 130)
        self._add_label_value(left + 10, top + 65, "Диагноз:", "DIAGNOSIS", left + 130)
        self._add_label_value(left + 10, top + 90, "Ритм:", "RHYTHM", left + 130)

        self._add_label_value(mid_x + 10, top + 15, "Направление:", "REFERRAL", mid_x + 150)
        self._add_label_value(mid_x + 10, top + 40, "Форма оплаты:", "PAYMENT_TYPE", mid_x + 150)
        self._add_label_value(mid_x + 10, top + 65, "Аппарат:", "DEVICE", mid_x + 150)

    def _draw_measure_box(
        self,
        left: float,
        top: float,
        width: float,
        height: float,
        title: str,
        fields: list[tuple[str, str]],
    ) -> None:
        right = left + width
        bottom = top + height
        self.canvas.create_rectangle(left, top, right, bottom, outline="#333")
        self.canvas.create_text(
            left + 10, top + 12, text=title, anchor="w", font=("Arial", 10, "bold")
        )

        y = top + 32
        for label, var_name in fields:
            self._add_label_value(left + 10, y, f"{label}:", var_name, left + 120)
            y += 18

    def _draw_valve_table(self, left: float, top: float, width: float) -> None:
        height = 170
        right = left + width
        bottom = top + height
        self.canvas.create_rectangle(left, top, right, bottom, outline="#333")
        self.canvas.create_text(
            left + 10, top + 12, text="Клапаны", anchor="w", font=("Arial", 10, "bold")
        )

        headers = ["VЕ", "Vmax", "Регург.", "Степень"]
        col_positions = [left + 160, left + 300, left + 440, left + 580]
        for header, x in zip(headers, col_positions):
            self.canvas.create_text(x, top + 32, text=header, anchor="w", font=("Arial", 9, "bold"))

        rows = [
            ("Митральный", ["MV_VE", "MV_VMAX", "MV_REGURG", "MV_GRADE"]),
            ("Аортальный", ["AV_VMAX", "AV_GRAD", "AV_REGURG", "AV_GRADE"]),
            ("Трикусп.", ["TV_VE", "TV_VMAX", "TV_REGURG", "TV_GRADE"]),
            ("Легочный", ["PV_VMAX", "PV_GRAD", "PV_REGURG", "PV_GRADE"]),
        ]

        y = top + 52
        for label, keys in rows:
            self.canvas.create_text(left + 10, y, text=label, anchor="w", font=("Arial", 9))
            for key, x in zip(keys, col_positions):
                self._add_value(key, x, y, anchor="w")
            y += 28

    def _draw_segments(self, left: float, top: float, width: float) -> None:
        right = left + width
        bottom = top + 230
        self.canvas.create_rectangle(left, top, right, bottom, outline="#333")
        self.canvas.create_text(
            left + 10, top + 12, text="Сегменты ЛЖ", anchor="w", font=("Arial", 10, "bold")
        )

        center_x = left + width / 2
        center_y = top + 95
        radius = 70
        self.canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            outline="#333",
            width=2,
        )

        positions = [
            (0, -45),
            (38, -20),
            (38, 20),
            (0, 45),
            (-38, 20),
            (-38, -20),
        ]
        for (dx, dy), key in zip(positions, SEGMENT_VARS):
            x = center_x + dx
            y = center_y + dy
            self.canvas.create_oval(x - 18, y - 18, x + 18, y + 18, outline="#333")
            self._add_value(key, x, y, anchor="center")

        bottom_y = top + 180
        start_x = left + 120
        spacing = 90
        for index, key in enumerate(SEGMENT_VARS):
            x = start_x + spacing * index
            self.canvas.create_oval(x - 14, bottom_y - 14, x + 14, bottom_y + 14, outline="#333")
            self._add_value(key, x, bottom_y, anchor="center")

        legend_x = right - 220
        self.canvas.create_text(legend_x, bottom_y - 20, text="1 - норма", anchor="w", font=("Arial", 8))
        self.canvas.create_text(legend_x, bottom_y, text="2 - гипокинезия", anchor="w", font=("Arial", 8))
        self.canvas.create_text(legend_x, bottom_y + 20, text="3 - акинезия", anchor="w", font=("Arial", 8))
        self.canvas.create_text(legend_x, bottom_y + 40, text="4 - дискинезия", anchor="w", font=("Arial", 8))

    def _draw_text_block(
        self, left: float, top: float, width: float, height: float, title: str, var_name: str
    ) -> None:
        right = left + width
        bottom = top + height
        self.canvas.create_rectangle(left, top, right, bottom, outline="#333")
        self.canvas.create_text(
            left + 10, top + 12, text=title, anchor="w", font=("Arial", 10, "bold")
        )
        self._add_value(var_name, left + 10, top + 32, anchor="nw", width=width - 20)

    def _add_label_value(
        self,
        x_label: float,
        y: float,
        label: str,
        var_name: str,
        x_value: float,
    ) -> None:
        self.canvas.create_text(x_label, y, text=label, anchor="w", font=("Arial", 9))
        self._add_value(var_name, x_value, y, anchor="w")

    def _add_value(
        self, var_name: str, x: float, y: float, anchor: str = "w", width: float | None = None
    ) -> None:
        item_id = self.canvas.create_text(
            x,
            y,
            text=var_name,
            anchor=anchor,
            font=("Arial", 9, "bold"),
            width=width,
        )
        self.text_items[var_name] = item_id


def main() -> None:
    root = tk.Tk()
    ttk.Style().theme_use("clam")
    EchoSheetApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
