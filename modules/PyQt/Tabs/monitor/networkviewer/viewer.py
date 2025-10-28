from modules.common_import import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import platform


class PingDialog(QDialog):
    def __init__(self, ip, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Ping 실행 중 - {ip}")
        self.resize(500, 400)

        self.layout = QVBoxLayout(self)

        self.output = QTextEdit(self)
        self.output.setReadOnly(True)
        self.layout.addWidget(self.output)

        self.stop_button = QPushButton("중지", self)
        self.stop_button.clicked.connect(self.stop_ping)
        self.layout.addWidget(self.stop_button)

        self.process = QProcess(self)
        self.process.setProgram("ping")

        import platform
        args = ["-t", ip] if platform.system().lower() == "windows" else [ip]
        self.process.setArguments(args)

        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(self.read_error)

        self.process.start()

    def read_output(self):
        raw_data = self.process.readAllStandardOutput().data()
        data = self.try_decode(raw_data)
        self.output.append(data.strip())

    def read_error(self):
        raw_data = self.process.readAllStandardError().data()
        data = self.try_decode(raw_data)
        self.output.append(f"[오류] {data.strip()}")

    def try_decode(self, data: bytes) -> str:
        encodings = ['utf-8']
        if platform.system().lower() == "windows":
            encodings += ['cp949', 'euc-kr']
        for enc in encodings:
            try:
                return data.decode(enc)
            except UnicodeDecodeError:
                continue
        return "[디코딩 실패]"

    def stop_ping(self):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.terminate()
            self.process.waitForFinished(1000)  # 1초 기다리고 안 되면
            if self.process.state() != QProcess.ProcessState.NotRunning:
                self.process.kill()
                self.process.waitForFinished()
        self.close()

    def closeEvent(self, event):
        self.stop_ping()  # 강제로 종료하고 닫기
        event.accept()


class NodeFormDialog(QDialog):
    def __init__(self, parent=None, node_data=None):
        super().__init__(parent)
        self.setWindowTitle("노드 생성 / 수정")
        self.resize(400, 300)

        self.node_data = node_data or {
            'id': -1, 'Category': '', 'IP_주소': '',
            'host_이름': '', 'host_설명': '', 'MAC_주소': '',
            '비고': '',  '상위IP': ''
        }

        self.result_data = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        # ID (label only)
        self.id_label = QLabel(str(self.node_data.get("id", -1)))
        form_layout.addRow("ID", self.id_label)

        # 상위IP (label only)
        self.parent_ip_label = QLabel(self.node_data.get("상위IP", ""))
        form_layout.addRow("상위 IP", self.parent_ip_label)

        # IP_주소
        self.ip_edit = QLineEdit(self.node_data.get("IP_주소", ""))
        ip_regex = QRegularExpression(r'^(\d{1,3}\.){3}\d{1,3}$')
        self.ip_edit.setValidator(QRegularExpressionValidator(ip_regex))
        form_layout.addRow("IP 주소", self.ip_edit)

        # 나머지 항목들
        self.edits = {}
        for field in ["Category", "Category_순서", "host_이름", "host_설명", "MAC_주소", "비고", "Group"]:
            line_edit = QLineEdit(str(self.node_data.get(field, "")))
            form_layout.addRow(field, line_edit)
            self.edits[field] = line_edit

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("취소")
        self.ok_button.clicked.connect(self.on_ok)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def on_ok(self):
        ip_text = self.ip_edit.text().strip()
        if not self.ip_edit.hasAcceptableInput():
            QMessageBox.warning(self, "입력 오류", "올바른 IP 주소를 입력하세요.")
            return

        result = {
            'id': int(self.id_label.text()),
            '상위IP': self.parent_ip_label.text(),
            'IP_주소': ip_text,
        }
        for key, edit in self.edits.items():
            result[key] = edit.text().strip()

        self.result_data = result
        self.accept()

    def get_data(self):
        return self.result_data
    


class HostNode( QGraphicsPathItem):
    def __init__(self, host_data: dict, editable=False):
        super().__init__()  # 원형이 아닌 사각형, 크기 조정
        self.host_data = host_data
        self.ip = host_data.get("IP_주소", "N/A").rstrip()
        self.host_name = host_data.get("host_이름", "Unknown").rstrip()
        self.editable = editable

        self.color_map = {
            "N/A": "gray",
            "정상": "green",
            "경고": "orange",
            "주의": "yellow",
            "비정상": "red"
        }

        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

        self.text_item = self.create_text_item(self.host_name)

        self.render()

        # Z-order 조정: 노드가 에지 위로 오도록 설정
        self.setZValue(1)
        self.set_status(True)
    
    def render(self):
        # 텍스트 길이에 맞춰 사각형 크기 재조정
        text_width = self.text_item.boundingRect().width()
        text_height = self.text_item.boundingRect().height()

        # 사각형 크기 계산 (너비는 텍스트 길이에 맞추고, 높이는 고정)
        rect_width = max(text_width + 20, 80)  # 최소 너비는 80으로 고정
        rect_height = text_height + 20  # 텍스트 높이에 여백 추가

        # 라운드된 사각형 테두리 생성
        path = QPainterPath()
        path.addRoundedRect(-rect_width / 2, -rect_height / 2, rect_width, rect_height, 10, 10)  # 라운드된 사각형
        self.setPath(path)

        self.setPen(QPen(Qt.GlobalColor.black, 2))  # 테두리 설정
        self.setBrush(QBrush(QColor("green")))  # 배경 색상 설정

        # 텍스트 중앙 배치
        self.text_item.setPos(-self.text_item.boundingRect().width() / 2, -self.text_item.boundingRect().height() / 2)

    #### getter
    def get_host_data(self):
        return self.host_data
    def get_ip(self):
        return self.ip
    def get_label(self):
        return self.host_name

    def create_text_item(self, label: str) -> QGraphicsTextItem:
        """Create and return a QGraphicsTextItem for the node label."""
        text_item = QGraphicsTextItem(label, self)
        text_item.setDefaultTextColor(Qt.GlobalColor.white)
        return text_item

    def set_status(self, status:str ):
        color = self.color_map.get(status, "gray")
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(Qt.GlobalColor.black, 2))

    def mouseDoubleClickEvent(self, event):
        """Handle double-click events to trigger local ping."""
        if event.button() == Qt.MouseButton.LeftButton:
            try:
                dialog = PingDialog(self.ip, self.scene().viewer)
                dialog.exec()
            except Exception as e:
                print ( 'Ping 실행 중 오류 발생: ', e )


    def contextMenuEvent(self, event):
        menu = QMenu()
        print ( 'self.scene().viewer.topology_edit_mode : ', self.scene().viewer.topology_edit_mode )
        if self.scene().viewer.topology_edit_mode:
            # 노드 수정
            edit_node_action = QAction("노드 수정", menu)
            edit_node_action.triggered.connect(self.open_edit_dialog)
            menu.addAction(edit_node_action)

            # 노드 삭제
            remove_node_action = QAction("노드 삭제", menu)
            remove_node_action.triggered.connect(lambda: self.scene().viewer.remove_node(self.ip))
            menu.addAction(remove_node_action)

            # 구분선
            menu.addSeparator()

            # 부모 관계 삭제
            remove_parent_action = QAction("부모 관계 삭제", menu)
            remove_parent_action.triggered.connect(lambda: self.scene().viewer.remove_parent_of_node(self.ip))
            menu.addAction(remove_parent_action)

        # else: ### view only
        #     local_ping_action = QAction("Local Ping", menu)
        #     local_ping_action.triggered.connect(self.local_ping)
        #     menu.addAction(local_ping_action)

        menu.exec(event.screenPos())




    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        for item in self.scene().items():
            if isinstance(item, HostNode) and item is not self:
                if self.collidesWithItem(item):
                    self.scene().connect_nodes(parent=item, child=self)
                    break
        # 노드 이동 후 엣지 업데이트
        self.scene().viewer.render_edges()

    def update_data(self, updated_data: dict):
        self.host_data.update(updated_data)
        self.ip = updated_data.get("IP_주소", self.ip)
        self.host_name = updated_data.get("host_이름", self.host_name)
        self.text_item.setPlainText(self.host_name)
        self.render()

    def open_edit_dialog(self):
        # 현재 노드 데이터를 사전 형태로 구성
        # data = {
        #     "id": self.node_id,
        #     "Category": self.category,
        #     "Category_순서": self.order,
        #     "IP_주소": self.ip,
        #     "host_이름": self.hostname,
        #     "host_설명": self.description,
        #     "MAC_주소": self.mac,
        #     "비고": self.note,
        #     "Group": self.group,
        #     "상위IP": self.parent_ip,
        # }

        dialog = NodeFormDialog(node_data=self.host_data)
        if dialog.exec():
            updated = dialog.get_data()
            print ( 'updated : ', updated )
            self.update_data(updated)
            # 노드가 변경되었으므로, 엣지 업데이트 필요
            self.scene().viewer.render_edges()

class EdgeItem(QGraphicsLineItem):
    def __init__(self, parent_node: HostNode, child_node: HostNode):
        super().__init__()
        self.parent_node = parent_node
        self.child_node = child_node

        pen = QPen(Qt.GlobalColor.black, 2)
        self.setPen(pen)
        self.setZValue(-1)

        self.update_position()

    def update_position(self):
        line = QLineF(self.parent_node.scenePos(), self.child_node.scenePos())
        self.setLine(line)

class StatusPieChart(QGraphicsItem):
    def __init__(self, summary: dict, radius=60, parent=None):
        super().__init__(parent)
        self.summary = summary
        self.radius = radius
        self.colors = {
            "정상": QColor("green"),
            "주의": QColor("yellow"),
            "경고": QColor("orange"),
            "비정상": QColor("red"),
            "N/A": QColor("gray")
        }

    def boundingRect(self):
        return QRectF(0, 0, self.radius * 2, self.radius * 2)

    def paint(self, painter, option, widget):
        total = self.summary.get("총 host", 0)
        if total == 0:
            return
        start_angle = 0
        for key, color in self.colors.items():
            value = self.summary.get(key, 0)
            if value <= 0:
                continue
            span_angle = 360 * value / total
            painter.setBrush(QBrush(color))
            painter.drawPie(self.boundingRect(), int(start_angle * 16), int(span_angle * 16))
            start_angle += span_angle

class CustomView(QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._zoom_factor = 1.15  # 확대/축소 비율
        self.setDragMode(QGraphicsView.ScrollHandDrag)  # 마우스 드래그로 이동 가능

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            zoom = self._zoom_factor
        else:
            zoom = 1 / self._zoom_factor
        self.scale(zoom, zoom)


class CustomScene(QGraphicsScene):
    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer

    def connect_nodes(self, parent: HostNode, child: HostNode):
        if not self.viewer.topology_edit_mode:
            return
        parent_ip = parent.ip
        child_ip = child.ip
        if not parent_ip or not child_ip or child_ip in self.viewer.parent_relations:
            return
        self.viewer.parent_relations[child_ip] = parent_ip
        self.viewer.edges.append((parent_ip, child_ip))
        self.viewer.render_edges()

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
        if not self.viewer.topology_edit_mode:
            return
        item = self.itemAt(event.scenePos(), QTransform())
        if item is None:
            menu = QMenu()
            add_node_action = QAction("노드 생성", menu)
            add_node_action.triggered.connect(lambda: self.viewer.create_node_at(event.scenePos()))
            menu.addAction(add_node_action)
            menu.exec(event.screenPos())
        else:
            super().contextMenuEvent(event)

class Base_StatusSummary(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.summary = {}
    
    def setup_ui(self):
        self.pie_view = QLabel()
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.pie_view)
        layout.addWidget(self.info_label)
        self.setLayout(layout)



    def update_summary(self, summary: dict):
        self.summary = summary
        self._update_pie()
        self._update_label()

    def _update_pie(self):

        figure = Figure(figsize=(3, 3))
        canvas = FigureCanvas(figure)
        ax = figure.add_subplot(111)

        labels = []
        sizes = []
        colors = {
            "정상": "green",
            "주의": "blue",
            "경고": "orange",
            "비정상": "red",
            "N/A": "gray"
        }

        for key, color in colors.items():
            count = self.summary.get(key, 0)
            if count > 0:
                labels.append(f"{key} ({count})")
                sizes.append(count)

        ax.clear()
        ax.pie(sizes, labels=labels, colors=[colors[l.split()[0]] for l in labels], startangle=90, autopct='%1.1f%%')
        ax.axis("equal")

        layout = self.layout()
        layout.replaceWidget(self.pie_view, canvas)
        self.pie_view.deleteLater()
        self.pie_view = canvas

    def _update_label(self):
        total = self.summary.get("총 host", 0)
        text = "\n".join(f"{k}: {v}" for k, v in self.summary.items() if k != "총 host")
        self.info_label.setText(f"<b>총 host:</b> {total}\n{text}")

class StatusSummaryDialog(QDialog, Base_StatusSummary):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("네트워크 상태 통계")
        self.setMinimumSize(300, 300)

        self.setup_ui()

class Widget_StatusSummary(Base_StatusSummary):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

from modules.mixin.lazyparentattrmixin_V2 import LazyParentAttrMixin_V2
class NetworkTopologyViewer(QWidget, LazyParentAttrMixin_V2):
    """ view 용 
        kwargs:
        plot_datas : plot 용 데이터 ,api get 사용
        topology_edit_mode : 편집 모드 여부
    """
    def __init__(self, parent, plot_datas: list[dict]=None, ws_url_name:str=None, topology_edit_mode:bool=False):
        super().__init__(parent)
        self.event_bus = event_bus
        self._start_time = None
        self._stop_time = None

        self.ws_url_name = ws_url_name or 'network_monitor'
        self.ws_url = INFO.get_WS_URL_by_name(self.ws_url_name)

        self.plot_datas = plot_datas
        self.topology_edit_mode = topology_edit_mode
        self.ui_initialized = False

        self.nodes: Dict[str, HostNode] = {}
        self.node_positions: Dict[str, QPointF] = {}
        self.node_items: Dict[str, HostNode] = {}
        self.edges: List[Tuple[str, str]] = []
        self.edge_items: List[QGraphicsLineItem] = []
        self.parent_relations: Dict[str, str] = {}
        self.ping_status: Dict[str, bool] = {}

        self.map_ip_result = defaultdict(list)
        self.max_ping_count = 6     ### result를 최대 6개만 유지

        self.dialog_status:Optional[StatusSummaryDialog] = None
        self.pie_chart_item = None  # pie chart holder

        self.run_lazy_attr()


    def on_all_lazy_attrs_ready(self):
        try:
            APP_ID = self.lazy_attrs['APP_ID']
            self.APP_ID = APP_ID
            self.app_dict = INFO.APP_권한_MAP_ID_TO_APP[APP_ID]
            self.table_name = Utils.get_table_name(APP_ID)
            self.init_ui()
            if self.plot_datas:
                self.load_plot_data(self.plot_datas)
            self.subscribe_gbus()

            if hasattr(self, 'data') and self.data:
                self.on_data_changed(self.data)

        except Exception as e:
            logger.error(f"on_all_lazy_attrs_ready 오류: {e}")
            logger.error(f"{traceback.format_exc()}")
            trace = traceback.format_exc().replace('\n', '<br>')
            Utils.generate_QMsg_critical(self, title='on_all_lazy_attrs_ready 오류', text=f"{e}<br>{trace}")



    @property
    def start_status_text(self):
        if not self._start_time:    
            self._start_time = datetime.now()
        return f"모니터링 시작({self._start_time.strftime('%Y-%m-%d %H:%M:%S')})"
    @property
    def stop_status_text(self):
        if not self._stop_time:
            self._stop_time = datetime.now()    
        return f"모니터링 중지({self._stop_time.strftime('%Y-%m-%d %H:%M:%S')})"

    def init_ui(self):
        layout = QVBoxLayout(self)

        wid_container = QWidget()
        layout_container = QHBoxLayout(wid_container)
        self.lb_status = QLabel("")
        layout_container.addWidget(self.lb_status)
        self.pb_status = CustomPushButton(wid_container, "상태 요약(PIE-Chart)")
        self.pb_status.clicked.connect(self.show_summary_pie_chart)
        layout_container.addWidget(self.pb_status)
        layout.addWidget(wid_container)

        self.scene = CustomScene(self)
        self.view = CustomView(self.scene)
        layout.addWidget(self.view)
        self.ui_initialized = True
        # if self.topology_edit_mode:
        #     refresh_btn = QPushButton("수동 새로고침")
        #     refresh_btn.clicked.connect(self.manual_refresh)
        #     layout.addWidget(refresh_btn)

    def get_current_topology_data(self) -> List[Dict]:
        scene_width = self.scene.width()
        scene_height = self.scene.height()

        data = []
        for ip, node_item in self.node_items.items():
            pos = node_item.pos()
            node_data = node_item.get_host_data()
            if 'id' not in node_data:
                node_data['id'] = -1
            
            node_data.update ({
                "rel_x": round(pos.x() / scene_width, 4),
                "rel_y": round(pos.y() / scene_height, 4)
            })
            data.append(node_data)
        return data

    def load_plot_data(self, plot_datas: List[Dict]):
        self.plot_datas = plot_datas
        # ⛔ 리스트 참조 먼저 clear
        self.nodes.clear()
        self.edges.clear()
        self.edge_items.clear()  # <-- 여기!!
        self.node_items.clear()
        self.parent_relations.clear()

        self.scene.clear()  # <-- 이후에 clear 안전함`

        children_map: Dict[str, List[str]] = {}
        node_data_map: Dict[str, Dict] = {}

        for item in plot_datas:
            ip = item.get("IP_주소", "").strip()
            parent_ip = item.get("상위IP", "").strip() if item.get("상위IP") else None
            if not ip:
                continue
            node_data_map[ip] = item
            if parent_ip and ip != parent_ip:
                children_map.setdefault(parent_ip, []).append(ip)
                self.edges.append((parent_ip, ip))
                self.parent_relations[ip] = parent_ip
            else:
                children_map.setdefault(None, []).append(ip)
        # 💡 상대 좌표 기반으로 위치 복원

        # 복원 전 고정된 scene 크기 설정 (이 크기 기준으로 상대좌표 복원됨)
        self.scene.setSceneRect(0, 0, 2000, 1500)  # 또는 너가 알고 있는 fixed 기준
        for ip, node_data in node_data_map.items():
            node = HostNode(node_data)
            rel_x = node_data.get("rel_x")
            rel_y = node_data.get("rel_y")

            if rel_x is not None and rel_y is not None:
                # scene 크기 기준 복원
                x = float(rel_x) * self.scene.width()
                y = float(rel_y) * self.scene.height()
                pos = QPointF(x, y)
                node.setPos(pos)
            else:
                # fallback - 나중에 정렬하는 코드 추가해도 됨
                node.setPos(QPointF(0, 0))  # or skip?

            self.scene.addItem(node)
            self.nodes[ip] = node
            self.node_items[ip] = node

        # def assign_positions(ip: str, depth: int, x_offset: int) -> int:
        #     node_data = node_data_map[ip]
        #     node = HostNode(node_data)
        #     children = children_map.get(ip, [])
        #     cur_x = x_offset
        #     for child_ip in children:
        #         cur_x = assign_positions(child_ip, depth + 1, cur_x)
        #     if children:
        #         avg_x = sum(self.node_positions[child_ip].x() for child_ip in children) / len(children)
        #         pos = QPointF(avg_x, depth * 120)
        #     else:
        #         pos = QPointF(x_offset * 120, depth * 120)
        #         cur_x += 1
        #     node.setPos(pos)
        #     self.scene.addItem(node)
        #     self.nodes[ip] = node
        #     self.node_items[ip] = node
        #     self.node_positions[ip] = pos
        #     return cur_x

        # roots = children_map.get(None, [])
        # x_start = 0
        # for root_ip in roots:
        #     x_start = assign_positions(root_ip, depth=0, x_offset=x_start)

        self.render_edges()

    def render_edges(self):
        for item in self.edge_items:
            if item.scene() is not None:  # 살아있으면만 제거
                self.scene.removeItem(item)
        self.edge_items.clear()

        for parent_ip, child_ip in self.edges:
            parent_node = self.node_items.get(parent_ip)
            child_node = self.node_items.get(child_ip)
            if parent_node and child_node:
                line = QGraphicsLineItem(
                    parent_node.x(), parent_node.y(),
                    child_node.x(), child_node.y()
                )
                line.setPen(QPen(Qt.GlobalColor.black, 2))
                self.scene.addItem(line)
                self.edge_items.append(line)

    def create_node_at(self, pos: QPointF):
        dialog = NodeFormDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            node_info = dialog.get_data()
            print ( 'node_info : ', node_info )
            if node_info:
                new_ip = node_info["IP_주소"]
                new_name = node_info["host_이름"]
                new_data = {"IP_주소":  new_ip, "host_이름": new_name}
                node = HostNode(new_data, editable=True)
                node.setPos(pos)
                self.scene.addItem(node)
                self.nodes[new_ip] = node
                self.node_items[new_ip] = node
                self.node_positions[new_ip] = pos
                print(f"노드 생성됨: {new_ip}")

    def remove_node(self, ip: str):
        node = self.node_items.pop(ip, None)
        if node:
            self.scene.removeItem(node)
        self.nodes.pop(ip, None)
        self.node_positions.pop(ip, None)
        self.parent_relations = {c: p for c, p in self.parent_relations.items() if c != ip and p != ip}
        self.edges = [(p, c) for (p, c) in self.edges if p != ip and c != ip]
        self.render_edges()
        print(f"노드 삭제됨: {ip}")

    def remove_parent_of_node(self, child_ip: str):
        parent_ip = self.parent_relations.pop(child_ip, None)
        if parent_ip:
            self.edges = [(p, c) for (p, c) in self.edges if not (p == parent_ip and c == child_ip)]
            self.render_edges()

    def on_ws_received (self, msg:dict) -> None:
        """ ws 메시지 수신 시 호출되는 함수 """
        try:
            prev_status = self.lb_status.text()
            self.prev_timestamp = copy.deepcopy(getattr( self , 'timestamp', ''))
            timestamp = msg.get('timestamp', None)
            if timestamp:
                self.timestamp = Utils.format_datetime_str_with_weekday( timestamp, with_year=True, with_weekday=True)
                self.lb_status.setText(f"{self.start_status_text} : Update Time : {self.timestamp} ( 이전 update : {self.prev_timestamp} )")
            else:
                self.lb_status.setText(prev_status)

            self.set_ping_status(msg['message'])
            if self.dialog_status and self.dialog_status.isVisible():
                summary = self.get_ping_status_summary()
                self.dialog_status.update_summary(summary)

        except Exception as e:
            logger.error(f"on_ws_received : {e}")
            logger.error(f"{traceback.format_exc()}")

    def set_ping_status(self, status_list: List[Dict[str, list]]):
        """ 현재 노드들의 ping 상태 업데이트 """
        self.ping_status = status_list

        if isinstance(status_list, list):
            for resultDict in status_list:
                for ip, value in resultDict.items():
                    self.map_ip_result[ip].append(value[0])
                    if len(self.map_ip_result[ip]) > self.max_ping_count:
                        self.map_ip_result[ip].pop(0)

            for ip, node in self.node_items.items():        
                node.set_status( self.calculate_ping_status(self.map_ip_result.get(ip, [])))
        else:
            logger.error(f"set_ping_status : {status_list} 형식 오류")
            logger.error( status_list )

    def calculate_ping_status(self, result_list:list[bool]) -> str:
        """ ping status를  str 으로 반환 """
        if not result_list:
            return "N/A"
        total = len(result_list)
        true_count = sum(1 for v in result_list if v is True)
        if total == true_count:
            return "정상"
        elif true_count == 0:
            return "비정상"
        elif true_count < 2:
            return "경고"
        else:
            return "주의"
        
    def get_ping_status_summary(self) -> dict:
        """전체 ping 상태에 대한 통계 요약"""
        statuses = [self.calculate_ping_status(pings) for pings in self.map_ip_result.values()]
        counts = Counter(statuses)

        summary = {
            "총 host": len(statuses),
            "정상": counts.get("정상", 0),
            "주의": counts.get("주의", 0),
            "경고": counts.get("경고", 0),
            "비정상": counts.get("비정상", 0),
            "N/A": counts.get("N/A", 0),
        }
        return summary

    def manual_refresh(self):
        print("Ping or data refresh triggered manually.")

    def subscribe_gbus(self):
        self.event_bus.subscribe(
            f"{self.ws_url}", 
            self.on_ws_received    
            )
        self.lb_status.setText(self.start_status_text)
        self._stop_time = None
        
    def unsubscribe_gbus(self):
        self.event_bus.unsubscribe(
            f"{self.ws_url}", 
            self.on_ws_received
            )
        self.lb_status.setText(self.stop_status_text)
        self._start_time = None

    def run_stop(self):
        self.unsubscribe_gbus()


    def update_pie_chart(self, summary: dict):
        if self.pie_chart_item:
            self.scene.removeItem(self.pie_chart_item)

        pie = StatusPieChart(summary)
        pie.setPos(20, 20)  # 좌측 상단에 배치
        self.scene.addItem(pie)
        self.pie_chart_item = pie

    def show_summary_pie_chart(self):
        if not self.dialog_status:
            self.dialog_status = StatusSummaryDialog(self)
        summary = self.get_ping_status_summary()
        self.dialog_status.update_summary(summary)
        self.dialog_status.show()
        self.dialog_status.raise_()
