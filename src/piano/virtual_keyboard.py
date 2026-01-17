#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 27 22:57:59 2021

@author: mherrera
Modified for visual improvement
"""

import cv2
import numpy as np
import math
from src.utils import round_half_up
from src.config.theme import Theme
from src.vision.stereo_config import StereoConfig
from src.piano.keyboard_renderer import KeyboardRenderer

class VirtualKeyboard():
    __white_map = {
        # Primera octava: C, D, E, F, G, A, B
        0: 0,   1: 2,   2: 4,   3: 5,   4: 7,   5: 9,   6: 11,
        # Segunda octava: C, D, E, F, G, A, B
        7: 12,  8: 14,  9: 16,  10: 17, 11: 19, 12: 21, 13: 23
    }

    __black_map = {
        # Primera octava: C#, D#, F#, G#, A#
        0: 1,   1: 3,   2: None, 3: 6,   4: 8,   5: 10,  6: None,
        # Segunda octava: C#, D#, F#, G#, A#
        7: 13,  8: 15,  9: None, 10: 18, 11: 20, 12: 22, 13: None
    }

    __keyboard_piano_map = {
        # Primera octava (C4=60 a B4=71)
        0: 60,   1: 61,   2: 62,   3: 63,   4: 64,   5: 65,   6: 66,   7: 67,
        8: 68,   9: 69,  10: 70,  11: 71,
        # Segunda octava (C5=72 a B5=83)
        12: 72,  13: 73,  14: 74,  15: 75,  16: 76,  17: 77,  18: 78,  19: 79,
        20: 80,  21: 81,  22: 82,  23: 83
    }


    def __init__(self, canvas_w, canvas_h, kb_white_n_keys):
        self.img = None
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h

        self.kb_x0 = int(round_half_up(canvas_w * StereoConfig.KEYBOARD_X0_RATIO))
        self.kb_y0 = int(round_half_up(canvas_h * StereoConfig.KEYBOARD_Y0_RATIO))
        self.kb_x1 = int(round_half_up(canvas_w * StereoConfig.KEYBOARD_X1_RATIO))
        self.kb_y1 = int(round_half_up(canvas_h * StereoConfig.KEYBOARD_Y1_RATIO))

        self.kb_white_n_keys = kb_white_n_keys
        self.kb_len = self.kb_x1 - self.kb_x0
        
        pass
        
        self.white_kb_height = self.kb_y1 - self.kb_y0
        self.white_key_width = int(self.kb_len / self.kb_white_n_keys)
        
        self.black_key_width = self.white_key_width * (StereoConfig.BLACK_KEY_WIDTH_RATIO / StereoConfig.WHITE_KEY_WIDTH_RATIO)
        self.black_key_heigth = self.white_kb_height * StereoConfig.BLACK_KEY_HEIGHT_RATIO

        self.keys_without_black = \
            list({none_keys for none_keys in self.__black_map
                  if self.__black_map[none_keys] is None})

        self.key_id = None
        self.rectangle = []
        self.upper_zone_divisions = []
        
        # Lista de nombres de notas para visualización
        self.white_key_names = ["Do", "Re", "Mi", "Fa", "Sol", "La", "Si"]
        
        # Matriz inversa para corrección de clicks en AR
        self.M_inv = None
        self.ar_mode_active = False
        self.screen_key_polygons = [] # Poligonos de teclas en coordenadas de pantalla



    def new_key(self, key_id, top_left, bottom_rigth):
        self.key_id = key_id
        self.rectangle = [top_left, bottom_rigth]
        return key_id, self.rectangle

    def generate_logical_key_geometries(self):
        """Genera geometrías base (rectángulos) para todas las teclas en coordenadas lógicas (planas)"""
        geometries = [] # Lista de dicts {id, black, pts}
        
        # 1. Teclas Blancas
        for p in range(self.kb_white_n_keys):
            x_line_pos = self.kb_x0 + self.white_key_width * p
            
            # Rectángulo completo de la tecla blanca
            pts = [
                [x_line_pos, self.kb_y0],
                [x_line_pos + self.white_key_width, self.kb_y0],
                [x_line_pos + self.white_key_width, self.kb_y1],
                [x_line_pos, self.kb_y1]
            ]
            
            # Map visual index p to key_id
            key_id = -1
            if p in self.__white_map:
                key_id = self.__white_map[p]
                
            if key_id != -1:
                geometries.append({
                    'id': key_id,
                    'black': False,
                    'pts': np.array([pts], dtype=np.float32)
                })

        # 2. Teclas Negras
        for p in range(self.kb_white_n_keys):
            # Posicion visual aproximada (debe coincidir con draw_flat)
            x_line_pos_next = self.kb_x0 + self.white_key_width * (p+1)
            
            # Lógica de posición tecla negra (copiada de draw_flat con logica estándar)
            # Simplificación: Usamos la logica estándar para calcular el rect
            # NOTA: Esta lógica asume el layout estándar sin espejo para la geometría base.
            # El espejo se maneja visualmente o invirtiendo coordenadas después.
            
            # [FIX] Usar modulo para octavas
            base_p = p % 7
            
            b_bk_x0 = 0
            b_bk_x1 = 0
            
            if base_p in (0, 3, 4): # Izquierda
                b_bk_x0 = int(round_half_up(x_line_pos_next - self.black_key_width*(2/3)))
                b_bk_x1 = int(round_half_up(x_line_pos_next + self.black_key_width*(1/3)))
            elif base_p in (1, 5): # Derecha
                b_bk_x0 = int(round_half_up(x_line_pos_next - self.black_key_width*(1/3)))
                b_bk_x1 = int(round_half_up(x_line_pos_next + self.black_key_width*(2/3)))
            else: # Centro (O no hay)
                b_bk_x0 = int(round_half_up(x_line_pos_next - self.black_key_width/2))
                b_bk_x1 = int(round_half_up(x_line_pos_next + self.black_key_width/2))
            
            # Teclas que TIENEN negra a su derecha
            # 0(Do), 1(Re), 3(Fa), 4(Sol), 5(La) -> tienen negra
            # 7(Do), 8(Re), ...
            has_black = base_p in (0, 1, 3, 4, 5)
            
            if has_black:
                # Validar key_id negra
                 if p in self.__black_map and self.__black_map[p] is not None:
                    key_id = self.__black_map[p]
                    pts = [
                        [b_bk_x0, self.kb_y0],
                        [b_bk_x1, self.kb_y0],
                        [b_bk_x1, int(round_half_up(self.kb_y0 + self.black_key_heigth))],
                        [b_bk_x0, int(round_half_up(self.kb_y0 + self.black_key_heigth))]
                    ]
                    geometries.append({
                        'id': key_id,
                        'black': True,
                        'pts': np.array([pts], dtype=np.float32)
                    })
        return geometries



    def draw_perspective(self, img, corners, active_keys=None, hand_landmarks=None):
        """
        Dibuja el teclado en estilo CYBERPUNK (AR/WYSIWYG)
        
        Args:
            img: Imagen de destino
            corners: Esquinas detectadas de la mesa
            active_keys: Lista de IDs de teclas activas actualmente
        """
        if active_keys is None:
            active_keys = []
            
        # 1. Definir Puntos Origen y Destino (Igual que antes)
        src_pts = np.float32([
            [self.kb_x0, self.kb_y0],
            [self.kb_x1, self.kb_y0],
            [self.kb_x1, self.kb_y1],
            [self.kb_x0, self.kb_y1]
        ])
        dst_pts = np.float32(corners)
        
        try:
            matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
            self.M_inv = np.linalg.inv(matrix)
            self.ar_mode_active = True
            self.screen_key_polygons = [] # Reiniciar polígonos
            
            # === GENERACIÓN DE POLÍGONOS (Lógica Geométrica) ===
            logical_geoms = self.generate_logical_key_geometries()
            
            # === NUEVO RENDERIZADOR ===
            # Lazy initialization del renderizador profesional
            if not hasattr(self, 'renderer'):
                self.renderer = KeyboardRenderer(num_octaves=2) # Asumimos 2 octavas estándar
            
            # Mapeo de IDs: Sistema (Cromático) -> Renderer (Secuencial Visual)
            # Sistema: 0=Do, 1=Do#, 2=Re...
            # Renderer: 0..13 (Blancas), 14..23 (Negras)
            
            renderer_active_keys = []
            if active_keys:
                # Construir mapas inversos si no existen
                if not hasattr(self, '_chromatic_to_renderer_map'):
                     self._chromatic_to_renderer_map = {}
                     
                     # Blancas: 0..13
                     for w_idx in range(14): # 2 octavas * 7
                         if w_idx in self.__white_map:
                             chrom_id = self.__white_map[w_idx]
                             self._chromatic_to_renderer_map[chrom_id] = w_idx
                     
                     # Negras: 14..23
                     # Las negras se generan en orden de aparición en el renderer.
                     # KeyboardRenderer: black_keys list order.
                     # Octava 0: C#, D#, F#, G#, A# (5 teclas)
                     # Octava 1: C#, D#, F#, G#, A# (5 teclas)
                     # Total offset = 14
                     
                     black_chromatic_ids = [
                         1, 3, 6, 8, 10,       # Octava 0
                         13, 15, 18, 20, 22    # Octava 1
                     ]
                     
                     for i, chrom_id in enumerate(black_chromatic_ids):
                         renderer_id = 14 + i
                         self._chromatic_to_renderer_map[chrom_id] = renderer_id
                
                # Convertir active_keys
                for k in active_keys:
                    if k in self._chromatic_to_renderer_map:
                        renderer_active_keys.append(self._chromatic_to_renderer_map[k])
            
            # Delegar renderizado visual al módulo profesional
            # Nota: 'img' se modifica in-place
            self.renderer.render(img, corners, renderer_active_keys, hand_landmarks)
            
            # === GENERACIÓN DE POLÍGONOS DE DETECCIÓN (Invisible) ===
            # Mantenemos esta lógica para que el clic funcione
            # pero ya NO DIBUJAMOS nada aquí.
            for key_geom in sorted(logical_geoms, key=lambda x: 1 if x['black'] else 0):
                pts_src = key_geom['pts'] 
                pts_dst = cv2.perspectiveTransform(pts_src, matrix)[0]
                poly_pts = pts_dst.astype(np.int32)
                
                self.screen_key_polygons.append({
                    'id': key_geom['id'],
                    'black': key_geom['black'],
                    'contour': poly_pts
                })

        except Exception as e:
            print(f"[VirtualKeyboard] Error AR Render: {e}")
            import traceback
            traceback.print_exc()
            self.M_inv = None
            self.ar_mode_active = False
            self.screen_key_polygons = []
            
    def get_note_name(self, key_id):
        """Retorna el nombre solfeo de la tecla"""
        notes = ["Do", "Re", "Mi", "Fa", "Sol", "La", "Si"]
        # Mapa simple asumiendo inicio en Do (octava 0)
        # key_id va 0..23 (2 octavas)
        # Blancas: 0,1,2,3,4,5,6...
        # Mapeo real depende de __white_map y __black_map
        # Simplificación: usar modulo 7 para blancas
        
        # Encontrar índice de blanca
        white_idx = -1
        for p, kid in self.__white_map.items():
            if kid == key_id:
                white_idx = p
                break
        
        if white_idx != -1:
            return notes[white_idx % 7]
        return ""

    def draw_virtual_keyboard(self, img, active_keys=None, hand_landmarks=None):
        """Dibuja el teclado decidiendo automáticamente entre AR (perspectiva) o plano"""
        # Seleccionar modo según si hay calibración de mesa VÁLIDA
        use_perspective = False
        debug_msg = ""
        
    def draw_virtual_keyboard(self, img, active_keys=[], hand_landmarks=[], corners=None):
        """
        Dibuja el teclado virtual en la imagen proporcionada.
        Args:
            img: Imagen de destino
            active_keys: Lista de IDs de teclas activas para feedback visual
            hand_landmarks: Lista de punots de manos para oclusión
            corners: Lista opcional de 4 esquinas [(x,y)...] para dibujar. 
                     Si es None, usa StereoConfig.TABLE_CORNERS
        """
        # Calcular esquinas si no se proporcionan
        use_perspective = False
        
        # Resetear estado AR
        self.ar_mode_active = False
        self.M_inv = None
        
        target_corners = corners if corners is not None else StereoConfig.TABLE_CORNERS
        
        if target_corners is not None:
             self.current_corners = target_corners
             use_perspective = True
             debug_msg = "AR MODE (Corners Loaded)"
        else:
             debug_msg = "FLAT MODE (No corners)"

        # Dibujar
        if use_perspective:
            # === ESCALADO DE COORDENADAS ===
            # Si tenemos la resolución de referencia de la calibración, escalamos los puntos
            # a la resolución actual de la imagen.
            h, w = img.shape[:2]
            
            current_corners = self.current_corners
            
            if hasattr(StereoConfig, 'CALIB_PIXEL_WIDTH') and StereoConfig.CALIB_PIXEL_WIDTH and \
               hasattr(StereoConfig, 'CALIB_PIXEL_HEIGHT') and StereoConfig.CALIB_PIXEL_HEIGHT:
                
                calib_w = StereoConfig.CALIB_PIXEL_WIDTH
                calib_h = StereoConfig.CALIB_PIXEL_HEIGHT
                
                # Solo escalar si hay diferencia significativa
                if calib_w != w or calib_h != h:
                    scale_x = w / calib_w
                    scale_y = h / calib_h
                    
                    scaled_corners = []
                    for pt in StereoConfig.TABLE_CORNERS:
                        scaled_corners.append([int(pt[0] * scale_x), int(pt[1] * scale_y)])
                    
                    current_corners = scaled_corners
                    # print(f"[VirtualKeyboard] SCALED corners: {scale_x:.2f}x, {scale_y:.2f}y -> {current_corners}")
            
            ar_corners = current_corners
            
            # === VALIDACIÓN ===
            margin = 500 # Margen generoso
            corners_valid = True
            
            for pt in current_corners:
                if not (-margin <= pt[0] <= w + margin and -margin <= pt[1] <= h + margin):
                    corners_valid = False
                    debug_msg = f"AR INVALID: {pt} outside {w}x{h}"
                    break
            
            if corners_valid:
                # === RECTIFICACIÓN DE FORMA (REACTIVADO PARA WYSIWYG) ===
                # El usuario quiere un "rectángulo perfecto".
                # Convertimos los 4 puntos arbitrarios en un Rectángulo Rotado (RotatedRect).
                
                pts = np.array(current_corners, dtype=np.float32)
                
                # 1. Centro
                center = np.mean(pts, axis=0)
                
                # 2. Vectores principales
                vec_top = pts[1] - pts[0]
                width_top = np.linalg.norm(vec_top)
                
                vec_bottom = pts[2] - pts[3]
                width_bottom = np.linalg.norm(vec_bottom)
                
                vec_left = pts[3] - pts[0]
                height_left = np.linalg.norm(vec_left)
                
                vec_right = pts[2] - pts[1]
                height_right = np.linalg.norm(vec_right)
                
                # 3. Promedios
                avg_width = (width_top + width_bottom) / 2.0
                avg_height = (height_left + height_right) / 2.0
                
                # 4. Ángulo (usamos el borde superior como referencia principal de rotación)
                angle_rad = np.arctan2(vec_top[1], vec_top[0])
                angle_deg = np.degrees(angle_rad)
                
                # 5. Reconstruir esquinas perfectas (BoxPoints)
                rect = ((center[0], center[1]), (avg_width, avg_height), angle_deg)
                
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                
                # Ordenar esquinas: TL, TR, BR, BL
                rect_corners = np.zeros((4, 2), dtype="float32")
                s = box.sum(axis=1)
                rect_corners[0] = box[np.argmin(s)] # TL
                rect_corners[2] = box[np.argmax(s)] # BR

                diff = np.diff(box, axis=1)
                rect_corners[1] = box[np.argmin(diff)] # TR
                rect_corners[3] = box[np.argmax(diff)] # BL
                
                current_corners = rect_corners.tolist()
                
                # Usar esquinas rectificadas
                ar_corners = current_corners
                
                use_perspective = True
                # print(f"[VirtualKeyboard] Rectified to PERFECT RECTANGLE: {current_corners}")
            else:
                if not hasattr(self, '_warn_shown_ar_invalid'):
                     print(f"[WARN] {debug_msg} (Further warnings suppressed)")
                     self._warn_shown_ar_invalid = True
        else:
            if not StereoConfig.TABLE_CORNERS:
                debug_msg = "NO AR DATA"
            else:
                 debug_msg = f"AR DATA BAD LEN: {len(StereoConfig.TABLE_CORNERS)}"
            # print(f"[VirtualKeyboard] Drawing FLAT: {debug_msg}")
        
        if use_perspective and ar_corners:
            try:
                self.draw_perspective(img, ar_corners, active_keys, hand_landmarks)
            except Exception as e:
                print(f"[WARN] Error en draw_perspective: {e}, usando modo plano")
                cv2.putText(img, f"AR ERROR: {str(e)[:20]}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
                self.draw_virtual_keyboard_flat(img)
        else:
            self.draw_virtual_keyboard_flat(img)
            # Mostrar por qué falló AR (temporalmente para diagnóstico)
            # Solo mostrar si hay datos pero son invalidos
            if StereoConfig.TABLE_CORNERS:
                 cv2.putText(img, debug_msg, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    def draw_virtual_keyboard_flat(self, img):
        """Dibuja el teclado plano tradicional (lógica original)"""
        # Reiniciar divisiones de zona superior para evitar duplicados y fugas de memoria
        self.upper_zone_divisions = []

        # Prepara shapes (Fondo blanco semitransparente para las teclas)
        shapes = np.zeros_like(img, np.uint8)
        cv2.rectangle(
            img=shapes,
            pt1=(self.kb_x0, self.kb_y0),
            pt2=(self.kb_x1, self.kb_y1),
            color=(255, 255, 255),
            thickness=cv2.FILLED)

        alpha = StereoConfig.KEYBOARD_ALPHA
        mask = shapes.astype(bool)
        img[mask] = cv2.addWeighted(img, alpha, shapes, 1 - alpha, 0)[mask]

        # Configuración de fuente para las etiquetas
        font_face = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.55
        font_thickness = 2
        text_color = (0, 0, 0) # Negro elegante

        # Verificar si estamos en modo espejo
        is_mirrored = getattr(StereoConfig, 'MIRROR_HORIZONTAL', False)

        for p in range(self.kb_white_n_keys):
            # En modo espejo, invertir el índice visual para dibujar
            # pero mantener la lógica de detección igual
            if is_mirrored:
                visual_p = self.kb_white_n_keys - 1 - p
            else:
                visual_p = p
            
            x_line_pos = self.kb_x0 + self.white_key_width * (p+1)

            # --- DIBUJAR TECLAS NEGRAS ---
            # En modo espejo usamos visual_p para determinar qué teclas tienen negras
            check_p = visual_p if is_mirrored else p
            
            # Las teclas sin negra son: Mi (2), Si (6) en cada octava
            keys_without_black_visual = [2, 6, 9, 13]  # Mi y Si de cada octava
            
            if check_p not in keys_without_black_visual:
                # Determinar posición de la tecla negra según el patrón del piano
                # En modo espejo, las posiciones también se invierten
                if is_mirrored:
                    # Invertir la lógica de posicionamiento
                    if check_p % 7 in (0, 3, 4):  # Do#, Fa#, Sol#
                        b_bk_x0 = int(round_half_up(x_line_pos - self.black_key_width*(1/3)))
                        b_bk_x1 = int(round_half_up(x_line_pos + self.black_key_width*(2/3)))
                    elif check_p % 7 in (1, 5):  # Re#, La#
                        b_bk_x0 = int(round_half_up(x_line_pos - self.black_key_width*(2/3)))
                        b_bk_x1 = int(round_half_up(x_line_pos + self.black_key_width*(1/3)))
                    else:
                        b_bk_x0 = int(round_half_up(x_line_pos - self.black_key_width/2))
                        b_bk_x1 = int(round_half_up(x_line_pos + self.black_key_width/2))
                else:
                    if p in (0, 3, 4): # Izquierda
                        b_bk_x0 = int(round_half_up(x_line_pos - self.black_key_width*(2/3)))
                        b_bk_x1 = int(round_half_up(x_line_pos + self.black_key_width*(1/3)))
                    elif p in (1, 5): # Derecha
                        b_bk_x0 = int(round_half_up(x_line_pos - self.black_key_width*(1/3)))
                        b_bk_x1 = int(round_half_up(x_line_pos + self.black_key_width*(2/3)))
                    else: # Centro
                        b_bk_x0 = int(round_half_up(x_line_pos - self.black_key_width/2))
                        b_bk_x1 = int(round_half_up(x_line_pos + self.black_key_width/2))

                # Tecla negra rellena (Gris oscuro para que no sea transparente en la máscara AR)
                cv2.rectangle(
                    img=img,
                    pt1=(b_bk_x0, self.kb_y0),
                    pt2=(b_bk_x1, int(round_half_up(self.kb_y0 + self.black_key_heigth))),
                    color=(30, 30, 30),
                    thickness=cv2.FILLED)
                
                # Borde gris sutil para las teclas negras
                cv2.rectangle(
                    img=img,
                    pt1=(b_bk_x0, self.kb_y0),
                    pt2=(b_bk_x1, int(round_half_up(self.kb_y0 + self.black_key_heigth))),
                    color=(60, 60, 60),
                    thickness=1)

                self.new_key(p, (b_bk_x0, self.kb_y0),
                             (b_bk_x1, int(round_half_up(self.kb_y0 + self.black_key_heigth))))
                # Guardar tupla (id_tecla, rectangulo) para que find_key_in_upper_zone funcione correctamente
                self.upper_zone_divisions.append((p, self.rectangle))

            # --- LÍNEAS SEPARADORAS DE TECLAS BLANCAS ---
            cv2.line(img=img,
                     pt1=(int(round_half_up(x_line_pos)), self.kb_y0),
                     pt2=(int(round_half_up(x_line_pos)), self.kb_y1),
                     color=(0, 0, 0), # Línea negra delgada
                     thickness=1)

            # --- ETIQUETAS DE NOTAS (Nuevo diseño limpio) ---
            
            # 1. Obtener nombre de la nota (usando visual_p para modo espejo)
            note_name = self.white_key_names[visual_p % 7]
            
            # 2. Calcular el tamaño exacto del texto para centrarlo
            (text_w, text_h), baseline = cv2.getTextSize(note_name, font_face, font_scale, font_thickness)
            
            # 3. Calcular posición central X de la tecla
            key_center_x = x_line_pos - self.white_key_width / 2
            
            # 4. Definir posición final del texto (Centrado en X, cerca del fondo en Y)
            text_x = int(key_center_x - text_w / 2)
            text_y = int(self.kb_y1 - 15) # 15 píxeles desde el borde inferior

            # 5. Dibujar texto limpio
            cv2.putText(img=img, text=note_name,
                        org=(text_x, text_y),
                        fontFace=font_face,
                        fontScale=font_scale,
                        color=text_color,
                        thickness=font_thickness,
                        lineType=cv2.LINE_AA) # LINE_AA para bordes suaves

        # Borde exterior del teclado
        cv2.rectangle(img, (self.kb_x0, self.kb_y0),
                      (self.kb_x1, self.kb_y1), (0, 0, 0), 2)

    def intersect(self, pointXY):
        # Transforma el punto si estamos en modo AR
        x_check, y_check = pointXY
        
        if self.ar_mode_active and self.M_inv is not None:
             # Convertir punto a formato np (1, 1, 2) para perspectiveTransform
             pt_np = np.array([[[float(x_check), float(y_check)]]], dtype=np.float32)
             pt_transformed = cv2.perspectiveTransform(pt_np, self.M_inv)
             x_check = float(pt_transformed[0][0][0])
             y_check = float(pt_transformed[0][0][1])
             
        if x_check > self.kb_x0 and x_check < self.kb_x1 and \
                y_check > self.kb_y0 and y_check < self.kb_y1:
            return True
        return False

    def find_key_in_upper_zone(self, x_kb_pos, y_kb_pos):
        key_id = -1
        for k in self.upper_zone_divisions:
            if x_kb_pos > k[1][0][0] and x_kb_pos < k[1][1][0]:
                key_id = k[0]
                break
        return key_id

    def find_key(self, x_pos, y_pos):
        # [FIX] COORDENADAS: RAW vs DISPLAY
        # Las coordenadas de entrada (x_pos, y_pos) vienen del detector de manos (RAW frame).
        
        input_x, input_y = x_pos, y_pos
        
        # === MODO AR (WYSIWYG) ===
        # En modo AR, los polígonos están en el espacio de coordenadas del frame RAW
        # (porque draw_perspective dibuja sobre el frame sin transformar).
        # Por lo tanto, usamos las coordenadas RAW directamente sin transformación.
        if self.ar_mode_active and hasattr(self, 'screen_key_polygons') and self.screen_key_polygons:
            # DEBUG: Mostrar coordenadas de entrada vs rango de poligonos
            if not hasattr(self, '_debug_coord_shown'):
                first_poly = self.screen_key_polygons[0]
                last_poly = self.screen_key_polygons[-1]
                x1,y1,w1,h1 = cv2.boundingRect(first_poly['contour'])
                x2,y2,w2,h2 = cv2.boundingRect(last_poly['contour'])
                print(f"[DEBUG] Using RAW coords in AR: ({input_x:.0f},{input_y:.0f})")
                print(f"[DEBUG] Poly Range: FirstKey({x1},{y1} to {x1+w1},{y1+h1}), LastKey({x2},{y2} to {x2+w2},{y2+h2})")
                self._debug_coord_shown = True
            
            found_key_id = None
            found_poly_type = ""
            
            # Buscar primero en teclas negras (están encima)
            # Usar coordenadas RAW directamente
            check_x, check_y = input_x, input_y
            
            for poly in reversed(self.screen_key_polygons):
                # PointPolygonTest: (contour, pt, measureDist)
                # Returns: +ve distance (inside), -ve distance (outside), 0 (on edge)
                # IMPORTANT: measureDist=True to get pixel distance for tolerance check
                dist = cv2.pointPolygonTest(poly['contour'], (check_x, check_y), True)
                
                if dist >= -5: # [WYSIWYG] Tolerancia de 5 pixeles
                    found_key_id = poly['id']
                    found_poly_type = "Black" if poly['black'] else "White"
                    if poly['black']:
                        break
                    break
            
            if found_key_id is not None:
                # print(f"[KEY_DEBUG] AR HIT! ({check_x:.0f},{check_y:.0f}) -> {found_key_id} ({found_poly_type})")
                return found_key_id
            
            return None

        # === MODO PLANO (FALLBACK) ===
        # En modo plano, necesitamos aplicar la transformación de display
        if hasattr(StereoConfig, 'transform_point_for_display'):
             x_pos, y_pos = StereoConfig.transform_point_for_display((x_pos, y_pos), self.canvas_w, self.canvas_h)
        
        # Si está activado el modo espejo, invertir la posición X
        if getattr(StereoConfig, 'MIRROR_HORIZONTAL', False):
            # Invertir X respecto al centro del teclado
            x_pos = self.kb_x0 + (self.kb_x1 - x_pos)
        
        x = x_pos - self.kb_x0
        y = y_pos - self.kb_y0

        key_found = None
        if y < self.black_key_heigth:
            key = x/self.white_key_width*2
            key = math.floor(key)

            key = self.find_key_in_upper_zone(x_pos, y_pos)
            if key == -1:
                key = x/self.white_key_width
                key = math.floor(key)
                if int(key) in self.__white_map:
                    key_found = self.__white_map[int(key)]
            else:
                if int(key) in self.__black_map:
                    key_found = self.__black_map[int(key)]
        else:
            key = x/self.white_key_width
            key = math.floor(key)
            if int(key) in self.__white_map:
                key_found = self.__white_map[int(key)]
                
        # DEBUG: Imprimir si se detecta una tecla
        # if key_found is not None:
        #      print(f"[KEY_DEBUG] FLAT HIT: {key_found}")
             
        return key_found

    def note_from_key(self, key):
        return self.__keyboard_piano_map[key]