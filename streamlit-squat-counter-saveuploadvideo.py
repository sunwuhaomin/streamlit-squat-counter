import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import datetime
import tempfile
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Google Drive API setup
SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = 'credentials.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=credentials)

# Function to upload file to Google Drive
def upload_to_drive(file_path, file_name):
    file_metadata = {'name': file_name}
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Initialize drawing utility
mp_drawing = mp.solutions.drawing_utils

def calculate_angle(a, b, c):
    a = np.array(a)  # First
    b = np.array(b)  # Mid
    c = np.array(c)  # End
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle > 180.0:
        angle = 360-angle
        
    return angle

def process_video(video_source, is_file=False):
    if is_file:
        cap = cv2.VideoCapture(video_source)
    else:
        cap = cv2.VideoCapture(0)  # Use webcam

    while cap.isOpened() and st.session_state.exercise_active:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Recolor image to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
    
        # Make detection
        results = pose.process(image)
    
        # Recolor back to BGR
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # Extract landmarks
        try:
            landmarks = results.pose_landmarks.landmark
            
            # Get coordinates
            hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            
            # Calculate angle
            angle = calculate_angle(hip, knee, ankle)
            
            # Squat counter logic
            if angle > 160:
                st.session_state.stage = "up"
            if angle < 120 and st.session_state.stage == 'up':
                st.session_state.stage = "down"
                st.session_state.counter += 1
            
            # Save position data
            st.session_state.position_data.append({
                'timestamp': datetime.datetime.now(),
                'hip_x': hip[0],
                'hip_y': hip[1],
                'knee_x': knee[0],
                'knee_y': knee[1],
                'ankle_x': ankle[0],
                'ankle_y': ankle[1],
                'angle': angle,
                'stage': st.session_state.stage,
                'counter': st.session_state.counter
            })
                
        except:
            pass
        
        # Render squat counter
        # Setup status box
        cv2.rectangle(image, (0,0), (225,73), (245,117,16), -1)
        
        # Rep data
        cv2.putText(image, 'REPS', (15,12), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
        cv2.putText(image, str(st.session_state.counter), 
                    (10,60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2, cv2.LINE_AA)
        
        # Stage data
        cv2.putText(image, 'STAGE', (65,12), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
        cv2.putText(image, st.session_state.stage, 
                    (60,60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2, cv2.LINE_AA)
        
        # Render detections
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2), 
                                mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2) 
                                )               
        
        # Display the resulting frame
        st.session_state.video_frame.image(image, channels="BGR")
        st.session_state.counter_text.text(f"Squat Count: {st.session_state.counter}")
        st.session_state.stage_text.text(f"Stage: {st.session_state.stage}")

    cap.release()

# Streamlit app
def main():
    st.title("Squat Counter with Streamlit and MediaPipe")

    # Streamlit widgets
    video_file = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov"])
    start_button = st.button("Start Exercise")
    stop_button = st.button("Stop Exercise")
    save_button = st.button("Save Data")

    # Initialize session state
    if 'counter' not in st.session_state:
        st.session_state.counter = 0
    if 'stage' not in st.session_state:
        st.session_state.stage = None
    if 'position_data' not in st.session_state:
        st.session_state.position_data = []
    if 'exercise_active' not in st.session_state:
        st.session_state.exercise_active = False

    # Create placeholders
    st.session_state.counter_text = st.empty()
    st.session_state.stage_text = st.empty()
    st.session_state.video_frame = st.empty()

    if start_button:
        st.session_state.exercise_active = True
        st.session_state.counter = 0
        st.session_state.stage = None
        st.session_state.position_data = []

        if video_file is not None:
            # Save uploaded file to a temporary file
            tfile = tempfile.NamedTemporaryFile(delete=False) 
            tfile.write(video_file.read())
            process_video(tfile.name, is_file=True)
        else:
            process_video(0)  # Use webcam if no file is uploaded

    if stop_button:
        st.session_state.exercise_active = False

    if save_button and st.session_state.position_data:
        # Save position data to CSV
        df = pd.DataFrame(st.session_state.position_data)
        csv_path = "squat_position_data.csv"
        df.to_csv(csv_path, index=False)

        # Upload CSV to Google Drive
        file_id = upload_to_drive(csv_path, "squat_position_data.csv")
        st.success(f"Data uploaded to Google Drive with file ID: {file_id}")
        st.write(f"https://drive.google.com/file/d/{file_id}/view")

if __name__ == "__main__":
    main()
