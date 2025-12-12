#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calibrador de Profundidad - Fase 3
Calcula el factor de corrección de profundidad específico del sistema
"""

import cv2
import numpy as np
import json
from pathlib import Path
from .calibration_config import CalibrationConfig

# Importar load_depth_estimator
try:
    from ..vision.depth_estimator import load_depth_estimator
except ImportError:
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from vision.depth_estimator import load_depth_estimator



class DepthCalibrator:
    """
    Calibrador para determinar el factor de corrección de profundidad
    Mide a distancias conocidas y calcula el factor óptimo
    """
    
    def __init__(self, depth_estimator, width=1280, height=720):
        """
        Args:
            depth_estimator: Instancia de DepthEstimator ya calibrado (Fase 1+2)
            width: Ancho de la imagen
            height: Alto de la imagen
        """
        self.depth_estimator = depth_estimator
        self.width = width
        self.height = height
        
        # Resultados de mediciones
        self.measurements = []  # [(distancia_real, distancia_medida), ...]
        
        # Factor calculado
        self.correction_factor = 1.0
        
    def calculate_depth(self, landmarks_left, landmarks_right):
        """
        Calcula la profundidad del dedo índice usando landmarks
        
        Args:
            landmarks_left: Landmarks de mano izquierda (MediaPipe)
            landmarks_right: Landmarks de mano derecha (MediaPipe)
            
        Returns:
            float: Profundidad en cm (sin corrección) o None
        """
        if not landmarks_left or not landmarks_right:
            return None
            
        # Obtener índice de ambas cámaras (landmark 8)
        # MediaPipe landmarks object has a .landmark attribute which is the list
        try:
            index_left = landmarks_left.landmark[8]
            index_right = landmarks_right.landmark[8]
        except AttributeError:
            # Fallback in case it's already a list (though unlikely with MP)
            index_left = landmarks_left[8]
            index_right = landmarks_right[8]
        
        # Convertir a coordenadas de píxel
        x_left = index_left.x * self.width
        y_left = index_left.y * self.height
        x_right = index_right.x * self.width
        y_right = index_right.y * self.height
        
        # Triangular sin corrección (usar factor 1.0 temporalmente)
        original_factor = self.depth_estimator.DEPTH_CORRECTION_FACTOR
        self.depth_estimator.DEPTH_CORRECTION_FACTOR = 1.0
        
        point_3d = self.depth_estimator.triangulate_point_DLT(
            (x_left, y_left), (x_right, y_right)
        )
        
        self.depth_estimator.DEPTH_CORRECTION_FACTOR = original_factor
        
        if point_3d is not None:
            return point_3d[2]  # Profundidad Z
            
        return None

    def add_measurement(self, real_distance, measured_depth):
        """
        Agrega una medición válida
        
        Args:
            real_distance: Distancia real objetivo (cm)
            measured_depth: Profundidad medida por el sistema (cm)
        """
        self.measurements.append((real_distance, measured_depth))
        print(f"✓ Medición agregada: {real_distance}cm real → {measured_depth:.2f}cm medido")

    def calculate_and_save(self):
        """
        Calcula el factor de corrección final y lo guarda
        
        Returns:
            float: Factor de corrección calculado o None si falla
        """
        if len(self.measurements) < 3:
            print(f"✗ Error: Se necesitan al menos 3 mediciones (tienes {len(self.measurements)})")
            return None
            
        self.correction_factor = self._calculate_correction_factor()
        self._save_correction_factor()
        
        return self.correction_factor
    
    def _calculate_correction_factor(self):
        """
        Calcula el factor de corrección óptimo usando regresión lineal
        
        Returns:
            float: Factor de corrección (slope de la regresión)
        """
        if not self.measurements:
            return 1.0
        
        real_distances = np.array([m[0] for m in self.measurements])
        measured_distances = np.array([m[1] for m in self.measurements])
        
        # Regresión lineal: real = factor * medido
        # factor = mean(real / medido)
        ratios = real_distances / measured_distances
        factor = np.mean(ratios)
        
        return factor
    
    def _save_correction_factor(self):
        """Guarda el factor de corrección en el archivo de calibración"""
        try:
            calib_file = CalibrationConfig.CALIBRATION_FILE
            
            # Leer calibración existente
            with open(calib_file, 'r') as f:
                calib_data = json.load(f)
            
            # Agregar sección de profundidad (Fase 3)
            calib_data['depth_correction'] = {
                'factor': self.correction_factor,
                'measurements': [
                    {'real_cm': real, 'measured_cm': measured}
                    for real, measured in self.measurements
                ],
                'num_samples': len(self.measurements)
            }
            
            # Guardar
            with open(calib_file, 'w') as f:
                json.dump(calib_data, f, indent=4)
            
            print(f"✓ Factor de corrección guardado en: {calib_file}")
            
        except Exception as e:
            print(f"⚠ Error al guardar factor de corrección: {e}")
