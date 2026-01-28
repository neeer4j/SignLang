"""
Camera Module - OpenCV Video Capture Wrapper
"""
import cv2
import time
from config import CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT


class Camera:
    """Handles webcam capture and frame preprocessing."""
    
    def __init__(self, camera_index: int = CAMERA_INDEX):
        self.camera_index = camera_index
        self.cap = None
        self.fps = 0
        self._last_time = time.time()
        self._frame_count = 0
    
    def start(self) -> bool:
        """Start the camera capture."""
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            return False
        
        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        return True
    
    def read(self):
        """Read a frame from the camera.
        
        Returns:
            tuple: (success, frame_bgr, frame_rgb)
        """
        if self.cap is None:
            return False, None, None
        
        success, frame = self.cap.read()
        if not success:
            return False, None, None
        
        # Flip horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Convert to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Update FPS
        self._update_fps()
        
        return True, frame, frame_rgb
    
    def _update_fps(self):
        """Calculate current FPS."""
        self._frame_count += 1
        current_time = time.time()
        elapsed = current_time - self._last_time
        
        if elapsed >= 1.0:
            self.fps = self._frame_count / elapsed
            self._frame_count = 0
            self._last_time = current_time
    
    def stop(self):
        """Release camera resources."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def is_opened(self) -> bool:
        """Check if camera is currently open."""
        return self.cap is not None and self.cap.isOpened()
    
    def get_fps(self) -> float:
        """Get current FPS."""
        return self.fps
