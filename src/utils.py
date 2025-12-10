#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilidades generales para el proyecto
"""

import math

def round_half_up(n, decimals=0):
    """
    Redondea un número al entero más cercano (o decimales especificados).
    El .5 siempre se redondea hacia arriba (a diferencia del round() de Python 3).
    """
    multiplier = 10 ** decimals
    return math.floor(n*multiplier + 0.5) / multiplier
