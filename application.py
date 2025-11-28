import os
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import cv2
import numpy as np
import mediapipe as mp
import pickle
import base64

# --- APP & ML CONFIGURATION ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_ml_service_key'
CORS(app) 
socketio = SocketIO(app, cors_allowed_origins="*")

# --- MODEL & MEDIAPIPE INITIALIZATION ---
try:
    with open("./asl_prediction/ASL_model.p", "rb") as f: model_dict = pickle.load(f); model = model_dict["model"]
except FileNotFoundError: print("Error: Model file not found."); model = None

labels = { "a": "A", "b": "B", "c": "C", "d": "D", "e": "E", "f": "F", "g": "G", "h": "H", "i": "I", "j": "J", "k": "K", "l": "L", "m": "M", "n": "N", "o": "O", "p": "P", "q": "Q", "r": "R", "s": "S", "t": "T", "u": "U", "v": "V", "w": "W", "x": "X", "y": "Y", "z": "Z" }
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.5)

# --- WEBSOCKET PREDICTION LOGIC ---
@socketio.on('process_frame')
def handle_frame(data):
    image_data = base64.b64decode(data['image_data'].split(',')[1])
    np_arr = np.frombuffer(image_data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # Flip the frame for model consistency
    frame = cv2.flip(frame, 1)

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)
    
    prediction = "" 
    landmarks = []
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            for landmark in hand_landmarks.landmark: landmarks.append({'x': landmark.x, 'y': landmark.y, 'z': landmark.z})
            if model:
                try:
                    data_aux = []; x_ = [lm.x for lm in hand_landmarks.landmark]; y_ = [lm.y for lm in hand_landmarks.landmark]
                    for i in range(len(hand_landmarks.landmark)): data_aux.append(hand_landmarks.landmark[i].x - min(x_)); data_aux.append(hand_landmarks.landmark[i].y - min(y_))
                    prediction = labels.get(model.predict([np.asarray(data_aux)])[0], "")
                except Exception as e: print(f"Prediction error: {e}")
                
    socketio.emit('prediction_result', {'prediction': prediction, 'landmarks': landmarks})

# --- The /video_feed route is no longer needed ---

if __name__ == '__main__':
    socketio.run(app, port=5001, debug=True)