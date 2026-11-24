# Maya × ComfyUI

Maya 뷰포트 화면을 ComfyUI img2img로 보내고, 생성된 이미지를 다시 Maya 카메라의 image plane으로 불러오는 도구입니다. (2024 콘텐츠 원캠퍼스 인공지능 분야 프로젝트)

```
Maya 뷰포트 캡처 (playblast → PNG)
  → Flask 중계 서버 POST /generate
  → ComfyUI API: 이미지 업로드 → img2img 워크플로 제출 → 완료 대기 → 결과 수신
  → Maya: 결과 저장 후 현재 카메라 image plane으로 연결
```

## 구조

```
maya/comfy_tool.py        Maya 도구 창 (프롬프트·Steps·Denoise), 캡처·전송·불러오기. Maya 기본 Python만 사용
bridge/server.py          Flask 중계 서버
bridge/comfy_client.py    ComfyUI HTTP API 클라이언트 (/upload/image, /prompt, /history, /view)
bridge/workflows/img2img.json   ComfyUI API 형식 워크플로
tools/video_to_frames.py  영상 → frame_0000.png 연속 이미지 (ComfyUI 배치 입력용)
tests/                    pytest (ComfyUI 응답을 흉내 낸 흐름 검사)
```

## 실행

```bash
# 1. ComfyUI 실행 (기본 http://127.0.0.1:8188)

# 2. 중계 서버
cd bridge
pip install -r requirements.txt
COMFYUI_CKPT=<체크포인트 파일 이름> python server.py    # http://127.0.0.1:5000
```

```python
# 3. Maya Script Editor (Python)
import sys; sys.path.append(r"<저장소 경로>/maya")
import comfy_tool; comfy_tool.show()
```

```bash
# 영상 → 프레임
python tools/video_to_frames.py video/dance.mp4 frame/ --every 2 --size 512

# 테스트
pip install flask requests pytest && pytest -q tests
```

| 환경변수 | 기본값 |
|---|---|
| `COMFYUI_URL` | `http://127.0.0.1:8188` |
| `COMFYUI_CKPT` | 워크플로에 적힌 체크포인트 |
| `MAYA_COMFY_BRIDGE` (Maya 쪽) | `http://127.0.0.1:5000` |
