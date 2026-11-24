"""ComfyUI HTTP API 클라이언트.

흐름: /upload/image 로 입력 이미지 업로드 → 워크플로 노드 값 채우기 → /prompt 제출
     → /history/{prompt_id} 를 폴링해 완료 확인 → /view 로 결과 이미지 받기
"""
from __future__ import annotations

import copy
import json
import random
import time
import uuid
from pathlib import Path

import requests

WORKFLOW_DIR = Path(__file__).resolve().parent / "workflows"


def load_workflow(name: str = "img2img") -> dict:
    return json.loads((WORKFLOW_DIR / f"{name}.json").read_text(encoding="utf-8"))


def fill_img2img(workflow: dict, *, image_name: str, prompt: str, negative: str = "",
                 steps: int = 20, cfg: float = 7.0, denoise: float = 0.6,
                 seed: int | None = None, ckpt: str | None = None) -> dict:
    """img2img 워크플로의 입력 노드 값을 바꾼 사본을 돌려준다."""
    wf = copy.deepcopy(workflow)
    nodes = {n["class_type"]: (k, n) for k, n in wf.items()}

    wf[nodes["LoadImage"][0]]["inputs"]["image"] = image_name
    if ckpt:
        wf[nodes["CheckpointLoaderSimple"][0]]["inputs"]["ckpt_name"] = ckpt

    sampler = wf[nodes["KSampler"][0]]["inputs"]
    sampler.update(steps=steps, cfg=cfg, denoise=denoise,
                   seed=seed if seed is not None else random.randint(0, 2**32 - 1))
    # KSampler 의 positive / negative 가 가리키는 텍스트 노드에 프롬프트를 넣는다
    wf[sampler["positive"][0]]["inputs"]["text"] = prompt
    wf[sampler["negative"][0]]["inputs"]["text"] = negative
    return wf


class ComfyClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8188", timeout: float = 300,
                 poll_interval: float = 1.0, session: requests.Session | None = None):
        self.base = base_url.rstrip("/")
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.http = session or requests.Session()
        self.client_id = uuid.uuid4().hex

    def upload_image(self, png: bytes, name: str) -> str:
        res = self.http.post(f"{self.base}/upload/image",
                             files={"image": (name, png, "image/png")},
                             data={"overwrite": "true"}, timeout=30)
        res.raise_for_status()
        info = res.json()
        sub = info.get("subfolder")
        return f"{sub}/{info['name']}" if sub else info["name"]

    def queue(self, workflow: dict) -> str:
        res = self.http.post(f"{self.base}/prompt",
                             json={"prompt": workflow, "client_id": self.client_id}, timeout=30)
        res.raise_for_status()
        return res.json()["prompt_id"]

    def wait(self, prompt_id: str) -> dict:
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            res = self.http.get(f"{self.base}/history/{prompt_id}", timeout=30)
            res.raise_for_status()
            entry = res.json().get(prompt_id)
            if entry:
                status = entry.get("status", {})
                if status.get("status_str") == "error":
                    raise RuntimeError(f"ComfyUI 실행 오류: {status.get('messages')}")
                if entry.get("outputs"):
                    return entry["outputs"]
            time.sleep(self.poll_interval)
        raise TimeoutError(f"{self.timeout}초 안에 생성이 끝나지 않았습니다.")

    def fetch_images(self, outputs: dict) -> list[bytes]:
        images = []
        for node in outputs.values():
            for img in node.get("images", []):
                res = self.http.get(f"{self.base}/view", params={
                    "filename": img["filename"],
                    "subfolder": img.get("subfolder", ""),
                    "type": img.get("type", "output"),
                }, timeout=60)
                res.raise_for_status()
                images.append(res.content)
        return images

    def img2img(self, png: bytes, prompt: str, **params) -> bytes:
        name = self.upload_image(png, f"maya_{uuid.uuid4().hex[:8]}.png")
        wf = fill_img2img(load_workflow("img2img"), image_name=name, prompt=prompt, **params)
        images = self.fetch_images(self.wait(self.queue(wf)))
        if not images:
            raise RuntimeError("생성된 이미지가 없습니다.")
        return images[0]
