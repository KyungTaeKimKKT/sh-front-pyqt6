# network_viewer/demo.py

import sys
import asyncio
from PyQt6.QtWidgets import QApplication
from viewer import NetworkTopologyViewer
import json
# 샘플 데이터

# plot_datas = [
#     {"IP_주소": "192.168.0.1", "host_이름": "Gateway", "host_설명": "Main router"},
#     {"IP_주소": "192.168.0.2", "host_이름": "Switch", "host_설명": "24-port switch"},
#     {"IP_주소": "192.168.0.3", "host_이름": "NAS", "host_설명": "File server"},
#     {"IP_주소": "192.168.0.4", "host_이름": "Camera", "host_설명": "IP camera"}
# ]
# async def run_app():
#     app = QApplication(sys.argv)
#     viewer = NetworkTopologyViewer(plot_datas)
#     viewer.resize(800, 600)
#     viewer.show()

#     async def update_loop():
#         while True:
#             ping_result = await ping_all([h["IP_주소"] for h in plot_datas])
#             viewer.set_ping_results(ping_result)
#             await asyncio.sleep(5)

#     asyncio.create_task(update_loop())
#     sys.exit(app.exec())


def run_app():
    import time
    from datas import datas, result
    plot_datas = datas
    # result = json.loads(result)
    print ( 'result : ', result , type(result) )
    app = QApplication(sys.argv)
    viewer = NetworkTopologyViewer(plot_datas, topology_edit_mode=True)
    # viewer = NetworkTopologyViewer(plot_deatas, topology_edit_mode=False)
    viewer.resize(1000, 700)
    viewer.show()
    time.sleep(2)
    viewer.set_ping_status(result)
    sys.exit(app.exec())

if __name__ == "__main__":
    run_app()



    # app = QApplication(sys.argv)
    # viewer = NetworkTopologyViewer(plot_datas)
    # viewer.resize(800, 600)
    # viewer.show()

    # sys.exit(app.exec())