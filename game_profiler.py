# -*- coding: utf-8 -*-
"""
game_profiler.py - Sistema de auto-tuning basado en características del juego
Analiza el comportamiento del juego para aplicar optimizaciones personalizadas
"""

import time
import psutil
from typing import Optional, List, Dict
from dataclasses import dataclass


@dataclass
class GameProfile:
    """Perfil de características de un juego"""
    name: str
    cpu_bound: bool = False  # vs GPU bound
    network_intensive: bool = False
    vram_usage_high: bool = False
    thread_count_high: bool = False
    avg_cpu_percent: float = 0.0
    avg_memory_mb: float = 0.0
    thread_count: int = 0
    network_connections: int = 0


class GameProfiler:
    """
    Analiza el comportamiento de un juego en tiempo de ejecución
    y determina qué optimizaciones aplicar
    """
    
    def __init__(self):
        self.profiles = {}
    
    def detect_characteristics(self, game_pid: int, sample_duration: int = 10) -> Optional[GameProfile]:
        """
        Analiza el comportamiento del juego para determinar su perfil
        
        Args:
            game_pid: PID del proceso del juego
            sample_duration: Duración del análisis en segundos
            
        Returns:
            GameProfile con las características detectadas
        """
        try:
            proc = psutil.Process(game_pid)
            game_name = proc.name()
            profile = GameProfile(name=game_name)
            
            print(f"Analizando características de {game_name}...")
            
            # Muestrear CPU y memoria durante el período especificado
            cpu_samples = []
            memory_samples = []
            
            for i in range(sample_duration):
                try:
                    cpu_samples.append(proc.cpu_percent(interval=1))
                    memory_samples.append(proc.memory_info().rss / (1024 * 1024))  # MB
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
            
            if not cpu_samples:
                return None
            
            # Calcular promedios
            profile.avg_cpu_percent = round(sum(cpu_samples) / len(cpu_samples), 2)
            profile.avg_memory_mb = round(sum(memory_samples) / len(memory_samples), 2)
            
            # Determinar si es CPU-bound
            # Si el uso de CPU es consistentemente alto (>70%), probablemente CPU-bound
            if profile.avg_cpu_percent > 70:
                profile.cpu_bound = True
                print(f"  → Detectado como CPU-bound ({profile.avg_cpu_percent}% CPU)")
            else:
                print(f"  → Detectado como GPU-bound ({profile.avg_cpu_percent}% CPU)")
            
            # Verificar conteo de hilos
            try:
                profile.thread_count = proc.num_threads()
                if profile.thread_count > 20:
                    profile.thread_count_high = True
                    print(f"  → Alto número de hilos detectado ({profile.thread_count})")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
            # Verificar actividad de red
            try:
                connections = proc.connections()
                profile.network_connections = len(connections)
                if profile.network_connections > 5:
                    profile.network_intensive = True
                    print(f"  → Juego con uso intensivo de red ({profile.network_connections} conexiones)")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
            # Estimar uso de VRAM (aproximación basada en uso de RAM)
            # Juegos modernos típicamente usan 2-4GB de VRAM si usan >4GB de RAM
            if profile.avg_memory_mb > 4000:
                profile.vram_usage_high = True
                print(f"  → Alto uso de memoria detectado ({profile.avg_memory_mb:.1f} MB)")
            
            # Guardar perfil para referencia futura
            self.profiles[game_name] = profile
            
            print(f"✓ Análisis completado para {game_name}")
            return profile
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"Error analizando proceso: {e}")
            return None
        except Exception as e:
            print(f"Error inesperado en análisis: {e}")
            return None
    
    def get_recommended_optimizations(self, profile: GameProfile) -> List[str]:
        """
        Determina qué optimizaciones aplicar según el perfil del juego
        
        Args:
            profile: Perfil del juego
            
        Returns:
            Lista de optimizaciones recomendadas
        """
        optimizations = []
        
        # Optimizaciones base para todos los juegos
        optimizations.extend([
            "Timer Resolution",
            "GameDVR Disable",
            "Power Plan"
        ])
        
        # Optimizaciones específicas según características
        if profile.cpu_bound:
            # Enfoque en optimizaciones de CPU
            optimizations.extend([
                "CPU Cache Optimization",
                "Quantum Length Adjustment",
                "Core Parking Disable",
                "CPU Affinity Optimization"
            ])
            print("  → Aplicando optimizaciones para juego CPU-bound")
        
        if profile.network_intensive:
            # Enfoque en optimizaciones de red
            optimizations.extend([
                "Network QoS Policy",
                "TCP/IP Optimization",
                "Network Throttling Disable"
            ])
            print("  → Aplicando optimizaciones de red")
        
        if profile.thread_count_high:
            # Optimizar para multi-threading
            optimizations.extend([
                "Core Parking Disable",
                "Multi-Core Affinity",
                "Thread Priority Boost"
            ])
            print("  → Aplicando optimizaciones para multi-threading")
        
        if profile.vram_usage_high:
            # Optimizaciones de GPU/VRAM
            optimizations.extend([
                "GPU Memory Optimization",
                "GPU IRQ Affinity",
                "TDR Timeout Extension"
            ])
            print("  → Aplicando optimizaciones de GPU/VRAM")
        
        # Si no es CPU-bound, probablemente es GPU-bound
        if not profile.cpu_bound:
            optimizations.extend([
                "GPU Memory Optimization",
                "GPU Settings Optimization",
                "GPU IRQ Affinity"
            ])
            print("  → Aplicando optimizaciones para juego GPU-bound")
        
        return list(set(optimizations))  # Eliminar duplicados
    
    def save_profile(self, profile: GameProfile, filename: str = "game_profiles.json") -> None:
        """
        Guarda el perfil del juego en un archivo JSON
        
        Args:
            profile: Perfil a guardar
            filename: Nombre del archivo
        """
        import json
        import os
        
        profiles_data = {}
        
        # Cargar perfiles existentes
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    profiles_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Agregar/actualizar perfil
        profiles_data[profile.name] = {
            'cpu_bound': profile.cpu_bound,
            'network_intensive': profile.network_intensive,
            'vram_usage_high': profile.vram_usage_high,
            'thread_count_high': profile.thread_count_high,
            'avg_cpu_percent': profile.avg_cpu_percent,
            'avg_memory_mb': profile.avg_memory_mb,
            'thread_count': profile.thread_count,
            'network_connections': profile.network_connections,
        }
        
        # Guardar
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(profiles_data, f, indent=2)
        
        print(f"✓ Perfil guardado: {filename}")
    
    def load_profile(self, game_name: str, filename: str = "game_profiles.json") -> Optional[GameProfile]:
        """
        Carga un perfil guardado previamente
        
        Args:
            game_name: Nombre del juego
            filename: Nombre del archivo
            
        Returns:
            GameProfile si existe, None si no
        """
        import json
        import os
        
        if not os.path.exists(filename):
            return None
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                profiles_data = json.load(f)
            
            if game_name not in profiles_data:
                return None
            
            data = profiles_data[game_name]
            profile = GameProfile(
                name=game_name,
                cpu_bound=data.get('cpu_bound', False),
                network_intensive=data.get('network_intensive', False),
                vram_usage_high=data.get('vram_usage_high', False),
                thread_count_high=data.get('thread_count_high', False),
                avg_cpu_percent=data.get('avg_cpu_percent', 0.0),
                avg_memory_mb=data.get('avg_memory_mb', 0.0),
                thread_count=data.get('thread_count', 0),
                network_connections=data.get('network_connections', 0),
            )
            
            print(f"✓ Perfil cargado para {game_name}")
            return profile
            
        except (json.JSONDecodeError, IOError, KeyError) as e:
            print(f"Error cargando perfil: {e}")
            return None


if __name__ == "__main__":
    # Ejemplo de uso
    profiler = GameProfiler()
    
    # Buscar un proceso de juego para analizar (ejemplo)
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name'].lower()
            # Buscar un proceso conocido para probar
            if 'valorant' in name or 'csgo' in name or 'league' in name:
                print(f"Encontrado juego: {proc.info['name']} (PID: {proc.info['pid']})")
                
                # Analizar características (muestreo de 5 segundos para demo)
                profile = profiler.detect_characteristics(proc.info['pid'], sample_duration=5)
                
                if profile:
                    # Obtener recomendaciones
                    optimizations = profiler.get_recommended_optimizations(profile)
                    
                    print("\nOptimizaciones recomendadas:")
                    for opt in optimizations:
                        print(f"  - {opt}")
                    
                    # Guardar perfil
                    profiler.save_profile(profile)
                
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    else:
        print("No se encontró ningún juego en ejecución para analizar")
