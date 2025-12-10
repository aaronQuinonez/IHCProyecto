#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Calibración Estereoscópica Profesional v2.0
Fase 1: Calibración individual de cámaras (25 fotos cada una)
Fase 2: Calibración estéreo (8-15 pares simultáneos)
Proceso continuo e integrado
"""

from .qt_calibration_manager import QtCalibrationManager, run_qt_calibration
from .camera_calibrator import CameraCalibrator
from .stereo_calibrator import StereoCalibrator
from .calibration_config import CalibrationConfig

__all__ = [
    'QtCalibrationManager',
    'run_qt_calibration',
    'CameraCalibrator', 
    'StereoCalibrator',
    'CalibrationConfig'
]

__version__ = '2.0.0'
