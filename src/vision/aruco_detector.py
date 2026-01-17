#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArUco Marker Detector for AR Keyboard

Detects ArUco markers in camera frames and calculates the 3D pose
to position the virtual keyboard in augmented reality.
"""

import cv2
import numpy as np
from src.vision.stereo_config import StereoConfig


class ArucoDetector:
    """
    Detects ArUco markers and calculates keyboard corners from marker pose.
    
    The keyboard is positioned relative to the marker with a configurable offset.
    """
    
    # Supported ArUco dictionaries
    DICTIONARIES = {
        "4X4_50": cv2.aruco.DICT_4X4_50,
        "4X4_100": cv2.aruco.DICT_4X4_100,
        "5X5_50": cv2.aruco.DICT_5X5_50,
        "5X5_100": cv2.aruco.DICT_5X5_100,
        "6X6_50": cv2.aruco.DICT_6X6_50,
    }
    
    def __init__(self, camera_matrix=None, dist_coeffs=None, 
                 marker_size_cm=15.0, dictionary_name="4X4_50", marker_id=0):
        """
        Initialize ArUco detector.
        
        Args:
            camera_matrix: 3x3 intrinsic camera matrix. If None, uses StereoConfig.
            dist_coeffs: Distortion coefficients. If None, uses StereoConfig.
            marker_size_cm: Physical size of the marker in centimeters.
            dictionary_name: ArUco dictionary to use (e.g., "4X4_50").
            marker_id: Expected marker ID to track (default 0).
        """
        # Camera calibration
        if camera_matrix is not None:
            self.camera_matrix = camera_matrix
        elif hasattr(StereoConfig, 'CAMERA_MATRIX_LEFT') and StereoConfig.CAMERA_MATRIX_LEFT is not None:
            self.camera_matrix = StereoConfig.CAMERA_MATRIX_LEFT
        else:
            # Fallback: approximate matrix for 640x480
            self.camera_matrix = np.array([
                [600.0, 0.0, 320.0],
                [0.0, 600.0, 240.0],
                [0.0, 0.0, 1.0]
            ], dtype=np.float32)
        
        if dist_coeffs is not None:
            self.dist_coeffs = dist_coeffs
        elif hasattr(StereoConfig, 'DIST_COEFFS_LEFT') and StereoConfig.DIST_COEFFS_LEFT is not None:
            self.dist_coeffs = StereoConfig.DIST_COEFFS_LEFT
        else:
            self.dist_coeffs = np.zeros(5, dtype=np.float32)
        
        # Marker configuration
        self.marker_size_cm = marker_size_cm
        self.marker_id = marker_id
        
        # ArUco setup
        dict_id = self.DICTIONARIES.get(dictionary_name, cv2.aruco.DICT_4X4_50)
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(dict_id)
        self.aruco_params = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
        
        # Last known pose (for smoothing/fallback)
        self.last_rvec = None
        self.last_tvec = None
        self.last_corners = None
        self.detection_valid = False
        
        # Keyboard geometry relative to marker (cm)
        # If None, it will be calculated from offset/width/height (axis-aligned)
        self.keyboard_relative_corners = None

        # Keyboard offset from marker (in cm, relative to marker center)
        # Default: keyboard is to the right of the marker
        self.keyboard_offset_x = 10.0  # cm to the right
        self.keyboard_offset_y = 0.0   # cm down
        
        # Keyboard dimensions (2 octaves, standard proportions)
        self.keyboard_width_cm = 40.0   # ~40cm for 2 octaves
        self.keyboard_height_cm = 12.0  # ~12cm depth
    
    def detect(self, frame):
        """
        Detect ArUco marker in frame and calculate pose.
        
        Args:
            frame: BGR image from camera.
            
        Returns:
            dict with keys:
                - 'detected': bool, True if marker found
                - 'corners_2d': 4x2 array of marker corners in image pixels
                - 'keyboard_corners': 4x2 array of keyboard corners in image pixels
                - 'rvec': rotation vector (3x1)
                - 'tvec': translation vector (3x1)
        """
        result = {
            'detected': False,
            'corners_2d': None,
            'keyboard_corners': None,
            'rvec': None,
            'tvec': None
        }
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect markers
        corners, ids, rejected = self.detector.detectMarkers(gray)
        
        if ids is None or len(ids) == 0:
            self.detection_valid = False
            return result
        
        # Find our target marker
        target_idx = None
        for i, mid in enumerate(ids):
            if mid[0] == self.marker_id:
                target_idx = i
                break
        
        if target_idx is None:
            self.detection_valid = False
            return result
        
        # Get marker corners (4 points, in image coordinates)
        marker_corners = corners[target_idx][0]  # Shape: (4, 2)
        
        # Define marker corners in 3D (marker coordinate system, Z=0)
        # Marker is centered at origin, size in cm
        # OpenCV ArUco returns corners in order: TopLeft, TopRight, BottomRight, BottomLeft
        # Using marker-local coords: X right, Y forward (up in marker plane)
        # TopLeft  (0) -> (-s, +s, 0)  (left, forward)
        # TopRight (1) -> (+s, +s, 0)  (right, forward)
        # BotRight (2) -> (+s, -s, 0)  (right, back)
        # BotLeft  (3) -> (-s, -s, 0)  (left, back)
        half_size = self.marker_size_cm / 2.0
        object_points = np.array([
            [-half_size,  half_size, 0],  # TopLeft
            [ half_size,  half_size, 0],  # TopRight
            [ half_size, -half_size, 0],  # BottomRight
            [-half_size, -half_size, 0]   # BottomLeft
        ], dtype=np.float32)
        
        # Solve PnP to get pose
        success, rvec, tvec = cv2.solvePnP(
            object_points,
            marker_corners,
            self.camera_matrix,
            self.dist_coeffs,
            flags=cv2.SOLVEPNP_IPPE_SQUARE
        )
        
        if not success:
            self.detection_valid = False
            return result
        
        # Store pose
        self.last_rvec = rvec
        self.last_tvec = tvec
        self.last_corners = marker_corners
        self.detection_valid = True
        
        # Calculate keyboard corners in 3D (relative to marker)
        keyboard_corners_3d = self._calculate_keyboard_corners_3d()
        
        # Project keyboard corners to 2D image
        keyboard_corners_2d, _ = cv2.projectPoints(
            keyboard_corners_3d,
            rvec,
            tvec,
            self.camera_matrix,
            self.dist_coeffs
        )
        keyboard_corners_2d = keyboard_corners_2d.reshape(-1, 2)
        
        result['detected'] = True
        result['corners_2d'] = marker_corners
        result['keyboard_corners'] = keyboard_corners_2d
        result['rvec'] = rvec
        result['tvec'] = tvec
        
        return result
    
    def _calculate_keyboard_corners_3d(self):
        """
        Calculate keyboard corner positions in 3D relative to marker.
        Returns 4 corners: top-left, top-right, bottom-right, bottom-left.
        """
        if self.keyboard_relative_corners is not None:
             # Use explicit relative geometry (e.g. from calibration)
             corners = np.array(self.keyboard_relative_corners, dtype=np.float32)
             # Ensure Z is 0 if passed as 2D
             if corners.shape[1] == 2:
                 corners = np.hstack((corners, np.zeros((4, 1), dtype=np.float32)))
             return corners

        # Default: Calculate from offset/dim (axis-aligned fallback)
        # Keyboard position (cm from marker center)
        x_start = self.keyboard_offset_x
        y_start = self.keyboard_offset_y
        
        # Keyboard corners (Z=0, same plane as marker)
        corners = np.array([
            [x_start, y_start, 0],                                          # Top-left
            [x_start + self.keyboard_width_cm, y_start, 0],                 # Top-right
            [x_start + self.keyboard_width_cm, y_start + self.keyboard_height_cm, 0],  # Bottom-right
            [x_start, y_start + self.keyboard_height_cm, 0]                 # Bottom-left
        ], dtype=np.float32)
        
        return corners
    
    def draw_marker_debug(self, frame, result):
        """
        Draw detected marker and keyboard outline for debugging.
        
        Args:
            frame: Image to draw on (modified in-place).
            result: Result dict from detect().
        """
        if not result['detected']:
            cv2.putText(frame, "ArUco: NOT DETECTED", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            return
        
        # Draw marker corners
        corners = result['corners_2d']
        for i in range(4):
            pt1 = tuple(corners[i].astype(int))
            pt2 = tuple(corners[(i + 1) % 4].astype(int))
            cv2.line(frame, pt1, pt2, (0, 255, 0), 2)
        
        # Draw keyboard outline
        kb_corners = result['keyboard_corners']
        for i in range(4):
            pt1 = tuple(kb_corners[i].astype(int))
            pt2 = tuple(kb_corners[(i + 1) % 4].astype(int))
            cv2.line(frame, pt1, pt2, (255, 0, 255), 2)
        
        # Status text
        cv2.putText(frame, f"ArUco: DETECTED (ID={self.marker_id})", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    def set_marker_size(self, size_cm):
        """Update marker size (call when user changes UI setting)."""
        self.marker_size_cm = size_cm
    
    def set_keyboard_offset(self, offset_x_cm, offset_y_cm):
        """Set keyboard position relative to marker center (Fallback)."""
        self.keyboard_offset_x = offset_x_cm
        self.keyboard_offset_y = offset_y_cm
    
    def set_keyboard_dimensions(self, width_cm, height_cm):
        """Set keyboard size (Fallback)."""
        self.keyboard_width_cm = width_cm
        self.keyboard_height_cm = height_cm

    def set_relative_corners(self, corners):
        """
        Set precise relative corners (4 points) from calibration.
        Allows arbitrary rotation/skew relative to marker.
        Args:
            corners: List or array of 4 points [[x1,y1], [x2,y2], ...]
        """
        if corners is not None:
            self.keyboard_relative_corners = np.array(corners, dtype=np.float32)
        else:
            self.keyboard_relative_corners = None


def generate_aruco_marker(marker_id=0, size_pixels=500, dictionary_name="4X4_50", output_path=None):
    """
    Generate an ArUco marker image.
    
    Args:
        marker_id: ID of the marker (0-49 for 4X4_50).
        size_pixels: Size of the output image in pixels.
        dictionary_name: ArUco dictionary name.
        output_path: If provided, save marker to this path.
        
    Returns:
        numpy array with the marker image (grayscale).
    """
    dict_id = ArucoDetector.DICTIONARIES.get(dictionary_name, cv2.aruco.DICT_4X4_50)
    aruco_dict = cv2.aruco.getPredefinedDictionary(dict_id)
    
    marker_img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, size_pixels)
    
    # Add white border for printing
    border = 50
    marker_with_border = cv2.copyMakeBorder(
        marker_img, border, border, border, border,
        cv2.BORDER_CONSTANT, value=255
    )
    
    if output_path:
        cv2.imwrite(output_path, marker_with_border)
        print(f"[ArUco] Marker saved to: {output_path}")
    
    return marker_with_border
