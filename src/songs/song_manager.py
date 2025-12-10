#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor de canciones del modo ritmo
Registra y carga canciones disponibles
"""

import pkgutil
import importlib
import inspect
from pathlib import Path
from src.songs.song_base import BaseSong
import src.songs.chart_files as chart_package


class SongManager:
    """Gestor centralizado de canciones del modo ritmo"""
    
    def __init__(self):
        self._songs = {}
        self._song_order = []
        self._load_songs()
    
    def _load_songs(self):
        """Carga automáticamente todas las canciones del directorio chart_files/"""
        # Rutas para buscar módulos
        path = chart_package.__path__
        prefix = chart_package.__name__ + "."

        # Iterar sobre archivos .py en chart_files/
        for _, name, _ in pkgutil.iter_modules(path, prefix):
            try:
                module = importlib.import_module(name)
                
                # Buscar clases dentro del archivo
                for member_name, obj in inspect.getmembers(module):
                    # Verificar si es una clase, si hereda de BaseSong y no es BaseSong en sí misma
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseSong) and 
                        obj is not BaseSong):
                        
                        # Instanciamos la canción
                        song_instance = obj()
                        song_name = song_instance.name
                        self._songs[song_name] = song_instance
                        self._song_order.append(song_name)
                        print(f"✓ Canción cargada: {song_name}")
            except Exception as e:
                print(f"✗ Error al cargar {name}: {e}")
    
    def get_all_songs(self):
        """
        Devuelve todas las canciones disponibles como diccionario
        (compatibilidad con código existente)
        
        Returns:
            dict: Diccionario {name: song_instance}
        """
        return self._songs.copy()
    
    def get_all_songs_list(self):
        """
        Devuelve todas las canciones disponibles en orden como lista de tuplas
        
        Returns:
            list: Lista de tuplas (name, song_instance)
        """
        return [(name, self._songs[name]) for name in self._song_order]
    
    def get_song(self, song_name):
        """
        Obtiene una canción específica por nombre
        
        Args:
            song_name: Nombre de la canción
        
        Returns:
            BaseSong o None si no existe
        """
        return self._songs.get(song_name)
    
    def get_song_info(self, song_name):
        """Obtiene información de una canción sin instanciarla"""
        song = self.get_song(song_name)
        return song.get_info() if song else None
    
    def count(self):
        """Devuelve el número de canciones disponibles"""
        return len(self._songs)


# Instancia global del gestor
_song_manager = None

def get_song_manager():
    """Devuelve instancia única del gestor de canciones"""
    global _song_manager
    if _song_manager is None:
        _song_manager = SongManager()
    return _song_manager

def get_all_songs():
    """
    Función de compatibilidad con código existente
    Retorna diccionario de canciones
    """
    return get_song_manager().get_all_songs()