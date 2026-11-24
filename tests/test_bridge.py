import base64
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bridge"))

import comfy_client  # noqa: E402
from comfy_client import ComfyClient, fill_img2img, load_workflow  # noqa: E402


class Resp:
    def __init__(self, json_data=None, content=b""):
        self._json, self.content = json_data, content

    def raise_for_status(self):
        pass

    def json(self):
        return self._json


class FakeSession:
    """ComfyUI API 를 흉내 낸다. history 는 두 번째 조회에서 완료된다."""

    def __init__(self):
        self.calls, self.history_polls, self.queued = [], 0, None

    def post(self, url, **kw):
        self.calls.append(("POST", url))
        if url.endswith("/upload/image"):
            return Resp({"name": "maya_x.png", "subfolder": ""})
        if url.endswith("/prompt"):
            self.queued = kw["json"]["prompt"]
            return Resp({"prompt_id": "abc"})
        raise AssertionError(url)

    def get(self, url, **kw):
        self.calls.append(("GET", url))
        if "/history/" in url:
            self.history_polls += 1
            if self.history_polls < 2:
                return Resp({})
            return Resp({"abc": {"status": {"status_str": "success"},
                                 "outputs": {"8": {"images": [{"filename": "maya_00001_.png",
                                                               "subfolder": "", "type": "output"}]}}}})
        if url.endswith("/view"):
            return Resp(content=b"PNGDATA")
        raise AssertionError(url)


def test_fill_img2img_sets_prompt_and_image():
    wf = fill_img2img(load_workflow(), image_name="in.png", prompt="a castle", negative="blurry",
                      steps=12, denoise=0.4, seed=7, ckpt="model.safetensors")
    assert wf["2"]["inputs"]["image"] == "in.png"
    assert wf["4"]["inputs"]["text"] == "a castle"
    assert wf["5"]["inputs"]["text"] == "blurry"
    assert wf["6"]["inputs"]["steps"] == 12 and wf["6"]["inputs"]["seed"] == 7
    assert wf["1"]["inputs"]["ckpt_name"] == "model.safetensors"
    assert load_workflow()["4"]["inputs"]["text"] == ""  # 원본은 그대로


def test_img2img_flow():
    s = FakeSession()
    client = ComfyClient("http://comfy", poll_interval=0, session=s)
    assert client.img2img(b"png", "a castle", seed=1) == b"PNGDATA"
    assert s.queued["2"]["inputs"]["image"] == "maya_x.png"
    assert s.history_polls == 2


def test_wait_raises_on_error():
    class ErrSession(FakeSession):
        def get(self, url, **kw):
            return Resp({"abc": {"status": {"status_str": "error", "messages": ["oom"]}, "outputs": {}}})

    with pytest.raises(RuntimeError):
        ComfyClient(session=ErrSession(), poll_interval=0).wait("abc")


def test_server_generate(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path))
    import importlib
    import server
    importlib.reload(server)

    class FakeComfy:
        def img2img(self, png, prompt, **params):
            assert png == b"raw" and prompt == "sky"
            return b"OUT"

    server.app.config["COMFY"] = FakeComfy()
    client = server.app.test_client()
    res = client.post("/generate", json={"image": base64.b64encode(b"raw").decode(), "prompt": "sky"})
    body = res.get_json()
    assert res.status_code == 200 and base64.b64decode(body["image"]) == b"OUT"
    assert Path(body["saved"]).read_bytes() == b"OUT"
    assert client.post("/generate", json={"prompt": "sky"}).status_code == 400
