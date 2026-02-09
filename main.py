from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PyQt6 import QtCore, QtGui, QtWidgets, uic
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter


@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str
    group: str
    kind: str
    placeholder: str = ""
    options: tuple[str, ...] = ()


class ReportRenderer:
    page_width_mm = 210.0
    page_height_mm = 297.0

    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    def set_data(self, data: dict[str, str]) -> None:
        self.data = dict(data)

    def draw(
        self,
        painter: QtGui.QPainter,
        target_rect: QtCore.QRectF,
        dpi_x: float,
        dpi_y: float,
    ) -> None:
        dpi = min(dpi_x, dpi_y)
        px_per_mm = dpi / 25.4
        page_px_w = self.page_width_mm * px_per_mm
        page_px_h = self.page_height_mm * px_per_mm

        scale = min(
            target_rect.width() / page_px_w,
            target_rect.height() / page_px_h,
        )
        scale_px_per_mm = px_per_mm * scale

        page_w_px = page_px_w * scale
        page_h_px = page_px_h * scale
        origin_x = target_rect.x() + (target_rect.width() - page_w_px) / 2.0
        origin_y = target_rect.y() + (target_rect.height() - page_h_px) / 2.0
        page_rect = QtCore.QRectF(origin_x, origin_y, page_w_px, page_h_px)

        painter.save()
        painter.setPen(QtGui.QPen(QtGui.QColor("#404040"), 1))
        painter.setBrush(QtGui.QColor("white"))
        painter.drawRect(page_rect)
        painter.setClipRect(page_rect)
        self._draw_content(painter, origin_x, origin_y, scale_px_per_mm, scale)
        painter.restore()

    def _value(self, key: str) -> str:
        value = str(self.data.get(key, "")).strip()
        return value if value else "—"

    def _font_mm(self, mm_size: float, scale: float, bold: bool = False) -> QtGui.QFont:
        point_size = mm_size * 72.0 / 25.4 * scale
        font = QtGui.QFont("Arial")
        font.setPointSizeF(point_size)
        font.setBold(bold)
        return font

    def _draw_content(
        self,
        painter: QtGui.QPainter,
        origin_x: float,
        origin_y: float,
        scale_px_per_mm: float,
        scale: float,
    ) -> None:
        def mm_rect(x_mm: float, y_mm: float, w_mm: float, h_mm: float) -> QtCore.QRectF:
            return QtCore.QRectF(
                origin_x + x_mm * scale_px_per_mm,
                origin_y + y_mm * scale_px_per_mm,
                w_mm * scale_px_per_mm,
                h_mm * scale_px_per_mm,
            )

        def draw_text(
            x_mm: float,
            y_mm: float,
            w_mm: float,
            h_mm: float,
            text: str,
            font_mm: float = 3.2,
            bold: bool = False,
            align: QtCore.Qt.TextFlag = QtCore.Qt.TextFlag.AlignLeft
            | QtCore.Qt.TextFlag.AlignVCenter,
        ) -> None:
            painter.save()
            painter.setFont(self._font_mm(font_mm, scale, bold))
            painter.setPen(QtGui.QColor("#202020"))
            painter.drawText(mm_rect(x_mm, y_mm, w_mm, h_mm), align, text)
            painter.restore()

        def draw_line(y_mm: float) -> None:
            painter.save()
            painter.setPen(QtGui.QPen(QtGui.QColor("#909090"), 1))
            painter.drawLine(
                mm_rect(margin_mm, y_mm, usable_w_mm, 0).topLeft(),
                mm_rect(margin_mm, y_mm, usable_w_mm, 0).topRight(),
            )
            painter.restore()

        def line_text(label: str, key: str, unit: str | None = None) -> str:
            value = self._value(key)
            if unit and value != "—":
                return f"{label}: {value} {unit}"
            return f"{label}: {value}"

        def draw_single_line(y_mm: float, label: str, key: str, unit: str | None = None) -> float:
            draw_text(margin_mm, y_mm, usable_w_mm, line_h_mm, line_text(label, key, unit))
            return y_mm + line_h_mm

        def draw_pair_line(
            y_mm: float,
            left: tuple[str, str, str | None],
            right: tuple[str, str, str | None],
        ) -> float:
            gap_mm = 6.0
            col_w_mm = (usable_w_mm - gap_mm) / 2.0
            draw_text(margin_mm, y_mm, col_w_mm, line_h_mm, line_text(*left))
            draw_text(
                margin_mm + col_w_mm + gap_mm,
                y_mm,
                col_w_mm,
                line_h_mm,
                line_text(*right),
            )
            return y_mm + line_h_mm

        def draw_section(y_mm: float, title: str) -> float:
            draw_text(margin_mm, y_mm, usable_w_mm, line_h_mm, title, font_mm=3.6, bold=True)
            return y_mm + line_h_mm

        def draw_text_block(y_mm: float, title: str, key: str, height_mm: float) -> float:
            y_mm = draw_section(y_mm, title)
            box = mm_rect(margin_mm, y_mm, usable_w_mm, height_mm)
            painter.save()
            painter.setPen(QtGui.QPen(QtGui.QColor("#909090"), 1))
            painter.drawRect(box)
            painter.restore()
            inset = 2.0
            draw_text(
                margin_mm + inset,
                y_mm + inset,
                usable_w_mm - inset * 2,
                height_mm - inset * 2,
                self._value(key),
                font_mm=3.0,
                align=QtCore.Qt.TextFlag.AlignLeft
                | QtCore.Qt.TextFlag.AlignTop
                | QtCore.Qt.TextFlag.TextWordWrap,
            )
            return y_mm + height_mm

        margin_mm = 12.0
        usable_w_mm = self.page_width_mm - margin_mm * 2.0
        line_h_mm = 6.0
        y_mm = margin_mm

        draw_text(
            margin_mm,
            y_mm,
            usable_w_mm,
            line_h_mm,
            "ТРАНСТОРАКАЛЬНАЯ ЭХОКАРДИОГРАММА",
            font_mm=5.0,
            bold=True,
            align=QtCore.Qt.TextFlag.AlignCenter | QtCore.Qt.TextFlag.AlignVCenter,
        )
        y_mm += line_h_mm + 2.0
        draw_text(
            margin_mm,
            y_mm,
            usable_w_mm,
            line_h_mm,
            f"ОТ {self._value('report_date')}",
            font_mm=3.6,
            bold=True,
            align=QtCore.Qt.TextFlag.AlignCenter | QtCore.Qt.TextFlag.AlignVCenter,
        )
        y_mm += line_h_mm + 2.0
        draw_line(y_mm)
        y_mm += 4.0

        y_mm = draw_section(y_mm, "Пациент")
        y_mm = draw_single_line(y_mm, "ФИО", "patient_name")
        y_mm = draw_pair_line(
            y_mm,
            ("Возраст", "age", "лет"),
            ("Пол", "sex", None),
        )
        y_mm = draw_single_line(y_mm, "Диагноз", "diagnosis")
        y_mm = draw_single_line(y_mm, "Направление", "referral")
        y_mm = draw_pair_line(
            y_mm,
            ("Ритм", "rhythm", None),
            ("Частота", "heart_rate", "уд/мин"),
        )
        y_mm = draw_single_line(y_mm, "Площадь тела", "bsa", "м кв.")

        y_mm += 2.0
        draw_line(y_mm)
        y_mm += 4.0

        y_mm = draw_section(y_mm, "Размеры и объемы")
        y_mm = draw_pair_line(
            y_mm,
            ("ЛЖ КДР", "lv_edd", "мм"),
            ("ЛЖ КСР", "lv_esd", "мм"),
        )
        y_mm = draw_pair_line(
            y_mm,
            ("МЖП", "ivs", "мм"),
            ("ЗСЛЖ", "pw", "мм"),
        )
        y_mm = draw_pair_line(
            y_mm,
            ("КДО", "edv", "мл"),
            ("КСО", "esv", "мл"),
        )
        y_mm = draw_pair_line(
            y_mm,
            ("ФВ", "ef", "%"),
            ("Масса ЛЖ", "lv_mass", "г"),
        )
        y_mm = draw_pair_line(
            y_mm,
            ("ПЖ", "rv_size", "мм"),
            ("ЛП", "la_size", "мм"),
        )
        y_mm = draw_pair_line(
            y_mm,
            ("ПП", "ra_size", "мм"),
            ("Аорта корень", "aorta_root", "мм"),
        )
        y_mm = draw_pair_line(
            y_mm,
            ("Аорта восх.", "asc_aorta", "мм"),
            ("ЛА", "pulm_artery", "мм"),
        )

        y_mm += 2.0
        draw_line(y_mm)
        y_mm += 4.0

        y_mm = draw_section(y_mm, "Клапаны")
        y_mm = draw_pair_line(
            y_mm,
            ("Митральный градиент", "mitral_grad", "мм рт. ст."),
            ("Регургитация", "mitral_regurg", None),
        )
        y_mm = draw_pair_line(
            y_mm,
            ("Аортальный градиент", "aortic_grad", "мм рт. ст."),
            ("Регургитация", "aortic_regurg", None),
        )
        y_mm = draw_pair_line(
            y_mm,
            ("Трикуспидальная регургитация", "tricuspid_regurg", None),
            ("Давление ЛА", "pulm_pressure", "мм рт. ст."),
        )

        y_mm += 2.0
        draw_line(y_mm)
        y_mm += 4.0

        y_mm = draw_text_block(y_mm, "Сегменты", "segment_summary", 18.0)
        y_mm += 4.0
        draw_line(y_mm)
        y_mm += 4.0

        y_mm = draw_text_block(y_mm, "Описание", "description", 38.0)
        y_mm += 4.0
        draw_line(y_mm)
        y_mm += 4.0

        y_mm = draw_text_block(y_mm, "Заключение", "conclusion", 22.0)
        y_mm += 6.0

        draw_text(
            margin_mm,
            y_mm,
            usable_w_mm,
            line_h_mm,
            f"Врач: {self._value('doctor')}",
            font_mm=3.2,
        )


class ReportPageWidget(QtWidgets.QWidget):
    def __init__(self, renderer: ReportRenderer, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.renderer = renderer
        self.setMinimumSize(600, 800)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QtGui.QColor("#e6e6e6"))
        self.renderer.draw(
            painter,
            QtCore.QRectF(self.rect()),
            self.logicalDpiX(),
            self.logicalDpiY(),
        )

    def draw_to_painter(
        self,
        painter: QtGui.QPainter,
        target_rect: QtCore.QRectF,
        dpi_x: float,
        dpi_y: float,
    ) -> None:
        self.renderer.draw(painter, target_rect, dpi_x, dpi_y)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        ui_path = Path(__file__).resolve().parent / "ui" / "main_window.ui"
        uic.loadUi(ui_path.as_posix(), self)

        self.renderer = ReportRenderer()
        self.page_widget = ReportPageWidget(self.renderer, self)
        self.pageLayout.addWidget(self.page_widget)

        self.inputs: dict[str, QtWidgets.QWidget] = {}
        self.data: dict[str, str] = {}
        self._build_form()
        self._connect_print()
        self._sync_from_widgets()

    def _field_specs(self) -> Iterable[FieldSpec]:
        return [
            FieldSpec("report_date", "Дата исследования", "Общее", "date"),
            FieldSpec("patient_name", "ФИО", "Общее", "line"),
            FieldSpec("age", "Возраст", "Общее", "line"),
            FieldSpec("sex", "Пол", "Общее", "combo", options=("—", "мужской", "женский")),
            FieldSpec("diagnosis", "Диагноз", "Общее", "line"),
            FieldSpec("referral", "Направление", "Общее", "line"),
            FieldSpec("rhythm", "Ритм", "Общее", "line"),
            FieldSpec("heart_rate", "Частота, уд/мин", "Общее", "line"),
            FieldSpec("bsa", "Площадь тела, м кв.", "Общее", "line"),
            FieldSpec("lv_edd", "ЛЖ КДР, мм", "Размеры и объемы", "line"),
            FieldSpec("lv_esd", "ЛЖ КСР, мм", "Размеры и объемы", "line"),
            FieldSpec("ivs", "МЖП, мм", "Размеры и объемы", "line"),
            FieldSpec("pw", "ЗСЛЖ, мм", "Размеры и объемы", "line"),
            FieldSpec("edv", "КДО, мл", "Размеры и объемы", "line"),
            FieldSpec("esv", "КСО, мл", "Размеры и объемы", "line"),
            FieldSpec("ef", "ФВ, %", "Размеры и объемы", "line"),
            FieldSpec("lv_mass", "Масса ЛЖ, г", "Размеры и объемы", "line"),
            FieldSpec("rv_size", "ПЖ, мм", "Размеры и объемы", "line"),
            FieldSpec("la_size", "ЛП, мм", "Размеры и объемы", "line"),
            FieldSpec("ra_size", "ПП, мм", "Размеры и объемы", "line"),
            FieldSpec("aorta_root", "Аорта корень, мм", "Размеры и объемы", "line"),
            FieldSpec("asc_aorta", "Аорта восх., мм", "Размеры и объемы", "line"),
            FieldSpec("pulm_artery", "ЛА, мм", "Размеры и объемы", "line"),
            FieldSpec("mitral_grad", "Митральный градиент", "Клапаны", "line"),
            FieldSpec("mitral_regurg", "Митральная регургитация", "Клапаны", "line"),
            FieldSpec("aortic_grad", "Аортальный градиент", "Клапаны", "line"),
            FieldSpec("aortic_regurg", "Аортальная регургитация", "Клапаны", "line"),
            FieldSpec("tricuspid_regurg", "Трикуспидальная регургитация", "Клапаны", "line"),
            FieldSpec("pulm_pressure", "Давление ЛА", "Клапаны", "line"),
            FieldSpec("segment_summary", "Сегменты", "Текст", "multi"),
            FieldSpec("description", "Описание", "Текст", "multi"),
            FieldSpec("conclusion", "Заключение", "Текст", "multi"),
            FieldSpec("doctor", "Врач", "Текст", "line"),
        ]

    def _build_form(self) -> None:
        group_boxes: dict[str, QtWidgets.QGroupBox] = {}
        group_layouts: dict[str, QtWidgets.QFormLayout] = {}

        for spec in self._field_specs():
            if spec.group not in group_boxes:
                box = QtWidgets.QGroupBox(spec.group)
                layout = QtWidgets.QFormLayout()
                layout.setFieldGrowthPolicy(
                    QtWidgets.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
                )
                box.setLayout(layout)
                self.formLayout.addWidget(box)
                group_boxes[spec.group] = box
                group_layouts[spec.group] = layout

            widget = self._make_widget(spec)
            self.inputs[spec.key] = widget
            group_layouts[spec.group].addRow(spec.label, widget)

        self.formLayout.addStretch(1)

    def _make_widget(self, spec: FieldSpec) -> QtWidgets.QWidget:
        if spec.kind == "date":
            widget = QtWidgets.QDateEdit()
            widget.setCalendarPopup(True)
            widget.setDate(QtCore.QDate.currentDate())
            widget.dateChanged.connect(
                lambda date, k=spec.key: self._update_data(k, date.toString("dd.MM.yyyy"))
            )
            return widget

        if spec.kind == "combo":
            widget = QtWidgets.QComboBox()
            widget.addItems(list(spec.options))
            widget.currentTextChanged.connect(
                lambda text, k=spec.key: self._update_data(k, text)
            )
            return widget

        if spec.kind == "multi":
            widget = QtWidgets.QPlainTextEdit()
            widget.setMinimumHeight(90)
            widget.textChanged.connect(
                lambda k=spec.key, w=widget: self._update_data(k, w.toPlainText())
            )
            return widget

        widget = QtWidgets.QLineEdit()
        if spec.placeholder:
            widget.setPlaceholderText(spec.placeholder)
        widget.textChanged.connect(lambda text, k=spec.key: self._update_data(k, text))
        return widget

    def _sync_from_widgets(self) -> None:
        for key, widget in self.inputs.items():
            if isinstance(widget, QtWidgets.QLineEdit):
                self._update_data(key, widget.text())
            elif isinstance(widget, QtWidgets.QPlainTextEdit):
                self._update_data(key, widget.toPlainText())
            elif isinstance(widget, QtWidgets.QDateEdit):
                self._update_data(key, widget.date().toString("dd.MM.yyyy"))
            elif isinstance(widget, QtWidgets.QComboBox):
                self._update_data(key, widget.currentText())

    def _update_data(self, key: str, value: str) -> None:
        self.data[key] = value
        self.renderer.set_data(self.data)
        self.page_widget.update()

    def _connect_print(self) -> None:
        self.printButton.clicked.connect(self._print_report)

    def _print_report(self) -> None:
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QtGui.QPageSize(QtGui.QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QtGui.QPageLayout.Orientation.Portrait)

        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        painter = QtGui.QPainter(printer)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        page_rect = QtCore.QRectF(printer.pageRect(QPrinter.Unit.DevicePixel))
        self.page_widget.draw_to_painter(
            painter, page_rect, printer.logicalDpiX(), printer.logicalDpiY()
        )
        painter.end()


def main() -> None:
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
