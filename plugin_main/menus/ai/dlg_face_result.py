from __future__ import annotations

from modules.common_import_v3 import *
import sys
import requests


from modules.PyQt.compoent_v2.imageViewer.lb_with_qnetwork import Lbl_Image_with_QNetwork as ImageLabel
class DecisionImageWidget(QWidget):
    """decision_images 한 개 dict 를 보여주는 위젯"""
    def __init__(self, data: dict):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # info
        info_label = QLabel(f"user_id: {data['user_id']}, "
                            f"score: {data['score']:.3f}, "
                            f"id: {data['id']}")
        layout.addWidget(info_label)

        # 요청image vs db_image
        hl = QHBoxLayout()
        hl.addWidget(ImageLabel(self, url=data.get('request_image',None)))
        hl.addWidget(ImageLabel(self, url=data.get('db_image',None)))
        layout.addLayout(hl)


class RecognitionResultDialog(QDialog):
    def __init__(self, parent=None, result_data: dict=None):
        super().__init__(parent)
        self.setWindowTitle("얼굴 인식 결과")
        self.resize(800, 600)

        main_layout = QVBoxLayout(self)

        # 상단 summary
        summary = (f"Status: { 'Success' if result_data.get('success', False) else 'Failed'}\n"
                   f"Recognized User ID: {result_data.get('recognized_user_id')}\n"
                   f"Similarity: {result_data.get('similarity'):.3f}\n"
                   f"Num Images: {result_data.get('num_images')}")
        main_layout.addWidget(QLabel(summary))

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        vbox = QVBoxLayout(container)

        # decision_images 표시
        print (f"result_data: {result_data}")
        for item in result_data.get("decision_images", []):
            vbox.addWidget(DecisionImageWidget(item))

        scroll.setWidget(container)
        main_layout.addWidget(scroll)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    sample_data = {
        'status': 'success',
        'recognized_user_id': 1,
        'similarity': 0.9907389059794116,
        'num_images': 4,
        'decision_images': [
            {
                'user_id': 1,
                'score': 0.9907389059794116,
                'id': 71,
                '요청image': '/home/kkt/development/proj/intranet_sh/shapi/media/tmp/ai_face/probe_3_1757493265.jpg',
                'db_image': 'http://192.168.7.108:9999/media/ai/faces/augmented/admin_admin/face_LwWXFM8_rot15.jpg'
            },
            {
                'user_id': 1,
                'score': 0.9900990569857526,
                'id': 71,
                '요청image': '/home/kkt/development/proj/intranet_sh/shapi/media/tmp/ai_face/probe_2_1757493265.jpg',
                'db_image': 'http://192.168.7.108:9999/media/ai/faces/augmented/admin_admin/face_LwWXFM8_rot15.jpg'
            },
            {
                'user_id': 1,
                'score': 0.9594345470014518,
                'id': 75,
                '요청image': '/home/kkt/development/proj/intranet_sh/shapi/media/tmp/ai_face/probe_1_1757493265.jpg',
                'db_image': 'http://192.168.7.108:9999/media/ai/faces/augmented/admin_admin/face_fERiSSb_rot-15.jpg'
            }
        ]
    }

    dlg = RecognitionResultDialog(sample_data)
    dlg.exec()