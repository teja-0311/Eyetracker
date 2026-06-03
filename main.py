import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import subprocess
import os

pyautogui.FAILSAFE = False
EYE_AR_THRESH = 0.20
EYE_AR_CONSEC_FRAMES = 2
DOUBLE_BLINK_MAX_TIME = 1.0
TRIPLE_BLINK_MAX_TIME = 1.5
SMOOTHING = 0.85  
DEBUG_DRAW = True
FRAME_SIZE = (640, 480)
CALIBRATION_BUFFER = 0.1 
SENSITIVITY = 0.65  

LONG_BLINK_TIME = 1.5
EXIT_TIME = 3.0

screen_w, screen_h = pyautogui.size()
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)

LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]
IRIS_IDX = [474, 475, 476, 477]

class ActionState:
    def __init__(self):
        self.drag_mode = False
        self.scroll_mode = False
        self.keyboard_mode = False
        self.last_action_time = 0
        self.both_eyes_closed_start = 0
        self.scroll_direction = 0
        
action_state = ActionState()

def eye_aspect_ratio(eye):
    A = np.linalg.norm(np.array(eye[1]) - np.array(eye[5]))
    B = np.linalg.norm(np.array(eye[2]) - np.array(eye[4]))
    C = np.linalg.norm(np.array(eye[0]) - np.array(eye[3]))
    return (A + B) / (2.0 * C)

def open_keyboard():
    try:
        if os.name == 'nt':  
            subprocess.Popen(['osk'], shell=True)
        elif os.name == 'posix':  
            pass
        print("[ACTION] On-screen keyboard opened.")
        return True
    except Exception as e:
        print(f"[WARN] Could not open keyboard: {e}")
        print("[INFO] You can manually open the on-screen keyboard")
        return False

def close_keyboard():
    try:
        subprocess.run(['taskkill', '/f', '/im', 'osk.exe'], capture_output=True)
        print("[ACTION] On-screen keyboard closed.")
        return True
    except Exception as e:
        return False

def can_perform_action():
    current_time = time.time()
    if current_time - action_state.last_action_time < 0.5:
        return False
    action_state.last_action_time = current_time
    return True

def perform_left_click():
    if can_perform_action():
        pyautogui.click()
        print("[ACTION] Left click")
        return True
    return False

def perform_right_click():
    if can_perform_action():
        pyautogui.rightClick()
        print("[ACTION] Right click")
        return True
    return False

def perform_double_click():
    if can_perform_action():
        pyautogui.doubleClick()
        print("[ACTION] Double click")
        return True
    return False

def toggle_scroll_mode():
    if can_perform_action():
        action_state.scroll_mode = not action_state.scroll_mode
        action_state.scroll_direction = 0
        print(f"[ACTION] Scroll mode: {action_state.scroll_mode}")
        return True
    return False

def toggle_keyboard_mode():
    if can_perform_action():
        action_state.keyboard_mode = not action_state.keyboard_mode
        if action_state.keyboard_mode:
            success = open_keyboard()
            if not success:
                action_state.keyboard_mode = False
        else:
            close_keyboard()
        print(f"[ACTION] Keyboard mode: {action_state.keyboard_mode}")
        return True
    return False

def perform_scroll(direction):
    if action_state.scroll_mode and direction != 0:
        scroll_amount = direction * 80
        pyautogui.scroll(scroll_amount)
        direction_text = "down" if direction > 0 else "up"
        print(f"[ACTION] Scrolling {direction_text}")

cap = cv2.VideoCapture(0)
blink_data = {
    "L": {"counter": 0, "timestamps": [], "last_blink_end": 0, "waiting_for_triple": False},
    "R": {"counter": 0, "timestamps": [], "last_blink_end": 0, "waiting_for_triple": False},
    "BOTH": {"counter": 0, "timestamps": [], "last_blink_end": 0, "waiting_for_triple": False}
}

last_mouse_x, last_mouse_y = pyautogui.position()
calib_points = {
    "top_left": None, "top_right": None,
    "bottom_left": None, "bottom_right": None,
    "center": None
}

print("[INFO] Enhanced 4-Point Calibration for Precise Cursor Control")
print("Look at the CORNERS of your screen:")
print("1 = Top Left | 2 = Top Right | 3 = Bottom Left | 4 = Bottom Right | ENTER = Done")

def get_iris_center(mesh_points):
    try:
        iris_points = mesh_points[IRIS_IDX]
        return np.mean(iris_points, axis=0).astype(int)
    except:
        left_eye = mesh_points[LEFT_EYE_IDX]
        right_eye = mesh_points[RIGHT_EYE_IDX]
        return np.mean(np.vstack((left_eye, right_eye)), axis=0).astype(int)

def map_to_screen(iris_point):
    """Enhanced mapping using perspective transformation for accurate cursor positioning"""
    try:
        if (calib_points["top_left"] is None or calib_points["top_right"] is None or 
            calib_points["bottom_left"] is None or calib_points["bottom_right"] is None):
            return screen_w // 2, screen_h // 2
        
        iris = np.array(iris_point, dtype=np.float32)
        src_points = np.array([
            calib_points["top_left"],
            calib_points["top_right"], 
            calib_points["bottom_right"],
            calib_points["bottom_left"]
        ], dtype=np.float32)
        buffer_x = screen_w * CALIBRATION_BUFFER
        buffer_y = screen_h * CALIBRATION_BUFFER
        
        dst_points = np.array([
            [buffer_x, buffer_y],                    
            [screen_w - buffer_x, buffer_y],         
            [screen_w - buffer_x, screen_h - buffer_y], 
            [buffer_x, screen_h - buffer_y]          
        ], dtype=np.float32)
        
        matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        
        iris_reshaped = iris.reshape(1, 1, 2)
        screen_point = cv2.perspectiveTransform(iris_reshaped, matrix)
        
        screen_x = int(screen_point[0][0][0] * SENSITIVITY)
        screen_y = int(screen_point[0][0][1] * SENSITIVITY)
        
        screen_x = max(0, min(screen_w - 1, screen_x))
        screen_y = max(0, min(screen_h - 1, screen_y))
        
        return screen_x, screen_y
        
    except Exception as e:
        print(f"[MAPPING] Error: {e}, using center")
        return screen_w // 2, screen_h // 2

def detect_blink_pattern(side, current_time):
    """Enhanced blink pattern detection"""
    data = blink_data[side]
    
    
    data["timestamps"] = [t for t in data["timestamps"] if current_time - t < TRIPLE_BLINK_MAX_TIME]
    
    count = len(data["timestamps"])
    
    if count >= 3:
        total_time = data["timestamps"][-1] - data["timestamps"][0]
        if total_time < TRIPLE_BLINK_MAX_TIME:
            print(f"[BLINK] {side} triple blink detected ({total_time:.2f}s)")
            data["timestamps"].clear()
            data["waiting_for_triple"] = False
            return "TRIPLE"
    
    if count >= 2 and not data["waiting_for_triple"]:
        time_between = data["timestamps"][-1] - data["timestamps"][-2]
        if time_between < DOUBLE_BLINK_MAX_TIME:
            time_since_last = current_time - data["timestamps"][-1]
            if time_since_last < 0.5:  
                data["waiting_for_triple"] = True
                return "WAITING"
            else:
                print(f"[BLINK] {side} double blink detected ({time_between:.2f}s)")
                data["timestamps"].clear()
                return "DOUBLE"
    
    if data["waiting_for_triple"] and count >= 2:
        time_since_last = current_time - data["timestamps"][-1]
        if time_since_last >= 0.5:
            time_between = data["timestamps"][-1] - data["timestamps"][-2]
            print(f"[BLINK] {side} double blink confirmed ({time_between:.2f}s)")
            data["timestamps"].clear()
            data["waiting_for_triple"] = False
            return "DOUBLE"
    
    return None

def detect_head_tilt_for_scroll(mesh_points):
    """Improved head tilt detection for scrolling using normalized coordinates"""
    try:
        nose_tip = mesh_points[1]      
        forehead = mesh_points[10]     
        chin = mesh_points[152]        
        nose_to_forehead = nose_tip[1] - forehead[1]   
        nose_to_chin = nose_tip[1] - chin[1]           
        
        head_tilt_ratio = (nose_to_forehead - nose_to_chin) * 2
        
        if head_tilt_ratio > 0.15:    
            return 1
        elif head_tilt_ratio < -0.15: 
            return -1
        else:                         
            return 0
            
    except Exception as e:
        print(f"[HEAD TILT] Error: {e}")
        return 0
calibration_complete = False
calibration_steps = [
    ("top_left", "Look at TOP-LEFT corner and press 1"),
    ("top_right", "Look at TOP-RIGHT corner and press 2"), 
    ("bottom_right", "Look at BOTTOM-RIGHT corner and press 3"),
    ("bottom_left", "Look at BOTTOM-LEFT corner and press 4")
]
current_step = 0

print("\n🎯 PRECISE CALIBRATION INSTRUCTIONS:")
print("1. Sit in your normal position")
print("2. Look DIRECTLY at each screen corner with your EYES")
print("3. Keep your HEAD STILL, move only your eyes")
print("4. Press the number key when you're sure you're looking at the corner")
print("5. Complete all 4 corners for accurate cursor control\n")

while not calibration_complete and current_step < len(calibration_steps):
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, FRAME_SIZE)
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    iris_center = None
    if results.multi_face_landmarks:
        mesh_points = np.array([(p.x, p.y) for p in results.multi_face_landmarks[0].landmark])
        mesh_points[:, 0] *= w
        mesh_points[:, 1] *= h
        iris_center = get_iris_center(mesh_points)

        if iris_center is not None:
            cv2.circle(frame, tuple(iris_center), 8, (0, 0, 255), -1)
            calibrated_count = sum(1 for point in calib_points.values() if point is not None)
            if calibrated_count >= 2:
                screen_x, screen_y = map_to_screen(iris_center)
                cv2.putText(frame, f"Predicted: ({screen_x}, {screen_y})", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            cv2.putText(frame, f"Iris: ({iris_center[0]}, {iris_center[1]})", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    step_name, instruction = calibration_steps[current_step]
    cv2.putText(frame, instruction, (10, h-120), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    
    progress = f"Step {current_step + 1}/4: {step_name.upper().replace('_', ' ')}"
    cv2.putText(frame, progress, (10, h-80), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    calibrated_points = [key for key, point in calib_points.items() if point is not None]
    if calibrated_points:
        status_text = f"Calibrated: {', '.join(calibrated_points)}"
        cv2.putText(frame, status_text, (10, h-40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('1') and iris_center is not None and current_step == 0:
        calib_points["top_left"] = iris_center.copy()
        print(f"[CALIB] Top Left: {iris_center}")
        current_step += 1
    elif key == ord('2') and iris_center is not None and current_step == 1:
        calib_points["top_right"] = iris_center.copy()
        print(f"[CALIB] Top Right: {iris_center}")
        current_step += 1
    elif key == ord('3') and iris_center is not None and current_step == 2:
        calib_points["bottom_right"] = iris_center.copy()
        print(f"[CALIB] Bottom Right: {iris_center}")
        current_step += 1
    elif key == ord('4') and iris_center is not None and current_step == 3:
        calib_points["bottom_left"] = iris_center.copy()
        print(f"[CALIB] Bottom Left: {iris_center}")
        current_step += 1
    elif key == 13:  
        if all(calib_points[key] is not None for key in ["top_left", "top_right", "bottom_left", "bottom_right"]):
            calibration_complete = True
            print("[SUCCESS] 4-point calibration complete!")
            print(f"Screen mapping area established")
        else:
            print("[WARN] Please complete all 4 corner calibrations!")
    elif key == 27:
        cap.release()
        cv2.destroyAllWindows()
        exit()

    cv2.imshow("Precise 4-Point Calibration", frame)
print("\n[TEST] Testing cursor mapping accuracy...")
test_positions = [
    ("Top-Left", calib_points["top_left"]),
    ("Top-Right", calib_points["top_right"]),
    ("Bottom-Right", calib_points["bottom_right"]),
    ("Bottom-Left", calib_points["bottom_left"]),
    ("Center", ((calib_points["top_left"][0] + calib_points["top_right"][0]) // 2, 
                (calib_points["top_left"][1] + calib_points["bottom_left"][1]) // 2))
]

print("Mapping test results:")
for name, point in test_positions:
    if point is not None:
        screen_x, screen_y = map_to_screen(point)
        expected_x = 0 if "Left" in name else screen_w if "Right" in name else screen_w // 2
        expected_y = 0 if "Top" in name else screen_h if "Bottom" in name else screen_h // 2
        accuracy = f"✓" if abs(screen_x - expected_x) < 50 and abs(screen_y - expected_y) < 50 else "✗"
        print(f"  {accuracy} {name}: Expected ~({expected_x}, {expected_y}) → Got ({screen_x}, {screen_y})")

cv2.destroyAllWindows()

print("\n" + "="*70)
print("🎯 COMPLETE EYE CONTROL SYSTEM - READY!")
print("="*70)
print(f"📏 Screen: {screen_w} x {screen_h} (Full coverage)")
print("\n👁️  SIMPLIFIED GESTURE CONTROLS:")
print("Left Eye Double Blink    → Left Click")
print("Right Eye Double Blink   → Right Click") 
print("Both Eyes Double Blink   → Double Click")
print("Left Eye Triple Blink    → Toggle Scroll Mode")
print("Right Eye Triple Blink   → Toggle Drag Mode")
print("Both Eyes Triple Blink   → Toggle Keyboard")
print("Both Eyes Closed 1.5s    → Keyboard Toggle")
print("Both Eyes Closed 3s      → Exit Program")
print("\n🖱️  SCROLL MODE:")
print("- Tilt HEAD UP to scroll UP")
print("- Tilt HEAD DOWN to scroll DOWN")
print("- Keep head straight to stop scrolling")
print("\n🚀 Starting complete eye control system...")
frame_count = 0
program_start_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        continue
        
    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, FRAME_SIZE)
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    iris_center = None
    left_ear = right_ear = 0
    current_time = time.time()
    head_tilt = 0

    if results.multi_face_landmarks:
        mesh_points_normalized = np.array([(p.x, p.y) for p in results.multi_face_landmarks[0].landmark])
        mesh_points = mesh_points_normalized.copy()
        mesh_points[:, 0] *= w
        mesh_points[:, 1] *= h

        iris_center = get_iris_center(mesh_points)

        left_eye = mesh_points[LEFT_EYE_IDX]
        right_eye = mesh_points[RIGHT_EYE_IDX]
        left_ear = eye_aspect_ratio(left_eye)
        right_ear = eye_aspect_ratio(right_eye)
        left_closed = left_ear < EYE_AR_THRESH
        right_closed = right_ear < EYE_AR_THRESH
        both_closed = left_closed and right_closed
        head_tilt = detect_head_tilt_for_scroll(mesh_points_normalized)
        if action_state.scroll_mode:
            if head_tilt != action_state.scroll_direction:
                action_state.scroll_direction = head_tilt
                if head_tilt != 0:
                    perform_scroll(head_tilt)
        if both_closed:
            if action_state.both_eyes_closed_start == 0:
                action_state.both_eyes_closed_start = current_time
            else:
                closed_duration = current_time - action_state.both_eyes_closed_start
                
                if closed_duration >= LONG_BLINK_TIME and closed_duration < EXIT_TIME:
                    if not action_state.keyboard_mode and can_perform_action():
                        toggle_keyboard_mode()
                        action_state.both_eyes_closed_start = 0
                
                elif closed_duration >= EXIT_TIME:
                    print("[ACTION] Long blink detected - Exiting program...")
                    cap.release()
                    cv2.destroyAllWindows()
                    if action_state.keyboard_mode:
                        close_keyboard()
                    exit()
        else:
            action_state.both_eyes_closed_start = 0
        for side, closed in [("L", left_closed), ("R", right_closed), ("BOTH", both_closed)]:
            data = blink_data[side]
            
            if closed:
                data["counter"] += 1
            else:
                if data["counter"] >= EYE_AR_CONSEC_FRAMES:
                    data["timestamps"].append(current_time)
                    data["last_blink_end"] = current_time
                    # print(f"[BLINK] {side} eye blink detected")
                data["counter"] = 0
        for side in ["L", "R", "BOTH"]:
            pattern = detect_blink_pattern(side, current_time)
            if pattern:
                if pattern == "DOUBLE":
                    if side == "L":
                        perform_left_click()
                    elif side == "R":
                        perform_right_click()
                    elif side == "BOTH":
                        perform_double_click()
                elif pattern == "TRIPLE":
                    if side == "L":
                        toggle_scroll_mode()
                    elif side == "R":
                        if can_perform_action():
                            action_state.drag_mode = not action_state.drag_mode
                            if action_state.drag_mode:
                                pyautogui.mouseDown()
                                print("[ACTION] Drag started")
                            else:
                                pyautogui.mouseUp()
                                print("[ACTION] Drag ended")
                    elif side == "BOTH":
                        toggle_keyboard_mode()
        if iris_center is not None:
            screen_x, screen_y = map_to_screen(iris_center)
            last_mouse_x = last_mouse_x * SMOOTHING + screen_x * (1 - SMOOTHING)
            last_mouse_y = last_mouse_y * SMOOTHING + screen_y * (1 - SMOOTHING)
            pyautogui.moveTo(int(last_mouse_x), int(last_mouse_y))
        if iris_center is not None:
            cv2.circle(frame, tuple(iris_center), 5, (0, 0, 255), -1)
        waiting_status = []
        for side in ["L", "R", "BOTH"]:
            if blink_data[side]["waiting_for_triple"]:
                waiting_status.append(f"{side}:WAITING")
        blink_counts = f"Blinks - L:{len(blink_data['L']['timestamps'])} R:{len(blink_data['R']['timestamps'])} B:{len(blink_data['BOTH']['timestamps'])}"
        if waiting_status:
            blink_counts += " | " + " ".join(waiting_status)
        long_blink_info = ""
        if action_state.both_eyes_closed_start > 0:
            closed_duration = current_time - action_state.both_eyes_closed_start
            long_blink_info = f" | Long: {closed_duration:.1f}s"
            if closed_duration >= LONG_BLINK_TIME:
                long_blink_info += " [KEYBOARD]"
        status_lines = [
            f"Cursor: {int(last_mouse_x)}, {int(last_mouse_y)} / {screen_w}x{screen_h}",
            f"Left: {left_ear:.3f} {'[CLOSED]' if left_closed else '[OPEN]'} | Right: {right_ear:.3f} {'[CLOSED]' if right_closed else '[OPEN]'}",
            blink_counts + long_blink_info,
            f"Head Tilt: {['UP', 'STRAIGHT', 'DOWN'][head_tilt+1]} | Scroll: {'ON' if action_state.scroll_mode else 'OFF'}",
            f"Drag: {'ON' if action_state.drag_mode else 'OFF'} | Keyboard: {'ON' if action_state.keyboard_mode else 'OFF'}"
        ]        
        for i, line in enumerate(status_lines):
            color = (0, 255, 0) if i > 0 else (255, 255, 0)
            cv2.putText(frame, line, (10, 30 + i*22), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

    cv2.imshow("Complete Eye Control - All Functions Working", frame)
    
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
if action_state.keyboard_mode:
    close_keyboard()