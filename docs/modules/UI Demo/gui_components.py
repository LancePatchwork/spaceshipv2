#!/usr/bin/env python3
"""
GUI Components for Starship Simulator UI Prototype
"""

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from typing import List, Dict, Optional
from dataclasses import dataclass

# Import from main file
from M14_UI_Prototype_Bridge_DC_Widgets_Demo import (
    RetroTheme,
    DCNode,
    NodeStatus,
    DEMO_NODES,
    DEMO_EDGES,
    DEMO_CREW,
    DEMO_DEPTS,
    SRSState,
    init_srs,
    solve_flows,
)


class DraggableWindow(QWidget):
    """Base class for draggable, resizable windows with retro styling"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # Window state
        self.dragging = False
        self.resizing = False
        self.drag_offset = QPoint()
        self.resize_offset = QPoint()

        # Styling
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {RetroTheme.BACKGROUND.name()};
                color: {RetroTheme.TEXT.name()};
                font-family: 'MS Sans Serif';
                font-size: 9px;
            }}
        """
        )

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self.header = QFrame()
        self.header.setFixedHeight(32)
        self.header.setStyleSheet(
            f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {RetroTheme.SURFACE.name()}, stop:1 {RetroTheme.BACKGROUND.name()});
                border: 1px solid {RetroTheme.BORDER.name()};
                border-bottom: 1px solid black;
            }}
        """
        )

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(8, 4, 8, 4)

        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet(
            f"""
            QLabel {{
                color: {RetroTheme.STATUS_OK.name()};
                font-size: 12px;
                font-weight: bold;
            }}
        """
        )

        # Title
        self.title_label = QLabel(self.windowTitle())
        self.title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {RetroTheme.TEXT.name()};
                font-weight: bold;
                font-size: 9px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
        """
        )

        # Window controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(4)

        self.min_btn = QPushButton("_")
        self.max_btn = QPushButton("□")
        self.close_btn = QPushButton("×")

        for btn in [self.min_btn, self.max_btn, self.close_btn]:
            btn.setFixedSize(16, 16)
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {RetroTheme.SURFACE.name()};
                    border: 1px solid {RetroTheme.BORDER.name()};
                    color: {RetroTheme.TEXT_DIM.name()};
                    font-size: 8px;
                }}
                QPushButton:hover {{
                    background-color: {RetroTheme.BORDER.name()};
                }}
            """
            )

        self.close_btn.clicked.connect(self.close)

        header_layout.addWidget(self.status_indicator)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addLayout(controls_layout)

        # Content area
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet(
            f"""
            QWidget {{
                background-color: {RetroTheme.BACKGROUND.name()};
                border: 1px solid {RetroTheme.BORDER.name()};
                border-top: none;
            }}
        """
        )

        layout.addWidget(self.header)
        layout.addWidget(self.content_widget)

        # Resize handle
        self.resize_handle = QFrame()
        self.resize_handle.setFixedSize(12, 12)
        self.resize_handle.setStyleSheet(
            f"""
            QFrame {{
                background-color: {RetroTheme.SURFACE.name()};
                border: 1px solid {RetroTheme.BORDER.name()};
            }}
        """
        )
        self.resize_handle.setCursor(Qt.SizeFDiagCursor)

        # Position resize handle
        self.resize_handle.setParent(self)
        self.resize_handle.show()
        self.update_resize_handle_position()

    def update_resize_handle_position(self):
        """Update the position of the resize handle"""
        self.resize_handle.move(self.width() - 12, self.height() - 12)

    def resizeEvent(self, event):
        """Override resize event to update resize handle position"""
        super().resizeEvent(event)
        self.update_resize_handle_position()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            # Check if clicking on resize handle
            if self.resize_handle.geometry().contains(event.pos()):
                self.resizing = True
                self.resize_offset = event.pos()
            # Check if clicking on header for dragging
            elif self.header.geometry().contains(event.pos()):
                self.dragging = True
                # Store the global position of the click relative to the window
                self.drag_start_global = event.globalPos()
                self.drag_start_window = self.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging:
            # Calculate how far the mouse has moved from the initial click
            delta = event.globalPos() - self.drag_start_global
            # Move the window by that same amount from its original position
            new_pos = self.drag_start_window + delta
            self.move(new_pos)
        elif self.resizing:
            # Calculate new size based on mouse position
            current_rect = self.geometry()
            new_width = max(320, event.globalPos().x() - current_rect.left())
            new_height = max(240, event.globalPos().y() - current_rect.top())
            self.resize(new_width, new_height)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.dragging = False
        self.resizing = False
        super().mouseReleaseEvent(event)


class DamageControlWindow(DraggableWindow):
    """Damage Control visualization with node graph"""

    def __init__(self, parent=None):
        super().__init__("Damage Control", parent)
        self.setMinimumSize(600, 400)
        self.setup_damage_control()

    def setup_damage_control(self):
        layout = QVBoxLayout(self.content_widget)
        layout.setContentsMargins(8, 8, 8, 8)

        # Create graphics view for node visualization
        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        self.graphics_view.setStyleSheet(
            f"""
            QGraphicsView {{
                background-color: {RetroTheme.BACKGROUND.name()};
                border: 1px solid {RetroTheme.BORDER.name()};
            }}
        """
        )

        # Add nodes and edges
        self.setup_nodes()
        self.setup_edges()

        layout.addWidget(self.graphics_view)

    def setup_nodes(self):
        for node in DEMO_NODES:
            # Create node ellipse
            ellipse = QGraphicsEllipseItem(node.x * 60, node.y * 40, 50, 30)

            # Set color based on status
            status_colors = {
                NodeStatus.OK: RetroTheme.STATUS_OK,
                NodeStatus.WARNING: RetroTheme.STATUS_WARNING,
                NodeStatus.DEGRADED: RetroTheme.STATUS_DEGRADED,
                NodeStatus.OFFLINE: RetroTheme.STATUS_OFFLINE,
                NodeStatus.BREACH: RetroTheme.STATUS_BREACH,
            }

            color = status_colors.get(node.status, RetroTheme.STATUS_OK)
            ellipse.setBrush(QBrush(color))
            ellipse.setPen(QPen(RetroTheme.BORDER, 2))

            # Add text label
            text = QGraphicsTextItem(node.label)
            text.setPos(node.x * 60 + 5, node.y * 40 + 8)
            text.setDefaultTextColor(RetroTheme.TEXT)
            text.setFont(RetroTheme.get_font(8))

            self.graphics_scene.addItem(ellipse)
            self.graphics_scene.addItem(text)

    def setup_edges(self):
        for from_id, to_id in DEMO_EDGES:
            from_node = next((n for n in DEMO_NODES if n.id == from_id), None)
            to_node = next((n for n in DEMO_NODES if n.id == to_id), None)

            if from_node and to_node:
                line = QGraphicsLineItem(
                    from_node.x * 60 + 25,
                    from_node.y * 40 + 15,
                    to_node.x * 60 + 25,
                    to_node.y * 40 + 15,
                )
                line.setPen(QPen(RetroTheme.TEXT_DIM, 2))
                self.graphics_scene.addItem(line)


class CrewManagerWindow(DraggableWindow):
    """Crew and Department Management"""

    def __init__(self, parent=None):
        super().__init__("Crew Manager", parent)
        self.setMinimumSize(500, 350)
        self.setup_crew_manager()

    def setup_crew_manager(self):
        layout = QVBoxLayout(self.content_widget)
        layout.setContentsMargins(8, 8, 8, 8)

        # Create tab widget
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet(
            f"""
            QTabWidget::pane {{
                border: 1px solid {RetroTheme.BORDER.name()};
                background-color: {RetroTheme.BACKGROUND.name()};
            }}
            QTabBar::tab {{
                background-color: {RetroTheme.SURFACE.name()};
                border: 1px solid {RetroTheme.BORDER.name()};
                padding: 4px 8px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {RetroTheme.BACKGROUND.name()};
                border-bottom: 1px solid {RetroTheme.BACKGROUND.name()};
            }}
        """
        )

        # Crew tab
        crew_tab = self.create_crew_tab()
        tab_widget.addTab(crew_tab, "Crew")

        # Departments tab
        dept_tab = self.create_departments_tab()
        tab_widget.addTab(dept_tab, "Departments")

        layout.addWidget(tab_widget)

    def create_crew_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Crew table
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Name", "Department", "Roles", "Skills", "Status"])

        # Populate crew data
        table.setRowCount(len(DEMO_CREW))
        for i, crew in enumerate(DEMO_CREW):
            table.setItem(i, 0, QTableWidgetItem(crew.name))
            table.setItem(i, 1, QTableWidgetItem(crew.dept))
            table.setItem(i, 2, QTableWidgetItem(", ".join(crew.roles)))
            skills_str = ", ".join([f"{k}: {v}" for k, v in crew.skills.items()])
            table.setItem(i, 3, QTableWidgetItem(skills_str))
            table.setItem(i, 4, QTableWidgetItem(crew.status))

        table.resizeColumnsToContents()
        layout.addWidget(table)

        return widget

    def create_departments_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Department tree
        tree = QTreeWidget()
        tree.setHeaderLabels(["Department", "Min Required", "Assigned", "Status"])

        for dept in DEMO_DEPTS:
            item = QTreeWidgetItem()
            item.setText(0, dept.label)
            item.setText(1, str(dept.min))
            item.setText(2, str(len(dept.assigned)))

            # Status based on min requirements
            if len(dept.assigned) >= dept.min:
                item.setText(3, "✓ Adequate")
                item.setForeground(3, QBrush(RetroTheme.STATUS_OK))
            else:
                item.setText(3, "⚠ Understaffed")
                item.setForeground(3, QBrush(RetroTheme.STATUS_WARNING))

            tree.addTopLevelItem(item)

        tree.resizeColumnToContents(0)
        layout.addWidget(tree)

        return widget


class SRSInspectorWindow(DraggableWindow):
    """SRS Flow Inspector"""

    def __init__(self, parent=None):
        super().__init__("SRS Flow Inspector", parent)
        self.setMinimumSize(600, 400)
        self.srs_state = init_srs()
        self.setup_srs_inspector()

    def setup_srs_inspector(self):
        layout = QVBoxLayout(self.content_widget)
        layout.setContentsMargins(8, 8, 8, 8)

        # Controls
        controls_layout = QHBoxLayout()

        self.shield_toggle = QCheckBox("Shield Power")
        self.shield_toggle.stateChanged.connect(self.update_shield_demand)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_flows)

        controls_layout.addWidget(self.shield_toggle)
        controls_layout.addStretch()
        controls_layout.addWidget(self.refresh_btn)

        layout.addLayout(controls_layout)

        # Flow visualization
        self.flow_table = QTableWidget()
        self.flow_table.setColumnCount(4)
        self.flow_table.setHorizontalHeaderLabels(["From", "To", "Rate", "Status"])

        layout.addWidget(self.flow_table)

        # Port status
        self.port_table = QTableWidget()
        self.port_table.setColumnCount(6)
        self.port_table.setHorizontalHeaderLabels(
            ["Port", "Module", "Dir", "Resource", "Cap", "Online"]
        )

        layout.addWidget(self.port_table)

        self.refresh_flows()
        self.update_port_table()

    def update_shield_demand(self, state):
        if state == Qt.Checked:
            self.srs_state.demand["shield.in"] = 400
        else:
            self.srs_state.demand["shield.in"] = 0
        self.refresh_flows()

    def refresh_flows(self):
        flows = solve_flows(self.srs_state)

        self.flow_table.setRowCount(len(flows))
        for i, flow in enumerate(flows):
            self.flow_table.setItem(i, 0, QTableWidgetItem(flow.from_port))
            self.flow_table.setItem(i, 1, QTableWidgetItem(flow.to_port))
            self.flow_table.setItem(i, 2, QTableWidgetItem(f"{flow.rate:.1f}"))
            self.flow_table.setItem(i, 3, QTableWidgetItem("Active"))

        self.flow_table.resizeColumnsToContents()

    def update_port_table(self):
        self.port_table.setRowCount(len(self.srs_state.ports))
        for i, port in enumerate(self.srs_state.ports):
            self.port_table.setItem(i, 0, QTableWidgetItem(port.id))
            self.port_table.setItem(i, 1, QTableWidgetItem(port.module))
            self.port_table.setItem(i, 2, QTableWidgetItem(port.dir.value))
            self.port_table.setItem(i, 3, QTableWidgetItem(port.resource))
            self.port_table.setItem(i, 4, QTableWidgetItem(str(port.cap)))
            self.port_table.setItem(i, 5, QTableWidgetItem("✓" if port.online else "✗"))

        self.port_table.resizeColumnsToContents()


class EventInboxWindow(DraggableWindow):
    """Event Inbox with Priority System"""

    def __init__(self, parent=None):
        super().__init__("Event Inbox", parent)
        self.setMinimumSize(500, 300)
        self.setup_event_inbox()

    def setup_event_inbox(self):
        layout = QVBoxLayout(self.content_widget)
        layout.setContentsMargins(8, 8, 8, 8)

        # Priority controls
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("Captain Override Priority:"))

        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(0, 100)
        self.priority_spin.setValue(50)

        priority_layout.addWidget(self.priority_spin)
        priority_layout.addStretch()

        layout.addLayout(priority_layout)

        # Event list
        self.event_list = QTreeWidget()
        self.event_list.setHeaderLabels(["Time", "Event", "Priority", "Source", "Actions"])

        # Add some demo events
        demo_events = [
            ("14:32:15", "Power shortage detected", "HIGH", "SRS", "Override"),
            ("14:31:42", "Reactor temperature rising", "MEDIUM", "Thermal", "Acknowledge"),
            ("14:30:18", "Crew member J. Rao assigned", "LOW", "Crew", "View"),
            ("14:29:55", "Shield generator offline", "HIGH", "Damage Control", "Override"),
        ]

        for time, event, priority, source, action in demo_events:
            item = QTreeWidgetItem()
            item.setText(0, time)
            item.setText(1, event)
            item.setText(2, priority)
            item.setText(3, source)
            item.setText(4, action)

            # Color code by priority
            if priority == "HIGH":
                item.setForeground(2, QBrush(RetroTheme.STATUS_BREACH))
            elif priority == "MEDIUM":
                item.setForeground(2, QBrush(RetroTheme.STATUS_WARNING))
            else:
                item.setForeground(2, QBrush(RetroTheme.STATUS_OK))

            self.event_list.addTopLevelItem(item)

        self.event_list.resizeColumnToContents(0)
        layout.addWidget(self.event_list)


class MainWindow(QMainWindow):
    """Main application window with start menu"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Starship Simulator - Bridge")
        self.setGeometry(100, 100, 1200, 800)

        # Set retro styling
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background-color: {RetroTheme.BACKGROUND.name()};
                color: {RetroTheme.TEXT.name()};
            }}
        """
        )

        # Track open windows
        self.open_windows = []

        self.setup_ui()

    def setup_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Start menu bar
        menu_bar = QFrame()
        menu_bar.setFixedHeight(40)
        menu_bar.setStyleSheet(
            f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {RetroTheme.SURFACE.name()}, stop:1 {RetroTheme.BACKGROUND.name()});
                border-bottom: 1px solid {RetroTheme.BORDER.name()};
            }}
        """
        )

        menu_layout = QHBoxLayout(menu_bar)
        menu_layout.setContentsMargins(8, 4, 8, 4)

        # Start button
        start_btn = QPushButton("START")
        start_btn.setFixedSize(80, 32)
        start_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {RetroTheme.SURFACE.name()}, stop:1 {RetroTheme.BACKGROUND.name()});
                border: 2px outset {RetroTheme.BORDER.name()};
                font-weight: bold;
                font-size: 9px;
            }}
            QPushButton:pressed {{
                border: 2px inset {RetroTheme.BORDER.name()};
            }}
        """
        )
        start_btn.clicked.connect(self.show_start_menu)

        menu_layout.addWidget(start_btn)
        menu_layout.addStretch()

        # Status bar
        status_label = QLabel("Ready")
        status_label.setStyleSheet(
            f"""
            QLabel {{
                color: {RetroTheme.TEXT_DIM.name()};
                font-size: 9px;
            }}
        """
        )
        menu_layout.addWidget(status_label)

        layout.addWidget(menu_bar)

        # Main content area
        content_area = QLabel("Starship Simulator Bridge\nClick START to open system windows")
        content_area.setAlignment(Qt.AlignCenter)
        content_area.setStyleSheet(
            f"""
            QLabel {{
                color: {RetroTheme.TEXT_DIM.name()};
                font-size: 16px;
                background-color: {RetroTheme.BACKGROUND.name()};
            }}
        """
        )
        layout.addWidget(content_area)

    def show_start_menu(self):
        """Show context menu with available windows"""
        menu = QMenu(self)

        # Add menu items for each window type
        dc_action = QAction("Damage Control", self)
        dc_action.triggered.connect(self.open_damage_control)
        menu.addAction(dc_action)

        crew_action = QAction("Crew Manager", self)
        crew_action.triggered.connect(self.open_crew_manager)
        menu.addAction(crew_action)

        srs_action = QAction("SRS Inspector", self)
        srs_action.triggered.connect(self.open_srs_inspector)
        menu.addAction(srs_action)

        events_action = QAction("Event Inbox", self)
        events_action.triggered.connect(self.open_event_inbox)
        menu.addAction(events_action)

        # Show menu at cursor position
        menu.exec(self.mapToGlobal(self.sender().pos() + QPoint(0, self.sender().height())))

    def open_damage_control(self):
        window = DamageControlWindow(self)
        window.show()
        self.open_windows.append(window)

    def open_crew_manager(self):
        window = CrewManagerWindow(self)
        window.show()
        self.open_windows.append(window)

    def open_srs_inspector(self):
        window = SRSInspectorWindow(self)
        window.show()
        self.open_windows.append(window)

    def open_event_inbox(self):
        window = EventInboxWindow(self)
        window.show()
        self.open_windows.append(window)
