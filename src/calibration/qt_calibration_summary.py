import sys
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSpacerItem, QSizePolicy, QFrame, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPalette

class CalibrationSummaryDialog(QDialog):
    # Return codes
    ACTION_START = 1
    ACTION_RECALIBRATE_STEREO = 2
    ACTION_RECALIBRATE_DEPTH = 4  # Nuevo código para Fase 3
    ACTION_RECALIBRATE_ALL = 3
    ACTION_EXIT = 0

    def __init__(self, summary_data):
        super().__init__()
        self.summary = summary_data
        self.result_action = self.ACTION_EXIT
        
        self.setWindowTitle("Resumen de Calibración")
        self.setMinimumSize(900, 700)
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QLabel.title {
                color: #00C8FF;
                font-size: 28px;
                font-weight: bold;
            }
            QLabel.subtitle {
                color: #cccccc;
                font-size: 14px;
            }
            QLabel.section-title {
                color: #00C8FF;
                font-size: 20px;
                font-weight: bold;
                margin-top: 10px;
            }
            QLabel.label-key {
                color: #aaaaff;
                font-size: 16px;
                font-weight: bold;
            }
            QLabel.label-value {
                color: #ffffff;
                font-size: 16px;
            }
            QLabel.status-ok {
                color: #00ff00;
                font-weight: bold;
            }
            QLabel.status-warn {
                color: #ffaa00;
                font-weight: bold;
            }
            QFrame.separator {
                background-color: #444444;
                max-height: 2px;
            }
            QFrame.box {
                border: 1px solid #00C8FF;
                border-radius: 5px;
                background-color: #3b3b3b;
                padding: 10px;
            }
            QPushButton {
                background-color: #00C8FF;
                color: #000000;
                border: none;
                padding: 12px 20px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #33D6FF;
            }
            QPushButton#btn-exit {
                background-color: #555555;
                color: #ffffff;
            }
            QPushButton#btn-exit:hover {
                background-color: #777777;
            }
        """)
        
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(15)
        
        # Header
        header_layout = QVBoxLayout()
        title = QLabel("CALIBRACIÓN COMPLETA")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel(f"Fecha: {self.summary.get('fecha', 'N/A')}   |   Versión: {self.summary.get('version', '2.0')}")
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addLayout(header_layout)
        
        self._add_separator(main_layout)
        
        # Phase 1 Section
        lbl_p1 = QLabel("FASE 1: CALIBRACIÓN INDIVIDUAL")
        lbl_p1.setProperty("class", "section-title")
        main_layout.addWidget(lbl_p1)
        
        p1_layout = QVBoxLayout()
        p1_layout.setSpacing(5)
        
        # Left Camera
        row_left = QHBoxLayout()
        row_left.addWidget(QLabel("Cámara IZQUIERDA:"))
        err_left = self.summary.get('error_left', 'N/A')
        val_left = f"{err_left:.6f} px" if isinstance(err_left, float) else str(err_left)
        row_left.addWidget(QLabel(val_left))
        row_left.addStretch()
        p1_layout.addLayout(row_left)
        
        # Right Camera
        row_right = QHBoxLayout()
        row_right.addWidget(QLabel("Cámara DERECHA:"))
        err_right = self.summary.get('error_right', 'N/A')
        val_right = f"{err_right:.6f} px" if isinstance(err_right, float) else str(err_right)
        row_right.addWidget(QLabel(val_right))
        row_right.addStretch()
        p1_layout.addLayout(row_right)
        
        main_layout.addLayout(p1_layout)
        
        self._add_separator(main_layout)
        
        # Phase 2 Section
        lbl_p2 = QLabel("FASE 2: CALIBRACIÓN ESTÉREO")
        lbl_p2.setProperty("class", "section-title")
        main_layout.addWidget(lbl_p2)
        
        p2_layout = QVBoxLayout()
        
        # Baseline
        row_base = QHBoxLayout()
        row_base.addWidget(QLabel("Baseline (distancia):"))
        base_val = self.summary.get('baseline_cm', 'N/A')
        val_base = f"{base_val:.2f} cm" if isinstance(base_val, float) else str(base_val)
        lbl_base = QLabel(val_base)
        lbl_base.setStyleSheet("color: #00C8FF; font-weight: bold; font-size: 18px;")
        row_base.addWidget(lbl_base)
        row_base.addStretch()
        p2_layout.addLayout(row_base)
        
        # RMS Error
        row_rms = QHBoxLayout()
        row_rms.addWidget(QLabel("Error RMS:"))
        rms_val = self.summary.get('error_stereo', 'N/A')
        val_rms = f"{rms_val:.4f}" if isinstance(rms_val, float) else str(rms_val)
        row_rms.addWidget(QLabel(val_rms))
        
        # Quality indicator
        if isinstance(rms_val, float):
            quality = "EXCELENTE" if rms_val < 0.3 else "BUENA" if rms_val < 0.5 else "REGULAR" if rms_val < 1.0 else "MALA"
            color = "#00ff00" if rms_val < 0.5 else "#ffff00" if rms_val < 1.0 else "#ff0000"
            lbl_qual = QLabel(quality)
            lbl_qual.setStyleSheet(f"color: {color}; font-weight: bold; margin-left: 20px;")
            row_rms.addWidget(lbl_qual)
            
        row_rms.addStretch()
        p2_layout.addLayout(row_rms)
        
        main_layout.addLayout(p2_layout)
        
        self._add_separator(main_layout)
        
        # Phase 3 Section (NEW)
        lbl_p3 = QLabel("FASE 3: PROFUNDIDAD")
        lbl_p3.setProperty("class", "section-title")
        main_layout.addWidget(lbl_p3)
        
        p3_layout = QVBoxLayout()
        
        # Correction Factor
        row_factor = QHBoxLayout()
        row_factor.addWidget(QLabel("Factor de Corrección:"))
        
        # Intentar obtener factor de corrección (puede estar en 'correction_factor' o 'depth_correction_factor')
        factor_val = self.summary.get('correction_factor', 'N/A')
        
        if factor_val == 'N/A':
            factor_val = self.summary.get('depth_correction_factor', 'N/A')
             
        val_factor = f"{factor_val:.4f}" if isinstance(factor_val, float) else str(factor_val)
        lbl_factor = QLabel(val_factor)
        lbl_factor.setStyleSheet("color: #00C8FF; font-weight: bold; font-size: 16px;")
        row_factor.addWidget(lbl_factor)
        row_factor.addStretch()
        p3_layout.addLayout(row_factor)
        
        main_layout.addLayout(p3_layout)
        
        self._add_separator(main_layout)
        
        # Warning Box
        warn_frame = QFrame()
        warn_frame.setProperty("class", "box")
        warn_layout = QVBoxLayout(warn_frame)
        
        lbl_warn_title = QLabel("ESTA CALIBRACIÓN ES VÁLIDA PARA:")
        lbl_warn_title.setStyleSheet("color: #00C8FF; font-weight: bold;")
        lbl_warn_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_warn1 = QLabel("- La misma ubicación física de las cámaras")
        lbl_warn1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_warn2 = QLabel("- Si moviste las cámaras, RE-CALIBRA")
        lbl_warn2.setStyleSheet("color: #ffaa00;")
        lbl_warn2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        warn_layout.addWidget(lbl_warn_title)
        warn_layout.addWidget(lbl_warn1)
        warn_layout.addWidget(lbl_warn2)
        
        main_layout.addWidget(warn_frame)
        
        main_layout.addStretch()
        
        # Buttons
        btn_layout = QVBoxLayout()
        
        btn_recalibrate = QPushButton("RE-CALIBRAR")
        btn_recalibrate.setObjectName("btn-all")
        btn_recalibrate.clicked.connect(lambda: self._finish(self.ACTION_RECALIBRATE_ALL))
        btn_layout.addWidget(btn_recalibrate)
        
        btn_exit = QPushButton("VOLVER")
        btn_exit.setObjectName("btn-exit")
        btn_exit.clicked.connect(lambda: self._finish(self.ACTION_EXIT))
        btn_layout.addWidget(btn_exit)
        
        main_layout.addLayout(btn_layout)
        
        self.setLayout(main_layout)

    def _add_separator(self, layout):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setProperty("class", "separator")
        layout.addWidget(line)

    def _finish(self, action):
        self.result_action = action
        self.accept()

def show_calibration_summary(summary_data):
    """
    Muestra el diálogo de resumen y retorna la acción seleccionada
    """
    app = QApplication.instance()
    owns_app = False
    if not app:
        app = QApplication(sys.argv)
        owns_app = True
        
    dialog = CalibrationSummaryDialog(summary_data)
    dialog.exec()
    
    result = dialog.result_action
    
    if owns_app:
        app.quit()
        
    return result
