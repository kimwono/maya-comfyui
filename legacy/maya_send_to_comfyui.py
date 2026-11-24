import maya.cmds as cmds
import requests
import json

# ComfyUI의 URL
COMFYUI_URL = "http://127.0.0.1:8188/api/endpoint"  # 실제 API 엔드포인트로 변경 필요

def send_data_to_comfyui(data):
    try:
        # 데이터 JSON 포맷으로 변환
        json_data = json.dumps(data)

        # POST 요청 전송
        response = requests.post(COMFYUI_URL, json=json_data)

        # 응답 상태 코드 확인
        if response.status_code == 200:
            print("데이터 전송 성공:", response.json())
        else:
            print("데이터 전송 실패:", response.status_code, response.text)

    except Exception as e:
        print("오류 발생:", str(e))

# 예시 데이터 (렌더링 파라미터 등)
data_to_send = {
    "image_width": 1920,
    "image_height": 1080,
    "style": "artistic",
    "settings": {
        "quality": "high"
    }
}

# 데이터 전송 함수 호출
send_data_to_comfyui(data_to_send)
