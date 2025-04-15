import cv2
import numpy as np

# 입력 영상
cap = cv2.VideoCapture("chessboard_video.MOV")
overlay_img = cv2.imread("diana.png", cv2.IMREAD_UNCHANGED)
overlay_img = cv2.flip(overlay_img, 1)  # 좌우 뒤집기

# 출력 영상 설정
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
fps = cap.get(cv2.CAP_PROP_FPS)
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
out = cv2.VideoWriter('diana_ar_output.mp4', fourcc, fps, (w, h))

# 체스보드
chessboard_size = (9, 6)
square_size = 1.0
objp = np.zeros((chessboard_size[0]*chessboard_size[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2)

# 카메라 파라미터 (캘리브레이션 결과)
camera_matrix = np.array([[1662.27, 0, 952.06],
                          [0, 1663.99, 542.80],
                          [0, 0, 1]])
dist_coeffs = np.array([0.2060, -0.5026, -0.00009, -0.00277, -0.4573])

# 반복 처리
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    found, corners = cv2.findChessboardCorners(gray, chessboard_size, None)

    if found:
        # refine corners
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

        # pose estimation
        _, rvec, tvec = cv2.solvePnP(objp, corners2, camera_matrix, dist_coeffs)

        # 3D 평면 설정
        base = np.array([1.7, 0.5, 0])
        board_pts = np.float32([
            [0, 0, -3.5],
            [5, 0, -3.5],
            [5, 1, 0],
            [0, 1, 0]
        ]) + base

        # 투영
        dst_pts, _ = cv2.projectPoints(board_pts, rvec, tvec, camera_matrix, dist_coeffs)
        dst_pts = dst_pts.reshape(-1, 2).astype(np.float32)

        h_overlay, w_overlay = overlay_img.shape[:2]
        src_pts = np.float32([[0, 0], [w_overlay, 0], [w_overlay, h_overlay], [0, h_overlay]])

        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped = cv2.warpPerspective(overlay_img, M, (frame.shape[1], frame.shape[0]), flags=cv2.INTER_LINEAR)

        # 알파 블렌딩
        if overlay_img.shape[2] == 4:
            alpha = warped[:, :, 3] / 255.0
            for c in range(3):
                frame[:, :, c] = (1 - alpha) * frame[:, :, c] + alpha * warped[:, :, c]
        else:
            mask = np.any(warped > 0, axis=2)
            frame[mask] = warped[mask]

    out.write(frame)

cap.release()
out.release()
print("AR 영상 완성: diana_ar_output.mp4")