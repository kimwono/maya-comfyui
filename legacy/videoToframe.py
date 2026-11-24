import sys
import os

current_dir = os.path.dirname(os.path.realpath(__file__))   # 현재 디렉토리 얻기
print(current_dir)
sys.path.append(current_dir)                                 # 시스템 패스로 추가

import cv2

video = cv2.VideoCapture("video\chu.mp4")
frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
print('전체 video frame =', frame_count)

for i in range(frame_count):
    ret, frame = video.read()
    if ret:
        image_path=f'frame/frame_' + '{0:04d}'.format(i)+'.png'  # 파일 형식 frame0000.png   숫자 갯수가 일정해야
                                                                    # comfyUI batch파일에서 순차적으로 1씩 증가 load Image 됨

        print(image_path)
        cv2.imwrite(image_path, frame)

    if cv2.waitKey(0) & 0xFF == ord('q'):
            break
video.release()
