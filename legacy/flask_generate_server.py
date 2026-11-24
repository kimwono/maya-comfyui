from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate_image():
    data = request.json

    # 요청 데이터에서 필요한 정보 추출
    prompt = data.get('prompt')
    width = data.get('width', 512)  # 기본값 설정
    height = data.get('height', 512)  # 기본값 설정
    style = data.get('style', 'default')  # 기본값 설정

    # 이미지 생성 로직 (여기에 실제 생성 로직을 구현)
    # 예시로, 이미지 생성 결과를 반환하는 과정은 생략
    # 실제로는 AI 모델을 호출해 이미지를 생성해야 함

    # 이미지 생성 후 반환할 데이터
    generated_image_url = "http://example.com/generated_image.png"  # 실제 생성된 이미지 URL로 변경

    return jsonify({
        "success": True,
        "image_url": generated_image_url,
        "prompt": prompt,
        "width": width,
        "height": height,
        "style": style
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8188)
