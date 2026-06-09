"""
attendance_lbph_enhanced_with_batches.py

Enhanced LBPH-based Face Attendance System with Batch support.

Changes:
 - students.csv contains an additional 'Batch' column (comma-separated if multiple)
 - Registration asks for Batch(s)
 - Before starting attendance the teacher is prompted to choose a batch (or ALL)
 - Only students belonging to the chosen batch will be marked present
 - If a detected face belongs to a different batch, a blocked event 'blocked_batch' is logged

Run:
    python attendance_lbph_enhanced_with_batches.py

Requirements:
    pip install opencv-contrib-python numpy pandas
"""
import os
import cv2
import time
import shutil
import numpy as np
import pandas as pd
from datetime import datetime, date, time as dt_time, timedelta

# ---------- CONFIG ----------
IMAGES_DIR = "registered_faces"
STUDENTS_CSV = "students.csv"
MODEL_FILE = "lbph_model.yml"
LABEL_MAP_FILE = "label_map.csv"
ATTENDANCE_CSV = "attendance_events.csv"
ATTENDANCE_SUMMARY = "attendance_summary.csv"

CAPTURE_COUNT = 25
FACE_SIZE = (200, 200)
HAAR_MODEL = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
RECOGNITION_THRESHOLD = 70.0
EXIT_TIMEOUT = 6.0
DEBOUNCE_SECONDS = 1.5
CAMERA_INDEX = 0

SESSION_START = "09:00"
SESSION_END = "10:00"
MIN_INCLASS_SECONDS = 40 * 60

os.makedirs(IMAGES_DIR, exist_ok=True)

# Helpers
def time_str_to_time(s: str) -> dt_time:
    return datetime.strptime(s, "%H:%M").time()

SESSION_START_T = time_str_to_time(SESSION_START)
SESSION_END_T = time_str_to_time(SESSION_END)

def _today_session_interval():
    today = date.today()
    start_dt = datetime.combine(today, SESSION_START_T)
    end_dt = datetime.combine(today, SESSION_END_T)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    return start_dt, end_dt

def overlap_seconds(interval_start: datetime, interval_end: datetime, window_start: datetime, window_end: datetime) -> float:
    latest_start = max(interval_start, window_start)
    earliest_end = min(interval_end, window_end)
    delta = (earliest_end - latest_start).total_seconds()
    return max(0.0, delta)

# Student helpers (now with Batch column)
def load_students():
    if os.path.exists(STUDENTS_CSV):
        df = pd.read_csv(STUDENTS_CSV, dtype=str)
        # ensure Batch column exists
        if 'Batch' not in df.columns:
            df['Batch'] = ''
        return df
    return pd.DataFrame(columns=["Student_ID", "Name", "Folder", "Batch"])

def save_students(df):
    # ensure columns order
    cols = list(df.columns)
    # include Batch if missing
    if 'Batch' not in cols:
        cols.append('Batch')
    df.to_csv(STUDENTS_CSV, index=False, columns=cols)

# Registration
def register_student_interactive(student_id: str, name: str, batch_str: str = None):
    students = load_students()
    if student_id in students['Student_ID'].values:
        print(f"[WARN] Student ID {student_id} already registered.")
        return False

    folder = os.path.join(IMAGES_DIR, str(student_id))
    os.makedirs(folder, exist_ok=True)

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("Error: could not open camera")
        return False

    print("Position the student's face in front of the camera.")
    print("Press SPACE to capture an image. Press ESC to cancel.")

    count = 0
    idx = 1
    last_capture = 0.0
    face_cascade = cv2.CascadeClassifier(HAAR_MODEL)

    try:
        while count < CAPTURE_COUNT:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame from camera")
                break

            display = frame.copy()
            h, w = display.shape[:2]
            cv2.putText(display, f"Captures: {count}/{CAPTURE_COUNT}", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
            cv2.putText(display, "Press SPACE to capture, ESC to cancel", (10, h-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80,80))
            for (x,y,fw,fh) in faces:
                cv2.rectangle(display, (x,y), (x+fw, y+fh), (0,255,0), 2)

            cv2.imshow("Register - Press SPACE", display)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                print("Registration cancelled")
                cap.release()
                cv2.destroyAllWindows()
                if len(os.listdir(folder)) == 0:
                    os.rmdir(folder)
                return False
            elif key == 32:  # SPACE
                if time.time() - last_capture < 0.4:
                    continue
                last_capture = time.time()
                if len(faces) > 0:
                    faces_sorted = sorted(faces, key=lambda r: r[2]*r[3], reverse=True)
                    x,y,fw,fh = faces_sorted[0]
                    face_img = frame[y:y+fh, x:x+fw]
                else:
                    h2, w2 = frame.shape[:2]
                    s = min(h2, w2)
                    cx, cy = w2//2, h2//2
                    x = max(0, cx - s//2); y = max(0, cy - s//2)
                    face_img = frame[y:y+s, x:x+s]

                face_resized = cv2.resize(face_img, FACE_SIZE)
                fname = os.path.join(folder, f"img_{idx:04d}.jpg")
                cv2.imwrite(fname, face_resized)
                print(f"Saved {fname}")
                idx += 1
                count += 1

        cap.release()
        cv2.destroyAllWindows()
    except KeyboardInterrupt:
        cap.release()
        cv2.destroyAllWindows()
        print("Interrupted; partial registration saved.")

    df = load_students()
    if batch_str is None:
        batch_str = input("Enter Batch(s) for this student (comma-separated if multiple): ").strip()
    new_row = {"Student_ID": str(student_id), "Name": name, "Folder": folder, "Batch": batch_str}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_students(df)
    print(f"Registered {name} (ID: {student_id}) with images in {folder} and Batch: {batch_str}")
    return True

# Prepare dataset & train LBPH
def prepare_dataset_and_train():
    students = load_students()
    if students.empty:
        print("No registered students. Register first.")
        return False

    images = []
    labels = []
    label_map = {}
    rev_map = {}
    current_label = 0

    for _, row in students.iterrows():
        sid = str(row['Student_ID'])
        folder = row['Folder']
        if not os.path.exists(folder):
            print(f"Warning: folder {folder} missing for {sid}")
            continue
        label_map[current_label] = sid
        rev_map[sid] = current_label
        for fname in sorted(os.listdir(folder)):
            if not fname.lower().endswith(('.jpg','.jpeg','.png')):
                continue
            path = os.path.join(folder, fname)
            img = cv2.imread(path)
            if img is None:
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, FACE_SIZE)
            images.append(gray)
            labels.append(current_label)
        current_label += 1

    if len(images) == 0:
        print("No face images found for training.")
        return False

    print(f"Training on {len(images)} samples for {len(label_map)} identities...")
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(images, np.array(labels))
    recognizer.write(MODEL_FILE)
    lm = pd.DataFrame([(k,v) for k,v in label_map.items()], columns=['label','student_id'])
    lm.to_csv(LABEL_MAP_FILE, index=False)
    print(f"Model saved to {MODEL_FILE}, labels saved to {LABEL_MAP_FILE}")
    return True

# Attendance runtime with batch filtering
class AttendanceSystem:
    def __init__(self):
        self.students = load_students()
        self.recognizer = None
        self.label_map = {}
        # presence holds runtime info and cumulative session seconds
        self.presence = {}
        for sid in self.students['Student_ID'].astype(str).tolist():
            self.presence[sid] = {
                "present": False,
                "current_enter_ts": None,
                "last_seen": None,
                "last_entry_log_time": 0,
                "cumulative_seconds": 0.0,
                "last_exit_ts": None,
            }
        self.load_model_if_exists()

        # manual session controls
        self.manual_session_start = None
        self.manual_session_end = None
        self.session_active = False
        self.capture_paused = False

        # batch in use for current attendance run; None => not selected yet
        self.current_batch = None  # string or 'ALL'

    def load_model_if_exists(self):
        if os.path.exists(MODEL_FILE) and os.path.exists(LABEL_MAP_FILE):
            try:
                self.recognizer = cv2.face.LBPHFaceRecognizer_create()
                self.recognizer.read(MODEL_FILE)
                lm = pd.read_csv(LABEL_MAP_FILE, dtype=str)
                self.label_map = {int(r['label']): str(r['student_id']) for _, r in lm.iterrows()}
                print(f"Loaded model ({len(self.label_map)} labels)")
            except Exception as e:
                print(f"Failed loading model: {e}")
                self.recognizer = None
        else:
            print("No trained model found. Train first.")

    def predict_on_face(self, face_bgr):
        if self.recognizer is None or len(self.label_map) == 0:
            return None, None, None
        gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, FACE_SIZE)
        label, confidence = self.recognizer.predict(gray)
        sid = self.label_map.get(int(label))
        if sid is None:
            return None, None, None
        name_row = self.students[self.students['Student_ID'].astype(str) == str(sid)]
        name = name_row['Name'].values[0] if not name_row.empty else 'Unknown'
        return str(sid), name, float(confidence)

    def _ensure_attendance_csv(self):
        if not os.path.exists(ATTENDANCE_CSV):
            pd.DataFrame(columns=['Timestamp','Student_ID','Name','Event','Details']).to_csv(ATTENDANCE_CSV, index=False)

    def log_event(self, student_id, name, event_type, details=None):
        ts = datetime.now().isoformat(sep=' ', timespec='seconds')
        row = {'Timestamp': ts, 'Student_ID': student_id, 'Name': name, 'Event': event_type, 'Details': details or ''}
        self._ensure_attendance_csv()
        df = pd.read_csv(ATTENDANCE_CSV, dtype=str)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df.to_csv(ATTENDANCE_CSV, index=False)
        print(f"[{event_type.upper()}] {name} ({student_id}) at {ts} {(' - '+details) if details else ''}")

    def student_batches(self, student_id: str):
        """Return list of batches for a student (trimmed, uppercased for comparison)."""
        row = self.students[self.students['Student_ID'].astype(str) == str(student_id)]
        if row.empty:
            return []
        raw = row.iloc[0].get('Batch', '')
        items = [b.strip() for b in str(raw).split(',') if b.strip()!='']
        return [b.upper() for b in items]

    def batch_matches(self, student_id: str, selected_batch: str):
        """Return True if student's batches include selected_batch or if selected_batch == 'ALL'."""
        if selected_batch is None or selected_batch.upper() == 'ALL':
            return True
        return selected_batch.upper() in self.student_batches(student_id)

    def _count_overlap_and_add(self, sid, enter_dt, exit_dt):
        s_start, s_end = self.get_session_interval()
        overlap = overlap_seconds(enter_dt, exit_dt, s_start, s_end)
        info = self.presence.setdefault(sid, {
            "present": False,
            "current_enter_ts": None,
            "last_seen": None,
            "last_entry_log_time": 0,
            "cumulative_seconds": 0.0,
            "last_exit_ts": None,
        })
        info['cumulative_seconds'] = info.get('cumulative_seconds', 0.0) + overlap
        return overlap

    def get_session_interval(self):
        if self.session_active and self.manual_session_start:
            start = self.manual_session_start
            end = self.manual_session_end or datetime.now()
            return start, end
        if self.manual_session_start and self.manual_session_end:
            return self.manual_session_start, self.manual_session_end
        return _today_session_interval()

    def evaluate_session_and_write_summary(self):
        s_start, s_end = self.get_session_interval()
        now = datetime.now()
        rows = []
        for sid in self.students['Student_ID'].astype(str).tolist():
            info = self.presence.get(sid, {})
            cum = info.get('cumulative_seconds', 0.0)
            if info.get('present') and info.get('current_enter_ts'):
                enter_dt = datetime.fromtimestamp(info['current_enter_ts'])
                overlap = overlap_seconds(enter_dt, now, s_start, s_end)
                cum += overlap
            status = 'Present' if cum >= MIN_INCLASS_SECONDS else 'Absent'
            name = self.students[self.students['Student_ID'].astype(str) == sid]['Name'].values[0] if not self.students[self.students['Student_ID'].astype(str) == sid].empty else ''
            rows.append({'Date': s_start.date().isoformat(), 'Student_ID': sid, 'Name': name, 'CumulativeSeconds': int(cum), 'Status': status})
        df = pd.DataFrame(rows)
        df.to_csv(ATTENDANCE_SUMMARY, index=False)
        print(f"Attendance summary written to {ATTENDANCE_SUMMARY}")
        return df

    def run(self):
        # require teacher to select batch before starting
        if self.current_batch is None:
            chosen = self.prompt_choose_batch()
            if chosen is None:
                print("Batch selection cancelled. Returning to menu.")
                return
            self.current_batch = chosen
            print(f"Attendance will only record for batch: {self.current_batch}")

        cap = cv2.VideoCapture(CAMERA_INDEX)
        if not cap.isOpened():
            print("Could not open camera")
            return

        face_cascade = cv2.CascadeClassifier(HAAR_MODEL)
        print("Starting attendance. Press q to quit, t to train, r to reload model, v to view log, s to save session summary.")
        print("While in attendance mode: press 'c' to START class (manual), 'e' to END class (manual and write summary), 'p' to pause/resume capture.")

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Camera read failed")
                    break
                h, w = frame.shape[:2]
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                if not self.capture_paused:
                    detections = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80,80))
                else:
                    detections = []

                for (x,y,fw,fh) in detections:
                    pad_x = int(0.15 * fw); pad_y = int(0.15 * fh)
                    x0 = max(0, x - pad_x); y0 = max(0, y - pad_y)
                    x1 = min(w, x + fw + pad_x); y1 = min(h, y + fh + pad_y)
                    face_roi = frame[y0:y1, x0:x1].copy()

                    student_id, name, confidence = self.predict_on_face(face_roi)
                    label_text = 'Unknown'
                    color = (0,0,255)

                    if student_id is not None and confidence < RECOGNITION_THRESHOLD:
                        label_text = f"{name} ({student_id})"
                        color = (0,255,0)
                        now_t = time.time()
                        info = self.presence.get(student_id)
                        if info is None:
                            self.presence[student_id] = {"present": False, "current_enter_ts": None, "last_seen": None, "last_entry_log_time": 0, "cumulative_seconds": 0.0, "last_exit_ts": None}
                            info = self.presence[student_id]

                        info['last_seen'] = now_t

                        # check batch match
                        if not self.batch_matches(student_id, self.current_batch):
                            # detected but belongs to different batch -> do not mark presence; log blocked attempt
                            self.log_event(student_id, name, 'blocked_batch', details=f"detected for batch {', '.join(self.student_batches(student_id))} while current batch is {self.current_batch}")
                        else:
                            if not info['present']:
                                if now_t - info['last_entry_log_time'] > DEBOUNCE_SECONDS:
                                    info['present'] = True
                                    info['current_enter_ts'] = now_t
                                    info['last_entry_log_time'] = now_t

                                    details = None
                                    if info.get('last_exit_ts'):
                                        absent_sec = now_t - info['last_exit_ts']
                                        details = f"re-entry, absent_seconds={int(absent_sec)}"
                                        self.log_event(student_id, name, 'absent_interval', details=str(int(absent_sec)))

                                    enter_dt = datetime.fromtimestamp(now_t)
                                    s_start, s_end = self.get_session_interval()
                                    if enter_dt > s_start:
                                        details2 = f"late (entered at {enter_dt.time().isoformat(timespec='minutes')})"
                                        if details:
                                            details = details + "; " + details2
                                        else:
                                            details = details2
                                        self.log_event(student_id, name, 'late', details=details2)

                                    self.log_event(student_id, name, 'entry', details=details)

                    cv2.rectangle(frame, (x0,y0), (x1,y1), color, 2)
                    cv2.putText(frame, label_text, (x0, y0 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    if student_id is not None and confidence is not None:
                        cv2.putText(frame, f"Conf:{confidence:.1f}", (x0, y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

                # check exits
                now_ts = time.time()
                for sid, info in list(self.presence.items()):
                    if info.get('present'):
                        last_seen = info.get('last_seen') or 0
                        if now_ts - last_seen > EXIT_TIMEOUT:
                            info['present'] = False
                            exit_ts = last_seen if last_seen else now_ts
                            enter_ts = info.get('current_enter_ts')
                            if enter_ts:
                                enter_dt = datetime.fromtimestamp(enter_ts)
                                exit_dt = datetime.fromtimestamp(exit_ts)
                                overlap = self._count_overlap_and_add(sid, enter_dt, exit_dt)
                                s_start, s_end = self.get_session_interval()
                                if exit_dt < s_end and overlap > 0:
                                    details = f"early_leave (left at {exit_dt.time().isoformat(timespec='minutes')})"
                                    self.log_event(sid, self.students[self.students['Student_ID'].astype(str) == str(sid)]['Name'].values[0], 'early_leave', details=details)

                            info['last_exit_ts'] = exit_ts
                            info['current_enter_ts'] = None
                            info['last_seen'] = None
                            self.log_event(sid, self.students[self.students['Student_ID'].astype(str) == str(sid)]['Name'].values[0], 'exit')

                present_count = sum(1 for v in self.presence.values() if v.get('present'))
                total_reg = len(self.students)

                sess_text = 'No active session'
                if self.session_active and self.manual_session_start:
                    sess_text = f"Session started at {self.manual_session_start.time().isoformat(timespec='minutes')}"
                elif self.manual_session_start and self.manual_session_end:
                    sess_text = f"Last session: {self.manual_session_start.time().isoformat(timespec='minutes')} - {self.manual_session_end.time().isoformat(timespec='minutes')}"

                pause_text = 'PAUSED' if self.capture_paused else ''

                cv2.putText(frame, f"Present: {present_count} | Registered: {total_reg}", (10,25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
                cv2.putText(frame, sess_text + (' - '+pause_text if pause_text else ''), (10,50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)
                cv2.putText(frame, f"Batch: {self.current_batch}", (10,75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)

                cv2.imshow('Attendance - LBPH (enhanced)', frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print('Quitting... evaluating session and writing summary...')
                    if self.session_active:
                        self.manual_session_end = datetime.now()
                        self.session_active = False
                    self.evaluate_session_and_write_summary()
                    break
                elif key == ord('t'):
                    print('[CMD] Training...')
                    ok = prepare_dataset_and_train()
                    if ok:
                        self.load_model_if_exists()
                elif key == ord('r'):
                    print('[CMD] Reload model...')
                    self.load_model_if_exists()
                elif key == ord('v'):
                    self.view_today_report()
                elif key == ord('s'):
                    self.evaluate_session_and_write_summary()
                elif key == ord('c'):
                    self.manual_session_start = datetime.now()
                    self.manual_session_end = None
                    self.session_active = True
                    print(f"Manual session START at {self.manual_session_start.isoformat(sep=' ', timespec='seconds')}")
                    self.log_event('SYSTEM', 'SYSTEM', 'session_start', details=self.manual_session_start.isoformat(sep=' ', timespec='seconds'))
                elif key == ord('e'):
                    if self.session_active or self.manual_session_start:
                        self.manual_session_end = datetime.now()
                        self.session_active = False
                        print(f"Manual session END at {self.manual_session_end.isoformat(sep=' ', timespec='seconds')}")
                        self.log_event('SYSTEM', 'SYSTEM', 'session_end', details=self.manual_session_end.isoformat(sep=' ', timespec='seconds'))
                        self.evaluate_session_and_write_summary()
                elif key == ord('p'):
                    self.capture_paused = not self.capture_paused
                    print('Capture paused' if self.capture_paused else 'Capture resumed')

        except KeyboardInterrupt:
            print('Interrupted by user; evaluating session...')
            if self.session_active:
                self.manual_session_end = datetime.now()
                self.session_active = False
            self.evaluate_session_and_write_summary()
        finally:
            cap.release()
            cv2.destroyAllWindows()

    def view_today_report(self):
        date_str = datetime.now().strftime('%Y-%m-%d')
        if not os.path.exists(ATTENDANCE_CSV):
            print('No attendance records yet')
            return
        df = pd.read_csv(ATTENDANCE_CSV, dtype=str)
        df['Date'] = pd.to_datetime(df['Timestamp']).dt.date.astype(str)
        day = df[df['Date'] == date_str]
        if day.empty:
            print(f'No records for {date_str}')
            return
        print(f"\n=== Attendance events for {date_str} ===")
        print(day[['Timestamp','Student_ID','Name','Event','Details']].to_string(index=False))
        print('====================================')
    def view_attendance_list(self, date_str: str = None, batch: str = None, export_path: str = None):
        
        # default to today
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')

        # normalize batch
        selected_batch = None if batch is None else (batch.upper() if batch.upper() != 'ALL' else 'ALL')

        # build base student list (filtered by batch if provided)
        students_df = load_students()
        if students_df.empty:
            print("No students registered.")
            return

        # helper to check batch membership
        def student_in_batch(sid):
            if selected_batch is None or selected_batch == 'ALL':
                return True
            row = students_df[students_df['Student_ID'].astype(str) == str(sid)]
            if row.empty:
                return False
            raw = row.iloc[0].get('Batch', '') or ''
            parts = [p.strip().upper() for p in str(raw).split(',') if p.strip()]
            return selected_batch in parts

        # try reading attendance_summary first
        summary_exists = os.path.exists(ATTENDANCE_SUMMARY)
        df_summary = None
        if summary_exists:
            try:
                df_summary = pd.read_csv(ATTENDANCE_SUMMARY, dtype=str)
                # ensure Date column
                if 'Date' not in df_summary.columns:
                    df_summary = None
            except Exception:
                df_summary = None

        if df_summary is not None and date_str in df_summary['Date'].values:
            day = df_summary[df_summary['Date'] == date_str]
            # filter by batch membership
            filtered_ids = [sid for sid in day['Student_ID'].astype(str).tolist() if student_in_batch(sid)]
            day = day[day['Student_ID'].astype(str).isin(filtered_ids)]
            result_df = day[['Student_ID', 'Name', 'CumulativeSeconds', 'Status']].copy()
        else:
            # reconstruct from events
            if not os.path.exists(ATTENDANCE_CSV):
                print("No attendance events found (attendance_events.csv missing).")
                return

            ev_df = pd.read_csv(ATTENDANCE_CSV, dtype=str)
            # parse timestamps to datetime
            ev_df['Timestamp_dt'] = pd.to_datetime(ev_df['Timestamp'], errors='coerce')
            ev_df = ev_df.dropna(subset=['Timestamp_dt'])
            # keep only events for requested date
            ev_df['Date'] = ev_df['Timestamp_dt'].dt.date.astype(str)
            day_ev = ev_df[ev_df['Date'] == date_str].copy()
            # build session window for that date
            try:
                d = datetime.strptime(date_str, '%Y-%m-%d').date()
                session_start = datetime.combine(d, SESSION_START_T)
                session_end = datetime.combine(d, SESSION_END_T)
                if session_end <= session_start:
                    session_end += timedelta(days=1)
            except Exception:
                print("Invalid date format. Use YYYY-MM-DD.")
                return

            # prepare result rows
            rows = []
            # consider all students (but will filter by batch later)
            for _, srow in students_df.iterrows():
                sid = str(srow['Student_ID'])
                name = srow['Name']
                if not student_in_batch(sid):
                    continue

                s_events = day_ev[day_ev['Student_ID'].astype(str) == sid].sort_values('Timestamp_dt')
                cum_seconds = 0.0
                last_entry = None

                for _, er in s_events.iterrows():
                    ev = (er['Event'] or '').strip().lower()
                    ts = er['Timestamp_dt']
                    if ev == 'entry':
                        # start a new interval if none open
                        if last_entry is None:
                            last_entry = ts
                        # if already open, ignore duplicate entry
                    elif ev == 'exit':
                        if last_entry is not None:
                            enter_dt = last_entry
                            exit_dt = ts
                            # overlap with session window
                            overlap = overlap_seconds(enter_dt, exit_dt, session_start, session_end)
                            cum_seconds += overlap
                            last_entry = None
                        else:
                            # exit without entry -> ignore
                            pass
                    elif ev == 'absent_interval':
                        # absent_interval events were logged by system with Details = seconds absent,
                        # they don't affect entry/exit pairing; skip
                        pass
                    elif ev == 'session_start' or ev == 'session_end' or ev == 'late' or ev == 'early_leave' or ev == 'blocked_batch' or ev == 'correction_note' or ev == 'system':
                        # ignore for interval reconstruction
                        pass
                    else:
                        # treat unknown events: if they look like 'entry'/'exit' in Details, skip
                        pass

                # if still open interval at end of day, assume they left at session_end (or last event time)
                if last_entry is not None:
                    enter_dt = last_entry
                    exit_dt = session_end
                    overlap = overlap_seconds(enter_dt, exit_dt, session_start, session_end)
                    cum_seconds += overlap
                    last_entry = None

                status = 'Present' if cum_seconds >= MIN_INCLASS_SECONDS else 'Absent'
                rows.append({'Student_ID': sid, 'Name': name, 'CumulativeSeconds': int(cum_seconds), 'Status': status})

            result_df = pd.DataFrame(rows)

        # split present / absent
        if result_df is None or result_df.empty:
            print(f"No attendance records for {date_str} (after batch filter).")
            return

        present = result_df[result_df['Status'] == 'Present'].sort_values('Name')
        absent = result_df[result_df['Status'] == 'Absent'].sort_values('Name')

        # print nicely
        print('\n' + '='*50)
        print(f"Attendance list for {date_str} (Batch: {selected_batch or 'ALL'})")
        print('='*50)
        print("\nPRESENT:")
        if present.empty:
            print("  (none)")
        else:
            for _, r in present.iterrows():
                secs = int(r.get('CumulativeSeconds', 0))
                h = secs // 3600; m = (secs % 3600)//60; s = secs % 60
                print(f"  {r['Student_ID']} | {r['Name']} | {secs}s ({h}h {m}m {s}s)")

        print("\nABSENT:")
        if absent.empty:
            print("  (none)")
        else:
            for _, r in absent.iterrows():
                secs = int(r.get('CumulativeSeconds', 0))
                h = secs // 3600; m = (secs % 3600)//60; s = secs % 60
                print(f"  {r['Student_ID']} | {r['Name']} | {secs}s ({h}h {m}m {s}s)")

        # optional export
        if export_path:
            result_df.to_csv(export_path, index=False)
            print(f"\nExported attendance summary for {date_str} to {export_path}")
    

    # fetch & export unchanged from earlier
    def fetch_attendance_data(self, start_date=None, end_date=None, student_id=None, export_path=None):
        if not os.path.exists(ATTENDANCE_CSV):
            print('No attendance records yet')
            return None
        df = pd.read_csv(ATTENDANCE_CSV, dtype=str)
        df['Timestamp_dt'] = pd.to_datetime(df['Timestamp'])
        if start_date:
            sd = pd.to_datetime(start_date)
            df = df[df['Timestamp_dt'] >= sd]
        if end_date:
            ed = pd.to_datetime(end_date) + pd.Timedelta(days=1)
            df = df[df['Timestamp_dt'] < ed]
        if student_id:
            df = df[df['Student_ID'].astype(str) == str(student_id)]
        df = df.drop(columns=['Timestamp_dt'])
        if export_path:
            df.to_csv(export_path, index=False)
            print(f'Exported filtered attendance to {export_path}')
        else:
            if df.empty:
                print('No records found for given filters')
            else:
                print(df.to_string(index=False))
        return df

    # Admin operations
    def remove_student(self, student_id: str):
        sid = str(student_id)
        students = load_students()
        row = students[students['Student_ID'].astype(str) == sid]
        if row.empty:
            print(f"Student {sid} not found")
            return False
        folder = row.iloc[0]['Folder']
        if os.path.exists(folder) and os.path.isdir(folder):
            try:
                shutil.rmtree(folder)
                print(f"Removed folder {folder}")
            except Exception as e:
                print(f"Failed removing folder {folder}: {e}")
        students = students[students['Student_ID'].astype(str) != sid]
        save_students(students)
        if sid in self.presence:
            self.presence.pop(sid)
        print(f"Student {sid} removed from registry. Please retrain model to update recognizer (option 2).")
        return True

    def manual_correction(self, student_id: str, event_type: str, reason: str, timestamp=None):
        ts = timestamp or datetime.now().isoformat(sep=' ', timespec='seconds')
        name = self.students[self.students['Student_ID'].astype(str) == str(student_id)]['Name'].values[0] if not self.students[self.students['Student_ID'].astype(str) == str(student_id)].empty else ''
        row = {'Timestamp': ts, 'Student_ID': str(student_id), 'Name': name, 'Event': event_type, 'Details': reason}
        self._ensure_attendance_csv()
        df = pd.read_csv(ATTENDANCE_CSV, dtype=str)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df.to_csv(ATTENDANCE_CSV, index=False)
        print(f"Manual correction logged for {student_id}: {event_type} - {reason}")

    # Batch helper: list all batches in system
    def list_all_batches(self):
        students = load_students()
        batches = set()
        for b in students.get('Batch', '').astype(str).tolist():
            for part in b.split(','):
                p = part.strip()
                if p:
                    batches.add(p.upper())
        return sorted(list(batches))

    def prompt_choose_batch(self):
        # get available batches and let teacher choose
        batches = self.list_all_batches()
        print("\nAvailable batches:")
        if not batches:
            print("  (none found) - you can enter any batch name or use ALL")
        else:
            for i, b in enumerate(batches, 1):
                print(f"  {i}) {b}")
        print("  A) ALL batches")
        choice = input("Select batch by number, enter batch name, or 'A' for ALL (or blank to cancel): ").strip()
        if choice == '':
            return None
        if choice.lower() == 'a':
            return 'ALL'
        # if numeric
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(batches):
                return batches[idx]
            else:
                print("Invalid number; cancelling.")
                return None
        # else treat input as batch name
        return choice.strip().upper()

# Console UI
def main_console():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    system = AttendanceSystem()

    while True:
        print('\n' + '='*80)
        print('LBPH FACE ATTENDANCE SYSTEM (ENHANCED) - WITH BATCHES')
        print('='*80)
        print('1) Register new student')
        print('2) Train recognizer')
        print('3) Start attendance (recognize & log) -- will ask for batch')
        print("4) View today's events")
        print('5) List registered students')
        print('6) Remove a student from registry')
        print('7) Manual correction / update attendance (admin)')
        print('8) Fetch / export attendance data')
        print('9) List batches in system')
        print('10) Exit')
        print('11) View attendance list (Present / Absent)')

        choice = input('Enter choice (1-11): ').strip()

        if choice == '1':
            sid = input('Student ID: ').strip()
            name = input('Student Name: ').strip()
            batch = input('Batch(s) (comma-separated if multiple): ').strip()
            if sid and name:
                register_student_interactive(sid, name, batch)
                system.students = load_students()
                system.presence.setdefault(sid, {"present": False, "current_enter_ts": None, "last_seen": None, "last_entry_log_time": 0, "cumulative_seconds": 0.0, "last_exit_ts": None})
            else:
                print('Invalid input')
        elif choice == '2':
            prepare_dataset_and_train()
            system.load_model_if_exists()
        elif choice == '3':
            # reset current batch so prompt will occur in run()
            system.current_batch = None
            system.run()
        elif choice == '4':
            system.view_today_report()
        elif choice == '5':
            s = load_students()
            if s.empty:
                print('No students registered')
            else:
                print(s[['Student_ID','Name','Batch']].to_string(index=False))
        elif choice == '6':
            sid = input('Student ID to remove: ').strip()
            confirm = input(f"Are you sure you want to DELETE student {sid}? This removes images and registry entry. (yes/no): ").strip().lower()
            if confirm == 'yes':
                system.remove_student(sid)
                system.students = load_students()
        elif choice == '7':
            sid = input('Student ID for correction: ').strip()
            ev = input('Event type (entry / exit / correction_note): ').strip()
            reason = input('Reason / details: ').strip()
            ts = input('Optional timestamp (YYYY-MM-DD HH:MM:SS) or leave blank for now: ').strip()
            timestamp = ts if ts else None
            system.manual_correction(sid, ev, reason, timestamp)
        elif choice == '8':
            print('\nFetch / Export Attendance Data')
            print("a) View today's events")
            print("b) Export full attendance CSV")
            print("c) Filter by date range")
            print("d) Filter by student ID")
            sub = input('Choose option (a-d): ').strip().lower()
            if sub == 'a':
                system.view_today_report()
            elif sub == 'b':
                path = input('Export path (e.g. all_attendance.csv): ').strip() or 'all_attendance.csv'
                system.fetch_attendance_data(export_path=path)
            elif sub == 'c':
                sd = input('Start date (YYYY-MM-DD): ').strip()
                ed = input('End date (YYYY-MM-DD): ').strip()
                path = input('Optional export path (leave blank to only display): ').strip() or None
                system.fetch_attendance_data(start_date=sd, end_date=ed, export_path=path)
            elif sub == 'd':
                sid = input('Student ID: ').strip()
                path = input('Optional export path (leave blank to only display): ').strip() or None
                system.fetch_attendance_data(student_id=sid, export_path=path)
            else:
                print('Invalid option')
        elif choice == '9':
            batches = system.list_all_batches()
            if not batches:
                print("No batches found.")
            else:
                print("Batches:")
                for b in batches:
                    print(" -", b)
        elif choice == '10':
            print('Goodbye')
            break
        elif choice == '11':
            d = input('Date (YYYY-MM-DD) or blank for today: ').strip()
            b = input('Batch or ALL (leave blank for ALL): ').strip()
            d = d if d else None
            b = b if b else 'ALL'
            p = input('Optional export path (leave blank to skip): ').strip() or None
            system.view_attendance_list(date_str=d, batch=b, export_path=p)

            

if __name__ == '__main__':
    main_console()

