import json
import subprocess
import math
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import (
    QPainter, QPen, QBrush, QColor,
    QFont, QPainterPath
)

# ─────────────────────────────────────────
#  COLORS
# ─────────────────────────────────────────

COLOR_BG         = QColor("#0F172A")
COLOR_EDGE       = QColor("#334155")
COLOR_CONTROLLER = QColor("#F59E0B")
COLOR_SWITCH     = QColor("#3B82F6")
COLOR_HOST       = QColor("#10B981")
COLOR_ATTACK     = QColor("#EF4444")
COLOR_TEXT       = QColor("#E2E8F0")
COLOR_TEXT_DIM   = QColor("#64748B")

# ─────────────────────────────────────────
#  TOPOLOGY CANVAS
#  Draws the network map
# ─────────────────────────────────────────

class TopologyCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.nodes     = []
        self.positions = {}   # node_id → (x, y)
        self.setMinimumSize(600, 500)

        # Animation
        self.pulse_value  = 0
        self.pulse_growing = True
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)   # 20fps animation

    # ── Calculate node positions ──────────
    def calculate_positions(self):
        self.positions = {}
        w = self.width()
        h = self.height()

        for node in self.nodes:
            nid  = node["id"]
            ntype = node["type"]

            # Controller → center
            if ntype == "CONTROLLER":
                self.positions[nid] = (w // 2, h // 2)

            # Switches → triangle around controller
            elif ntype == "SWITCH":
                switch_nodes = [n for n in self.nodes if n["type"] == "SWITCH"]
                idx = switch_nodes.index(node)
                angle = (2 * math.pi * idx / len(switch_nodes)) - math.pi / 2
                radius = min(w, h) * 0.28
                x = w // 2 + int(radius * math.cos(angle))
                y = h // 2 + int(radius * math.sin(angle))
                self.positions[nid] = (x, y)

            # Hosts → circle around their switch
            elif ntype == "HOST":
                # find parent switch
                parent_switch = None
                for n in self.nodes:
                    if n["type"] == "SWITCH" and nid in n["connections"]:
                        parent_switch = n
                        break

                if parent_switch:
                    sx, sy = self.positions.get(parent_switch["id"], (w//2, h//2))
                    host_siblings = [
                        n for n in self.nodes
                        if n["type"] == "HOST"
                        and parent_switch["id"] in n["connections"]
                    ]
                    idx = host_siblings.index(node)
                    angle = (2 * math.pi * idx / len(host_siblings)) - math.pi / 2

                    # angle offset per switch so hosts don't overlap
                    switch_nodes = [n for n in self.nodes if n["type"] == "SWITCH"]
                    s_idx = switch_nodes.index(parent_switch)
                    angle += (2 * math.pi * s_idx / len(switch_nodes))

                    radius = min(w, h) * 0.15
                    x = sx + int(radius * math.cos(angle))
                    y = sy + int(radius * math.sin(angle))
                    self.positions[nid] = (x, y)

    # ── Animation tick ─────────────────────
    def animate(self):
        if self.pulse_growing:
            self.pulse_value += 3
            if self.pulse_value >= 20:
                self.pulse_growing = False
        else:
            self.pulse_value -= 3
            if self.pulse_value <= 0:
                self.pulse_growing = True
        self.update()

    # ── Get node color ─────────────────────
    def get_node_color(self, node):
        if node["status"] in ("UNDER_ATTACK", "COMPROMISED"):
            return COLOR_ATTACK
        if node["type"] == "CONTROLLER":
            return COLOR_CONTROLLER
        if node["type"] == "SWITCH":
            return COLOR_SWITCH
        return COLOR_HOST

    # ── Paint everything ───────────────────
    def paintEvent(self, event):
        if not self.nodes:
            return

        # Recalculate positions when size changes
        self.calculate_positions()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.fillRect(self.rect(), COLOR_BG)

        # Draw edges first
        self.draw_edges(painter)

        # Draw nodes on top
        self.draw_nodes(painter)

    # ── Draw edges (connections) ───────────
    def draw_edges(self, painter):
        pen = QPen(COLOR_EDGE, 2, Qt.SolidLine)
        painter.setPen(pen)

        drawn_edges = set()
        for node in self.nodes:
            nid = node["id"]
            for conn_id in node["connections"]:
                edge = tuple(sorted([nid, conn_id]))
                if edge in drawn_edges:
                    continue
                drawn_edges.add(edge)

                if nid in self.positions and conn_id in self.positions:
                    x1, y1 = self.positions[nid]
                    x2, y2 = self.positions[conn_id]
                    painter.drawLine(x1, y1, x2, y2)

    # ── Draw nodes ─────────────────────────
    def draw_nodes(self, painter):
        for node in self.nodes:
            nid   = node["id"]
            ntype = node["type"]
            color = self.get_node_color(node)

            if nid not in self.positions:
                continue

            x, y = self.positions[nid]

            # Node size by type
            if ntype == "CONTROLLER":
                radius = 28
            elif ntype == "SWITCH":
                radius = 20
            else:
                radius = 13

            # Pulse effect for attacked nodes
            if node["status"] in ("UNDER_ATTACK", "COMPROMISED"):
                pulse_r = radius + self.pulse_value // 3
                pulse_color = QColor(COLOR_ATTACK)
                pulse_color.setAlpha(60)
                painter.setBrush(QBrush(pulse_color))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(
                    x - pulse_r, y - pulse_r,
                    pulse_r * 2, pulse_r * 2
                )

            # Glow effect
            glow_color = QColor(color)
            glow_color.setAlpha(40)
            painter.setBrush(QBrush(glow_color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(
                x - radius - 6, y - radius - 6,
                (radius + 6) * 2, (radius + 6) * 2
            )

            # Main circle
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.white, 2))
            painter.drawEllipse(
                x - radius, y - radius,
                radius * 2, radius * 2
            )

            # Icon text inside node
            painter.setPen(QPen(Qt.white))
            if ntype == "CONTROLLER":
                icon = "C"
                font = QFont("Arial", 13, QFont.Bold)
            elif ntype == "SWITCH":
                icon = "S"
                font = QFont("Arial", 10, QFont.Bold)
            else:
                icon = "H"
                font = QFont("Arial", 8, QFont.Bold)

            painter.setFont(font)
            painter.drawText(
                x - radius, y - radius,
                radius * 2, radius * 2,
                Qt.AlignCenter, icon
            )

            # IP label below node
            painter.setFont(QFont("Arial", 8))
            painter.setPen(QPen(COLOR_TEXT_DIM))
            painter.drawText(
                x - 50, y + radius + 4,
                100, 16,
                Qt.AlignCenter, node["ip"]
            )

    # ── Load topology from C++ ─────────────
    def load_topology(self, nodes):
        self.nodes = nodes
        self.calculate_positions()
        self.update()

    # ── Simulate attack on a node ──────────
    def set_node_attack(self, node_id):
        for node in self.nodes:
            if node["id"] == node_id:
                node["status"] = "UNDER_ATTACK"
        self.update()

    # ── Reset all nodes to normal ──────────
    def reset_all(self):
        for node in self.nodes:
            node["status"] = "NORMAL"
        self.update()


# ─────────────────────────────────────────
#  LEGEND WIDGET
# ─────────────────────────────────────────

class Legend(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(24)

        items = [
            ("#F59E0B", "Controller"),
            ("#3B82F6", "Switch"),
            ("#10B981", "Host"),
            ("#EF4444", "Under Attack"),
        ]

        for color, label in items:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 18px; background: transparent;")

            text = QLabel(label)
            text.setStyleSheet("color: #94A3B8; font-size: 12px; background: transparent;")

            layout.addWidget(dot)
            layout.addWidget(text)

        layout.addStretch()


# ─────────────────────────────────────────
#  FULL TOPOLOGY PANEL
# ─────────────────────────────────────────

class TopologyPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.exe_path = r"backend\build\node_simulator.exe"
        self.nodes    = []
        self.setup_ui()
        self.load_from_cpp()

    # ── Build UI ───────────────────────────
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # ── Header ────────────────────────
        header = QHBoxLayout()

        title = QLabel("🗺️  Live Network Topology")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #38BDF8; background: transparent;")

        self.status_label = QLabel("● Loading...")
        self.status_label.setStyleSheet("color: #64748B; font-size: 13px; background: transparent;")

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.status_label)
        main_layout.addLayout(header)

        # ── Stats bar ─────────────────────
        self.stats_bar = QHBoxLayout()
        self.stat_total      = self.make_stat_card("Total Nodes", "0",   "#3B82F6")
        self.stat_hosts      = self.make_stat_card("Hosts",       "0",   "#10B981")
        self.stat_switches   = self.make_stat_card("Switches",    "0",   "#F59E0B")
        self.stat_controller = self.make_stat_card("Controller",  "0",   "#8B5CF6")
        self.stat_attacked   = self.make_stat_card("Under Attack","0",   "#EF4444")

        for card in [self.stat_total, self.stat_hosts,
                     self.stat_switches, self.stat_controller,
                     self.stat_attacked]:
            self.stats_bar.addWidget(card)
        main_layout.addLayout(self.stats_bar)

        # ── Canvas ────────────────────────
        self.canvas = TopologyCanvas()
        self.canvas.setStyleSheet("background-color: #0F172A; border-radius: 12px;")
        main_layout.addWidget(self.canvas, stretch=1)

        # ── Legend ────────────────────────
        legend = Legend()
        legend.setStyleSheet("background-color: #1E293B; border-radius: 8px;")
        main_layout.addWidget(legend)

        # ── Control buttons ───────────────
        btn_layout = QHBoxLayout()

        self.btn_reload = QPushButton("🔄  Reload Topology")
        self.btn_reload.setMinimumHeight(40)
        self.btn_reload.clicked.connect(self.load_from_cpp)
        self.btn_reload.setStyleSheet("""
            QPushButton {
                background: #1E40AF; color: white;
                border-radius: 8px; font-size: 13px;
                padding: 8px 20px;
            }
            QPushButton:hover { background: #2563EB; }
        """)

        self.btn_attack = QPushButton("⚠️  Simulate Attack")
        self.btn_attack.setMinimumHeight(40)
        self.btn_attack.clicked.connect(self.simulate_attack)
        self.btn_attack.setStyleSheet("""
            QPushButton {
                background: #991B1B; color: white;
                border-radius: 8px; font-size: 13px;
                padding: 8px 20px;
            }
            QPushButton:hover { background: #EF4444; }
        """)

        self.btn_reset = QPushButton("✅  Reset All")
        self.btn_reset.setMinimumHeight(40)
        self.btn_reset.clicked.connect(self.reset_attack)
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background: #065F46; color: white;
                border-radius: 8px; font-size: 13px;
                padding: 8px 20px;
            }
            QPushButton:hover { background: #10B981; }
        """)

        btn_layout.addWidget(self.btn_reload)
        btn_layout.addWidget(self.btn_attack)
        btn_layout.addWidget(self.btn_reset)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

    # ── Stat card widget ───────────────────
    def make_stat_card(self, label, value, color):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: #1E293B;
                border-radius: 10px;
                border-left: 4px solid {color};
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)

        val_label = QLabel(value)
        val_label.setFont(QFont("Arial", 22, QFont.Bold))
        val_label.setStyleSheet(f"color: {color}; background: transparent;")

        txt_label = QLabel(label)
        txt_label.setFont(QFont("Arial", 10))
        txt_label.setStyleSheet("color: #64748B; background: transparent;")

        layout.addWidget(val_label)
        layout.addWidget(txt_label)

        # store value label for updating
        frame.value_label = val_label
        return frame

    # ── Update stat cards ──────────────────
    def update_stats(self):
        total      = len(self.nodes)
        hosts      = sum(1 for n in self.nodes if n["type"] == "HOST")
        switches   = sum(1 for n in self.nodes if n["type"] == "SWITCH")
        controller = sum(1 for n in self.nodes if n["type"] == "CONTROLLER")
        attacked   = sum(1 for n in self.nodes if n["status"] == "UNDER_ATTACK")

        self.stat_total.value_label.setText(str(total))
        self.stat_hosts.value_label.setText(str(hosts))
        self.stat_switches.value_label.setText(str(switches))
        self.stat_controller.value_label.setText(str(controller))
        self.stat_attacked.value_label.setText(str(attacked))

    # ── Load topology from C++ exe ─────────
    def load_from_cpp(self):
        self.status_label.setText("● Loading...")
        self.status_label.setStyleSheet("color: #F59E0B; font-size: 13px; background: transparent;")

        try:
            import os
            # Build path relative to project root
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            exe  = os.path.join(base, "backend", "build", "node_simulator.exe")

            result = subprocess.run(
                [exe],
                capture_output=True,
                text=True,
                timeout=10
            )

            data = json.loads(result.stdout)
            self.nodes = data["nodes"]
            self.canvas.load_topology(self.nodes)
            self.update_stats()

            self.status_label.setText("● Connected — 19 Nodes Active")
            self.status_label.setStyleSheet(
                "color: #10B981; font-size: 13px; background: transparent;"
            )

        except FileNotFoundError:
            self.status_label.setText("● C++ exe not found — compile first")
            self.status_label.setStyleSheet(
                "color: #EF4444; font-size: 13px; background: transparent;"
            )
            self.load_demo_topology()

        except Exception as e:
            self.status_label.setText(f"● Error: {str(e)[:40]}")
            self.status_label.setStyleSheet(
                "color: #EF4444; font-size: 13px; background: transparent;"
            )
            self.load_demo_topology()

    # ── Demo topology (if C++ not compiled) ─
    def load_demo_topology(self):
        demo_nodes = []

        # Controller
        demo_nodes.append({
            "id": 0, "ip": "192.168.0.1",
            "type": "CONTROLLER", "status": "NORMAL",
            "connections": [1, 2, 3]
        })

        # 3 Switches
        for s in range(1, 4):
            conns = [0] + list(range(4 + (s-1)*5, 4 + s*5))
            demo_nodes.append({
                "id": s,
                "ip": f"192.168.{s}.1",
                "type": "SWITCH",
                "status": "NORMAL",
                "connections": conns
            })

        # 15 Hosts
        node_id = 4
        for s in range(1, 4):
            for h in range(1, 6):
                demo_nodes.append({
                    "id": node_id,
                    "ip": f"192.168.{s}.{h+1}",
                    "type": "HOST",
                    "status": "NORMAL",
                    "connections": [s]
                })
                node_id += 1

        self.nodes = demo_nodes
        self.canvas.load_topology(self.nodes)
        self.update_stats()
        self.status_label.setText("● Demo Mode — Compile C++ for live data")
        self.status_label.setStyleSheet(
            "color: #F59E0B; font-size: 13px; background: transparent;"
        )

    # ── Simulate attack on random host ─────
    def simulate_attack(self):
        import random
        hosts = [n for n in self.nodes if n["type"] == "HOST"]
        if hosts:
            target = random.choice(hosts)
            target["status"] = "UNDER_ATTACK"
            self.canvas.update()
            self.update_stats()
            self.status_label.setText(
                f"● ATTACK on {target['ip']} — SYN Flood Detected!"
            )
            self.status_label.setStyleSheet(
                "color: #EF4444; font-size: 13px; font-weight: bold; background: transparent;"
            )

    # ── Reset all to normal ────────────────
    def reset_attack(self):
        self.canvas.reset_all()
        for node in self.nodes:
            node["status"] = "NORMAL"
        self.update_stats()
        self.status_label.setText("● All nodes normal")
        self.status_label.setStyleSheet(
            "color: #10B981; font-size: 13px; background: transparent;"
        )