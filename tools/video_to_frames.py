"""영상을 frame_0000.png 형식의 연속 이미지로 저장한다.

ComfyUI 배치 로드(Load Image Batch 등)는 파일 번호가 0000, 0001 ... 처럼
자릿수가 일정해야 순서대로 1씩 증가하며 읽는다.

사용: python video_to_frames.py video/dance.mp4 frame/ [--every 2] [--size 512]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2


def video_to_frames(video_path: str, out_dir: str, every: int = 1, size: int | None = None) -> int:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        raise FileNotFoundError(video_path)

    total = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    print("전체 video frame =", total)

    saved, i = 0, 0
    while True:
        ret, frame = video.read()
        if not ret:
            break
        if i % every == 0:
            if size:
                h, w = frame.shape[:2]
                scale = size / max(h, w)
                frame = cv2.resize(frame, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)
            cv2.imwrite(str(out / f"frame_{saved:04d}.png"), frame)
            saved += 1
        i += 1
    video.release()
    return saved


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("out_dir")
    p.add_argument("--every", type=int, default=1, help="n 프레임마다 하나씩 저장")
    p.add_argument("--size", type=int, default=None, help="긴 변 기준 크기 조정")
    a = p.parse_args()
    n = video_to_frames(a.video, a.out_dir, a.every, a.size)
    print(f"{n}장 저장 → {a.out_dir}")
