# import matplotlib
# matplotlib.use("QtAgg")
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

# from PyQt6.QtWidgets import (
#     QWidget, QVBoxLayout, QHBoxLayout,
#     QLabel, QFrame, QSizePolicy
# )
# from PyQt6.QtCore import Qt


# # =========================
# # Metric Card
# # =========================
# class MetricCard(QFrame):
#     def __init__(self, title, color):
#         super().__init__()
#         self.setStyleSheet(f"""
#             QFrame {{
#                 background:#161B22;
#                 border:1px solid {color};
#                 border-radius:8px;
#                 padding:8px;
#             }}
#         """)
#         self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
#         self.setFixedHeight(80)

#         layout = QVBoxLayout(self)
#         layout.setSpacing(2)

#         self._title_lbl = QLabel(title)
#         self._title_lbl.setStyleSheet("color:#8B949E; font-size:11px;")

#         self._value_lbl = QLabel("—")
#         self._value_lbl.setStyleSheet(
#             f"color:{color}; font-size:22px; font-weight:bold;"
#         )

#         layout.addWidget(self._title_lbl)
#         layout.addWidget(self._value_lbl)

#     def set_value(self, text: str):
#         self._value_lbl.setText(text)


# # =========================
# # Performance Lab
# # =========================
# class PerformanceLab(QWidget):

#     def __init__(self):
#         super().__init__()
#         self.setStyleSheet("background:#0D1117;")

#         main_layout = QVBoxLayout(self)
#         main_layout.setContentsMargins(16, 16, 16, 16)
#         main_layout.setSpacing(12)

#         # ── Header ──
#         header = QLabel("HPC PERFORMANCE DASHBOARD")
#         header.setStyleSheet(
#             "color:#58A6FF; font-size:18px; font-weight:bold;"
#             "padding-bottom:4px; border-bottom:1px solid #21262D;"
#         )
#         main_layout.addWidget(header)

#         # ── Metric Cards ──
#         cards_row = QHBoxLayout()
#         cards_row.setSpacing(10)

#         self.card_speedup_omp = MetricCard("OMP Speedup",   "#39FF14")
#         self.card_speedup_mpi = MetricCard("MPI Speedup",   "#FF8C00")
#         self.card_accuracy    = MetricCard("Accuracy",      "#58A6FF")
#         self.card_tp          = MetricCard("True Positives","#FFD700")
#         self.card_fp          = MetricCard("False Positives","#FF4444")
#         self.card_fn          = MetricCard("False Negatives","#FF8C00")

#         for c in (self.card_speedup_omp, self.card_speedup_mpi,
#                   self.card_accuracy, self.card_tp,
#                   self.card_fp, self.card_fn):
#             cards_row.addWidget(c)

#         main_layout.addLayout(cards_row)

#         # ── Charts ──
#         self.figure, (self.ax_time, self.ax_detect) = plt.subplots(
#             1, 2, figsize=(11, 4)
#         )
#         self.figure.patch.set_facecolor("#0D1117")

#         for ax in (self.ax_time, self.ax_detect):
#             ax.set_facecolor("#161B22")
#             ax.tick_params(colors="#8B949E")
#             ax.title.set_color("#C9D1D9")
#             ax.yaxis.label.set_color("#8B949E")
#             for spine in ax.spines.values():
#                 spine.set_edgecolor("#30363D")

#         self.canvas = FigureCanvas(self.figure)
#         self.canvas.setStyleSheet("background:#0D1117;")
#         main_layout.addWidget(self.canvas)

#         # ── No-data placeholder ──
#         self._draw_placeholder()

#     # ─────────────────────────────────────────
#     # UPDATE
#     # ─────────────────────────────────────────
#     def update_charts(self, data: dict):

#         seq      = float(data["seq"])
#         omp      = float(data["omp"])
#         mpi      = float(data["mpi"])
#         tp       = int(data["tp"])
#         fp       = int(data["fp"])
#         fn       = int(data["fn"])
#         accuracy = float(data["accuracy"])

#         speedup_omp = seq / omp if omp > 0 else 1.0
#         speedup_mpi = seq / mpi if mpi > 0 else 1.0

#         # ── Update metric cards ──
#         self.card_speedup_omp.set_value(f"{speedup_omp:.2f}×")
#         self.card_speedup_mpi.set_value(f"{speedup_mpi:.2f}×")
#         self.card_accuracy.set_value(f"{accuracy*100:.1f}%")
#         self.card_tp.set_value(str(tp))
#         self.card_fp.set_value(str(fp))
#         self.card_fn.set_value(str(fn))

#         # ── Chart 1: Execution Time ──
#         self.ax_time.clear()
#         labels = ["Sequential", "OpenMP", "MPI (Sim)"]
#         values = [seq, omp, mpi]
#         colors = ["#FF4444", "#39FF14", "#58A6FF"]
#         bars   = self.ax_time.bar(labels, values, color=colors, width=0.5)
#         self.ax_time.set_title("Execution Time Comparison", color="#C9D1D9")
#         self.ax_time.set_ylabel("Time (μs)", color="#8B949E")
#         self.ax_time.set_facecolor("#161B22")

#         # Value labels on bars
#         for bar, val in zip(bars, values):
#             self.ax_time.text(
#                 bar.get_x() + bar.get_width() / 2,
#                 bar.get_height() * 1.01,
#                 f"{val:,.0f}",
#                 ha="center", va="bottom",
#                 color="#E0E0E0", fontsize=9
#             )

#         # Speedup annotations
#         if omp > 0:
#             self.ax_time.annotate(
#                 f"×{speedup_omp:.1f}",
#                 xy=(1, omp), xytext=(1, omp + seq * 0.05),
#                 color="#39FF14", ha="center", fontsize=9
#             )

#         # ── Chart 2: Detection Results ──
#         self.ax_detect.clear()
#         det_labels = ["True Positive", "False Positive", "False Negative"]
#         det_vals   = [tp, fp, fn]
#         det_colors = ["#39FF14", "#FF4444", "#FF8C00"]
#         d_bars = self.ax_detect.bar(det_labels, det_vals, color=det_colors, width=0.5)
#         self.ax_detect.set_title("Detection Metrics", color="#C9D1D9")
#         self.ax_detect.set_ylabel("Packet Count", color="#8B949E")
#         self.ax_detect.set_facecolor("#161B22")

#         for bar, val in zip(d_bars, det_vals):
#             self.ax_detect.text(
#                 bar.get_x() + bar.get_width() / 2,
#                 bar.get_height() * 1.01,
#                 str(val),
#                 ha="center", va="bottom",
#                 color="#E0E0E0", fontsize=9
#             )

#         for ax in (self.ax_time, self.ax_detect):
#             ax.tick_params(colors="#8B949E")
#             for spine in ax.spines.values():
#                 spine.set_edgecolor("#30363D")

#         self.figure.tight_layout(pad=2.0)
#         self.canvas.draw()

#     # ─────────────────────────────────────────
#     # PLACEHOLDER (before first run)
#     # ─────────────────────────────────────────
#     def _draw_placeholder(self):
#         for ax in (self.ax_time, self.ax_detect):
#             ax.clear()
#             ax.set_facecolor("#161B22")
#             ax.text(0.5, 0.5,
#                     "Run a simulation first",
#                     transform=ax.transAxes,
#                     ha="center", va="center",
#                     color="#484F58", fontsize=12)
#             for spine in ax.spines.values():
#                 spine.set_edgecolor("#30363D")
#             ax.tick_params(colors="#30363D")

#         self.figure.tight_layout(pad=2.0)
#         self.canvas.draw()




import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout,
    QLabel, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt


# =========================
# Metric Card
# =========================
class MetricCard(QFrame):
    def __init__(self, title, color):
        super().__init__()

        self.setStyleSheet(f"""
            QFrame {{
                background:#161B22;
                border:1px solid {color};
                border-radius:10px;
                padding:10px;
            }}
        """)

        # IMPORTANT FIX: allow proper vertical expansion instead of fixed height
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        self._title_lbl = QLabel(title)
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._title_lbl.setWordWrap(True)
        self._title_lbl.setStyleSheet("color:#8B949E; font-size:11px;")

        self._value_lbl = QLabel("—")
        self._value_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._value_lbl.setStyleSheet(
            f"color:{color}; font-size:24px; font-weight:bold;"
        )

        layout.addWidget(self._title_lbl)
        layout.addWidget(self._value_lbl)

    def set_value(self, text: str):
        self._value_lbl.setText(text)


# =========================
# Performance Lab
# =========================
class PerformanceLab(QWidget):

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background:#0D1117;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # ── Header ──
        header = QLabel("HPC PERFORMANCE DASHBOARD")
        header.setStyleSheet(
            "color:#58A6FF; font-size:18px; font-weight:bold;"
            "padding-bottom:6px; border-bottom:1px solid #21262D;"
        )
        main_layout.addWidget(header)

        # ── Metric Cards GRID FIX ──
        cards_grid = QGridLayout()
        cards_grid.setSpacing(12)

        # IMPORTANT FIX: make grid expand evenly
        for i in range(3):
            cards_grid.setColumnStretch(i, 1)

        self.card_speedup_omp = MetricCard("OMP Speedup",   "#39FF14")
        self.card_speedup_mpi = MetricCard("MPI Speedup",   "#FF8C00")
        self.card_accuracy    = MetricCard("Accuracy",      "#58A6FF")
        self.card_tp          = MetricCard("True Positives", "#FFD700")
        self.card_fp          = MetricCard("False Positives","#FF4444")
        self.card_fn          = MetricCard("False Negatives","#FF8C00")

        cards = [
            self.card_speedup_omp,
            self.card_speedup_mpi,
            self.card_accuracy,
            self.card_tp,
            self.card_fp,
            self.card_fn
        ]

        # 2 rows × 3 cols layout
        for i, card in enumerate(cards):
            row = i // 3
            col = i % 3
            cards_grid.addWidget(card, row, col)

        main_layout.addLayout(cards_grid)

        # ── Charts ──
        self.figure, (self.ax_time, self.ax_detect) = plt.subplots(
            1, 2, figsize=(11, 4)
        )
        self.figure.patch.set_facecolor("#0D1117")

        for ax in (self.ax_time, self.ax_detect):
            ax.set_facecolor("#161B22")
            ax.tick_params(colors="#8B949E")
            ax.title.set_color("#C9D1D9")
            ax.yaxis.label.set_color("#8B949E")
            for spine in ax.spines.values():
                spine.set_edgecolor("#30363D")

        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background:#0D1117;")
        main_layout.addWidget(self.canvas)

        self._draw_placeholder()

    # ─────────────────────────────────────────
    # UPDATE
    # ─────────────────────────────────────────
    def update_charts(self, data: dict):

        seq      = float(data["seq"])
        omp      = float(data["omp"])
        mpi      = float(data["mpi"])
        tp       = int(data["tp"])
        fp       = int(data["fp"])
        fn       = int(data["fn"])
        accuracy = float(data["accuracy"])

        speedup_omp = seq / omp if omp > 0 else 1.0
        speedup_mpi = seq / mpi if mpi > 0 else 1.0

        self.card_speedup_omp.set_value(f"{speedup_omp:.2f}×")
        self.card_speedup_mpi.set_value(f"{speedup_mpi:.2f}×")
        self.card_accuracy.set_value(f"{accuracy*100:.1f}%")
        self.card_tp.set_value(str(tp))
        self.card_fp.set_value(str(fp))
        self.card_fn.set_value(str(fn))

        self.ax_time.clear()
        labels = ["Sequential", "OpenMP", "MPI (Sim)"]
        values = [seq, omp, mpi]
        colors = ["#FF4444", "#39FF14", "#58A6FF"]
        bars   = self.ax_time.bar(labels, values, color=colors, width=0.5)
        self.ax_time.set_title("Execution Time Comparison", color="#C9D1D9")
        self.ax_time.set_ylabel("Time (μs)", color="#8B949E")
        self.ax_time.set_facecolor("#161B22")

        for bar, val in zip(bars, values):
            self.ax_time.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() * 1.01,
                f"{val:,.0f}",
                ha="center", va="bottom",
                color="#E0E0E0", fontsize=9
            )

        self.ax_detect.clear()
        det_labels = ["True Positive", "False Positive", "False Negative"]
        det_vals   = [tp, fp, fn]
        det_colors = ["#39FF14", "#FF4444", "#FF8C00"]
        d_bars = self.ax_detect.bar(det_labels, det_vals, color=det_colors, width=0.5)
        self.ax_detect.set_title("Detection Metrics", color="#C9D1D9")
        self.ax_detect.set_ylabel("Packet Count", color="#8B949E")
        self.ax_detect.set_facecolor("#161B22")

        for bar, val in zip(d_bars, det_vals):
            self.ax_detect.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() * 1.01,
                str(val),
                ha="center", va="bottom",
                color="#E0E0E0", fontsize=9
            )

        self.figure.tight_layout(pad=2.0)
        self.canvas.draw()

    # ─────────────────────────────────────────
    # PLACEHOLDER
    # ─────────────────────────────────────────
    def _draw_placeholder(self):
        for ax in (self.ax_time, self.ax_detect):
            ax.clear()
            ax.set_facecolor("#161B22")
            ax.text(0.5, 0.5,
                    "Run a simulation first",
                    transform=ax.transAxes,
                    ha="center", va="center",
                    color="#484F58", fontsize=12)
            for spine in ax.spines.values():
                spine.set_edgecolor("#30363D")
            ax.tick_params(colors="#30363D")

        self.figure.tight_layout(pad=2.0)
        self.canvas.draw()
