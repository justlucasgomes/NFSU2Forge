#!/usr/bin/env python3
"""
NFSU2Forge - Main Entry Point
A professional mod tool for Need for Speed Underground 2.
"""
import sys
import os
from pathlib import Path

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QIcon, QFont

from src.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("NFSU2Forge")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Lucas Gomes")
    app.setOrganizationDomain("github.com/justlucasgomes/NFSU2Forge")

    # Apply dark stylesheet
    style_path = Path(__file__).parent / "assets" / "styles" / "dark_theme.qss"
    if style_path.exists():
        app.setStyleSheet(style_path.read_text(encoding="utf-8"))

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
