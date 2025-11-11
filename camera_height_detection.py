# face_tracking_height_verified.py
# 필요: pip install opencv-python mediapipe numpy
import cv2
import numpy as np
import mediapipe as mp
import time
from collections import deque

# --------- 사용자/카메라 정보 (필수 입력) ----------
FX = 1200.0
FY = 1200.0
CX = 640.0
CY = 360.0

H_CAM = 1.5

DETECT_EVERY_N_FRAMES = 5
MAX_INACTIVE_FRAMES = 30
# 얼굴 검증 관련 하이퍼파라미터(필요시 조정)
FACE_SCORE_TH = 0.9        # FaceDetection 신뢰도 임계값
MIN_FACE_SIZE = 40            # w,h 최소 픽셀 크기
VERIFY_WITH_FACEMESH = True   # Face Mesh로 2차 검증 사용할지
VERIFY_EVERY_N_DETECTIONS = 1 # 검출 프레임마다(=1) 검증. 더 키우면 빨라지고 엄격도는 약간 감소.
FACEMESH_MIN_LANDMARKS = 200  # Face Mesh가 이 이상 랜드마크(468 중)를 잡아야 진짜 얼굴로 인정
ROI_PADDING_RATIO = 0.15      # 검증용 ROI 확장 비율
# ----------------------------------------------------

mp_face = mp.solutions.face_detection
mp_pose = mp.solutions.pose
mp_mesh = mp.solutions.face_mesh

class IDGenerator:
    def __init__(self):
        self.next_id = 0
    def get(self):
        i = self.next_id
        self.next_id += 1
        return i

class PersonState:
    def __init__(self, tracker, bbox, person_id):
        self.tracker = tracker
        self.bbox = bbox  # (x,y,w,h)
        self.id = person_id
        self.frames_missing = 0
        self.heights = deque(maxlen=10)

def ray_from_pixel(u, v, fx, fy, cx, cy):
    dx = (u - cx) / fx
    dy = (v - cy) / fy
    dz = 1.0
    return np.array([dx, dy, dz], dtype=float)

def distance_to_ground_from_pixel(u, v, fx, fy, cx, cy, H_cam):
    d = ray_from_pixel(u, v, fx, fy, cx, cy)
    d_y = d[1]
    if abs(d_y) < 1e-8:
        return None
    t = -H_cam / d_y
    if t <= 0:
        return None
    D = t * d[2]
    return D

def estimate_height_from_pixels(v_head, v_foot, fx, fy, cx, cy, H_cam, u_foot=None):
    h_px = (v_foot - v_head)
    if h_px <= 0:
        return None
    if u_foot is None:
        u_foot = cx
    D = distance_to_ground_from_pixel(u_foot, v_foot, fx, fy, cx, cy, H_cam)
    if D is None:
        return None
    H = (h_px * D) / fy
    return H, D

def bbox_bottom_center(bbox):
    x, y, w, h = bbox
    u = int(x + w/2)
    v = int(y + h)
    return u, v

def iou(boxA, boxB):
    (xA,yA,wA,hA) = boxA
    (xB,yB,wB,hB) = boxB
    x1 = max(xA, xB)
    y1 = max(yA, yB)
    x2 = min(xA+wA, xB+wB)
    y2 = min(yA+hA, yB+hB)
    if x2 <= x1 or y2 <= y1:
        return 0.0
    inter = (x2-x1)*(y2-y1)
    union = wA*hA + wB*hB - inter
    return inter/union

def expand_clip_roi(x, y, w, h, img_w, img_h, pad_ratio):
    pad_w = int(w * pad_ratio)
    pad_h = int(h * pad_ratio)
    nx = max(0, x - pad_w)
    ny = max(0, y - pad_h)
    nw = min(img_w - nx, w + 2*pad_w)
    nh = min(img_h - ny, h + 2*pad_h)
    return nx, ny, nw, nh

class FaceVerifier:
    """FaceDetection 1차 필터 + FaceMesh 2차 검증"""
    def __init__(self):
        self.mesh = mp_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.detect_counter = 0

    def passes_basic_filters(self, score, w, h):
        if score < FACE_SCORE_TH:
            return False
        if w < MIN_FACE_SIZE or h < MIN_FACE_SIZE:
            return False
        # 가로세로 비정상 비율 제거(너무 납작/긴 박스)
        ar = h / max(1, w)
        if ar < 0.8 or ar > 2.2:
            return False
        return True

    def verify_with_facemesh(self, frame_bgr, bbox):
        x,y,w,h = bbox
        img_h, img_w = frame_bgr.shape[:2]
        rx, ry, rw, rh = expand_clip_roi(x, y, w, h, img_w, img_h, ROI_PADDING_RATIO)
        roi = frame_bgr[ry:ry+rh, rx:rx+rw]
        if roi.size == 0:
            return False
        rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
        res = self.mesh.process(rgb)
        if not res.multi_face_landmarks:
            return False
        # 랜드마크 개수로 검증(보통 468개)
        n_lm = len(res.multi_face_landmarks[0].landmark)
        return n_lm >= FACEMESH_MIN_LANDMARKS

    def is_human_face(self, frame_bgr, bbox, score):
        # 1) 점수/크기/종횡비
        x,y,w,h = bbox
        if not self.passes_basic_filters(score, w, h):
            return False
        # 2) Facemesh는 간헐적으로만(성능 튜닝)
        self.detect_counter += 1
        if not VERIFY_WITH_FACEMESH:
            return True
        if (self.detect_counter % VERIFY_EVERY_N_DETECTIONS) != 0:
            return True
        return self.verify_with_facemesh(frame_bgr, bbox)

def main():
    cap = cv2.VideoCapture(0)
    idgen = IDGenerator()
    people = dict()

    face_detector = mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.5)
    pose_detector = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    verifier = FaceVerifier()

    frame_idx = 0
    fps_time = time.time()
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        img_h, img_w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Pose (ankles)
        pose_res = pose_detector.process(rgb)
        ankles = None
        if pose_res.pose_landmarks:
            lm = pose_res.pose_landmarks.landmark
            left_ankle_v = lm[31].y * img_h
            right_ankle_v = lm[32].y * img_h
            left_ankle_u = lm[31].x * img_w
            right_ankle_u = lm[32].x * img_w
            ankles = {'left': (left_ankle_u, left_ankle_v),
                      'right': (right_ankle_u, right_ankle_v)}

        faces_bboxes = []
        faces_scores = []
        if frame_idx % DETECT_EVERY_N_FRAMES == 0:
            face_res = face_detector.process(rgb)
            if face_res.detections:
                for det in face_res.detections:
                    r = det.location_data.relative_bounding_box
                    score = float(det.score[0]) if det.score else 0.0
                    x = int(max(0, r.xmin * img_w))
                    y = int(max(0, r.ymin * img_h))
                    w = int(r.width * img_w)
                    h = int(r.height * img_h)
                    if x+w > img_w: w = img_w - x
                    if y+h > img_h: h = img_h - y
                    # --- [중요] 사람 얼굴 검증 ---
                    bbox = (x,y,w,h)
                    if verifier.is_human_face(frame, bbox, score):
                        faces_bboxes.append(bbox)
                        faces_scores.append(score)
                    # --------------------------------

            # 매칭/업데이트
            assigned = set()
            for pid, pstate in list(people.items()):
                best_i = -1
                best_iou = 0.0
                for i, fb in enumerate(faces_bboxes):
                    if i in assigned: continue
                    val = iou(pstate.bbox, fb)
                    if val > best_iou:
                        best_iou = val
                        best_i = i
                if best_i != -1 and best_iou > 0.2:
                    fb = faces_bboxes[best_i]
                    tracker = cv2.TrackerCSRT_create()
                    tracker.init(frame, tuple(fb))
                    pstate.tracker = tracker
                    pstate.bbox = fb
                    pstate.frames_missing = 0
                    assigned.add(best_i)

            for i, fb in enumerate(faces_bboxes):
                if i in assigned: continue
                tracker = cv2.TrackerCSRT_create()
                tracker.init(frame, tuple(fb))
                new_id = idgen.get()
                people[new_id] = PersonState(tracker, fb, new_id)

        else:
            lost_ids = []
            for pid, pstate in list(people.items()):
                ok, box = pstate.tracker.update(frame)
                if ok:
                    x,y,w,h = [int(v) for v in box]
                    pstate.bbox = (x,y,w,h)
                    pstate.frames_missing = 0
                else:
                    pstate.frames_missing += 1
                if pstate.frames_missing > MAX_INACTIVE_FRAMES:
                    lost_ids.append(pid)
            for pid in lost_ids:
                del people[pid]

        # 표시/키 추정
        for pid, pstate in people.items():
            x,y,w,h = pstate.bbox
            v_head = y
            u_center = x + w/2
            v_foot = None
            u_foot = None
            if ankles:
                lu, lv = ankles['left']
                ru, rv = ankles['right']
                if abs(lu - u_center) < abs(ru - u_center):
                    u_foot, v_foot = lu, lv
                else:
                    u_foot, v_foot = ru, rv
                if not (0 <= v_foot <= img_h):
                    v_foot = None
            if v_foot is None:
                u_foot, v_foot = bbox_bottom_center(pstate.bbox)

            est = estimate_height_from_pixels(v_head, v_foot, FX, FY, CX, CY, H_CAM, u_foot=u_foot)
            height_text = "N/A"
            if est is not None:
                H_est, D = est
                pstate.heights.append(H_est)
                avgH = sum(pstate.heights)/len(pstate.heights)
                height_text = f"{avgH:.2f} m"

            cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
            cv2.putText(frame, f"ID:{pid}", (x, y-30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,0), 2)
            cv2.putText(frame, f"H: {height_text}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)
            cv2.circle(frame, (int(u_center), int(v_head)), 4, (0,0,255), -1)
            cv2.circle(frame, (int(u_foot), int(v_foot)), 4, (255,0,0), -1)

        if frame_idx % 10 == 0:
            now = time.time()
            fps = 10.0 / (now - fps_time) if (now - fps_time) > 1e-6 else 0.0
            fps_time = now
        cv2.putText(frame, f"Frame:{frame_idx} Faces:{len(people)}", (10,20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 2)

        cv2.imshow("FaceTrack+Height(Verified)", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break
        frame_idx += 1

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
