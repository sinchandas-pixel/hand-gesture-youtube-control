import cv2
import mediapipe as mp
import time

class HandDetector():
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon
        
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.maxHands, 
            min_detection_confidence=self.detectionCon, 
            min_tracking_confidence=self.trackCon)
        self.mpDraw = mp.solutions.drawing_utils

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if self.results.multi_hand_landmarks :
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        return img
    def findpositions(self,img,handno=0,draw=True):
        lmlist=[]
        if self.results.multi_hand_landmarks:
            if handno < len(self.results.multi_hand_landmarks):
                myhand = self.results.multi_hand_landmarks[handno]
    
        
                for id,lm in enumerate(myhand.landmark):
                    h,w,c=img.shape
                    size=min(h,w)
                    start_x = (w - size) // 2
                    start_y = (h - size) // 2
                    img_cropped = img[start_y:start_y+size, start_x:start_x+size]
                    cx,cy=int(lm.x*w),int(lm.y*h)
                    lmlist.append([id,cx,cy])
                    #if draw:
                        #cv2.circle(img,(cx,cy),1,(255,0,0),4)
        return lmlist
def main():
    pTime = 0
    cap = cv2.VideoCapture(0)
    detector = HandDetector()

    while True:
        success, img = cap.read()
        img = detector.findHands(img)
        lmlist=detector.findpositions(img)
        if len(lmlist) !=0:
            print(lmlist[4])
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime

        cv2.putText(img, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 0, 255), 3)
        cv2.imshow("Image", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
