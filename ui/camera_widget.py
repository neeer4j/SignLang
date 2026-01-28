"""
Camera Widget - Display webcam feed with landmarks and gesture tracking
"""
from PySide6.QtWidgets import QLabel, QVBoxLayout, QFrame
from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QImage, QPixmap
import cv2

from detector.camera import Camera
from detector.hand_tracker import HandTracker
from detector.features import FeatureExtractor
from detector.dynamic_gestures import DynamicGestureTracker


class CameraWidget(QFrame):
    """Widget to display camera feed with hand tracking overlay."""
    
    # Signals
    features_ready = Signal(object)           # Emitted when features are extracted
    hand_detected = Signal(bool)              # Emitted when hand detection status changes
    fps_updated = Signal(float)               # Emitted with current FPS
    dynamic_gesture_detected = Signal(str, float)  # Emitted when dynamic gesture detected (name, confidence)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("cameraFrame")
        
        # Components
        self.camera = Camera()
        self.hand_tracker = HandTracker()
        self.feature_extractor = FeatureExtractor()
        self.dynamic_tracker = DynamicGestureTracker()
        
        # State
        self.is_running = False
        self._last_hand_detected = False
        self.dynamic_gestures_enabled = True  # Toggle for dynamic gesture recognition
        
        # Setup UI
        self._setup_ui()
        
        # Timer for frame updates
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)
    
    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Video display label
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("background-color: #000000; border-radius: 12px;")
        self.video_label.setText("Camera Off")
        
        layout.addWidget(self.video_label)
    
    def start(self) -> bool:
        """Start camera capture."""
        if self.is_running:
            return True
        
        if not self.camera.start():
            self.video_label.setText("❌ Camera Error\nCould not access webcam")
            return False
        
        self.is_running = True
        self.dynamic_tracker.clear()  # Reset dynamic gesture tracker
        self.timer.start(33)  # ~30 FPS
        return True
    
    def stop(self):
        """Stop camera capture."""
        self.timer.stop()
        self.camera.stop()
        self.is_running = False
        self.video_label.setText("Camera Off")
        self.video_label.setPixmap(QPixmap())
        self.dynamic_tracker.clear()
    
    def set_dynamic_gestures_enabled(self, enabled: bool):
        """Enable or disable dynamic gesture recognition."""
        self.dynamic_gestures_enabled = enabled
        if not enabled:
            self.dynamic_tracker.clear()
    
    def _update_frame(self):
        """Process and display new frame."""
        success, frame_bgr, frame_rgb = self.camera.read()
        
        if not success:
            return
        
        # Process with MediaPipe
        self.hand_tracker.process(frame_rgb)
        
        # Check hand detection
        hand_detected = self.hand_tracker.has_hand()
        if hand_detected != self._last_hand_detected:
            self.hand_detected.emit(hand_detected)
            self._last_hand_detected = hand_detected
        
        # Get landmarks
        landmarks = None
        if hand_detected:
            landmarks = self.hand_tracker.get_landmarks()
            
            # Extract features for static gesture recognition
            features = self.feature_extractor.extract(landmarks)
            self.features_ready.emit(features)
        
        # Dynamic gesture tracking (runs even when hand disappears to finalize gestures)
        if self.dynamic_gestures_enabled:
            gesture_name, confidence = self.dynamic_tracker.update(landmarks)
            if gesture_name is not None and confidence > 0.6:
                self.dynamic_gesture_detected.emit(gesture_name, confidence)
        
        # Draw landmarks and tracking visualization on frame
        frame_bgr = self.hand_tracker.draw_landmarks(frame_bgr)
        frame_bgr = self._draw_tracking_overlay(frame_bgr)
        
        # Convert to QImage and display
        self._display_frame(frame_bgr)
        
        # Emit FPS
        self.fps_updated.emit(self.camera.get_fps())
    
    def _draw_tracking_overlay(self, frame):
        """Draw dynamic gesture tracking visualization."""
        if not self.dynamic_gestures_enabled:
            return frame
        
        # Draw trajectory if tracking
        if len(self.dynamic_tracker.position_buffer) > 1:
            positions = list(self.dynamic_tracker.position_buffer)
            h, w = frame.shape[:2]
            
            # Draw trajectory line
            for i in range(1, len(positions)):
                # Convert normalized coords to pixel coords
                x1 = int(positions[i-1][0] * w)
                y1 = int(positions[i-1][1] * h)
                x2 = int(positions[i][0] * w)
                y2 = int(positions[i][1] * h)
                
                # Draw with fading effect (older = more transparent)
                alpha = i / len(positions)
                color = (0, int(255 * alpha), int(255 * (1 - alpha)))
                thickness = max(1, int(3 * alpha))
                cv2.line(frame, (x1, y1), (x2, y2), color, thickness)
        
        # Show tracking state
        state = self.dynamic_tracker.state.value
        if state == "tracking":
            cv2.putText(frame, "TRACKING GESTURE...", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        return frame
    
    def _display_frame(self, frame_bgr):
        """Convert and display frame on label."""
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        
        # Create QImage
        q_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Scale to fit label while maintaining aspect ratio
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.video_label.setPixmap(scaled_pixmap)
    
    def is_active(self) -> bool:
        """Check if camera is active."""
        return self.is_running
    
    def release(self):
        """Clean up resources."""
        self.stop()
        self.hand_tracker.release()

