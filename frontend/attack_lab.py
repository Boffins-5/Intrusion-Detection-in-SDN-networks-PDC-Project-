from PyQt6.QtWidgets import (
    QListWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QGraphicsScene, QGraphicsView,
    QGraphicsEllipseItem, QGraphicsLineItem, QSlider, QLabel,
    QComboBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QPen
import random
import math


# =========================
# NODE ITEM
# =========================
class NodeItem(QGraphicsEllipseItem):
    def __init__(self, x, y, node_id):          # FIX: only 3 args
        super().__init__(-10, -10, 20, 20)
        self.setPos(x, y)
        self.node_id = node_id
        self.is_target = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_color()

    def mousePressEvent(self, event):
        self.is_target = not self.is_target
        self.update_color()

    def update_color(self):
        if self.is_target:
            self.setBrush(QBrush(QColor("#FF4444")))
            self.setPen(QPen(QColor("#FF0000"), 2))
        else:
            self.setBrush(QBrush(QColor("#2C3E50")))
            self.setPen(QPen(QColor("#4A90D9"), 1))


# =========================
# PACKET ITEM
# =========================
class PacketItem(QGraphicsEllipseItem):
    def __init__(self, x, y, color):
        super().__init__(-4, -4, 8, 8)
        self.setPos(x, y)
        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.dx = 0.0
        self.dy = 0.0


# =========================
# ATTACK LAB
# =========================
class AttackLab(QWidget):

    launch_requested = pyqtSignal(dict)     # emitted when Analyze is clicked
    animation_done   = pyqtSignal()         # emitted when animation timer expires

    def __init__(self):
        super().__init__()

        # FIX: initialize all lists here
        self.nodes          = []
        self.normal_packets = []
        self.attack_packets = []
        self.node_map       = []

        self._pending_config = None

        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self._simulate_step)

        self.anim_stop_timer = QTimer()
        self.anim_stop_timer.setSingleShot(True)
        self.anim_stop_timer.timeout.connect(self._on_animation_finished)

        self._build_ui()
        self._generate_topology()

    # ─────────────────────────────────────────
    # UI BUILD
    # ─────────────────────────────────────────
    def _build_ui(self):

        main = QHBoxLayout(self)
        main.setContentsMargins(4, 4, 4, 4)
        main.setSpacing(4)

        # ── GRAPH VIEW ──
        self.scene = QGraphicsScene()
        self.view  = QGraphicsView(self.scene)
        self.view.setStyleSheet("background:#0A0E1A; border:1px solid #1E3A5F;")
        self.view.setRenderHint(self.view.renderHints())
        main.addWidget(self.view, 4)

        # ── SIDEBAR ──
        sidebar = QFrame()
        sidebar.setFixedWidth(340)
        sidebar.setStyleSheet("""
            QFrame      { background:#0D1117; color:#E0E0E0; }
            QLabel      { color:#C9D1D9; font-size:12px; }
            QComboBox   { background:#161B22; color:#E0E0E0; border:1px solid #30363D;
                          padding:4px; border-radius:4px; }
            QPushButton { background:#21262D; color:#58A6FF; border:1px solid #30363D;
                          padding:6px; border-radius:4px; font-weight:bold; }
            QPushButton:hover   { background:#1F6FEB; color:white; }
            QPushButton:disabled{ background:#161B22; color:#484F58; }
            QSlider::groove:horizontal { height:4px; background:#30363D; border-radius:2px; }
            QSlider::handle:horizontal { background:#58A6FF; width:12px; height:12px;
                                         margin:-4px 0; border-radius:6px; }
            QListWidget { background:#161B22; color:#8B949E; border:1px solid #30363D;
                          font-size:11px; }
        """)

        side = QVBoxLayout(sidebar)
        side.setSpacing(6)

        # ── SECTION: NETWORK ──
        side.addWidget(self._section_label(" NETWORK TOPOLOGY"))

        self.node_label = QLabel("Nodes: 300")
        self.node_slider = QSlider(Qt.Orientation.Horizontal)
        self.node_slider.setRange(50, 1000)
        self.node_slider.setValue(300)
        self.node_slider.valueChanged.connect(
            lambda v: (self.node_label.setText(f"Nodes: {v}"), self._generate_topology())
        )
        side.addWidget(self.node_label)
        side.addWidget(self.node_slider)

        self.topology_combo = QComboBox()
        self.topology_combo.addItems(["Random", "Cluster"])
        self.topology_combo.currentTextChanged.connect(lambda _: self._generate_topology())
        side.addWidget(QLabel("Topology"))
        side.addWidget(self.topology_combo)

        # ── SECTION: ATTACK ──
        side.addWidget(self._section_label(" ATTACK CONFIG"))

        self.attack_combo = QComboBox()
        self.attack_combo.addItems(["ICMP_FLOOD", "TCP_SYN", "SLOWLORIS", "FLOW_OVERFLOW"])
        side.addWidget(QLabel("Attack Type"))
        side.addWidget(self.attack_combo)

        self.packet_label = QLabel("Packets: 20000")
        self.packet_slider = QSlider(Qt.Orientation.Horizontal)
        self.packet_slider.setRange(10000, 1000000)
        self.packet_slider.setValue(20000)
        self.packet_slider.valueChanged.connect(
            lambda v: self.packet_label.setText(f"Packets: {v}")
        )
        side.addWidget(self.packet_label)
        side.addWidget(self.packet_slider)

        # ── SECTION: ANIMATION ──
        side.addWidget(self._section_label(" ANIMATION"))

        self.anim_label = QLabel("Duration: 5 sec")
        self.anim_slider = QSlider(Qt.Orientation.Horizontal)
        self.anim_slider.setRange(2, 30)
        self.anim_slider.setValue(5)
        self.anim_slider.valueChanged.connect(
            lambda v: self.anim_label.setText(f"Duration: {v} sec")
        )
        side.addWidget(self.anim_label)
        side.addWidget(self.anim_slider)

        # ── SECTION: TARGETS ──
        side.addWidget(self._section_label(" TARGET NODES"))
        self.target_count_label = QLabel("Click nodes on canvas to select targets")
        self.target_count_label.setWordWrap(True)
        self.target_count_label.setStyleSheet("color:#8B949E; font-size:11px;")
        side.addWidget(self.target_count_label)

        # ── BUTTONS ──
        side.addWidget(self._section_label(" CONTROLS"))

        self.btn_run     = QPushButton("  Run Animation")
        self.btn_stop    = QPushButton("  Stop")
        self.btn_reset   = QPushButton("  Reset")
        self.btn_analyze = QPushButton("  Analyze (Run Backend)")

        self.btn_analyze.setStyleSheet(
            "background:#1F6FEB; color:white; font-size:13px; padding:8px; border-radius:4px;"
        )

        for btn in (self.btn_run, self.btn_stop, self.btn_reset, self.btn_analyze):
            side.addWidget(btn)

        self.btn_run.clicked.connect(self._on_run_clicked)
        self.btn_stop.clicked.connect(self._stop_animation)
        self.btn_reset.clicked.connect(self._reset)
        self.btn_analyze.clicked.connect(self._on_analyze_clicked)

        # ── LOG ──
        side.addWidget(self._section_label(" LOG"))
        self.log_list = QListWidget()
        self.log_list.setMaximumHeight(140)
        side.addWidget(self.log_list)
        side.addStretch()

        main.addWidget(sidebar, 1)

    def _section_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "color:#58A6FF; font-size:11px; font-weight:bold;"
            "margin-top:6px; padding:3px 0;"
            "border-bottom:1px solid #21262D;"
        )
        return lbl

    # ─────────────────────────────────────────
    # TOPOLOGY GENERATION  (single clean method)
    # ─────────────────────────────────────────
    def _generate_topology(self):
        self._stop_animation()
        self.scene.clear()
        self.nodes.clear()
        self.node_map.clear()
        self.normal_packets.clear()
        self.attack_packets.clear()

        count = self.node_slider.value()
        mode  = self.topology_combo.currentText()

        for i in range(count):
            if mode == "Cluster":
                angle = i * 0.3
                r     = random.randint(40, 280)
                x     = math.cos(angle) * r
                y     = math.sin(angle) * r
            else:
                x = random.randint(-320, 320)
                y = random.randint(-220, 220)

            node = NodeItem(x, y, i)
            self.scene.addItem(node)
            self.nodes.append(node)
            self.node_map.append((x, y))

        self._log(f"Topology generated: {count} nodes ({mode})")
        self._update_target_label()

    # ─────────────────────────────────────────
    # ANIMATION
    # ─────────────────────────────────────────
    def _on_run_clicked(self):
        if not self.nodes:
            return
        self.sim_timer.start(30)
        duration_ms = self.anim_slider.value() * 1000
        self.anim_stop_timer.start(duration_ms)
        self._log(f"Animation started ({self.anim_slider.value()} sec)")

    def trigger_visual_simulation(self):
        """Called by main window after user confirms launch."""
        self._on_run_clicked()

    def _stop_animation(self):
        self.sim_timer.stop()
        self.anim_stop_timer.stop()

    def _on_animation_finished(self):
        self._stop_animation()
        self._log("Animation complete → launching backend…")
        self.animation_done.emit()          # main.py listens to this

    def _simulate_step(self):
        if not self.nodes:
            return

        max_pkts = self.packet_slider.value()
        attack   = self.attack_combo.currentText()

        # Normal traffic (blue)
        if len(self.normal_packets) < max_pkts * 0.6:
            src = random.choice(self.nodes)
            dst = random.choice(self.nodes)
            pkt = PacketItem(src.x(), src.y(), QColor("#00BFFF"))
            pkt.dx = (dst.x() - src.x()) * 0.02
            pkt.dy = (dst.y() - src.y()) * 0.02
            self.scene.addItem(pkt)
            self.normal_packets.append(pkt)

        # Attack traffic
        if len(self.attack_packets) < max_pkts * 0.4:
            src = random.choice(self.nodes)
            color_map = {
                "ICMP_FLOOD"   : QColor("#FF4444"),
                "TCP_SYN"      : QColor("#FFD700"),
                "SLOWLORIS"    : QColor("#39FF14"),
                "FLOW_OVERFLOW": QColor("#FF8C00"),
            }
            pkt = PacketItem(src.x(), src.y(),
                             color_map.get(attack, QColor("red")))
            pkt.dx = random.uniform(-2.5, 2.5)
            pkt.dy = random.uniform(-2.5, 2.5)
            self.scene.addItem(pkt)
            self.attack_packets.append(pkt)

        # Move all packets
        dead_n, dead_a = [], []
        for pkt in self.normal_packets:
            pkt.setPos(pkt.x() + pkt.dx, pkt.y() + pkt.dy)
            if abs(pkt.x()) > 400 or abs(pkt.y()) > 300:
                self.scene.removeItem(pkt)
                dead_n.append(pkt)
        for pkt in self.attack_packets:
            pkt.setPos(pkt.x() + pkt.dx, pkt.y() + pkt.dy)
            if abs(pkt.x()) > 400 or abs(pkt.y()) > 300:
                self.scene.removeItem(pkt)
                dead_a.append(pkt)

        for p in dead_n: self.normal_packets.remove(p)
        for p in dead_a: self.attack_packets.remove(p)

        # Update target highlight
        self._update_target_label()

    # ─────────────────────────────────────────
    # RESET
    # ─────────────────────────────────────────
    def _reset(self):
        self._stop_animation()
        self.normal_packets.clear()
        self.attack_packets.clear()
        self._generate_topology()
        self._log("Reset complete")

    # ─────────────────────────────────────────
    # ANALYZE → emit config to main.py
    # ─────────────────────────────────────────
    def _on_analyze_clicked(self):
        targets = [n.node_id for n in self.nodes if n.is_target]

        if not targets:
            self._log("ERROR: Click at least 1 red node as target")
            return

        config = {
            "nodes"  : self.node_slider.value(),
            "targets": targets,
            "attack" : self.attack_combo.currentText(),
            "packets": self.packet_slider.value(),
            "mode"   : self.topology_combo.currentText(),
        }
        self._log(f"Launching: {len(targets)} targets | {config['attack']}")
        self.launch_requested.emit(config)

    # ─────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────
    def get_targets(self):
        return [n for n in self.nodes if n.is_target]

    def set_loading_state(self, loading: bool):
        self.btn_analyze.setEnabled(not loading)
        self.btn_run.setEnabled(not loading)
        self.btn_analyze.setText(
            "⏳  Running Backend…" if loading else "⚡  Analyze (Run Backend)"
        )

    def _update_target_label(self):
        t = len(self.get_targets())
        self.target_count_label.setText(
            f"Selected Targets: {t}"
            if t > 0 else "Click nodes on canvas to select targets"
        )

    def _log(self, msg: str):
        self.log_list.addItem(msg)
        if self.log_list.count() > 200:
            self.log_list.takeItem(0)
        self.log_list.scrollToBottom()
