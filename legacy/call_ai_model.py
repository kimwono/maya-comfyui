import requests

# AI 모델 API의 URL
AI_MODEL_URL = "http://example-ai-model.com/generate"  # 실제 AI 모델의 URL로 변경 필요

def call_ai_model(prompt, width, height, style):
    try:
        # AI 모델에 보낼 데이터 설정
        payload = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "style": style
        }

        # POST 요청 전송
        response = requests.post(AI_MODEL_URL, json=payload)

        # 응답 상태 코드 확인
        if response.status_code == 200:
            return response.json()  # JSON 응답 반환
        else:
            print("AI 모델 호출 실패:", response.status_code, response.text)
            return None

    except Exception as e:
        print("오류 발생:", str(e))
        return None

# 예시 사용
result = call_ai_model("A beautiful sunset over the mountains", 1920, 1080, "artistic")
if result:
    print("생성된 이미지 URL:", result.get("image_url"))
