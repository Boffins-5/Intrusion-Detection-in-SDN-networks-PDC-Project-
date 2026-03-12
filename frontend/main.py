import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QPushButton,
    QStackedWidget, QLabel, QFrame
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon

# ─────────────────────────────────────────
#  DARK THEME
# ─────────────────────────────────────────

DARK_THEME = """
    QMainWindow {
        background-color: #0F172A;
    }
    QWidget {
        background-color: #0F172A;
        color: #E2E8F0;
        font-family: Arial;
    }
    QPushButton {
        background-color: #1E293B;
        color: #94A3B8;
        border: none;
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 13px;
        text-align: left;
    }
    QPushButton:hover {
        background-color: #1E40AF;
        color: #FFFFFF;
    }
    QPushButton:checked {
        background-color: #2563EB;
        color: #FFFFFF;
        font-weight: bold;
    }
    QLabel {
        color: #E2E8F0;
    }
    QFrame {
        background-color: #1E293B;
        border-radius: 10px;
    }
"""

# ─────────────────────────────────────────
#  PLACEHOLDER PANELS
#  Will be replaced one by one each day
# ─────────────────────────────────────────

def make_placeholder(title, color, description):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setAlignment(Qt.AlignCenter)

    # Icon + Title
    title_label = QLabel(title)
    title_label.setFont(QFont("Arial", 28, QFont.Bold))
    title_label.setStyleSheet(f"color: {color}; background: transparent;")
    title_label.setAlignment(Qt.AlignCenter)

    # Description
    desc_label = QLabel(description)
    desc_label.setFont(QFont("Arial", 14))
    desc_label.setStyleSheet("color: #64748B; background: transparent;")
    desc_label.setAlignment(Qt.AlignCenter)

    layout.addWidget(title_label)
    layout.addSpacing(10)
    layout.addWidget(desc_label)


    return widget

# ─────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────

class Sidebar(QWidget):
    def __init__(self, stack, parent=None):
        super().__init__(parent)
        self.stack = stack
        self.setFixedWidth(220)
        self.setStyleSheet("background-color: #0F172A;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(6)

        # App title
        title = QLabel("SDN Detector")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #38BDF8; padding: 10px; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Parallel Computing System")
        subtitle.setFont(QFont("Arial", 9))
        subtitle.setStyleSheet("color: #475569; background: transparent;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #1E293B; max-height: 1px;")
        layout.addWidget(line)
        layout.addSpacing(10)

        # Nav buttons
        self.buttons = []
        nav_items = [
            ("🗺️   Topology Map",        0, "#3B82F6"),
            ("📈   Traffic Charts",       1, "#10B981"),
            ("🚨   Attack Alerts",        2, "#EF4444"),
            ("📊   Performance",          3, "#F59E0B"),
        ]

        for label, index, color in nav_items:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFont(QFont("Arial", 12))
            btn.setMinimumHeight(48)
            btn.clicked.connect(lambda checked, i=index: self.switch_panel(i))
            layout.addWidget(btn)
            self.buttons.append(btn)

        # Select first button by default
        self.buttons[0].setChecked(True)

        layout.addStretch()

        # Divider
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet("background-color: #1E293B; max-height: 1px;")
        layout.addWidget(line2)
        layout.addSpacing(10)

        # Bottom buttons
        settings_btn = QPushButton("⚙️   Settings")
        settings_btn.setFont(QFont("Arial", 11))
        settings_btn.setMinimumHeight(44)
        layout.addWidget(settings_btn)



    def switch_panel(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)

# ─────────────────────────────────────────
#  MAIN WINDOW
# ─────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SDN Attack Detection System")
        self.setGeometry(100, 100, 1280, 780)
        self.setMinimumSize(1024, 640)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Stacked panels
        self.stack = QStackedWidget()

        # Add placeholder panels
        self.stack.addWidget(make_placeholder(
            "🗺️  Live Topology Map",
            "#3B82F6",
            "Animated network nodes — hosts, switches, SDN controller\nBuilding on Day 3"
        ))
        self.stack.addWidget(make_placeholder(
            "📈  Real-Time Traffic Charts",
            "#10B981",
            "Packets/sec, protocol distribution, IP heatmap\nBuilding on Day 4"
        ))
        self.stack.addWidget(make_placeholder(
            "🚨  Attack Alerts Panel",
            "#EF4444",
            "Live attack detection log with severity levels\nBuilding on Day 5"
        ))
        self.stack.addWidget(make_placeholder(
            "📊  Performance Dashboard",
            "#F59E0B",
            "Speedup charts — Sequential vs OpenMP vs MPI vs GPU\nBuilding on Days 6-9"
        ))

        # Sidebar
        sidebar = Sidebar(self.stack)

        # Vertical separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("background-color: #1E293B; max-width: 1px;")

        # Assemble layout
        main_layout.addWidget(sidebar)
        main_layout.addWidget(separator)
        main_layout.addWidget(self.stack)

        self.setStyleSheet(DARK_THEME)

# ─────────────────────────────────────────
#  LAUNCH APP
# ─────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
