#!/usr/bin/env python3
"""
Starship Simulator — UI Prototype (Retro Dark Win95)
- Movable, resizable windows
- Tabbed content
- Damage Control: node layout (railway/BSG-style) with right-click context menu → event prefill
- Crew Manager & Department Manager windows with context menus
- Systems (Power/Thermal) window (graphs placeholder)
- Market & Contracts window (tables placeholder)
- SRS Flow Inspector (ports/flows placeholder)
- Event Inbox with captain override priority
- Start menu spawns windows; retro Win95 chrome

Note: Frontend-only prototype. Hook to real data/events later per M02.
"""

import sys
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QPushButton, QTabWidget, QTableWidget, 
    QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QTextEdit,
    QSlider, QCheckBox, QComboBox, QSpinBox, QGroupBox, QFrame,
    QMenu, QMessageBox, QDialog, QDialogButtonBox, QFormLayout,
    QLineEdit, QScrollArea, QSplitter, QProgressBar, QGraphicsView,
    QGraphicsScene, QGraphicsItem, QGraphicsEllipseItem, QGraphicsLineItem,
    QGraphicsTextItem, QGraphicsRectItem, QGraphicsProxyWidget
)
from PySide6.QtCore import (
    Qt, QTimer, QRect, QPoint, QSize, Signal, QObject, QPropertyAnimation,
    QEasingCurve, QParallelAnimationGroup, QSequentialAnimationGroup
)
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QFontMetrics, QPalette,
    QLinearGradient, QRadialGradient, QIcon, QPixmap, QAction,
    QMouseEvent, QKeyEvent, QWheelEvent, QPainterPath
)


# ---------------------------------------------
# Data Models
# ---------------------------------------------

class NodeStatus(Enum):
    OK = "ok"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    WARNING = "warning"
    BREACH = "breach"

@dataclass
class DCNode:
    id: str
    label: str
    deck: str
    x: int
    y: int
    status: NodeStatus
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class Crew:
    id: str
    name: str
    dept: str
    roles: List[str]
    skills: Dict[str, int]
    status: str

@dataclass
class Department:
    id: str
    label: str
    min: int
    assigned: List[str]

class PortDir(Enum):
    IN = "in"
    OUT = "out"

@dataclass
class Port:
    id: str
    module: str
    dir: PortDir
    resource: str
    cap: int
    base_cap: int
    online: bool = True

@dataclass
class Edge:
    from_port: str
    to_port: str
    enabled: bool = True

@dataclass
class Flow:
    from_port: str
    to_port: str
    rate: float

@dataclass
class SRSState:
    ports: List[Port]
    edges: List[Edge]
    demand: Dict[str, float]


# ---------------------------------------------
# Demo Data
# ---------------------------------------------

DEMO_NODES = [
    DCNode("prop", "Propulsion", "D2", 1, 7, NodeStatus.OK, ["power"]),
    DCNode("reactor", "Reactor", "D2", 3, 7, NodeStatus.WARNING, ["power"]),
    DCNode("battery", "Battery Bank", "D2", 5, 7, NodeStatus.OK, ["power"]),
    DCNode("life", "Life Support", "D3", 3, 3, NodeStatus.OK, ["life_support"]),
    DCNode("ops", "Ops & Sensors", "D3", 5, 3, NodeStatus.OK, ["sensors"]),
    DCNode("med", "Med Bay", "D3", 7, 3, NodeStatus.OK, ["medical"]),
    DCNode("cargoA", "Cargo A", "D1", 1, 1, NodeStatus.OK),
    DCNode("refinery", "Refinery", "D1", 3, 1, NodeStatus.DEGRADED, ["industry"]),
    DCNode("mining", "Mining Prep", "D1", 5, 1, NodeStatus.OK, ["industry"]),
    DCNode("bridge", "Bridge/CIC", "D4", 5, 11, NodeStatus.OK, ["command"]),
]

DEMO_EDGES = [
    ("prop", "reactor"),
    ("reactor", "battery"),
    ("reactor", "life"),
    ("life", "ops"),
    ("ops", "med"),
    ("refinery", "battery"),
    ("mining", "refinery"),
    ("bridge", "ops"),
]

DEMO_CREW = [
    Crew("c1", "J. Rao", "engineering", ["DamageCtrl"], {"engineering": 66, "sensors": 18, "gunnery": 10}, "On duty"),
    Crew("c2", "M. Ortega", "ops", ["Sensors"], {"engineering": 22, "sensors": 74, "gunnery": 12}, "On duty"),
    Crew("c3", "K. Iwasaki", "tactical", ["Gunner"], {"engineering": 15, "sensors": 28, "gunnery": 81}, "Drill"),
    Crew("c4", "S. Bell", "medical", ["MedTech"], {"medical": 79, "sensors": 15}, "Standby"),
    Crew("c5", "A. Shankar", "engineering", ["Reactor"], {"engineering": 72, "sensors": 24}, "On duty"),
]

DEMO_DEPTS = [
    Department("engineering", "Engineering", 3, ["c1", "c5"]),
    Department("ops", "Operations", 2, ["c2"]),
    Department("tactical", "Tactical", 2, ["c3"]),
    Department("medical", "Medical", 1, ["c4"]),
]


# ---------------------------------------------
# SRS Logic
# ---------------------------------------------

def make_port(port_id: str, module: str, direction: PortDir, resource: str, cap: int, online: bool = True) -> Port:
    return Port(port_id, module, direction, resource, cap, cap, online)

def init_srs() -> SRSState:
    ports = [
        make_port("reactor.pwr_out", "reactor", PortDir.OUT, "power", 1200),
        make_port("battery.in", "battery", PortDir.IN, "power", 300),
        make_port("battery.out", "battery", PortDir.OUT, "power", 300),
        make_port("life.in", "life", PortDir.IN, "power", 40),
        make_port("refinery.in", "refinery", PortDir.IN, "power", 600),
        make_port("shield.in", "shield", PortDir.IN, "power", 400),
    ]
    
    edges = [
        Edge("reactor.pwr_out", "battery.in", True),
        Edge("reactor.pwr_out", "refinery.in", True),
        Edge("reactor.pwr_out", "life.in", True),
        Edge("reactor.pwr_out", "shield.in", True),
        Edge("battery.out", "shield.in", True),
    ]
    
    demand = {
        "battery.in": 300,
        "refinery.in": 600,
        "life.in": 40,
        "shield.in": 0,  # toggle on in UI to 400
    }
    
    return SRSState(ports, edges, demand)

def solve_flows(srs_state: SRSState) -> List[Flow]:
    sources = {}
    sinks = {}
    port_by_id = {p.id: p for p in srs_state.ports}
    
    for port in srs_state.ports:
        if not port.online:
            if port.dir == PortDir.OUT:
                sources[port.id] = 0
            else:
                sinks[port.id] = 0
            continue
            
        if port.dir == PortDir.OUT:
            sources[port.id] = port.cap
        else:
            sinks[port.id] = min(port.cap, srs_state.demand.get(port.id, 0))
    
    flows = []
    for edge in srs_state.edges:
        if not edge.enabled:
            continue
            
        src = port_by_id.get(edge.from_port)
        dst = port_by_id.get(edge.to_port)
        
        if not src or not src.online or not dst or not dst.online:
            continue
            
        flow_rate = min(sources.get(edge.from_port, 0), sinks.get(edge.to_port, 0))
        if flow_rate > 0:
            flows.append(Flow(edge.from_port, edge.to_port, flow_rate))
            sources[edge.from_port] -= flow_rate
            sinks[edge.to_port] -= flow_rate
    
    return flows

def sum_out(flows: List[Flow], port_id: str) -> float:
    return sum(f.rate for f in flows if f.from_port == port_id)

def sum_in(flows: List[Flow], port_id: str) -> float:
    return sum(f.rate for f in flows if f.to_port == port_id)


# ---------------------------------------------
# Styling and Themes
# ---------------------------------------------

class RetroTheme:
    # Colors
    BACKGROUND = QColor(26, 26, 26)  # #1a1a1a
    SURFACE = QColor(42, 42, 42)     # #2a2a2a
    BORDER = QColor(58, 58, 58)      # #3a3a3a
    TEXT = QColor(229, 229, 229)     # #e5e5e5
    TEXT_DIM = QColor(156, 156, 156) # #9c9c9c
    
    # Status colors
    STATUS_OK = QColor(16, 185, 129)      # emerald-400
    STATUS_WARNING = QColor(245, 158, 11) # amber-500
    STATUS_DEGRADED = QColor(251, 146, 60) # orange-400
    STATUS_OFFLINE = QColor(107, 114, 128) # gray-500
    STATUS_BREACH = QColor(239, 68, 68)   # red-500
    
    # Gradients
    @staticmethod
    def header_gradient():
        gradient = QLinearGradient(0, 0, 0, 32)
        gradient.setColorAt(0, QColor(51, 51, 51))   # #333
        gradient.setColorAt(1, QColor(34, 34, 34))   # #222
        return gradient
    
    # Fonts
    @staticmethod
    def get_font(size: int = 9, bold: bool = False) -> QFont:
        font = QFont("MS Sans Serif", size)
        font.setBold(bold)
        return font


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Import GUI components
    from gui_components import MainWindow
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()