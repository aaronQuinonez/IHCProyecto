#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Professional Keyboard Renderer for AR

Renders the virtual keyboard with solid colors, shadows, and realistic appearance.
Designed for use with ArUco-tracked 3D positioning.
"""

import cv2
import numpy as np
from src.config.theme import Theme, ColorPalette


class KeyboardRenderer:
    """
    Professional renderer for virtual piano keyboard.
    
    Features:
    - Solid, realistic piano colors
    - Subtle shadows for depth
    - Anti-aliased edges
    - Key labels with solfège notation
    - Hand occlusion support
    """
    
    def __init__(self, num_octaves=2):
        """
        Initialize renderer.
        
        Args:
            num_octaves: Number of octaves to render (default 2).
        """
        self.num_octaves = num_octaves
        self.white_keys_per_octave = 7
        self.total_white_keys = num_octaves * self.white_keys_per_octave
        
        # Black key positions relative to white keys (0-indexed within octave)
        # After white keys: 0(C), 1(D), 2(E), 3(F), 4(G), 5(A), 6(B)
        # Black keys: C#(after 0), D#(after 1), F#(after 3), G#(after 4), A#(after 5)
        self.black_key_positions = [0, 1, 3, 4, 5]  # Positions after which black keys appear
        
        # Colors from Theme (centralized for consistency)
        self.color_white_idle = Theme.KEY_AR_WHITE_IDLE
        self.color_white_active = Theme.KEY_AR_WHITE_ACTIVE
        self.color_black_idle = Theme.KEY_AR_BLACK_IDLE
        self.color_black_active = Theme.KEY_AR_BLACK_ACTIVE
        self.color_shadow = Theme.KEY_AR_SHADOW
        self.color_border = ColorPalette.BLACK
        self.color_text = Theme.KEY_AR_TEXT_MAIN
        
        # Proportions
        self.black_key_width_ratio = 0.6   # Black key width relative to white
        self.black_key_height_ratio = 0.62 # Black key height relative to white
        
        # Solfège names
        self.note_names = ["Do", "Re", "Mi", "Fa", "Sol", "La", "Si"]
    
    def render(self, frame, corners, active_keys=None, hand_landmarks=None):
        """
        Render the keyboard onto the frame.
        
        Args:
            frame: BGR image to render onto.
            corners: 4 corners of keyboard area in image coordinates [[x,y], ...].
                     Order: top-left, top-right, bottom-right, bottom-left.
            active_keys: List of active key IDs (0-indexed).
            hand_landmarks: List of hand landmark points for occlusion.
            
        Returns:
            Modified frame with keyboard rendered.
        """
        if active_keys is None:
            active_keys = []
        if hand_landmarks is None:
            hand_landmarks = []
        
        # Validate corners
        if corners is None or len(corners) != 4:
            return frame
        
        corners = np.array(corners, dtype=np.float32)
        
        # Store original frame for occlusion restoration
        original_frame = frame.copy()
        
        # Generate key geometries in image space
        white_keys, black_keys = self._generate_key_geometries(corners)
        
        # === RENDER WHITE KEYS (Background layer) ===
        for i, key_pts in enumerate(white_keys):
            is_active = i in active_keys
            color = self.color_white_active if is_active else self.color_white_idle
            
            # Draw shadow first (offset down-right)
            shadow_pts = key_pts + np.array([3, 3], dtype=np.float32)
            cv2.fillPoly(frame, [shadow_pts.astype(np.int32)], self.color_shadow)
            
            # Draw key
            cv2.fillPoly(frame, [key_pts.astype(np.int32)], color)
            
            # Draw border
            cv2.polylines(frame, [key_pts.astype(np.int32)], True, 
                         self.color_border, 1, cv2.LINE_AA)
            
            # Draw label (solfège)
            if not is_active:  # Don't draw label when pressed
                self._draw_key_label(frame, key_pts, i)
        
        # === RENDER BLACK KEYS (Foreground layer) ===
        black_key_id_offset = self.total_white_keys  # Black keys are numbered after white
        for i, key_pts in enumerate(black_keys):
            key_id = black_key_id_offset + i
            is_active = key_id in active_keys
            color = self.color_black_active if is_active else self.color_black_idle
            
            # Draw shadow
            shadow_pts = key_pts + np.array([2, 2], dtype=np.float32)
            cv2.fillPoly(frame, [shadow_pts.astype(np.int32)], (0, 0, 0))
            
            # Draw key with 3D bevel effect (top lighter edge)
            cv2.fillPoly(frame, [key_pts.astype(np.int32)], color)
            
            # Top edge highlight (simulates top of 3D key)
            top_left = key_pts[0]
            top_right = key_pts[1]
            cv2.line(frame, tuple(top_left.astype(int)), tuple(top_right.astype(int)),
                    (80, 80, 80), 2, cv2.LINE_AA)
            
            # Border
            cv2.polylines(frame, [key_pts.astype(np.int32)], True,
                         self.color_border, 1, cv2.LINE_AA)
        
        # === APPLY HAND OCCLUSION ===
        if hand_landmarks:
            frame = self._apply_hand_occlusion(frame, original_frame, hand_landmarks)
        
        return frame
    
    def _generate_key_geometries(self, corners):
        """
        Generate key polygon geometries from keyboard corners.
        
        Args:
            corners: 4 corners of keyboard [TL, TR, BR, BL].
            
        Returns:
            Tuple of (white_keys, black_keys), each a list of 4-point polygons.
        """
        white_keys = []
        black_keys = []
        
        # Calculate transformation matrix from unit square to actual corners
        # Unit keyboard: (0,0) to (1,1)
        src_pts = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float32)
        dst_pts = corners.astype(np.float32)
        
        transform_matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
        
        # Generate white keys in normalized (0-1) space, then transform
        key_width = 1.0 / self.total_white_keys
        
        for i in range(self.total_white_keys):
            x0 = i * key_width
            x1 = (i + 1) * key_width
            
            # Key corners in normalized space
            key_pts_norm = np.array([
                [x0, 0], [x1, 0], [x1, 1], [x0, 1]
            ], dtype=np.float32)
            
            # Transform to image space
            key_pts = cv2.perspectiveTransform(
                key_pts_norm.reshape(1, -1, 2), transform_matrix
            )[0]
            
            white_keys.append(key_pts)
        
        # Generate black keys
        black_width = key_width * self.black_key_width_ratio
        black_height = self.black_key_height_ratio
        
        for octave in range(self.num_octaves):
            for pos in self.black_key_positions:
                # White key index this black key is after
                white_idx = octave * 7 + pos
                
                # Center of black key (between two white keys)
                x_center = (white_idx + 1) * key_width
                x0 = x_center - black_width / 2
                x1 = x_center + black_width / 2
                
                # Black key corners in normalized space
                key_pts_norm = np.array([
                    [x0, 0], [x1, 0], [x1, black_height], [x0, black_height]
                ], dtype=np.float32)
                
                # Transform to image space
                key_pts = cv2.perspectiveTransform(
                    key_pts_norm.reshape(1, -1, 2), transform_matrix
                )[0]
                
                black_keys.append(key_pts)
        
        return white_keys, black_keys
    
    def _draw_key_label(self, frame, key_pts, key_index):
        """
        Draw solfège label on a white key.
        """
        # Calculate centroid
        centroid = key_pts.mean(axis=0).astype(int)
        
        # Get note name
        octave_pos = key_index % 7
        note_name = self.note_names[octave_pos]
        
        # Position text at bottom portion of key
        text_y = int(centroid[1] + (key_pts[2][1] - key_pts[0][1]) * 0.3)
        
        # Get text size for centering
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4
        thickness = 1
        (text_w, text_h), _ = cv2.getTextSize(note_name, font, font_scale, thickness)
        
        text_x = int(centroid[0] - text_w / 2)
        
        # Draw text with slight shadow
        cv2.putText(frame, note_name, (text_x + 1, text_y + 1),
                   font, font_scale, (120, 120, 120), thickness + 1, cv2.LINE_AA)
        cv2.putText(frame, note_name, (text_x, text_y),
                   font, font_scale, self.color_text, thickness, cv2.LINE_AA)
    
    def _apply_hand_occlusion(self, frame, original_frame, hand_landmarks):
        """
        Apply hand occlusion to show hands on top of keyboard.
        
        Args:
            frame: Frame with keyboard rendered.
            original_frame: Original frame without keyboard.
            hand_landmarks: List of hand landmark point lists.
            
        Returns:
            Frame with hands appearing on top of keyboard.
        """
        # Create mask for hands
        hand_mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        
        for hand_pts in hand_landmarks:
            if len(hand_pts) < 3:
                continue
            
            pts_np = np.array(hand_pts, dtype=np.int32)
            
            # Create convex hull around hand
            hull = cv2.convexHull(pts_np)
            
            # Draw filled hull on mask
            cv2.fillPoly(hand_mask, [hull], 255)
        
        # Dilate mask slightly to cover edges
        kernel = np.ones((7, 7), np.uint8)
        hand_mask = cv2.dilate(hand_mask, kernel, iterations=1)
        
        # Restore original pixels where hand is
        frame[hand_mask == 255] = original_frame[hand_mask == 255]
        
        return frame
    
    def get_key_polygons(self, corners):
        """
        Get key polygons for hit detection.
        
        Args:
            corners: 4 corners of keyboard area.
            
        Returns:
            List of dicts with 'id', 'black', 'contour' for each key.
        """
        white_keys, black_keys = self._generate_key_geometries(np.array(corners))
        
        polygons = []
        
        # White keys (IDs 0 to N-1)
        for i, pts in enumerate(white_keys):
            polygons.append({
                'id': i,
                'black': False,
                'contour': pts.astype(np.int32)
            })
        
        # Black keys (IDs N to N+M-1)
        black_offset = len(white_keys)
        for i, pts in enumerate(black_keys):
            polygons.append({
                'id': black_offset + i,
                'black': True,
                'contour': pts.astype(np.int32)
            })
        
        return polygons
