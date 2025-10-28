from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from PyQt6.QtWidgets import *
from PyQt6.QtSvgWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import pydot
import datetime
from io import BytesIO
from pinger import PingManager
import asyncio
import threading

class HostNode(QGraphicsEllipseItem):
    def __init__(self, host_data, ping_status):
        super().__init__(-30, -30, 60, 60)
        self.host_data = host_data
        self.setBrush(QBrush(QColor("green" if ping_status else "red")))
        self.setPen(QPen(Qt.GlobalColor.black))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

        # 텍스트 추가
        label = host_data.get("host_이름", "Unknown")
        text = QGraphicsTextItem(label, self)
        text.setDefaultTextColor(Qt.GlobalColor.white)
        text.setPos(-text.boundingRect().width()/2, -10)

    def mousePressEvent(self, event):
        ip = self.host_data.get("IP_주소", "N/A")
        name = self.host_data.get("host_이름", "Unknown")
        설명 = self.host_data.get("host_설명", "")
        QToolTip.showText(event.screenPos().toPoint(), f"IP: {ip}\n이름: {name}\n{설명}")

class NetworkTopologyViewer(QWidget):
    def __init__(self, plot_datas):
        super().__init__()
        self.plot_datas = plot_datas
        self.ping_results = {}

        self.pinger = PingManager([host['IP_주소'] for host in plot_datas if host.get('IP_주소')])
        self.pinger.ping_updated.connect(self.on_ping_results)

        self.init_ui()
        

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.svg_widget = QSvgWidget()
        layout.addWidget(self.svg_widget)

        self.refresh_btn = QPushButton("수동 Ping 실행")
        self.refresh_btn.clicked.connect(self.run_local_ping)
        layout.addWidget(self.refresh_btn)

        self.update_graph()

    def run_local_ping(self):
        self.pinger.run_once()


    def on_ping_results(self, results: dict):
        self.ping_results = results
        self.update_graph()

    def run_ping(self):
        asyncio.create_task(self.pinger.run_once())

    def run_ping_loop(self):
        asyncio.run(self.pinger.run())

    # def init_ui(self):
    #     if self.layout():
    #         QWidget().setLayout(self.layout())  # 기존 layout 제거

    #     layout = QVBoxLayout()
    #     self.svg_widget = QSvgWidget()
    #     layout.addWidget(self.svg_widget)

    #     self.refresh_btn = QPushButton("수동 새로고침")
    #     self.refresh_btn.clicked.connect(self.run_ping)
    #     layout.addWidget(self.refresh_btn)

    #     self.setLayout(layout)  # 여기에서 명시적으로 설정

    #     self.update_graph()

    # def init_ui(self):
    #     self.setWindowTitle("네트워크 토폴로지 뷰어")
    #     layout = QVBoxLayout()

    #     self.status_label = QLabel("상태: 초기화 완료")
    #     self.svg_widget = QSvgWidget()
    #     self.refresh_btn = QPushButton("새로고침")

    #     self.refresh_btn.clicked.connect(self.update_graph)
    #     layout.addWidget(self.status_label)
    #     layout.addWidget(self.svg_widget)
    #     layout.addWidget(self.refresh_btn)
    #     self.setLayout(layout)

    #     self.update_graph()

    def set_ping_results(self, results: dict):
        self.ping_results = results
        self.update_graph()

    def get_color(self, host):
        ip = host.get("IP_주소")
        alive = self.ping_results.get(ip)
        return "#4CAF50" if alive else "#F44336"  # Green / Red

    # def update_graph(self):
    #     graph = pydot.Dot("my_graph", graph_type="digraph", bgcolor="white")

    #     for host in self.plot_datas:
    #         try:
    #             label_txt = f"{host.get('host_이름')} \n ({host.get('IP_주소')})"
    #             nodeName = host.get('IP_주소').replace('.', '_')
    #             color = self.get_color(host)
    #             graph.add_node(pydot.Node(nodeName, label=label_txt, style='filled',
    #                                       fillcolor=color, fontcolor='white'))
    #         except Exception as e:
    #             print('Node Generation error:', e)

    #     for host in self.plot_datas:
    #         try:
    #             parent = host.get("상위IP", '').replace('.', '_')
    #             child = host.get('IP_주소', '').replace('.', '_')
    #             if parent and child:
    #                 graph.add_edge(pydot.Edge(parent, child, color=self.get_color(host)))
    #         except Exception as e:
    #             print('Edge Generation error:', e)

    #     svg_data = graph.create_svg()
    #     svg_bytes = QByteArray(svg_data)
    #     self.svg_widget.load(svg_bytes)
    #     self.status_label.setText(f"갱신됨: {datetime.datetime.now().strftime('%H:%M:%S')}")

    def update_graph(self):
        graph = pydot.Dot("network", graph_type="digraph", bgcolor="white")

        for host in self.plot_datas:
            label = f"{host.get('host_이름')} \n({host.get('IP_주소')})"
            name = host.get('IP_주소', '').replace('.', '_')
            color = self.get_color(host)
            graph.add_node(pydot.Node(name, label=label, style='filled', fillcolor=color, fontcolor='white'))

        for host in self.plot_datas:
            상위IP = host.get("상위IP")
            하위IP = host.get("IP_주소")
            if not 상위IP or not 하위IP:
                continue
            graph.add_edge(pydot.Edge(상위IP.replace('.', '_'), 하위IP.replace('.', '_'),
                                    color=self.get_color(host)))

        svg_data = graph.create_svg()  # 이미 bytes
        self.svg_widget.load(svg_data)
