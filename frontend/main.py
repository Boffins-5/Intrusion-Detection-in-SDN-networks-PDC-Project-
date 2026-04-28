import sys

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QPushButton,
    QStackedWidget, QMessageBox, QLabel
)
from PyQt6.QtCore import Qt

from attack_lab import AttackLab
from performance_lab import PerformanceLab
from bridge import BackendWorker


class SDNGuard(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SDN Parallel Guard v3.0")
        self.resize(1400, 900)
        self.setStyleSheet("background:#0D1117; color:#E0E0E0;")

        self._worker        = None
        self._pending_config = None

        self._init_ui()

    # ─────────────────────────────────────────
    # UI
    # ─────────────────────────────────────────
    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── NAV SIDEBAR ──
        nav = QWidget()
        nav.setFixedWidth(160)
        nav.setStyleSheet("""
            QWidget   { background:#010409; }
            QPushButton {
                background:transparent; color:#8B949E;
                border:none; padding:12px 16px;
                font-size:13px; text-align:left; border-radius:6px;
            }
            QPushButton:hover   { background:#161B22; color:#E0E0E0; }
            QPushButton:checked { background:#1F6FEB; color:white; font-weight:bold; }
        """)

        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(8, 16, 8, 16)

        title = QLabel("SDN Guard")
        title.setStyleSheet("color:#58A6FF; font-size:16px; font-weight:bold; padding:8px;")
        nav_layout.addWidget(title)

        self.btn_attack = QPushButton("  Attack Lab")
        self.btn_perf   = QPushButton("  Performance")
        self.btn_attack.setCheckable(True)
        self.btn_perf.setCheckable(True)
        self.btn_attack.setChecked(True)

        nav_layout.addWidget(self.btn_attack)
        nav_layout.addWidget(self.btn_perf)
        nav_layout.addStretch()

        # ── STACK ──
        self.stack = QStackedWidget()

        self.attack_screen      = AttackLab()
        self.performance_screen = PerformanceLab()

        self.stack.addWidget(self.attack_screen)        # index 0
        self.stack.addWidget(self.performance_screen)   # index 1

        layout.addWidget(nav)
        layout.addWidget(self.stack)

        # ── NAV CONNECTIONS ──
        self.btn_attack.clicked.connect(lambda: self._switch(0))
        self.btn_perf.clicked.connect(lambda:   self._switch(1))

        # ── KEY SIGNALS ──
        # 1. User clicks Analyze → orchestrate
        self.attack_screen.launch_requested.connect(self._orchestrate)

        # 2. Animation finishes → run backend
        self.attack_screen.animation_done.connect(self._run_backend)

    def _switch(self, idx):
        self.stack.setCurrentIndex(idx)
        self.btn_attack.setChecked(idx == 0)
        self.btn_perf.setChecked(idx == 1)

    # ─────────────────────────────────────────
    # ORCHESTRATION
    # ─────────────────────────────────────────
    def _orchestrate(self, config: dict):
        """Called when Analyze is clicked in AttackLab."""
        if not config.get("targets"):
            QMessageBox.critical(self, "Error", "No targets selected")
            return

        self._pending_config = config          # save for when animation ends
        self._show_confirmation(config)

    def _show_confirmation(self, config: dict):
        msg = (
            f"<b>Start Simulation?</b><br><br>"
            f"Nodes: <b>{config['nodes']}</b><br>"
            f"Targets: <b>{len(config['targets'])}</b><br>"
            f"Attack: <b>{config['attack']}</b><br>"
            f"Packets: <b>{config['packets']}</b><br><br>"
            f"Animation will run first, then the C++ backend will execute."
        )

        reply = QMessageBox.question(
            self, "Confirm Execution", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.attack_screen.set_loading_state(True)
            self.attack_screen.trigger_visual_simulation()   # FIX: method now exists

    # ─────────────────────────────────────────
    # BACKEND
    # ─────────────────────────────────────────
    def _run_backend(self):
        """Called automatically when animation timer expires."""
        config = self._pending_config
        if not config:
            return

        # Kill any previous worker
        if self._worker:
            self._worker.quit()
            self._worker.wait()

        self._worker = BackendWorker(
            nodes   = config["nodes"],
            target  = config["targets"],
            packets = config["packets"],
            attack  = config["attack"],
            mode    = config["mode"],
        )
        self._worker.result_ready.connect(self._handle_results)
        self._worker.error_occurred.connect(self._handle_error)
        self._worker.start()

    # ─────────────────────────────────────────
    # RESULTS
    # ─────────────────────────────────────────
    def _handle_results(self, data: dict):
        self.attack_screen.set_loading_state(False)
        self._pending_config = None

        self.performance_screen.update_charts(data)
        self._switch(1)

        acc = data.get("accuracy", 0) * 100
        QMessageBox.information(
            self, "Analysis Complete",
            f"Attack Detected: <b>{data.get('type','?')}</b><br><br>"
            f"True Positives:  {data.get('tp', 0)}<br>"
            f"False Positives: {data.get('fp', 0)}<br>"
            f"False Negatives: {data.get('fn', 0)}<br>"
            f"Accuracy: <b>{acc:.2f}%</b>"
        )

    def _handle_error(self, msg: str):
        self.attack_screen.set_loading_state(False)
        self._pending_config = None
        QMessageBox.critical(self, "Backend Error", msg)


# ─────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = SDNGuard()
    window.show()
    sys.exit(app.exec())
