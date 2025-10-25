# -*- coding: utf-8 -*-
"""
performance_analytics.py - Sistema de telemetría y análisis de rendimiento
Recopila métricas de rendimiento de forma local y respetuosa con la privacidad
"""

import json
import os
import time
import psutil
import platform
from typing import List, Dict, Optional, Any
from pathlib import Path


class PerformanceAnalytics:
    """
    Clase para recopilar y analizar métricas de rendimiento del optimizador.
    Todos los datos se almacenan localmente, sin envío a servicios externos.
    """
    
    def __init__(self, metrics_file: str = "performance_metrics.json"):
        self.metrics_file = metrics_file
        self.metrics = {
            'sessions': [],
            'fps_improvements': {},
            'optimization_effectiveness': {}
        }
        self.load_metrics()
    
    def load_metrics(self) -> None:
        """Carga métricas históricas desde archivo"""
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    self.metrics = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error cargando métricas: {e}")
                # Mantener estructura por defecto
    
    def save_metrics(self) -> None:
        """Guarda métricas a disco"""
        try:
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(self.metrics, f, indent=2)
        except IOError as e:
            print(f"Error guardando métricas: {e}")
    
    def start_session(self, game_name: str, optimizations_applied: List[str]) -> int:
        """
        Inicia el seguimiento de una sesión de juego
        
        Args:
            game_name: Nombre del juego
            optimizations_applied: Lista de optimizaciones aplicadas
            
        Returns:
            ID de la sesión
        """
        session = {
            'game': game_name,
            'start_time': time.time(),
            'optimizations': optimizations_applied,
            'system_info': {
                'cpu_cores': psutil.cpu_count(),
                'ram_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'os': platform.platform(),
            }
        }
        self.metrics['sessions'].append(session)
        return len(self.metrics['sessions']) - 1  # session ID
    
    def record_fps_data(self, session_id: int, fps_samples: List[float]) -> None:
        """
        Registra datos de FPS durante la sesión
        
        Args:
            session_id: ID de la sesión
            fps_samples: Lista de muestras de FPS
        """
        if session_id < len(self.metrics['sessions']):
            session = self.metrics['sessions'][session_id]
            session['fps_samples'] = fps_samples
            session['avg_fps'] = round(sum(fps_samples) / len(fps_samples), 2)
            session['min_fps'] = round(min(fps_samples), 2)
            session['max_fps'] = round(max(fps_samples), 2)
            session['fps_variance'] = round(self._calculate_variance(fps_samples), 2)
    
    def end_session(self, session_id: int) -> None:
        """
        Finaliza el seguimiento de una sesión
        
        Args:
            session_id: ID de la sesión
        """
        if session_id < len(self.metrics['sessions']):
            self.metrics['sessions'][session_id]['end_time'] = time.time()
            self.save_metrics()
    
    def analyze_optimization_effectiveness(self) -> List[tuple]:
        """
        Analiza qué optimizaciones proporcionan mejores resultados
        
        Returns:
            Lista de tuplas (optimización, datos) ordenadas por efectividad
        """
        optimization_scores = {}
        
        for session in self.metrics['sessions']:
            if 'avg_fps' not in session:
                continue
            
            for opt in session.get('optimizations', []):
                if opt not in optimization_scores:
                    optimization_scores[opt] = {'fps_sum': 0, 'count': 0}
                
                optimization_scores[opt]['fps_sum'] += session['avg_fps']
                optimization_scores[opt]['count'] += 1
        
        # Calcular promedios
        results = {}
        for opt, data in optimization_scores.items():
            results[opt] = {
                'avg_fps': round(data['fps_sum'] / data['count'], 2),
                'sessions': data['count']
            }
        
        # Ordenar por efectividad
        sorted_results = sorted(
            results.items(),
            key=lambda x: x[1]['avg_fps'],
            reverse=True
        )
        
        return sorted_results
    
    def _calculate_variance(self, samples: List[float]) -> float:
        """
        Calcula la varianza de FPS (menor = más suave)
        
        Args:
            samples: Lista de muestras
            
        Returns:
            Varianza
        """
        if not samples:
            return 0
        mean = sum(samples) / len(samples)
        return sum((x - mean) ** 2 for x in samples) / len(samples)
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Genera un reporte completo de rendimiento
        
        Returns:
            Diccionario con estadísticas
        """
        report = {
            'total_sessions': len(self.metrics['sessions']),
            'total_gaming_hours': round(sum(
                (s.get('end_time', time.time()) - s['start_time']) / 3600
                for s in self.metrics['sessions']
            ), 2),
            'games_played': len(set(s['game'] for s in self.metrics['sessions'])),
            'top_games_by_sessions': self._top_games_by_count(),
            'optimization_effectiveness': self.analyze_optimization_effectiveness(),
        }
        
        return report
    
    def _top_games_by_count(self) -> List[tuple]:
        """
        Obtiene los juegos más jugados
        
        Returns:
            Lista de tuplas (juego, conteo) ordenadas
        """
        game_counts = {}
        for session in self.metrics['sessions']:
            game = session['game']
            game_counts[game] = game_counts.get(game, 0) + 1
        
        return sorted(game_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    def print_report(self) -> None:
        """Imprime un reporte de análisis de rendimiento"""
        report = self.generate_report()
        
        print("\n" + "="*60)
        print("     REPORTE DE ANÁLISIS DE RENDIMIENTO")
        print("="*60)
        print(f"Total de sesiones: {report['total_sessions']}")
        print(f"Horas totales de juego: {report['total_gaming_hours']:.1f}")
        print(f"Juegos únicos jugados: {report['games_played']}")
        
        print("\n--- Top 10 Juegos por Sesiones ---")
        for game, count in report['top_games_by_sessions']:
            print(f"  {game}: {count} sesiones")
        
        print("\n--- Efectividad de Optimizaciones ---")
        for opt, data in report['optimization_effectiveness']:
            print(f"  {opt}: {data['avg_fps']:.1f} FPS promedio ({data['sessions']} sesiones)")
        
        print("="*60 + "\n")


if __name__ == "__main__":
    # Ejemplo de uso
    analytics = PerformanceAnalytics()
    
    # Simular una sesión
    session_id = analytics.start_session("valorant.exe", [
        "Large Pages", "Core Parking", "MMCSS", "GPU IRQ Affinity"
    ])
    
    # Simular datos de FPS
    fps_samples = [120, 118, 125, 119, 122, 121, 117, 123, 120, 119]
    analytics.record_fps_data(session_id, fps_samples)
    
    analytics.end_session(session_id)
    
    # Generar reporte
    analytics.print_report()
