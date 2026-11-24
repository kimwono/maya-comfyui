"""Maya 안에서 실행하는 ComfyUI 연동 도구.

1) 현재 뷰포트(또는 지정 카메라)를 PNG 로 캡처
2) Flask 중계 서버(/generate)로 이미지와 프롬프트 전송
3) 생성된 이미지를 받아 저장하고, 현재 카메라의 image plane 으로 불러오기

Maya Script Editor(Python) 에서:
    import comfy_tool; comfy_tool.show()
Maya 기본 Python 만 사용한다 (requests 등 외부 패키지 불필요).
"""
from __future__ import annotations

import base64
import json
import os
import tempfile
import time
import urllib.error
import urllib.request

import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaUI as omui

BRIDGE_URL = os.getenv("MAYA_COMFY_BRIDGE", "http://127.0.0.1:5000")
WINDOW = "comfyToolWindow"


# ---------------------------------------------------------------- 캡처
def active_camera() -> str:
    view = omui.M3dView.active3dView()
    cam = om.MDagPath()
    view.getCamera(cam)
    return cam.fullPathName()


def capture_viewport(width: int = 1024, height: int = 1024, camera: str | None = None) -> str:
    """현재 프레임을 playblast 로 PNG 저장하고 경로를 돌려준다."""
    if camera:
        cmds.lookThru(camera)
    cmds.setAttr("defaultRenderGlobals.imageFormat", 32)  # PNG
    base = os.path.join(tempfile.gettempdir(), f"maya_capture_{int(time.time())}")
    frame = cmds.currentTime(q=True)
    path = cmds.playblast(
        filename=base, forceOverwrite=True, format="image", compression="png",
        width=width, height=height, startTime=frame, endTime=frame,
        showOrnaments=False, viewer=False, percent=100, quality=100,
        clearCache=True, framePadding=4,
    )
    # playblast 는 "이름.####.png" 형식 경로를 돌려준다
    real = path.replace("####", f"{int(frame):04d}")
    if not os.path.exists(real):
        raise RuntimeError(f"캡처 파일을 찾을 수 없습니다: {real}")
    return real


# ---------------------------------------------------------------- 전송
def request_generation(image_path: str, prompt: str, negative: str = "",
                       steps: int = 20, denoise: float = 0.6, timeout: float = 600) -> dict:
    with open(image_path, "rb") as f:
        payload = {
            "image": base64.b64encode(f.read()).decode(),
            "prompt": prompt,
            "negative": negative,
            "steps": steps,
            "denoise": denoise,
        }
    req = urllib.request.Request(
        f"{BRIDGE_URL}/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return json.loads(res.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"중계 서버 오류 {e.code}: {body}")


def save_result(b64_png: str, folder: str | None = None) -> str:
    folder = folder or os.path.join(cmds.workspace(q=True, rootDirectory=True), "images", "comfyui")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"comfy_{time.strftime('%Y%m%d_%H%M%S')}.png")
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64_png))
    return path


# ---------------------------------------------------------------- 불러오기
def attach_image_plane(image_path: str, camera: str) -> str:
    shape = cmds.listRelatives(camera, shapes=True, fullPath=True)
    cam_shape = shape[0] if shape else camera
    plane = cmds.imagePlane(camera=cam_shape, fileName=image_path)
    return plane[0]


def run(prompt: str, negative: str = "", steps: int = 20, denoise: float = 0.6,
        size: int = 1024) -> str:
    camera = active_camera()
    shot = capture_viewport(size, size)
    result = request_generation(shot, prompt, negative, steps, denoise)
    if not result.get("success"):
        raise RuntimeError(result.get("error", "생성 실패"))
    out = save_result(result["image"])
    attach_image_plane(out, camera)
    print(f"[comfy_tool] 생성 이미지: {out}")
    return out


# ---------------------------------------------------------------- UI
def show():
    if cmds.window(WINDOW, exists=True):
        cmds.deleteUI(WINDOW)
    cmds.window(WINDOW, title="Maya × ComfyUI", widthHeight=(380, 260))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=6)
    cmds.text(label="프롬프트", align="left")
    prompt = cmds.scrollField(wordWrap=True, height=60)
    cmds.text(label="네거티브 프롬프트", align="left")
    negative = cmds.textField(text="blurry, low quality")
    steps = cmds.intSliderGrp(label="Steps", field=True, minValue=5, maxValue=50, value=20)
    denoise = cmds.floatSliderGrp(label="Denoise", field=True, minValue=0.1, maxValue=1.0, value=0.6)

    def on_run(*_):
        text = cmds.scrollField(prompt, q=True, text=True).strip()
        if not text:
            cmds.warning("프롬프트를 입력하세요.")
            return
        cmds.waitCursor(state=True)
        try:
            out = run(text, cmds.textField(negative, q=True, text=True),
                      cmds.intSliderGrp(steps, q=True, value=True),
                      cmds.floatSliderGrp(denoise, q=True, value=True))
            cmds.inViewMessage(amg=f"생성 완료: {os.path.basename(out)}", pos="topCenter", fade=True)
        except Exception as e:
            cmds.confirmDialog(title="오류", message=str(e), button=["확인"])
        finally:
            cmds.waitCursor(state=False)

    cmds.button(label="캡처 → 생성 → 불러오기", height=36, command=on_run)
    cmds.showWindow(WINDOW)
