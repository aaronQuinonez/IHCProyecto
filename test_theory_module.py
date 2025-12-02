#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del módulo de teoría musical
Verifica que las lecciones se cargan correctamente
"""

import sys
sys.path.insert(0, 'c:/CodingWindows/IHC_Proyecto_Fork/IHCProyecto')

from src.theory import get_lesson_manager, TheoryUI

def test_lesson_loading():
    """Prueba que las lecciones se cargan correctamente"""
    print("="*60)
    print("TEST: Carga de módulo de teoría musical")
    print("="*60)
    
    # Obtener el gestor de lecciones
    manager = get_lesson_manager()
    
    print(f"\n✓ LessonManager inicializado")
    print(f"✓ Lecciones encontradas: {manager.count()}")
    
    # Listar todas las lecciones
    print("\nLecciones disponibles:")
    print("-" * 60)
    
    all_lessons = manager.get_all_lessons()
    for i, (lesson_id, lesson) in enumerate(all_lessons, 1):
        print(f"{i}. {lesson.name}")
        print(f"   ID: {lesson_id}")
        print(f"   Descripción: {lesson.description}")
        print(f"   Dificultad: {lesson.difficulty}")
        print()
    
    # Probar TheoryUI
    print("="*60)
    print("TEST: Inicialización de TheoryUI")
    print("="*60)
    
    theory_ui = TheoryUI(1280, 480)
    print(f"✓ TheoryUI inicializado")
    print(f"✓ Frame width: {theory_ui.frame_width}")
    print(f"✓ Frame height: {theory_ui.frame_height}")
    print(f"✓ Max visible: {theory_ui.max_visible}")
    
    # Simular navegación
    print("\nSimulando navegación:")
    print(f"  Índice inicial: {theory_ui.get_selected_index()}")
    
    theory_ui.navigate_down(len(all_lessons))
    print(f"  Después de navigate_down: {theory_ui.get_selected_index()}")
    
    theory_ui.navigate_down(len(all_lessons))
    print(f"  Después de navigate_down: {theory_ui.get_selected_index()}")
    
    theory_ui.navigate_up(len(all_lessons))
    print(f"  Después de navigate_up: {theory_ui.get_selected_index()}")
    
    theory_ui.reset_selection()
    print(f"  Después de reset: {theory_ui.get_selected_index()}")
    
    print("\n" + "="*60)
    print("✓ TODOS LOS TESTS PASARON")
    print("="*60)
    print("\nPara usar el módulo:")
    print("  1. Ejecuta: python src/main.py")
    print("  2. Presiona 'L' para entrar al modo teoría")
    print("  3. Usa flechas ↑/↓ y ENTER para seleccionar lecciones")
    print("  4. Presiona 'Q' para volver al modo libre")
    print()

if __name__ == '__main__':
    try:
        test_lesson_loading()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
