"""Redeemed_3D FDM Conversion Calculators — PySide6 port with Redeemed Engineering dark theme."""

from __future__ import annotations

import json
import math
import os
import re
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QDoubleValidator, QFont, QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

MM_PER_INCH = 25.4

# ── Palette (mirrors thread calculator) ──────────────────────────────────────
BACKGROUND = "#10141C"
PANEL      = "#171C26"
PANEL_ALT  = "#1D2430"
BORDER     = "#2A3444"
TEXT       = "#EAF1FF"
MUTED      = "#9BA9C0"
ACCENT     = "#5AA9FF"
SUCCESS    = "#5FD1A3"
WARNING    = "#FFBF69"
ERROR      = "#FF7B88"

APP_TITLE  = "Redeemed_3D FDM Conversion Calculators"

STYLESHEET = f"""
QWidget {{
    background: {BACKGROUND};
    color: {TEXT};
    font-family: "Segoe UI", "SF Pro Text", "Noto Sans", sans-serif;
    font-size: 10pt;
}}
QMainWindow {{
    background: {BACKGROUND};
}}

/* ── Cards ── */
QFrame#card {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 18px;
}}
QLabel#cardTitle {{
    font-size: 13px;
    font-weight: 700;
    color: {TEXT};
}}
QLabel#cardDescription {{
    color: {MUTED};
    font-size: 9pt;
}}

/* ── Section headings ── */
QLabel#h1 {{
    font-size: 20px;
    font-weight: 700;
}}
QLabel#h2 {{
    font-size: 13px;
    font-weight: 700;
}}

/* ── Field labels & helpers ── */
QLabel#fieldLabel {{
    font-size: 10px;
    font-weight: 600;
    color: {MUTED};
}}
QLabel#fieldHelper {{
    font-size: 9pt;
    color: {MUTED};
}}

/* ── Result rows ── */
QFrame#resultRow {{
    background: {PANEL_ALT};
    border: 1px solid {BORDER};
    border-radius: 14px;
}}
QLabel#resultKey {{
    font-size: 10px;
    font-weight: 600;
    color: {MUTED};
}}
QLabel#resultValue {{
    font-size: 13px;
    font-weight: 700;
    color: {TEXT};
}}

/* ── Metric tiles ── */
QFrame#metricTile {{
    background: {PANEL_ALT};
    border: 1px solid {BORDER};
    border-radius: 14px;
}}
QLabel#metricTileTitle {{
    font-size: 10px;
    font-weight: 600;
    color: {MUTED};
}}
QLabel#metricTileValue {{
    font-size: 15px;
    font-weight: 700;
    color: {TEXT};
}}

/* ── Inputs ── */
QLineEdit {{
    background: {PANEL_ALT};
    border: 1px solid {BORDER};
    border-radius: 10px;
    min-height: 40px;
    padding: 6px 10px;
    color: {TEXT};
    selection-background-color: {ACCENT};
    selection-color: #09111E;
}}
QLineEdit:hover {{ border-color: #3A4A61; }}
QLineEdit:focus {{ border: 1px solid {ACCENT}; }}
QLineEdit[invalid="true"] {{
    border: 1px solid {ERROR};
    background: #23171D;
}}

/* ── Buttons ── */
QPushButton {{
    background: {PANEL_ALT};
    border: 1px solid {BORDER};
    border-radius: 10px;
    min-height: 38px;
    min-width: 80px;
    padding: 6px 16px;
    font-weight: 600;
    font-size: 10pt;
    color: {TEXT};
    text-align: center;
}}
QPushButton:hover {{
    border-color: #4A5D77;
    background: #232D3A;
}}
QPushButton:pressed {{ background: #1A222D; }}
QPushButton#accentButton {{
    background: {ACCENT};
    color: #FFFFFF;
    border: 1px solid {ACCENT};
    min-width: 100px;
}}
QPushButton#accentButton:hover {{ background: #7AB9FF; color: #FFFFFF; }}
QPushButton#accentButton:disabled {{ background: #3A5A80; color: #FFFFFF; }}
QPushButton#successButton {{
    background: {PANEL_ALT};
    color: {SUCCESS};
    border: 1px solid {SUCCESS};
}}

/* ── Status label ── */
QLabel#statusLabel {{
    color: {ERROR};
    font-size: 9pt;
}}

/* ── Results block ── */
QLabel#resultsBlock {{
    background: {PANEL_ALT};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 10px 12px;
    color: {TEXT};
}}

/* ── Divider ── */
QFrame#divider {{
    background: {BORDER};
    max-height: 1px;
    border: none;
}}
"""


# ── Reusable widgets ──────────────────────────────────────────────────────────

class CardFrame(QFrame):
    """Rounded panel card matching the thread calculator style."""

    def __init__(self, title: str = "", description: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.content_layout = QVBoxLayout(self)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(12)

        if title:
            header = QVBoxLayout()
            header.setSpacing(3)
            title_label = QLabel(title)
            title_label.setObjectName("cardTitle")
            header.addWidget(title_label)
            if description:
                desc_label = QLabel(description)
                desc_label.setObjectName("cardDescription")
                desc_label.setWordWrap(True)
                header.addWidget(desc_label)
            self.content_layout.addLayout(header)


class LabeledInput(QWidget):
    """Label + QLineEdit + optional helper text."""

    def __init__(self, label_text: str, helper_text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.label = QLabel(label_text)
        self.label.setObjectName("fieldLabel")
        self.input = QLineEdit()
        self.input.setMinimumHeight(40)
        self.input.setClearButtonEnabled(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self.label)
        layout.addWidget(self.input)

        if helper_text:
            helper = QLabel(helper_text)
            helper.setObjectName("fieldHelper")
            helper.setWordWrap(True)
            layout.addWidget(helper)

    def set_error(self, has_error: bool) -> None:
        self.input.setProperty("invalid", has_error)
        self.input.style().unpolish(self.input)
        self.input.style().polish(self.input)


class ResultRow(QFrame):
    """Dark tile showing a key → value pair."""

    def __init__(self, key: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("resultRow")

        self._key_label = QLabel(key)
        self._key_label.setObjectName("resultKey")
        self._value_label = QLabel("—")
        self._value_label.setObjectName("resultValue")
        self._value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._value_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(1)
        layout.addWidget(self._key_label)
        layout.addWidget(self._value_label)

    def set_value(self, text: str) -> None:
        self._value_label.setText(text)

    def reset(self) -> None:
        self._value_label.setText("—")


class MetricTile(QFrame):
    """Small info tile (2-up grid)."""

    def __init__(self, title: str, value: str = "—", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("metricTile")
        self.setMinimumHeight(80)

        self._title_label = QLabel(title)
        self._title_label.setObjectName("metricTileTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("metricTileValue")
        self.value_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        layout.addWidget(self._title_label)
        layout.addWidget(self.value_label)


def _divider() -> QFrame:
    line = QFrame()
    line.setObjectName("divider")
    line.setFixedHeight(1)
    line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    return line


# ── Main window ───────────────────────────────────────────────────────────────

class ConversionWidget(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        self._feedback_timers: dict[QPushButton, QTimer] = {}
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._save_geometry)

        self._active_source: str | None = None

        self._build_ui()
        self._apply_fonts()
        self.setStyleSheet(STYLESHEET)
        self._connect_signals()
        self._restore_or_position()
        # Force style re-polish so objectName-based rules apply correctly on Windows
        for btn in self.findChildren(QPushButton):
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.update()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(16)

        root_layout.addWidget(self._build_header())

        # ── Scrollable content area ───────────────────────────────────────────
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollBar:vertical { background: #171C26; width: 8px; border-radius: 4px; }"
            "QScrollBar::handle:vertical { background: #2A3444; border-radius: 4px; min-height: 20px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
            "QScrollBar:horizontal { background: #171C26; height: 8px; border-radius: 4px; }"
            "QScrollBar::handle:horizontal { background: #2A3444; border-radius: 4px; min-width: 20px; }"
            "QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }"
        )

        scroll_contents = QWidget()
        scroll_contents.setStyleSheet("background: transparent;")
        columns = QHBoxLayout(scroll_contents)
        columns.setContentsMargins(0, 0, 0, 0)
        columns.setSpacing(16)

        left   = self._build_left_column()
        middle = self._build_middle_column()
        right  = self._build_right_column()

        # Give each column equal stretch so they share space evenly
        columns.addWidget(left,   1)
        columns.addWidget(middle, 1)
        columns.addWidget(right,  1)

        scroll_area.setWidget(scroll_contents)
        root_layout.addWidget(scroll_area, 1)

        self.setCentralWidget(root)

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("card")
        layout = QVBoxLayout(header)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(4)
        title = QLabel(APP_TITLE)
        title.setObjectName("h1")
        subtitle = QLabel("Unit conversion, quick calculator, and slicer design calculators. For use in CAD to help optimize designs for FDM printing.")
        subtitle.setObjectName("cardDescription")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        return header

    def _build_left_column(self) -> QWidget:
        card = CardFrame("MM ↔ Inch Conversion")
        card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)

        # ── MM input ──────────────────────────────────────────────────────────
        self.mm_input = LabeledInput("Millimeters (mm)")
        self.mm_input.input.setPlaceholderText("e.g. 25.4")
        num_validator = QDoubleValidator()
        num_validator.setNotation(QDoubleValidator.StandardNotation)
        self.mm_input.input.setValidator(num_validator)

        mm_row = QHBoxLayout()
        mm_row.setSpacing(8)
        mm_row.addWidget(self.mm_input, 1)
        self.copy_mm_btn = QPushButton("Copy")
        self.copy_mm_btn.setMinimumWidth(72)
        mm_row.addWidget(self.copy_mm_btn, 0, Qt.AlignBottom)
        card.content_layout.addLayout(mm_row)

        # ── Inch input ────────────────────────────────────────────────────────
        self.inch_input = LabeledInput("Inches (in)", "Accepts decimal, fraction (1/4), or mixed (1 1/4).")
        self.inch_input.input.setPlaceholderText("e.g. 1, 1/4, 1 3/8")

        inch_row = QHBoxLayout()
        inch_row.setSpacing(8)
        inch_row.addWidget(self.inch_input, 1)
        self.copy_inch_btn = QPushButton("Copy")
        self.copy_inch_btn.setMinimumWidth(72)
        inch_row.addWidget(self.copy_inch_btn, 0, Qt.AlignBottom)
        card.content_layout.addLayout(inch_row)

        # ── Display tiles ─────────────────────────────────────────────────────
        tiles_grid = QGridLayout()
        tiles_grid.setSpacing(8)
        self.tile_decimal = MetricTile("Inch decimal", "—")
        self.tile_fraction = MetricTile("Inch fraction", "—")
        tiles_grid.addWidget(self.tile_decimal, 0, 0)
        tiles_grid.addWidget(self.tile_fraction, 0, 1)
        card.content_layout.addLayout(tiles_grid)

        # ── Status ────────────────────────────────────────────────────────────
        self.converter_status = QLabel("")
        self.converter_status.setObjectName("statusLabel")
        self.converter_status.setWordWrap(True)
        card.content_layout.addWidget(self.converter_status)

        card.content_layout.addWidget(_divider())

        # ── Quick calculator ──────────────────────────────────────────────────
        calc_heading = QLabel("Quick Calculator")
        calc_heading.setObjectName("h2")
        card.content_layout.addWidget(calc_heading)

        self.calc_input = LabeledInput("Expression", "Arithmetic only: + − × ÷ ( )")
        self.calc_input.input.setPlaceholderText("e.g. 12.5 * 3 / 25.4")
        card.content_layout.addWidget(self.calc_input)

        self.calc_result_row = ResultRow("Result")
        card.content_layout.addWidget(self.calc_result_row)

        calc_btns = QHBoxLayout()
        calc_btns.setSpacing(8)
        self.copy_result_btn = QPushButton("Copy")
        self.copy_result_btn.setObjectName("accentButton")
        self.clear_calc_btn = QPushButton("Clear")
        calc_btns.addWidget(self.copy_result_btn)
        calc_btns.addWidget(self.clear_calc_btn)
        calc_btns.addStretch(1)
        card.content_layout.addLayout(calc_btns)

        card.content_layout.addStretch(1)
        return card

    def _build_middle_column(self) -> QWidget:
        col = QWidget()
        col.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        layout = QVBoxLayout(col)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # ── Layer height Calculator ─────────────────────────────────────────────
        layer_card = CardFrame(
            "Layer Height Calculator",
            "Find the nearest layer-friendly height for your target dimension.",
        )
        layer_inputs = QHBoxLayout()
        layer_inputs.setSpacing(10)
        self.layer_target_input = LabeledInput("Desired height (mm)")
        self.layer_target_input.input.setPlaceholderText("e.g. 3.0")
        self.layer_height_input = LabeledInput("Layer height (mm)")
        self.layer_height_input.input.setPlaceholderText("e.g. 0.2")
        layer_inputs.addWidget(self.layer_target_input)
        layer_inputs.addWidget(self.layer_height_input)
        layer_card.content_layout.addLayout(layer_inputs)

        self.layer_calc_btn = QPushButton("Calculate")
        self.layer_calc_btn.setObjectName("accentButton")
        layer_card.content_layout.addWidget(self.layer_calc_btn)

        self.layer_results_label = QLabel(
            "Exact layer count: —\nNearest clean multiple: —\nLower option: —\nSnap-up option: —"
        )
        self.layer_results_label.setObjectName("resultsBlock")
        self.layer_results_label.setWordWrap(True)
        self.layer_results_label.setMinimumHeight(90)
        layer_card.content_layout.addWidget(self.layer_results_label)

        layout.addWidget(layer_card)

        # ── Wall Count Calculator ─────────────────────────────────────────────────
        wall_card = CardFrame(
            "Wall Count Calculator",
            "Find the number of perimeters closest to your target wall thickness.",
        )
        wall_inputs = QHBoxLayout()
        wall_inputs.setSpacing(10)
        self.wall_target_input = LabeledInput("Target wall thickness (mm)")
        self.wall_target_input.input.setPlaceholderText("e.g. 1.6")
        self.line_width_input = LabeledInput("Line width (mm)")
        self.line_width_input.input.setPlaceholderText("e.g. 0.4")
        wall_inputs.addWidget(self.wall_target_input)
        wall_inputs.addWidget(self.line_width_input)
        wall_card.content_layout.addLayout(wall_inputs)

        self.wall_calc_btn = QPushButton("Calculate")
        self.wall_calc_btn.setObjectName("accentButton")
        wall_card.content_layout.addWidget(self.wall_calc_btn)

        self.wall_results_label = QLabel(
            "Exact wall count: —\nNearest printable thickness: —\nLower option: —\nSnap-up option: —"
        )
        self.wall_results_label.setObjectName("resultsBlock")
        self.wall_results_label.setWordWrap(True)
        self.wall_results_label.setMinimumHeight(90)
        wall_card.content_layout.addWidget(self.wall_results_label)

        layout.addWidget(wall_card)
        layout.addStretch(1)
        return col

    def _build_right_column(self) -> QWidget:
        card = CardFrame(
            "CAD Dimension Calculator",
            "Recalcualte your target dimensions to the nearest printable multiple of your layer height and line width.",
        )
        card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        self.snap_length_input    = LabeledInput("Desired length (mm)")
        self.snap_width_input     = LabeledInput("Desired width (mm)")
        self.snap_height_input    = LabeledInput("Desired height (mm)")
        self.snap_nozzle_input    = LabeledInput("Nozzle size (mm)")
        self.snap_layer_input     = LabeledInput("Layer height (mm)")
        self.snap_linewidth_input = LabeledInput("Line width (mm)")

        for w in (self.snap_length_input, self.snap_width_input, self.snap_height_input,
                  self.snap_nozzle_input, self.snap_layer_input, self.snap_linewidth_input):
            w.input.setPlaceholderText("mm")

        grid.addWidget(self.snap_length_input,    0, 0)
        grid.addWidget(self.snap_width_input,     0, 1)
        grid.addWidget(self.snap_height_input,    1, 0)
        grid.addWidget(self.snap_nozzle_input,    1, 1)
        grid.addWidget(self.snap_layer_input,     2, 0)
        grid.addWidget(self.snap_linewidth_input, 2, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        card.content_layout.addLayout(grid)

        self.snap_calc_btn = QPushButton("Calculate")
        self.snap_calc_btn.setObjectName("accentButton")
        card.content_layout.addWidget(self.snap_calc_btn)

        self.snap_summary_tile = MetricTile("Settings", "—")
        card.content_layout.addWidget(self.snap_summary_tile)

        snap_results_grid = QGridLayout()
        snap_results_grid.setSpacing(8)
        self.snap_length_row = ResultRow("Length snap")
        self.snap_width_row  = ResultRow("Width snap")
        self.snap_height_row = ResultRow("Height snap")
        snap_results_grid.addWidget(self.snap_length_row, 0, 0)
        snap_results_grid.addWidget(self.snap_width_row,  0, 1)
        snap_results_grid.addWidget(self.snap_height_row, 1, 0, 1, 2)
        snap_results_grid.setColumnStretch(0, 1)
        snap_results_grid.setColumnStretch(1, 1)
        card.content_layout.addLayout(snap_results_grid)

        card.content_layout.addStretch(1)
        return card

    # ── Theme / fonts ─────────────────────────────────────────────────────────

    def _apply_fonts(self) -> None:
        families = {f.lower(): f for f in QFontDatabase.families()}
        preferred = next(
            (families[n] for n in ("inter", "segoe ui", "sf pro text", "noto sans") if n in families),
            None,
        )
        if preferred:
            QApplication.instance().setFont(QFont(preferred, 10))

    # ── Signal wiring ─────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self.mm_input.input.textChanged.connect(self._on_mm_changed)
        self.inch_input.input.textChanged.connect(self._on_inch_changed)
        self.copy_mm_btn.clicked.connect(self._copy_mm)
        self.copy_inch_btn.clicked.connect(self._copy_inches)

        self.calc_input.input.textChanged.connect(self._on_calc_changed)
        self.copy_result_btn.clicked.connect(self._copy_result)
        self.clear_calc_btn.clicked.connect(self._clear_calc)

        self.layer_calc_btn.clicked.connect(self._calculate_layer)
        self.wall_calc_btn.clicked.connect(self._calculate_wall)
        self.snap_calc_btn.clicked.connect(self._calculate_snap)

    # ── Converter logic ───────────────────────────────────────────────────────

    def _on_mm_changed(self, text: str) -> None:
        if self._active_source == "inch":
            return
        self._active_source = "mm"
        raw = text.strip()
        if not raw:
            self.inch_input.input.clear()
            self._set_inch_display(None)
            self.converter_status.setText("")
            self.mm_input.set_error(False)
            self._active_source = None
            return
        try:
            mm = float(raw)
        except ValueError:
            self.converter_status.setText("Enter a valid millimeter number.")
            self.mm_input.set_error(True)
            self._active_source = None
            return
        self.mm_input.set_error(False)
        inches = mm / MM_PER_INCH
        self.inch_input.input.setText(self._fmt(inches))
        self._set_inch_display(inches)
        self.converter_status.setText("")
        self._active_source = None

    def _on_inch_changed(self, text: str) -> None:
        if self._active_source == "mm":
            return
        self._active_source = "inch"
        inches = self._parse_inches(text)
        if inches is None:
            self.mm_input.input.clear()
            self._set_inch_display(None)
            self.converter_status.setText("")
            self.inch_input.set_error(False)
            self._active_source = None
            return
        if math.isnan(inches):
            self.converter_status.setText("Use decimal, fraction (1/4), or mixed fraction (1 1/4).")
            self.inch_input.set_error(True)
            self._active_source = None
            return
        self.inch_input.set_error(False)
        self.mm_input.input.setText(self._fmt(inches * MM_PER_INCH))
        self._set_inch_display(inches)
        self.converter_status.setText("")
        self._active_source = None

    def _set_inch_display(self, inches: float | None) -> None:
        if inches is None:
            self.tile_decimal.value_label.setText("—")
            self.tile_fraction.value_label.setText("—")
        else:
            self.tile_decimal.value_label.setText(self._fmt(inches))
            self.tile_fraction.value_label.setText(self._to_mixed_fraction(inches))

    # ── Calculator logic ──────────────────────────────────────────────────────

    def _on_calc_changed(self, text: str) -> None:
        result, error = self._evaluate_expression(text)
        if result is None and error is None:
            self.calc_result_row.set_value("—")
        elif error:
            self.calc_result_row.set_value(error)
        else:
            self.calc_result_row.set_value(self._fmt(result, 10))

    def _clear_calc(self) -> None:
        self.calc_input.input.clear()
        self.calc_result_row.reset()

    # ── Layer helper ──────────────────────────────────────────────────────────

    def _calculate_layer(self) -> None:
        target = self._parse_positive(self.layer_target_input.input.text())
        layer  = self._parse_positive(self.layer_height_input.input.text())
        self.layer_target_input.set_error(math.isnan(target))
        self.layer_height_input.set_error(math.isnan(layer))
        if math.isnan(target) or math.isnan(layer):
            self.layer_results_label.setText("Please enter valid positive values for both fields.")
            return

        exact   = target / layer
        lower   = max(1, math.floor(exact))
        upper   = max(1, math.ceil(exact))
        nearest = max(1, round(exact))

        self.layer_results_label.setText(
            f"Exact layer count: {self._fmt(exact, 4)}\n"
            f"Nearest clean multiple: {self._fmt(nearest * layer, 4)} mm ({nearest} layers)\n"
            f"Lower option: {lower} layers = {self._fmt(lower * layer, 4)} mm\n"
            f"Snap-up option: {upper} layers = {self._fmt(upper * layer, 4)} mm"
        )

    # ── Wall helper ───────────────────────────────────────────────────────────

    def _calculate_wall(self) -> None:
        target     = self._parse_positive(self.wall_target_input.input.text())
        line_width = self._parse_positive(self.line_width_input.input.text())
        self.wall_target_input.set_error(math.isnan(target))
        self.line_width_input.set_error(math.isnan(line_width))
        if math.isnan(target) or math.isnan(line_width):
            self.wall_results_label.setText("Please enter valid positive values for both fields.")
            return

        exact   = target / line_width
        lower   = max(1, math.floor(exact))
        upper   = max(1, math.ceil(exact))
        nearest = max(1, round(exact))

        self.wall_results_label.setText(
            f"Exact wall count: {self._fmt(exact, 4)}\n"
            f"Nearest printable thickness: {nearest} perimeters = {self._fmt(nearest * line_width, 4)} mm\n"
            f"Lower option: {lower} perimeters = {self._fmt(lower * line_width, 4)} mm\n"
            f"Snap-up option: {upper} perimeters = {self._fmt(upper * line_width, 4)} mm"
        )

    # ── Snap helper ───────────────────────────────────────────────────────────

    def _calculate_snap(self) -> None:
        length     = self._parse_positive(self.snap_length_input.input.text())
        width      = self._parse_positive(self.snap_width_input.input.text())
        height     = self._parse_positive(self.snap_height_input.input.text())
        nozzle     = self._parse_positive(self.snap_nozzle_input.input.text())
        layer      = self._parse_positive(self.snap_layer_input.input.text())
        line_width = self._parse_positive(self.snap_linewidth_input.input.text())

        inputs = [
            (self.snap_length_input, length),
            (self.snap_width_input, width),
            (self.snap_height_input, height),
            (self.snap_nozzle_input, nozzle),
            (self.snap_layer_input, layer),
            (self.snap_linewidth_input, line_width),
        ]
        any_invalid = False
        for widget, value in inputs:
            widget.set_error(math.isnan(value))
            if math.isnan(value):
                any_invalid = True

        if any_invalid:
            for row in (self.snap_length_row, self.snap_width_row, self.snap_height_row):
                row.set_value("Fill all fields.")
            return

        lc, ls, ld = self._snap_dim(length, line_width)
        wc, ws, wd = self._snap_dim(width,  line_width)
        hc, hs, hd = self._snap_dim(height, layer)

        self.snap_summary_tile.value_label.setText(
            f"Nozzle {self._fmt(nozzle, 3)} mm  |  Layer {self._fmt(layer, 3)} mm  |  Line {self._fmt(line_width, 3)} mm"
        )
        self.snap_length_row.set_value(f"{lc} lines = {self._fmt(ls, 4)} mm  (Δ {self._fmt(ld, 4)} mm)")
        self.snap_width_row.set_value(f"{wc} lines = {self._fmt(ws, 4)} mm  (Δ {self._fmt(wd, 4)} mm)")
        self.snap_height_row.set_value(f"{hc} layers = {self._fmt(hs, 4)} mm  (Δ {self._fmt(hd, 4)} mm)")

    # ── Copy helpers ──────────────────────────────────────────────────────────

    def _copy_mm(self) -> None:
        text = self.mm_input.input.text().strip()
        if text:
            QApplication.clipboard().setText(text)
            self._flash(self.copy_mm_btn)

    def _copy_inches(self) -> None:
        text = self.inch_input.input.text().strip()
        if text:
            QApplication.clipboard().setText(text)
            self._flash(self.copy_inch_btn)

    def _copy_result(self) -> None:
        result, error = self._evaluate_expression(self.calc_input.input.text())
        if error or result is None:
            self.converter_status.setText("Enter a valid expression to copy.")
            return
        QApplication.clipboard().setText(self._fmt(result, 10))
        self._flash(self.copy_result_btn)

    def _flash(self, btn: QPushButton, ms: int = 900) -> None:
        original_text = btn.text()
        original_name = btn.objectName()
        btn.setText("Copied!")
        btn.setObjectName("successButton")
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        btn.setEnabled(False)

        if btn in self._feedback_timers:
            self._feedback_timers[btn].stop()

        timer = QTimer(self)
        timer.setSingleShot(True)

        def restore() -> None:
            btn.setText(original_text)
            btn.setObjectName(original_name)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.setEnabled(True)
            self._feedback_timers.pop(btn, None)

        timer.timeout.connect(restore)
        timer.start(ms)
        self._feedback_timers[btn] = timer

    # ── Window geometry persistence ───────────────────────────────────────────

    def _state_path(self) -> Path:
        base = Path(os.environ.get("APPDATA", str(Path.home())))
        folder = base / "MMInchWidget"
        folder.mkdir(parents=True, exist_ok=True)
        return folder / "state_pyside.json"

    def _save_geometry(self) -> None:
        geom = self.geometry()
        state = {"x": geom.x(), "y": geom.y(), "w": geom.width(), "h": geom.height()}
        try:
            self._state_path().write_text(json.dumps(state), encoding="utf-8")
        except Exception:
            pass

    def _restore_or_position(self) -> None:
        try:
            data = json.loads(self._state_path().read_text(encoding="utf-8"))
            self.setGeometry(data["x"], data["y"], data["w"], data["h"])
            return
        except Exception:
            pass
        screen = QApplication.primaryScreen().availableGeometry()
        margin = 16
        self.move(screen.right() - self.width() - margin, screen.top() + margin)

    def moveEvent(self, event) -> None:  # noqa: N802
        super().moveEvent(event)
        self._save_timer.start(250)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._save_timer.start(250)

    # ── Static helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _fmt(value: float, precision: int = 6) -> str:
        text = f"{value:.{precision}f}".rstrip("0").rstrip(".")
        return text if text else "0"

    @staticmethod
    def _parse_positive(text: str) -> float:
        try:
            v = float(text.strip())
        except ValueError:
            return float("nan")
        return v if v > 0 else float("nan")

    @staticmethod
    def _snap_dim(value: float, increment: float) -> tuple[int, float, float]:
        count = max(1, round(value / increment))
        snapped = count * increment
        return count, snapped, snapped - value

    @staticmethod
    def _gcd(a: int, b: int) -> int:
        a, b = abs(a), abs(b)
        while b:
            a, b = b, a % b
        return a or 1

    def _to_mixed_fraction(self, value: float, max_den: int = 64) -> str:
        if math.isnan(value):
            return "—"
        sign  = "-" if value < 0 else ""
        abs_v = abs(value)
        whole = int(abs_v)
        frac  = abs_v - whole
        if frac < 1e-12:
            return f"{sign}{whole}"
        best_num, best_den, best_err = 0, 1, float("inf")
        for den in range(1, max_den + 1):
            num = round(frac * den)
            err = abs((num / den) - frac)
            if err < best_err:
                best_num, best_den, best_err = num, den, err
        if best_num == 0:
            return f"{sign}{whole}"
        divisor = self._gcd(best_num, best_den)
        num, den = best_num // divisor, best_den // divisor
        return f"{sign}{num}/{den}" if whole == 0 else f"{sign}{whole} {num}/{den}"

    @staticmethod
    def _parse_inches(text: str) -> float | None:
        value = text.strip()
        if not value:
            return None
        m = re.match(r"^(-?\d+)\s+(\d+)\s*/\s*(\d+)$", value)
        if m:
            whole, num, den = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if den == 0:
                return float("nan")
            sign = -1 if whole < 0 else 1
            return sign * (abs(whole) + num / den)
        m = re.match(r"^(-?\d+)\s*/\s*(\d+)$", value)
        if m:
            num, den = int(m.group(1)), int(m.group(2))
            return float("nan") if den == 0 else num / den
        try:
            return float(value)
        except ValueError:
            return float("nan")

    @staticmethod
    def _evaluate_expression(expr: str) -> tuple[float | None, str | None]:
        text = expr.strip()
        if not text:
            return None, None
        if not re.fullmatch(r"[\d+\-*/().\s%]+", text):
            return None, "Only arithmetic characters are allowed."
        try:
            value = eval(text, {"__builtins__": {}}, {})  # noqa: S307
        except Exception:
            return None, "Invalid expression."
        if not isinstance(value, (int, float)):
            return None, "Invalid result."
        if not math.isfinite(value):
            return None, "Expression must return a finite number."
        return float(value), None


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Bypass Windows native style — ensures stylesheet colors render correctly
    app.setApplicationName(APP_TITLE)
    app.setOrganizationName("Redeemed Engineering")
    window = ConversionWidget()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
