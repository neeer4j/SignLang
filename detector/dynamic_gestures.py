"""
Dynamic Gesture Recognition - Track and recognize movement-based gestures

This module handles gestures that require motion tracking, such as:
- Letters like J, Z that require drawing in the air
- Signs like "hello" (waving), "thank you", etc.
- Custom dynamic gestures
"""
import numpy as np
from collections import deque
from typing import Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum


class GestureState(Enum):
    """States for dynamic gesture tracking."""
    IDLE = "idle"
    TRACKING = "tracking"
    DETECTED = "detected"


@dataclass
class GesturePattern:
    """Defines a dynamic gesture pattern."""
    name: str
    description: str
    min_frames: int  # Minimum frames to complete gesture
    max_frames: int  # Maximum frames before timeout
    pattern_matcher: callable  # Function to match the pattern


class DynamicGestureTracker:
    """Track and recognize dynamic (movement-based) gestures."""
    
    def __init__(self, buffer_size: int = 30, fps: int = 30):
        """Initialize the dynamic gesture tracker.
        
        Args:
            buffer_size: Number of frames to keep in history (default 1 second at 30fps)
            fps: Expected frames per second
        """
        self.buffer_size = buffer_size
        self.fps = fps
        
        # Tracking buffers
        self.landmark_buffer = deque(maxlen=buffer_size)
        self.position_buffer = deque(maxlen=buffer_size)  # Palm center positions
        self.velocity_buffer = deque(maxlen=buffer_size)
        self.timestamp_buffer = deque(maxlen=buffer_size)
        
        # State
        self.state = GestureState.IDLE
        self.current_gesture = None
        self.gesture_start_frame = 0
        self.frame_count = 0
        
        # Registered gesture patterns
        self.patterns: List[GesturePattern] = []
        self._register_default_patterns()
    
    def _register_default_patterns(self):
        """Register built-in gesture patterns."""
        # Letter J - index finger draws a J shape (down then curve left)
        self.patterns.append(GesturePattern(
            name="J",
            description="Draw letter J with index finger",
            min_frames=15,
            max_frames=45,
            pattern_matcher=self._match_j_gesture
        ))
        
        # Letter Z - draw Z in the air
        self.patterns.append(GesturePattern(
            name="Z", 
            description="Draw letter Z in the air",
            min_frames=20,
            max_frames=60,
            pattern_matcher=self._match_z_gesture
        ))
        
        # Wave gesture - hand moving side to side
        self.patterns.append(GesturePattern(
            name="WAVE",
            description="Wave hand side to side",
            min_frames=20,
            max_frames=90,
            pattern_matcher=self._match_wave_gesture
        ))
        
        # Circle gesture
        self.patterns.append(GesturePattern(
            name="CIRCLE",
            description="Draw a circle in the air",
            min_frames=20,
            max_frames=60,
            pattern_matcher=self._match_circle_gesture
        ))
    
    def update(self, landmarks) -> Tuple[Optional[str], float]:
        """Update tracker with new frame landmarks.
        
        Args:
            landmarks: List of 21 (x, y, z) tuples from MediaPipe
            
        Returns:
            tuple: (gesture_name or None, confidence 0-1)
        """
        if landmarks is None or len(landmarks) != 21:
            # No hand detected - check if we should finalize a gesture
            if self.state == GestureState.TRACKING:
                result = self._try_match_gestures()
                self._reset_tracking()
                return result
            return None, 0.0
        
        self.frame_count += 1
        landmarks_array = np.array(landmarks)
        
        # Calculate palm center (average of wrist and middle MCP)
        palm_center = (landmarks_array[0] + landmarks_array[9]) / 2
        
        # Calculate velocity if we have previous position
        velocity = np.zeros(3)
        if len(self.position_buffer) > 0:
            prev_pos = self.position_buffer[-1]
            velocity = palm_center - prev_pos
        
        # Add to buffers
        self.landmark_buffer.append(landmarks_array)
        self.position_buffer.append(palm_center)
        self.velocity_buffer.append(velocity)
        self.timestamp_buffer.append(self.frame_count)
        
        # Check for gesture start (significant movement)
        if self.state == GestureState.IDLE:
            if self._detect_movement_start():
                self.state = GestureState.TRACKING
                self.gesture_start_frame = self.frame_count
        
        # Check for gesture completion during tracking
        elif self.state == GestureState.TRACKING:
            frames_elapsed = self.frame_count - self.gesture_start_frame
            
            # Check if movement stopped or timeout
            if self._detect_movement_stop() or frames_elapsed > 60:
                result = self._try_match_gestures()
                self._reset_tracking()
                return result
        
        return None, 0.0
    
    def _detect_movement_start(self) -> bool:
        """Detect if significant movement has started."""
        if len(self.velocity_buffer) < 3:
            return False
        
        # Check recent velocities
        recent_velocities = list(self.velocity_buffer)[-3:]
        avg_speed = np.mean([np.linalg.norm(v) for v in recent_velocities])
        
        return avg_speed > 0.02  # Threshold for movement detection
    
    def _detect_movement_stop(self) -> bool:
        """Detect if movement has stopped."""
        if len(self.velocity_buffer) < 5:
            return False
        
        recent_velocities = list(self.velocity_buffer)[-5:]
        avg_speed = np.mean([np.linalg.norm(v) for v in recent_velocities])
        
        return avg_speed < 0.005  # Low velocity = stopped
    
    def _reset_tracking(self):
        """Reset tracking state."""
        self.state = GestureState.IDLE
        self.current_gesture = None
        self.gesture_start_frame = 0
    
    def _try_match_gestures(self) -> Tuple[Optional[str], float]:
        """Try to match buffered movement to known gestures."""
        if len(self.position_buffer) < 10:
            return None, 0.0
        
        best_match = None
        best_confidence = 0.0
        
        for pattern in self.patterns:
            confidence = pattern.pattern_matcher()
            if confidence > best_confidence and confidence > 0.6:
                best_confidence = confidence
                best_match = pattern.name
        
        return best_match, best_confidence
    
    def _get_trajectory(self) -> np.ndarray:
        """Get the trajectory as numpy array."""
        if len(self.position_buffer) < 2:
            return np.array([])
        return np.array(list(self.position_buffer))
    
    def _match_j_gesture(self) -> float:
        """Match J gesture: down then curve left/up."""
        trajectory = self._get_trajectory()
        if len(trajectory) < 15:
            return 0.0
        
        # Analyze trajectory segments
        n = len(trajectory)
        first_half = trajectory[:n//2]
        second_half = trajectory[n//2:]
        
        # First half should go down (positive y change in image coords)
        first_direction = first_half[-1] - first_half[0]
        going_down = first_direction[1] > 0.03
        
        # Second half should curve left (negative x) and possibly up
        second_direction = second_half[-1] - second_half[0]
        curving_left = second_direction[0] < -0.02
        
        if going_down and curving_left:
            # Calculate smoothness
            smoothness = self._calculate_smoothness(trajectory)
            return min(0.65 + smoothness * 0.35, 1.0)
        
        return 0.0
    
    def _match_z_gesture(self) -> float:
        """Match Z gesture: right, diagonal down-left, right."""
        trajectory = self._get_trajectory()
        if len(trajectory) < 20:
            return 0.0
        
        n = len(trajectory)
        third = n // 3
        
        seg1 = trajectory[:third]
        seg2 = trajectory[third:2*third]
        seg3 = trajectory[2*third:]
        
        # Segment 1: should go right
        dir1 = seg1[-1] - seg1[0]
        going_right1 = dir1[0] > 0.02
        
        # Segment 2: should go diagonal (left and down)
        dir2 = seg2[-1] - seg2[0]
        going_diagonal = dir2[0] < -0.02 and dir2[1] > 0.02
        
        # Segment 3: should go right again
        dir3 = seg3[-1] - seg3[0]
        going_right2 = dir3[0] > 0.02
        
        if going_right1 and going_diagonal and going_right2:
            smoothness = self._calculate_smoothness(trajectory)
            return min(0.6 + smoothness * 0.4, 1.0)
        
        return 0.0
    
    def _match_wave_gesture(self) -> float:
        """Match wave gesture: oscillating horizontal movement with OPEN PALM."""
        trajectory = self._get_trajectory()
        if len(trajectory) < 20:
            return 0.0
        
        # 1. Check if palm is OPEN (all fingers extended)
        if len(self.landmark_buffer) == 0:
            return 0.0
            
        latest_landmarks = self.landmark_buffer[-1]
        
        # Simple check for open palm: Fingertips should be far from wrist
        wrist = latest_landmarks[0]
        tips = [4, 8, 12, 16, 20] # Thumb, Index, Middle, Ring, Pinky
        extended_count = 0
        
        # Calculate palm scale (wrist to middle MCP)
        palm_scale = np.linalg.norm(latest_landmarks[9] - wrist)
        if palm_scale == 0: return 0.0
        
        for tip in tips:
            # Distance from wrist to tip
            dist = np.linalg.norm(latest_landmarks[tip] - wrist)
            # Relaxed threshold: > 1.5x palm scale (was 1.8x)
            if dist > palm_scale * 1.5:
                extended_count += 1
                
        # REQUIRE at least 4 fingers extended for a wave
        if extended_count < 4:
            return 0.0
        
        # 2. Check Y-axis stability (wave should be mostly horizontal)
        y_positions = trajectory[:, 1]
        y_range = np.max(y_positions) - np.min(y_positions)
        if y_range > 0.1:  # Vertical tolerance
            return 0.0
        
        # 3. Check X-axis Oscillations
        x_positions = trajectory[:, 0]
        x_velocity = np.diff(x_positions)
        sign_changes = np.sum(np.abs(np.diff(np.sign(x_velocity))) > 0)
        
        # Wave should have multiple direction changes (left-right-left)
        if sign_changes >= 3:
            # Check amplitude of oscillation
            x_range = np.max(x_positions) - np.min(x_positions)
            if x_range > 0.15: 
                confidence = min(0.5 + sign_changes * 0.1, 1.0)
                return confidence
        
        return 0.0
    
    def _match_circle_gesture(self) -> float:
        """Match circular gesture."""
        trajectory = self._get_trajectory()
        if len(trajectory) < 20:
            return 0.0
        
        # Calculate center of trajectory
        center = np.mean(trajectory[:, :2], axis=0)
        
        # Calculate distances from center
        distances = [np.linalg.norm(p[:2] - center) for p in trajectory]
        
        # For a circle, distances should be relatively constant
        distance_std = np.std(distances)
        distance_mean = np.mean(distances)
        
        if distance_mean > 0.03:  # Minimum circle size
            # Calculate how circular (low std relative to mean = circular)
            circularity = 1 - (distance_std / distance_mean)
            
            # Check if we complete the circle (end near start)
            start_end_dist = np.linalg.norm(trajectory[0, :2] - trajectory[-1, :2])
            closed = start_end_dist < distance_mean * 0.5
            
            if circularity > 0.5 and closed:
                return min(0.5 + circularity * 0.3 + (0.2 if closed else 0), 1.0)
        
        return 0.0
    
    def _calculate_smoothness(self, trajectory: np.ndarray) -> float:
        """Calculate trajectory smoothness (0=jerky, 1=smooth)."""
        if len(trajectory) < 3:
            return 0.5
        
        # Calculate acceleration (second derivative)
        velocities = np.diff(trajectory, axis=0)
        accelerations = np.diff(velocities, axis=0)
        
        # Lower acceleration magnitude = smoother
        avg_accel = np.mean([np.linalg.norm(a) for a in accelerations])
        
        # Normalize (empirical thresholds)
        smoothness = 1 - min(avg_accel / 0.01, 1.0)
        return max(0, smoothness)
    
    def get_trajectory_features(self) -> Optional[np.ndarray]:
        """Extract features from current trajectory for ML classification.
        
        Returns:
            Feature vector or None if not enough data
        """
        if len(self.position_buffer) < 10:
            return None
        
        trajectory = self._get_trajectory()
        features = []
        
        # Total displacement
        total_disp = trajectory[-1] - trajectory[0]
        features.extend(total_disp)
        
        # Path length
        path_length = sum(np.linalg.norm(np.diff(trajectory, axis=0), axis=1))
        features.append(path_length)
        
        # Bounding box
        bbox_min = np.min(trajectory, axis=0)
        bbox_max = np.max(trajectory, axis=0)
        bbox_size = bbox_max - bbox_min
        features.extend(bbox_size)
        
        # Velocity statistics
        velocities = np.diff(trajectory, axis=0)
        speeds = [np.linalg.norm(v) for v in velocities]
        features.append(np.mean(speeds))
        features.append(np.std(speeds))
        features.append(np.max(speeds))
        
        # Direction changes
        x_velocity = np.diff(trajectory[:, 0])
        y_velocity = np.diff(trajectory[:, 1])
        x_changes = np.sum(np.abs(np.diff(np.sign(x_velocity))) > 0)
        y_changes = np.sum(np.abs(np.diff(np.sign(y_velocity))) > 0)
        features.extend([x_changes, y_changes])
        
        # Smoothness
        features.append(self._calculate_smoothness(trajectory))
        
        return np.array(features, dtype=np.float32)
    
    def register_pattern(self, pattern: GesturePattern):
        """Register a custom gesture pattern."""
        self.patterns.append(pattern)
    
    def clear(self):
        """Clear all buffers and reset state."""
        self.landmark_buffer.clear()
        self.position_buffer.clear()
        self.velocity_buffer.clear()
        self.timestamp_buffer.clear()
        self._reset_tracking()
