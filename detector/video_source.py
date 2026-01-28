"""
Video Source Module - Unified video input abstraction

Provides abstract base class and implementations for webcam and video file sources,
enabling a unified frame processing pipeline.
"""
import cv2
import time
import os
from abc import ABC, abstractmethod
from typing import Optional, Tuple
import numpy as np

from config import CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT, FPS


class VideoSource(ABC):
    """Abstract base class for video input sources.
    
    Provides unified interface for both live camera and video file sources.
    """
    
    @abstractmethod
    def start(self) -> bool:
        """Start the video source.
        
        Returns:
            True if started successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def read(self) -> Tuple[bool, Optional[np.ndarray], Optional[np.ndarray]]:
        """Read a frame from the source.
        
        Returns:
            tuple: (success, frame_bgr, frame_rgb)
        """
        pass
    
    @abstractmethod
    def stop(self):
        """Stop and release the video source."""
        pass
    
    @abstractmethod
    def is_opened(self) -> bool:
        """Check if the source is currently active."""
        pass
    
    @abstractmethod
    def get_fps(self) -> float:
        """Get current/configured FPS."""
        pass
    
    def get_progress(self) -> float:
        """Get playback progress (0.0 to 1.0).
        
        Only meaningful for video files. Returns 0 for live sources.
        """
        return 0.0
    
    def seek(self, position: float):
        """Seek to a position in the video (0.0 to 1.0).
        
        Only meaningful for video files. No-op for live sources.
        """
        pass
    
    def get_duration(self) -> float:
        """Get total duration in seconds.
        
        Only meaningful for video files. Returns 0 for live sources.
        """
        return 0.0
    
    def is_seekable(self) -> bool:
        """Check if this source supports seeking."""
        return False
    
    def get_playback_speed(self) -> float:
        """Get current playback speed multiplier."""
        return 1.0
    
    def set_playback_speed(self, speed: float):
        """Set playback speed multiplier.
        
        Only meaningful for video files.
        """
        pass


class WebcamSource(VideoSource):
    """Live camera input source using OpenCV."""
    
    def __init__(self, camera_index: int = CAMERA_INDEX):
        """Initialize webcam source.
        
        Args:
            camera_index: Index of camera device (default from config)
        """
        self.camera_index = camera_index
        self.cap = None
        self._fps = 0.0
        self._last_time = time.time()
        self._frame_count = 0
    
    def start(self) -> bool:
        """Start webcam capture."""
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            return False
        
        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        return True
    
    def read(self) -> Tuple[bool, Optional[np.ndarray], Optional[np.ndarray]]:
        """Read a frame from webcam."""
        if self.cap is None:
            return False, None, None
        
        success, frame = self.cap.read()
        if not success:
            return False, None, None
        
        # Flip horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Convert to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Update FPS calculation
        self._update_fps()
        
        return True, frame, frame_rgb
    
    def _update_fps(self):
        """Calculate current FPS."""
        self._frame_count += 1
        current_time = time.time()
        elapsed = current_time - self._last_time
        
        if elapsed >= 1.0:
            self._fps = self._frame_count / elapsed
            self._frame_count = 0
            self._last_time = current_time
    
    def stop(self):
        """Release webcam resources."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def is_opened(self) -> bool:
        """Check if webcam is active."""
        return self.cap is not None and self.cap.isOpened()
    
    def get_fps(self) -> float:
        """Get current measured FPS."""
        return self._fps


class VideoFileSource(VideoSource):
    """Pre-recorded video file input source."""
    
    SUPPORTED_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv']
    
    def __init__(self, file_path: str = None):
        """Initialize video file source.
        
        Args:
            file_path: Path to video file (can be set later via load())
        """
        self.file_path = file_path
        self.cap = None
        
        # Video properties
        self._fps = FPS
        self._total_frames = 0
        self._current_frame = 0
        self._duration = 0.0
        
        # Playback control
        self._playback_speed = 1.0
        self._is_playing = False
        self._last_frame_time = 0.0
        
        # Fast processing mode (skip frame timing for batch processing)
        self.fast_mode = False
    
    def load(self, file_path: str) -> bool:
        """Load a video file.
        
        Args:
            file_path: Path to video file
            
        Returns:
            True if loaded successfully
        """
        # Validate file
        if not os.path.exists(file_path):
            return False
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.SUPPORTED_FORMATS:
            return False
        
        self.file_path = file_path
        return self.start()
    
    def start(self) -> bool:
        """Open video file for reading."""
        if not self.file_path:
            return False
        
        self.cap = cv2.VideoCapture(self.file_path)
        if not self.cap.isOpened():
            return False
        
        # Get video properties
        self._fps = self.cap.get(cv2.CAP_PROP_FPS) or FPS
        self._total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._duration = self._total_frames / self._fps if self._fps > 0 else 0
        self._current_frame = 0
        self._is_playing = True
        self._last_frame_time = time.time()
        
        return True
    
    def read(self) -> Tuple[bool, Optional[np.ndarray], Optional[np.ndarray]]:
        """Read next frame from video file.
        
        Respects playback speed unless in fast_mode.
        """
        if self.cap is None or not self._is_playing:
            return False, None, None
        
        # Frame timing (unless fast mode)
        if not self.fast_mode and self._playback_speed > 0:
            frame_interval = 1.0 / (self._fps * self._playback_speed)
            elapsed = time.time() - self._last_frame_time
            if elapsed < frame_interval:
                return False, None, None
        
        success, frame = self.cap.read()
        if not success:
            self._is_playing = False
            return False, None, None
        
        self._current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        self._last_frame_time = time.time()
        
        # Convert to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        return True, frame, frame_rgb
    
    def stop(self):
        """Release video file resources."""
        self._is_playing = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self._current_frame = 0
    
    def is_opened(self) -> bool:
        """Check if video is loaded and active."""
        return self.cap is not None and self.cap.isOpened()
    
    def get_fps(self) -> float:
        """Get video file FPS."""
        return self._fps
    
    def get_progress(self) -> float:
        """Get current playback progress (0.0 to 1.0)."""
        if self._total_frames <= 0:
            return 0.0
        return self._current_frame / self._total_frames
    
    def seek(self, position: float):
        """Seek to position in video.
        
        Args:
            position: Value between 0.0 (start) and 1.0 (end)
        """
        if self.cap is None:
            return
        
        position = max(0.0, min(1.0, position))
        target_frame = int(position * self._total_frames)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        self._current_frame = target_frame
    
    def get_duration(self) -> float:
        """Get total video duration in seconds."""
        return self._duration
    
    def is_seekable(self) -> bool:
        """Video files support seeking."""
        return True
    
    def get_playback_speed(self) -> float:
        """Get current playback speed."""
        return self._playback_speed
    
    def set_playback_speed(self, speed: float):
        """Set playback speed multiplier.
        
        Args:
            speed: Multiplier (0.5 = half speed, 2.0 = double speed)
        """
        self._playback_speed = max(0.1, min(4.0, speed))
    
    def pause(self):
        """Pause video playback."""
        self._is_playing = False
    
    def resume(self):
        """Resume video playback."""
        self._is_playing = True
        self._last_frame_time = time.time()
    
    def is_playing(self) -> bool:
        """Check if video is currently playing."""
        return self._is_playing
    
    def is_finished(self) -> bool:
        """Check if video has reached the end."""
        return self._current_frame >= self._total_frames - 1
    
    def get_current_time(self) -> float:
        """Get current playback time in seconds."""
        if self._fps <= 0:
            return 0.0
        return self._current_frame / self._fps
    
    def set_fast_mode(self, enabled: bool):
        """Enable/disable fast processing mode.
        
        In fast mode, frames are processed as quickly as possible
        without waiting for playback timing.
        """
        self.fast_mode = enabled
    
    @staticmethod
    def is_supported_format(file_path: str) -> bool:
        """Check if file format is supported."""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in VideoFileSource.SUPPORTED_FORMATS
