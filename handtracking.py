import cv2
import mediapipe as mp
import time

class handditector():
    def __init__(self,mode=False,maxhands=2,detectioncon=0.5,trackcon=0.5):
        self.mode= mode
        self.maxhands= maxhands
        self.detectioncon= detectioncon
        self.trackcon= trackcon

        self.mpHands=mp.solutions.hands
        self.hands=self.mpHands.Hands(self.mode,self.maxhands,self.detectioncon,self.trackcon)
        self.mpDraw=mp.solutions.drawing_utils
        hand_connections=self.mpHands.HAND_CONNECTIONS
#ptime=0
#ctime=0


        with self.mpHands.Hands(
    static_image_mode=False
)as hands:
    #while True:
        #success, img=cap.read()
            def findhands(self,img,draw=True):
                imgrgb=cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                results=self.hands.process(imgrgb)
                print(results.multi_hand_landmarks)
        
                if results.multi_hand_landmarks:
                    for handlms in results.multi_hand_landmarks:
                        if draw:
                            self.mpdraw.draw_landmarks(img,handlms,self.mphands.HAND_CONNECTIONS)
                        #for id,lm in enumerate(handlms.landmark):
                            
                            
                return img
                
        
        def main():
            ptime=0
            ctime=0
            cap = cv2.VideoCapture(0)
            detector=handditector()
            while True:
                success, img=cap.read()
                detector.findhands(img)
                ctime=time.time()
                fps=1/(ctime-ptime)
                ptime=ctime
                cv2.putText(img,str(int(fps)),(10,70),cv2.FONT_HERSHEY_TRIPLEX,3,(255,0,255),4)
                cv2.imshow('image',img)
                cv2.waitKey(1) & 0xFF == ord('Q')
        if __name__ == "main":
            main()