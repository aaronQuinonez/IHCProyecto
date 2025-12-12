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
from src.vision.stereo_config import StereoConfig

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

        if self.canvas_w == 640 and self.canvas_h == 480:
            self.kb_x0 = int(round_half_up(canvas_w * StereoConfig.KEYBOARD_X0_RATIO))
            self.kb_y0 = int(round_half_up(canvas_h * StereoConfig.KEYBOARD_Y0_RATIO))
            self.kb_x1 = int(round_half_up(canvas_w * StereoConfig.KEYBOARD_X1_RATIO))
            self.kb_y1 = int(round_half_up(canvas_h * StereoConfig.KEYBOARD_Y1_RATIO))

        self.kb_white_n_keys = kb_white_n_keys
        self.kb_len = self.kb_x1 - self.kb_x0
        self.white_kb_height = self.kb_y1 - self.kb_y0
        self.white_key_width = self.kb_len/kb_white_n_keys
        
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

    def new_key(self, key_id, top_left, bottom_rigth):
        self.key_id = key_id
        self.rectangle = [top_left, bottom_rigth]
        return key_id, self.rectangle

    def draw_virtual_keyboard(self, img):
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

        for p in range(self.kb_white_n_keys):
            x_line_pos = self.kb_x0 + self.white_key_width * (p+1)

            # --- DIBUJAR TECLAS NEGRAS ---
            if p not in self.keys_without_black:
                if p in (0, 3, 4): # Izquierda
                    b_bk_x0 = int(round_half_up(x_line_pos - self.black_key_width*(2/3)))
                    b_bk_x1 = int(round_half_up(x_line_pos + self.black_key_width*(1/3)))
                elif p in (1, 5): # Derecha
                    b_bk_x0 = int(round_half_up(x_line_pos - self.black_key_width*(1/3)))
                    b_bk_x1 = int(round_half_up(x_line_pos + self.black_key_width*(2/3)))
                else: # Centro
                    b_bk_x0 = int(round_half_up(x_line_pos - self.black_key_width/2))
                    b_bk_x1 = int(round_half_up(x_line_pos + self.black_key_width/2))

                # Tecla negra rellena
                cv2.rectangle(
                    img=img,
                    pt1=(b_bk_x0, self.kb_y0),
                    pt2=(b_bk_x1, int(round_half_up(self.kb_y0 + self.black_key_heigth))),
                    color=(0, 0, 0),
                    thickness=cv2.FILLED)
                
                # Borde gris sutil para las teclas negras
                cv2.rectangle(
                    img=img,
                    pt1=(b_bk_x0, self.kb_y0),
                    pt2=(b_bk_x1, int(round_half_up(self.kb_y0 + self.black_key_heigth))),
                    color=(50, 50, 50),
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
            
            # 1. Obtener nombre de la nota
            note_name = self.white_key_names[p % 7]
            
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
        if pointXY[0] > self.kb_x0 and pointXY[0] < self.kb_x1 and \
                pointXY[1] > self.kb_y0 and pointXY[1] < self.kb_y1:
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
        x = x_pos - self.kb_x0
        y = y_pos - self.kb_y0

        if y < self.black_key_heigth:
            key = x/self.white_key_width*2
            key = math.floor(key)

            key = self.find_key_in_upper_zone(x_pos, y_pos)
            if key == -1:
                key = x/self.white_key_width
                key = math.floor(key)
                return self.__white_map[int(key)]
            else:
                return self.__black_map[int(key)]
        else:
            key = x/self.white_key_width
            key = math.floor(key)
            return self.__white_map[int(key)]

    def note_from_key(self, key):
        return self.__keyboard_piano_map[key]