"""Maya 와 ComfyUI 사이의 Flask 중계 서버.

Maya 쪽은 표준 라이브러리(urllib)만으로 JSON 을 보내고 받도록 하고,
ComfyUI API 처리(업로드·워크플로·폴링·결과 수신)는 여기서 맡는다.

POST /generate
  요청: {"image": <base64 PNG>, "prompt": str, "negative": str,
         "steps": int, "cfg": float, "denoise": float, "seed": int}
  응답: {"success": true, "image": <base64 PNG>, "saved": <저장 경로>}
"""
from __future__ import annotations

import base64
import os
import time
from pathlib import Path

from flask import Flask, jsonify, request

from comfy_client import ComfyClient

COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")
CHECKPOINT = os.getenv("COMFYUI_CKPT") or None
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", Path(__file__).resolve().parent / "outputs"))

app = Flask(__name__)
app.config["COMFY"] = ComfyClient(COMFYUI_URL)


@app.get("/health")
def health():
    return jsonify(ok=True, comfyui=COMFYUI_URL)


@app.post("/generate")
def generate():
    data = request.get_json(silent=True) or {}
    if not data.get("image"):
        return jsonify(success=False, error="image(base64 PNG)가 필요합니다."), 400
    if not data.get("prompt"):
        return jsonify(success=False, error="prompt 가 필요합니다."), 400

    try:
        png = base64.b64decode(data["image"])
    except Exception:
        return jsonify(success=False, error="image 를 base64 로 읽을 수 없습니다."), 400

    params = {k: data[k] for k in ("negative", "steps", "cfg", "denoise", "seed") if k in data}
    if CHECKPOINT:
        params["ckpt"] = CHECKPOINT

    try:
        result = app.config["COMFY"].img2img(png, data["prompt"], **params)
    except Exception as e:
        return jsonify(success=False, error=f"{type(e).__name__}: {e}"), 502

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    saved = OUTPUT_DIR / f"gen_{time.strftime('%Y%m%d_%H%M%S')}.png"
    saved.write_bytes(result)
    return jsonify(success=True, image=base64.b64encode(result).decode(), saved=str(saved))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")))
