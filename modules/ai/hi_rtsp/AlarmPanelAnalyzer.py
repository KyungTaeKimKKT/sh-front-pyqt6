from __future__ import annotations
import cv2
import numpy as np
import torch
from collections import defaultdict

class AlarmPanelAnalyzer:
    """ led on/off 분석 """
    def __init__(self, model=None, known_colors: dict=None, **kwargs):
        """
        model: CNN 모델 (옵션)
        known_colors: LED 이름 -> BGR 값 (예: {"power": (0,0,255)})
        """
        self.model = model  # 필요 시 CNN 모델
        self.known_colors = known_colors or {}
        self.default_threshold = kwargs.get("default_threshold", 50.0)
        self.defulat_map_led = {
            "RED": {"color_bgr": (0,0,255), "threshold": 50.0},
            "GREEN": {"color_bgr": (0,255,0), "threshold": 50.0},
            "BLUE": {"color_bgr": (255,0,0), "threshold": 50.0},
            "YELLOW": {"color_bgr": (0,255,255), "threshold": 50.0},
            # "PURPLE": {"color_bgr": (255,0,255), "threshold": 50.0},
            # "CYAN": {"color_bgr": (255,255,0), "threshold": 50.0},
            # "WHITE": {"color_bgr": (255,255,255), "threshold": 50.0},
        }

    
    def run(self, image: np.ndarray, all_roi_dict: dict, map_led: dict=None, **kwargs):
        scan_results = self.analyze_by_scan(map_led=map_led, image=image, all_roi_dict=all_roi_dict)
        return self.decide(scan_results, **kwargs)


    def decide(self, scan_results: dict[str, list[dict]], threshold: float = None, **kwargs):
        """
        scan_results: analyze_by_scan 결과
        return: 최종 확정 결과
        {"LED1": {"led": "RED", "ON": True, "distance": 32.5}, ...}
        """
        threshold = threshold if threshold is not None else self.default_threshold
        final_results = {}
        for roi_name, candidates in scan_results.items():
            best = min(candidates, key=lambda x: x["distance"])
            is_on = best["distance"] < threshold
            final_results[roi_name] = {
                                        "led": best["led_color_name"],  # 여기 수정
                                        "ON": is_on,
                                        "distance": best["distance"]
                                    }
        # print (f"final_results: {final_results}")
        return final_results


    def analyze_with_known_colors(self, led_dict: dict, image: np.ndarray, roi_dict: dict):
        """
        led_dict: {"LED1": {...}, "LED2": {...}} 등, 해당 색상 LED 정보
        roi_dict: {"LED1": [(x1,y1),...,(x4,y4)], ...} 
        """
        results = defaultdict(dict)

        for led_color_name, led_color_info in led_dict.items():
            for roi_name, roi_points in roi_dict.items():
                pts = np.array(roi_points, dtype=np.int32)
                mask = np.zeros(image.shape[:2], dtype=np.uint8)
                cv2.fillPoly(mask, [pts], 255)

                mean_color = cv2.mean(image, mask=mask)[:3]  # BGR 평균

                distance = np.linalg.norm(np.array(mean_color) - np.array(led_color_info["color_bgr"]))
                return  {"led_color_name": led_color_name,  "distance": distance}
        return results


    def analyze_by_scan(self, map_led: dict=None, image: np.ndarray=None, all_roi_dict: dict=None) -> dict[str,list[dict]]:
        """
        map_led: { "RED": {...}, "GREEN": {...}, ... } 사용하지 않아도 구조상 유지
        roi_dict: {"LED1": [...], "LED2": [...]}
        return: scan 결과 누적
        """
        map_led = map_led if map_led is not None else self.defulat_map_led
        if image is None or all_roi_dict is None:
            raise ValueError("image 또는 all_roi_dict 가 없습니다.")

        all_results = defaultdict(list)
        for roi_name in all_roi_dict.keys():
            # roi_dict에서 하나씩 분석
            for map_led_name in map_led.keys():
                roi_scan = self.analyze_with_known_colors( led_dict={map_led_name: map_led[map_led_name]}, 
                                                            image=image, 
                                                            roi_dict={roi_name: all_roi_dict[roi_name]}
                                                            )
                all_results[roi_name].append(roi_scan)
        return all_results


        

    # --------------------------
    # 2. LED 색상을 모르는 경우, 단순 밝기 기반 ON/OFF 판단
    # --------------------------
    def analyze_with_only_brightness(self, image: np.ndarray, roi_dict: dict):
        """
        색상을 모르는 경우, 단순 밝기 기반 ON/OFF 판단
        """
        results = {}
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        for roi_name, points in roi_dict.items():
            mask = np.zeros(gray.shape, dtype=np.uint8)
            pts = np.array(points, dtype=np.int32)
            cv2.fillPoly(mask, [pts], 255)

            mean_intensity = cv2.mean(gray, mask=mask)[0]
            threshold = 100  # 밝기 기준, 경험적으로 조정
            results[roi_name] = "ON" if mean_intensity > threshold else "OFF"

        return results

    # --------------------------
    # 통합 분석
    # --------------------------
    def analyze(self, image: np.ndarray, roi_dict: dict):
        if self.known_colors:
            return self.analyze_with_known_colors(image, roi_dict)
        else:
            return self.analyze_unknown_color(image, roi_dict)