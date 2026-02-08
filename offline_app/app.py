from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, Optional, Tuple

from formulas import DEFAULT_VALUES, SEGMENT_VARS, compute_values

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import simpleSplit
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas as pdf_canvas

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def _register_pdf_fonts() -> Tuple[str, str]:
    if not REPORTLAB_AVAILABLE:
        return ("Helvetica", "Helvetica-Bold")

    candidates = [
        (
            "DejaVuSans",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ),
        (
            "Arial",
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf",
        ),
        (
            "LiberationSans",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ),
        (
            "NotoSans",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        ),
        (
            "ArialUnicode",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            None,
        ),
    ]

    for name, regular_path, bold_path in candidates:
        if regular_path and os.path.exists(regular_path):
            pdfmetrics.registerFont(TTFont(name, regular_path))
            bold_name = name
            if bold_path and os.path.exists(bold_path):
                bold_name = f"{name}-Bold"
                pdfmetrics.registerFont(TTFont(bold_name, bold_path))
            return (name, bold_name)

    return ("Helvetica", "Helvetica-Bold")


def _normalize_hex(value: str) -> str:
    if value.startswith("#") and len(value) == 4:
        return "#" + "".join([char * 2 for char in value[1:]])
    return value


def _parse_color(value: Optional[str]) -> Optional[colors.Color]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if value.lower() == "white":
        return colors.white
    if value.lower() == "black":
        return colors.black
    if value.startswith("#"):
        return colors.HexColor(_normalize_hex(value))
    return colors.black


class TkDrawer:
    def __init__(self, canvas: tk.Canvas) -> None:
        self.canvas = canvas

    def rect(
        self,
        left: float,
        top: float,
        right: float,
        bottom: float,
        fill: Optional[str] = None,
        outline: str = "#333",
        width: int = 1,
    ) -> None:
        self.canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill=fill or "",
            outline=outline,
            width=width,
        )

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        fill: str = "#333",
        width: int = 1,
    ) -> None:
        self.canvas.create_line(x1, y1, x2, y2, fill=fill, width=width)

    def oval(
        self,
        left: float,
        top: float,
        right: float,
        bottom: float,
        outline: str = "#333",
        width: int = 1,
    ) -> None:
        self.canvas.create_oval(left, top, right, bottom, outline=outline, width=width)

    def text(
        self,
        x: float,
        y: float,
        text: str,
        anchor: str = "w",
        font: Optional[Tuple[str, int, str]] = None,
        width: Optional[float] = None,
    ) -> int:
        return self.canvas.create_text(
            x,
            y,
            text=text,
            anchor=anchor,
            font=font or ("Arial", 9),
            width=width,
        )


class PdfDrawer:
    def __init__(
        self,
        pdf: pdf_canvas.Canvas,
        page_size: Tuple[float, float],
        design_width: float,
        design_height: float,
        margin: float = 24,
        fonts: Tuple[str, str] = ("Helvetica", "Helvetica-Bold"),
    ) -> None:
        self.pdf = pdf
        self.page_width, self.page_height = page_size
        self.design_width = design_width
        self.design_height = design_height

        available_width = self.page_width - 2 * margin
        available_height = self.page_height - 2 * margin
        self.scale = min(available_width / design_width, available_height / design_height)
        extra_x = (available_width - design_width * self.scale) / 2
        extra_y = (available_height - design_height * self.scale) / 2
        self.offset_x = margin + extra_x
        self.offset_y = margin + extra_y

        self.font_regular, self.font_bold = fonts

    def _map_point(self, x: float, y: float) -> Tuple[float, float]:
        pdf_x = self.offset_x + x * self.scale
        pdf_y = self.page_height - self.offset_y - y * self.scale
        return pdf_x, pdf_y

    def _resolve_font(
        self, font: Optional[Tuple[str, int, str]]
    ) -> Tuple[str, float]:
        if font is None:
            return self.font_regular, 9 * self.scale

        size = font[1] if len(font) > 1 else 9
        style = font[2] if len(font) > 2 else ""
        font_name = self.font_bold if "bold" in style.lower() else self.font_regular
        return font_name, size * self.scale

    def rect(
        self,
        left: float,
        top: float,
        right: float,
        bottom: float,
        fill: Optional[str] = None,
        outline: str = "#333",
        width: int = 1,
    ) -> None:
        x1, y1 = self._map_point(left, top)
        x2, y2 = self._map_point(right, bottom)
        box_left = min(x1, x2)
        box_bottom = min(y1, y2)
        box_width = abs(x2 - x1)
        box_height = abs(y2 - y1)

        stroke_color = _parse_color(outline)
        fill_color = _parse_color(fill)

        if stroke_color:
            self.pdf.setStrokeColor(stroke_color)
        if fill_color:
            self.pdf.setFillColor(fill_color)
        self.pdf.setLineWidth(width * self.scale)
        self.pdf.rect(
            box_left,
            box_bottom,
            box_width,
            box_height,
            stroke=1,
            fill=1 if fill_color else 0,
        )

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        fill: str = "#333",
        width: int = 1,
    ) -> None:
        px1, py1 = self._map_point(x1, y1)
        px2, py2 = self._map_point(x2, y2)
        stroke_color = _parse_color(fill)
        if stroke_color:
            self.pdf.setStrokeColor(stroke_color)
        self.pdf.setLineWidth(width * self.scale)
        self.pdf.line(px1, py1, px2, py2)

    def oval(
        self,
        left: float,
        top: float,
        right: float,
        bottom: float,
        outline: str = "#333",
        width: int = 1,
    ) -> None:
        x1, y1 = self._map_point(left, top)
        x2, y2 = self._map_point(right, bottom)
        stroke_color = _parse_color(outline)
        if stroke_color:
            self.pdf.setStrokeColor(stroke_color)
        self.pdf.setLineWidth(width * self.scale)
        self.pdf.ellipse(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

    def text(
        self,
        x: float,
        y: float,
        text: str,
        anchor: str = "w",
        font: Optional[Tuple[str, int, str]] = None,
        width: Optional[float] = None,
    ) -> None:
        font_name, font_size = self._resolve_font(font)
        self.pdf.setFont(font_name, font_size)

        px, py = self._map_point(x, y)
        baseline = py - font_size / 2

        if anchor == "center":
            self._draw_wrapped(px, py, text, font_name, font_size, width, "center")
            return
        if anchor == "e":
            self._draw_wrapped(px, py, text, font_name, font_size, width, "right")
            return
        if anchor == "nw":
            self._draw_wrapped(px, py, text, font_name, font_size, width, "left", top=True)
            return

        if width:
            self._draw_wrapped(px, py, text, font_name, font_size, width, "left")
            return
        self.pdf.drawString(px, baseline, text)

    def _draw_wrapped(
        self,
        px: float,
        py: float,
        text: str,
        font_name: str,
        font_size: float,
        width: Optional[float],
        align: str,
        top: bool = False,
    ) -> None:
        max_width = width * self.scale if width else 5000
        lines = simpleSplit(text, font_name, font_size, max_width)
        leading = font_size + 2
        if top:
            current_y = py - font_size
        else:
            current_y = py - font_size / 2

        for line in lines:
            if align == "center":
                self.pdf.drawCentredString(px, current_y, line)
            elif align == "right":
                self.pdf.drawRightString(px, current_y, line)
            else:
                self.pdf.drawString(px, current_y, line)
            current_y -= leading


class SheetLayout:
    def __init__(self) -> None:
        self.page_left = 30
        self.page_top = 30
        self.page_width = 980
        self.page_height = 1350
        self._draw = None
        self._value_writer = None

    def draw(self, draw: TkDrawer | PdfDrawer, value_writer) -> None:
        self._draw = draw
        self._value_writer = value_writer
        self._draw_sheet()

    def _draw_sheet(self) -> None:
        left = self.page_left
        top = self.page_top
        right = left + self.page_width
        bottom = top + self.page_height

        self._draw.rect(left, top, right, bottom, fill="white", outline="#333")

        header_bottom = top + 90
        self._draw.rect(left, top, right, header_bottom, fill="#e0e6f0", outline="#333")
        self._draw.text(
            left + 20,
            top + 25,
            text="ЭХОТЕКА",
            anchor="w",
            font=("Arial", 16, "bold"),
        )
        self._draw.text(
            right - 20,
            top + 25,
            text="Трансторакальная эхокг",
            anchor="e",
            font=("Arial", 12, "bold"),
        )

        title_y = header_bottom + 30
        self._draw.text(
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
        self._draw.line(left + 10, footer_y, right - 10, footer_y, fill="#333")
        self._draw.text(
            left + 20,
            footer_y + 20,
            text="Врач:",
            anchor="w",
            font=("Arial", 10, "bold"),
        )
        self._add_value("DOCTOR_NAME", left + 80, footer_y + 20, anchor="w")

    def _draw_info_block(self, left: float, top: float, right: float, bottom: float) -> None:
        self._draw.rect(left, top, right, bottom, outline="#333")

        mid_x = (left + right) / 2
        self._draw.line(mid_x, top, mid_x, bottom, fill="#333")

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
        self._draw.rect(left, top, right, bottom, outline="#333")
        self._draw.text(
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
        self._draw.rect(left, top, right, bottom, outline="#333")
        self._draw.text(
            left + 10, top + 12, text="Клапаны", anchor="w", font=("Arial", 10, "bold")
        )

        headers = ["VЕ", "Vmax", "Регург.", "Степень"]
        col_positions = [left + 160, left + 300, left + 440, left + 580]
        for header, x in zip(headers, col_positions):
            self._draw.text(x, top + 32, text=header, anchor="w", font=("Arial", 9, "bold"))

        rows = [
            ("Митральный", ["MV_VE", "MV_VMAX", "MV_REGURG", "MV_GRADE"]),
            ("Аортальный", ["AV_VMAX", "AV_GRAD", "AV_REGURG", "AV_GRADE"]),
            ("Трикусп.", ["TV_VE", "TV_VMAX", "TV_REGURG", "TV_GRADE"]),
            ("Легочный", ["PV_VMAX", "PV_GRAD", "PV_REGURG", "PV_GRADE"]),
        ]

        y = top + 52
        for label, keys in rows:
            self._draw.text(left + 10, y, text=label, anchor="w", font=("Arial", 9))
            for key, x in zip(keys, col_positions):
                self._add_value(key, x, y, anchor="w")
            y += 28

    def _draw_segments(self, left: float, top: float, width: float) -> None:
        right = left + width
        bottom = top + 230
        self._draw.rect(left, top, right, bottom, outline="#333")
        self._draw.text(
            left + 10, top + 12, text="Сегменты ЛЖ", anchor="w", font=("Arial", 10, "bold")
        )

        center_x = left + width / 2
        center_y = top + 95
        radius = 70
        self._draw.oval(
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
            self._draw.oval(x - 18, y - 18, x + 18, y + 18, outline="#333")
            self._add_value(key, x, y, anchor="center")

        bottom_y = top + 180
        start_x = left + 120
        spacing = 90
        for index, key in enumerate(SEGMENT_VARS):
            x = start_x + spacing * index
            self._draw.oval(
                x - 14, bottom_y - 14, x + 14, bottom_y + 14, outline="#333"
            )
            self._add_value(key, x, bottom_y, anchor="center")

        legend_x = right - 220
        self._draw.text(
            legend_x, bottom_y - 20, text="1 - норма", anchor="w", font=("Arial", 8)
        )
        self._draw.text(
            legend_x, bottom_y, text="2 - гипокинезия", anchor="w", font=("Arial", 8)
        )
        self._draw.text(
            legend_x, bottom_y + 20, text="3 - акинезия", anchor="w", font=("Arial", 8)
        )
        self._draw.text(
            legend_x, bottom_y + 40, text="4 - дискинезия", anchor="w", font=("Arial", 8)
        )

    def _draw_text_block(
        self, left: float, top: float, width: float, height: float, title: str, var_name: str
    ) -> None:
        right = left + width
        bottom = top + height
        self._draw.rect(left, top, right, bottom, outline="#333")
        self._draw.text(
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
        self._draw.text(x_label, y, text=label, anchor="w", font=("Arial", 9))
        self._add_value(var_name, x_value, y, anchor="w")

    def _add_value(
        self,
        var_name: str,
        x: float,
        y: float,
        anchor: str = "w",
        width: Optional[float] = None,
    ) -> None:
        self._value_writer(
            var_name,
            x,
            y,
            anchor=anchor,
            width=width,
            font=("Arial", 9, "bold"),
        )


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

        pdf_button = ttk.Button(toolbar, text="Save A4 PDF", command=self.export_pdf)
        pdf_button.pack(side="right")
        if not REPORTLAB_AVAILABLE:
            pdf_button.state(["disabled"])

        ttk.Button(toolbar, text="Refresh values", command=self.refresh).pack(
            side="right", padx=(0, 8)
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

        self.layout = SheetLayout()
        self.text_items: Dict[str, int] = {}

        self._draw_sheet()
        self.refresh()

        self.canvas.configure(
            scrollregion=(
                0,
                0,
                self.layout.page_left + self.layout.page_width + 60,
                self.layout.page_top + self.layout.page_height + 60,
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
        self.text_items = {}
        drawer = TkDrawer(self.canvas)
        self.layout.draw(drawer, self._add_value_canvas)

    def _add_value_canvas(
        self,
        var_name: str,
        x: float,
        y: float,
        anchor: str = "w",
        width: Optional[float] = None,
        font: Optional[Tuple[str, int, str]] = None,
    ) -> None:
        item_id = self.canvas.create_text(
            x,
            y,
            text=var_name,
            anchor=anchor,
            font=font or ("Arial", 9, "bold"),
            width=width,
        )
        self.text_items[var_name] = item_id

    def export_pdf(self) -> None:
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror(
                "PDF export unavailable",
                "reportlab is not installed. Install it to export A4 PDF.",
            )
            return

        filename = filedialog.asksaveasfilename(
            title="Save A4 PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not filename:
            return

        try:
            values = DEFAULT_VALUES.copy()
            values.update(compute_values())

            pdf = pdf_canvas.Canvas(filename, pagesize=A4)
            fonts = _register_pdf_fonts()
            drawer = PdfDrawer(
                pdf,
                page_size=A4,
                design_width=self.layout.page_width,
                design_height=self.layout.page_height,
                margin=24,
                fonts=fonts,
            )

            def value_writer(
                var_name: str,
                x: float,
                y: float,
                anchor: str = "w",
                width: Optional[float] = None,
                font: Optional[Tuple[str, int, str]] = None,
            ) -> None:
                value = values.get(var_name, var_name)
                drawer.text(x, y, text=str(value), anchor=anchor, font=font, width=width)

            self.layout.draw(drawer, value_writer)
            pdf.showPage()
            pdf.save()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("PDF export failed", f"Unable to export PDF:\n{exc}")


def main() -> None:
    root = tk.Tk()
    ttk.Style().theme_use("clam")
    EchoSheetApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
