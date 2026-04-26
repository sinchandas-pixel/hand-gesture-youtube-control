import cv2
import mediapipe as mp
import pyautogui
import time
import math

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# --- Helpers ---

def get_lm(lmlist, id):
    return lmlist[id][1], lmlist[id][2]  # x, y

def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def fingers_up(lmlist):
    tips = [4, 8, 12, 16, 20]
    fingers = []
    # Thumb: compare x (horizontal flip handled)
    fingers.append(1 if lmlist[4][1] > lmlist[3][1] else 0)
    # Other fingers: tip y < pip y means extended
    for tip in tips[1:]:
        fingers.append(1 if lmlist[tip][2] < lmlist[tip - 2][2] else 0)
    return fingers

def swipe_direction(history, axis='x', threshold=40):
    """Returns 'pos', 'neg', or None based on movement over recent frames."""
    if len(history) < 6:
        return None
    delta = history[-1][axis] - history[0][axis]
    if abs(delta) > threshold:
        return 'pos' if delta > 0 else 'neg'
    return None

# --- State ---
cooldown = 0.35
last_action = 0

prev_dist = None          # for two-finger volume
index_history = []        # for scroll (index finger y)
swipe_history = []        # for next/prev (hand x)
thumb_history = []        # for seek (thumb x)

like_start = None
dislike_start = None
HOLD_TIME = 1.0           # seconds to hold for like/dislike

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    now = time.time()
    acted = False

    if results.multi_hand_landmarks:
        for hand_lms in results.multi_hand_landmarks:
            lmlist = [[i, int(lm.x * frame.shape[1]), int(lm.y * frame.shape[0])]
                      for i, lm in enumerate(hand_lms.landmark)]
            mp_draw.draw_landmarks(frame, hand_lms, mp_hands.HAND_CONNECTIONS)

            fingers = fingers_up(lmlist)
            finger_count = sum(fingers)

            # Landmarks
            index_tip = get_lm(lmlist, 8)
            middle_tip = get_lm(lmlist, 12)
            thumb_tip  = get_lm(lmlist, 4)
            pinky_tip  = get_lm(lmlist, 20)
            wrist      = get_lm(lmlist, 0)

            # ─── Open palm → fist: Play/Pause ───────────────────────────────
            # Detected by transition; here we use fist (all fingers down) as toggle
            if fingers == [0, 0, 0, 0, 0] and (now - last_action) > cooldown:
                pyautogui.press('space')
                last_action = now
                acted = True

            # ─── Index + middle pinch close together: Mute ──────────────────
            elif fingers == [0, 1, 1, 0, 0]:
                pinch = distance(index_tip, middle_tip)
                if pinch < 30 and (now - last_action) > cooldown:
                    pyautogui.press('m')
                    last_action = now
                    acted = True

            # ─── All 5 fingers spread: Fullscreen ───────────────────────────
            elif fingers == [1, 1, 1, 1, 1] and (now - last_action) > cooldown:
                # Extra check: palm spread wide (thumb-pinky distance)
                if distance(thumb_tip, pinky_tip) > 150:
                    pyautogui.press('f')
                    last_action = now
                    acted = True

            # ─── Two fingers (✌): Volume via spread / pinch ─────────────────
            elif fingers == [0, 1, 1, 0, 0]:
                curr_dist = distance(index_tip, middle_tip)
                if prev_dist is not None and (now - last_action) > 0.15:
                    delta = curr_dist - prev_dist
                    if delta > 8:
                        pyautogui.press('volumeup')
                        last_action = now
                    elif delta < -8:
                        pyautogui.press('volumedown')
                        last_action = now
                prev_dist = curr_dist

            # ─── Index finger only: Scroll up / down ────────────────────────
            elif fingers == [0, 1, 0, 0, 0]:
                index_history.append({'y': index_tip[1]})
                if len(index_history) > 10:
                    index_history.pop(0)
                if len(index_history) >= 6 and (now - last_action) > 0.2:
                    dy = index_history[0]['y'] - index_history[-1]['y']
                    if dy > 25:
                        pyautogui.scroll(3)
                        last_action = now
                    elif dy < -25:
                        pyautogui.scroll(-3)
                        last_action = now
            else:
                index_history.clear()

            # ─── Three fingers: Swipe left/right → Next/Prev video ──────────
            if fingers == [0, 1, 1, 1, 0]:
                swipe_history.append({'x': wrist[0]})
                if len(swipe_history) > 12:
                    swipe_history.pop(0)
                direction = swipe_direction(swipe_history, 'x', threshold=60)
                if direction and (now - last_action) > cooldown:
                    if direction == 'pos':
                        pyautogui.hotkey('shift', 'n')   # next video
                    else:
                        pyautogui.hotkey('shift', 'p')   # previous video
                    last_action = now
                    swipe_history.clear()
            else:
                swipe_history.clear()

            # ─── Thumb only: Swipe left/right → Seek ±10s ───────────────────
            if fingers == [1, 0, 0, 0, 0]:
                thumb_history.append({'x': thumb_tip[0]})
                if len(thumb_history) > 10:
                    thumb_history.pop(0)
                direction = swipe_direction(thumb_history, 'x', threshold=45)
                if direction and (now - last_action) > cooldown:
                    if direction == 'pos':
                        pyautogui.press('right')   # +10s
                    else:
                        pyautogui.press('left')    # −10s
                    last_action = now
                    thumb_history.clear()
            else:
                thumb_history.clear()

            # ─── Thumbs up (held 1s): Like ───────────────────────────────────
            if fingers == [1, 0, 0, 0, 0] and thumb_tip[1] < wrist[1]:
                if like_start is None:
                    like_start = now
                elif (now - like_start) >= HOLD_TIME and (now - last_action) > 2.0:
                    pyautogui.press('shift+period')  # YouTube like shortcut: Shift+.
                    last_action = now
                    like_start = None
            else:
                like_start = None

            # ─── Thumbs down (held 1s): Dislike ─────────────────────────────
            if fingers == [1, 0, 0, 0, 0] and thumb_tip[1] > wrist[1]:
                if dislike_start is None:
                    dislike_start = now
                elif (now - dislike_start) >= HOLD_TIME and (now - last_action) > 2.0:
                    # No direct key; use tab navigation as fallback
                    pyautogui.hotkey('shift', 'comma')
                    last_action = now
                    dislike_start = None
            else:
                dislike_start = None

            # ─── Pinky + index (🤟): Captions ────────────────────────────────
            if fingers == [1, 1, 0, 0, 1] and (now - last_action) > cooldown:
                pyautogui.press('c')
                last_action = now

    else:
        # No hand → reset dynamic state
        prev_dist = None
        index_history.clear()
        swipe_history.clear()
        thumb_history.clear()
        like_start = None
        dislike_start = None

    cv2.imshow("YouTube Gesture Control", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()