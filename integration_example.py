# -*- coding: utf-8 -*-
"""
integration_example.py - Ejemplo de cómo integrar los nuevos módulos avanzados
Demuestra el uso de analytics, checkpoints y auto-tuning juntos
"""

import time
import psutil
from performance_analytics import PerformanceAnalytics
from optimization_checkpoint import OptimizationCheckpoint
from game_profiler import GameProfiler


def optimize_game_with_advanced_features(game_pid: int, game_name: str):
    """
    Ejemplo de función que integra todas las nuevas características avanzadas
    
    Args:
        game_pid: PID del proceso del juego
        game_name: Nombre del juego
    """
    print(f"\n{'='*60}")
    print(f"  OPTIMIZACIÓN AVANZADA PARA: {game_name}")
    print(f"{'='*60}\n")
    
    # 1. Crear checkpoint del sistema antes de optimizar
    print("Paso 1: Creando checkpoint del sistema...")
    checkpoint = OptimizationCheckpoint()
    checkpoint_path = checkpoint.create_checkpoint()
    print(f"✓ Checkpoint creado en: {checkpoint_path}\n")
    
    # 2. Perfilar el juego para determinar optimizaciones óptimas
    print("Paso 2: Analizando características del juego...")
    profiler = GameProfiler()
    
    # Cargar perfil guardado si existe, sino crear uno nuevo
    profile = profiler.load_profile(game_name)
    if not profile:
        print("  → No hay perfil guardado, creando perfil nuevo...")
        profile = profiler.detect_characteristics(game_pid, sample_duration=10)
        if profile:
            profiler.save_profile(profile)
    else:
        print("  → Perfil cargado desde archivo")
    
    if not profile:
        print("✗ Error: No se pudo crear perfil del juego")
        return False
    
    # Obtener recomendaciones de optimización
    optimizations = profiler.get_recommended_optimizations(profile)
    print(f"\n✓ {len(optimizations)} optimizaciones recomendadas:")
    for opt in optimizations:
        print(f"  - {opt}")
    print()
    
    # 3. Iniciar sesión de analytics
    print("Paso 3: Iniciando seguimiento de rendimiento...")
    analytics = PerformanceAnalytics()
    session_id = analytics.start_session(game_name, optimizations)
    print(f"✓ Sesión de analytics iniciada (ID: {session_id})\n")
    
    # 4. Aplicar optimizaciones (aquí irían las llamadas reales a funciones de modojuego.py)
    print("Paso 4: Aplicando optimizaciones...")
    try:
        # Simular aplicación de optimizaciones
        print("  → Aplicando optimizaciones específicas del perfil...")
        
        # Aquí irían las llamadas a funciones como:
        # if profile.cpu_bound:
        #     optimize_cpu_cache_for_game(game_pid)
        #     set_quantum_length()
        # if profile.network_intensive:
        #     create_qos_policy_for_game(game_name)
        # etc.
        
        time.sleep(1)  # Simular tiempo de aplicación
        print("✓ Optimizaciones aplicadas exitosamente\n")
        
    except Exception as e:
        print(f"✗ Error aplicando optimizaciones: {e}")
        print("  → Ejecutando rollback...")
        checkpoint.rollback(checkpoint_path)
        return False
    
    # 5. Monitorear sesión de juego (simulado)
    print("Paso 5: Monitoreando sesión de juego...")
    print("  → El juego está ejecutándose...")
    print("  → Recopilando datos de rendimiento...\n")
    
    # Simular recopilación de FPS (en implementación real vendría de un hook)
    fps_samples = [120, 118, 125, 119, 122, 121, 117, 123, 120, 119,
                   124, 120, 118, 122, 121, 119, 125, 123, 120, 121]
    
    # 6. Registrar datos de FPS
    analytics.record_fps_data(session_id, fps_samples)
    
    # 7. Finalizar sesión
    print("Paso 6: Finalizando sesión...")
    analytics.end_session(session_id)
    print("✓ Sesión de analytics finalizada\n")
    
    # 8. Generar reporte de rendimiento
    print("Paso 7: Generando reporte de rendimiento...")
    analytics.print_report()
    
    # 9. Limpiar checkpoints antiguos
    print("Paso 8: Limpiando checkpoints antiguos...")
    checkpoint.cleanup_old_checkpoints(keep_last=5)
    print("✓ Limpieza completada\n")
    
    print(f"{'='*60}")
    print("  OPTIMIZACIÓN COMPLETADA EXITOSAMENTE")
    print(f"{'='*60}\n")
    
    return True


def demo_standalone_features():
    """Demuestra características individuales de cada módulo"""
    
    print("\n" + "="*60)
    print("  DEMOSTRACIÓN DE CARACTERÍSTICAS INDIVIDUALES")
    print("="*60 + "\n")
    
    # Demo 1: Analytics
    print("--- Demo: Performance Analytics ---")
    analytics = PerformanceAnalytics()
    
    # Simular varias sesiones
    for i, (game, opts) in enumerate([
        ("valorant.exe", ["Large Pages", "Core Parking", "MMCSS"]),
        ("csgo.exe", ["GPU IRQ", "Network QoS", "Timer Resolution"]),
        ("league of legends.exe", ["Large Pages", "CPU Cache", "MMCSS"]),
    ]):
        sid = analytics.start_session(game, opts)
        fps = [120 + i*5 + j for j in range(-5, 6)]
        analytics.record_fps_data(sid, fps)
        analytics.end_session(sid)
    
    analytics.print_report()
    
    # Demo 2: Checkpoint
    print("\n--- Demo: Optimization Checkpoint ---")
    checkpoint = OptimizationCheckpoint()
    cp_path = checkpoint.create_checkpoint()
    
    print("\nCheckpoints disponibles:")
    for cp in checkpoint.list_checkpoints():
        print(f"  {cp['timestamp_readable']}: {cp['process_count']} procesos, "
              f"{cp['service_count']} servicios")
    
    # Demo 3: Game Profiler
    print("\n--- Demo: Game Profiler ---")
    profiler = GameProfiler()
    
    # Buscar un proceso para analizar (ejemplo con proceso actual)
    current_pid = psutil.Process().pid
    print(f"Analizando proceso actual (PID: {current_pid}) como ejemplo...")
    
    # En uso real, buscaríamos un proceso de juego real
    # profile = profiler.detect_characteristics(game_pid, sample_duration=5)
    
    print("\nEn uso real, esto analizaría:")
    print("  - Uso de CPU (CPU-bound vs GPU-bound)")
    print("  - Número de hilos (multi-threading)")
    print("  - Conexiones de red (juegos online)")
    print("  - Uso de memoria (estimación de VRAM)")
    print("  Y recomendaría optimizaciones específicas\n")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    import sys
    
    print("Gaming Optimizer - Demostración de Características Avanzadas")
    print("="*60)
    
    # Verificar si hay un argumento de PID de juego
    if len(sys.argv) > 2:
        game_pid = int(sys.argv[1])
        game_name = sys.argv[2]
        
        if psutil.pid_exists(game_pid):
            optimize_game_with_advanced_features(game_pid, game_name)
        else:
            print(f"Error: PID {game_pid} no existe")
    else:
        print("\nNo se proporcionó PID de juego, ejecutando demos standalone...\n")
        print("Uso: python integration_example.py <PID> <nombre_juego>")
        print("Ejemplo: python integration_example.py 1234 valorant.exe\n")
        
        demo_standalone_features()
    
    print("\nPara uso en producción, integre estas funciones en modojuego.py")
    print("Vea ADVANCED_MODULES_README.md para más detalles.\n")
