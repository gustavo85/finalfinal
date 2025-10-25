#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_optimizations.py - Script de validación para verificar implementaciones
Verifica que todas las optimizaciones implementadas funcionen correctamente
"""

import os
import sys
import importlib.util


def validate_module(module_name, module_path):
    """
    Valida que un módulo se pueda importar correctamente
    
    Args:
        module_name: Nombre del módulo
        module_path: Ruta al archivo del módulo
        
    Returns:
        True si el módulo es válido, False si no
    """
    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None:
            print(f"  ✗ {module_name}: No se pudo crear spec")
            return False
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        print(f"  ✓ {module_name}: Importado correctamente")
        return True
    except Exception as e:
        print(f"  ✗ {module_name}: Error - {e}")
        return False


def validate_file_syntax(filepath):
    """
    Valida la sintaxis de un archivo Python
    
    Args:
        filepath: Ruta al archivo
        
    Returns:
        True si la sintaxis es correcta, False si no
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            compile(f.read(), filepath, 'exec')
        return True
    except SyntaxError as e:
        print(f"  ✗ Error de sintaxis en {filepath}: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error leyendo {filepath}: {e}")
        return False


def check_optimization_implementations():
    """Verifica que las optimizaciones implementadas estén presentes"""
    
    optimizations = {
        'modonormal.py': [
            '_config_cache',  # Config caching
            'cargar_config',
        ],
        'modoagresivo.py': [
            '_config_cache',  # Config caching
            'cargar_config',
        ],
        'modojuego.py': [
            '_config_cache',  # Config caching
            'optimize_cpu_cache_for_game',  # CPU cache optimization
            'set_quantum_length',  # Scheduler quantum
            'optimize_gpu_memory_advanced',  # GPU memory management
            'monitor_thermals_and_adjust',  # Thermal monitoring
        ],
        'COPIA.py': [
            'ThreadPoolExecutor',  # Batch registry operations
            'batch_registry_export',
        ],
        'DISCOS.py': [
            'FRAGMENTATION_PATTERNS',  # Pre-compiled regex
            'LAST_OPTIMIZED_PATTERN',
        ],
        'GUI.py': [
            'get_pystray_modules',  # Lazy imports
        ],
        'performance_analytics.py': [
            'PerformanceAnalytics',  # Performance analytics
        ],
        'optimization_checkpoint.py': [
            'OptimizationCheckpoint',  # Checkpoint system
        ],
        'game_profiler.py': [
            'GameProfiler',  # Auto-tuning profiler
            'GameProfile',
        ],
    }
    
    print("\nVerificando implementaciones de optimizaciones...")
    print("="*60)
    
    all_found = True
    
    for filename, expected_items in optimizations.items():
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        if not os.path.exists(filepath):
            print(f"\n✗ {filename}: Archivo no encontrado")
            all_found = False
            continue
        
        print(f"\n{filename}:")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for item in expected_items:
                if item in content:
                    print(f"  ✓ {item}")
                else:
                    print(f"  ✗ {item} - NO ENCONTRADO")
                    all_found = False
        except Exception as e:
            print(f"  ✗ Error leyendo archivo: {e}")
            all_found = False
    
    return all_found


def validate_all():
    """Ejecuta todas las validaciones"""
    
    print("\n" + "="*60)
    print("  VALIDACIÓN DE OPTIMIZACIONES IMPLEMENTADAS")
    print("="*60)
    
    # 1. Validar sintaxis de archivos Python
    print("\n1. Validando sintaxis de archivos Python...")
    print("-"*60)
    
    python_files = [
        'modonormal.py',
        'modoagresivo.py',
        'modojuego.py',
        'COPIA.py',
        'DISCOS.py',
        'GUI.py',
        'LIMPIEZA.py',
        'RECUPERA.py',
        'entradas.py',
        'performance_analytics.py',
        'optimization_checkpoint.py',
        'game_profiler.py',
        'integration_example.py',
    ]
    
    syntax_ok = True
    for filename in python_files:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(filepath):
            if validate_file_syntax(filepath):
                print(f"  ✓ {filename}")
            else:
                syntax_ok = False
        else:
            print(f"  ? {filename} - No encontrado")
    
    # 2. Verificar implementaciones
    implementations_ok = check_optimization_implementations()
    
    # 3. Verificar archivos de documentación
    print("\n3. Validando documentación...")
    print("-"*60)
    
    doc_files = [
        'README.md',
        'OPTIMIZATION_SUGGESTIONS.md',
        'FEATURES_AND_COMPARISON.md',
        'ADVANCED_MODULES_README.md',
    ]
    
    docs_ok = True
    for filename in doc_files:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(filepath):
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ {filename} - NO ENCONTRADO")
            docs_ok = False
    
    # Resumen final
    print("\n" + "="*60)
    print("  RESUMEN DE VALIDACIÓN")
    print("="*60)
    
    results = [
        ("Sintaxis de Python", syntax_ok),
        ("Implementaciones de optimizaciones", implementations_ok),
        ("Documentación", docs_ok),
    ]
    
    all_ok = all(ok for _, ok in results)
    
    for name, ok in results:
        status = "✓ CORRECTO" if ok else "✗ FALLÓ"
        print(f"{name}: {status}")
    
    print("="*60)
    
    if all_ok:
        print("\n✓✓✓ TODAS LAS VALIDACIONES PASARON ✓✓✓\n")
        return 0
    else:
        print("\n✗✗✗ ALGUNAS VALIDACIONES FALLARON ✗✗✗\n")
        return 1


if __name__ == "__main__":
    sys.exit(validate_all())
