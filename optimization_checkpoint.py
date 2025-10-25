# -*- coding: utf-8 -*-
"""
optimization_checkpoint.py - Sistema de checkpoint/rollback para optimizaciones
Permite crear instantáneas del sistema antes de aplicar optimizaciones y restaurar si algo falla
"""

import os
import time
import json
import subprocess
import psutil
from typing import Dict, List, Optional
from pathlib import Path


class OptimizationCheckpoint:
    """
    Clase para crear checkpoints del sistema y permitir rollback de optimizaciones
    """
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        self.registry_exports = {}
        self.process_priorities = {}
        self.service_states = {}
        self.timestamp = time.time()
    
    def create_checkpoint(self) -> str:
        """
        Crea una instantánea del estado actual del sistema antes de optimizaciones
        
        Returns:
            Ruta del directorio del checkpoint
        """
        checkpoint_path = os.path.join(self.checkpoint_dir, str(int(self.timestamp)))
        os.makedirs(checkpoint_path, exist_ok=True)
        
        print(f"Creando checkpoint del sistema...")
        
        # Exportar claves de registro críticas
        self._backup_registry(checkpoint_path)
        
        # Guardar prioridades de procesos
        self._backup_process_priorities()
        
        # Guardar estados de servicios
        self._backup_service_states()
        
        # Guardar metadata del checkpoint
        self._save_metadata(checkpoint_path)
        
        print(f"✓ Checkpoint creado: {checkpoint_path}")
        return checkpoint_path
    
    def _backup_registry(self, checkpoint_path: str) -> None:
        """Exporta claves de registro críticas"""
        critical_keys = [
            (r"HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "graphics_drivers.reg"),
            (r"HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters", "tcpip_params.reg"),
            (r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "multimedia_profile.reg"),
            (r"HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl", "priority_control.reg"),
            (r"HKCU\Software\Microsoft\Windows\CurrentVersion\GameDVR", "gamedvr.reg"),
            (r"HKCU\Software\Microsoft\GameBar", "gamebar.reg"),
        ]
        
        for key, filename in critical_keys:
            filepath = os.path.join(checkpoint_path, filename)
            try:
                subprocess.run(
                    f'reg export "{key}" "{filepath}" /y',
                    shell=True, capture_output=True, timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                self.registry_exports[key] = filepath
            except (subprocess.TimeoutExpired, OSError):
                pass  # Clave no existe o no accesible
    
    def _backup_process_priorities(self) -> None:
        """Guarda prioridades actuales de procesos"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                self.process_priorities[proc.pid] = proc.nice()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    
    def _backup_service_states(self) -> None:
        """Guarda estados actuales de servicios de Windows"""
        try:
            for service in psutil.win_service_iter():
                try:
                    self.service_states[service.name()] = service.status()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except AttributeError:
            # psutil.win_service_iter no disponible en todas las plataformas
            pass
    
    def _save_metadata(self, checkpoint_path: str) -> None:
        """Guarda metadata del checkpoint"""
        metadata = {
            'timestamp': self.timestamp,
            'timestamp_readable': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.timestamp)),
            'process_count': len(self.process_priorities),
            'service_count': len(self.service_states),
            'registry_keys': list(self.registry_exports.keys()),
        }
        
        metadata_file = os.path.join(checkpoint_path, "metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
    
    def rollback(self, checkpoint_path: str) -> bool:
        """
        Restaura el sistema al estado del checkpoint
        
        Args:
            checkpoint_path: Ruta del checkpoint a restaurar
            
        Returns:
            True si el rollback fue exitoso
        """
        if not os.path.exists(checkpoint_path):
            print(f"✗ Checkpoint no encontrado: {checkpoint_path}")
            return False
        
        print(f"Restaurando desde checkpoint: {checkpoint_path}")
        
        try:
            # Restaurar registro
            self._restore_registry(checkpoint_path)
            
            # Restaurar prioridades de procesos (best effort)
            self._restore_process_priorities()
            
            # Restaurar estados de servicios
            self._restore_service_states()
            
            print(f"✓ Rollback completado desde {checkpoint_path}")
            return True
        except Exception as e:
            print(f"✗ Rollback falló: {e}")
            return False
    
    def _restore_registry(self, checkpoint_path: str) -> None:
        """Restaura claves de registro desde archivos .reg"""
        for reg_file in os.listdir(checkpoint_path):
            if reg_file.endswith('.reg'):
                filepath = os.path.join(checkpoint_path, reg_file)
                try:
                    subprocess.run(
                        f'reg import "{filepath}"',
                        shell=True, capture_output=True, timeout=10,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                except (subprocess.TimeoutExpired, OSError):
                    pass
    
    def _restore_process_priorities(self) -> None:
        """Restaura prioridades de procesos (best effort)"""
        for pid, priority in self.process_priorities.items():
            try:
                if psutil.pid_exists(pid):
                    psutil.Process(pid).nice(priority)
            except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                pass
    
    def _restore_service_states(self) -> None:
        """Restaura estados de servicios"""
        try:
            for service_name, target_status in self.service_states.items():
                try:
                    for service in psutil.win_service_iter():
                        if service.name() == service_name:
                            current_status = service.status()
                            
                            if target_status == 'running' and current_status != 'running':
                                service.start()
                            elif target_status == 'stopped' and current_status == 'running':
                                service.stop()
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                    pass
        except AttributeError:
            pass
    
    def list_checkpoints(self) -> List[Dict]:
        """
        Lista todos los checkpoints disponibles
        
        Returns:
            Lista de diccionarios con información de checkpoints
        """
        checkpoints = []
        
        if not os.path.exists(self.checkpoint_dir):
            return checkpoints
        
        for dirname in os.listdir(self.checkpoint_dir):
            checkpoint_path = os.path.join(self.checkpoint_dir, dirname)
            metadata_file = os.path.join(checkpoint_path, "metadata.json")
            
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        metadata['path'] = checkpoint_path
                        checkpoints.append(metadata)
                except (json.JSONDecodeError, IOError):
                    pass
        
        return sorted(checkpoints, key=lambda x: x['timestamp'], reverse=True)
    
    def cleanup_old_checkpoints(self, keep_last: int = 5) -> None:
        """
        Elimina checkpoints antiguos, manteniendo solo los más recientes
        
        Args:
            keep_last: Número de checkpoints recientes a mantener
        """
        checkpoints = self.list_checkpoints()
        
        if len(checkpoints) <= keep_last:
            return
        
        for checkpoint in checkpoints[keep_last:]:
            checkpoint_path = checkpoint['path']
            try:
                import shutil
                shutil.rmtree(checkpoint_path)
                print(f"✓ Checkpoint eliminado: {checkpoint_path}")
            except OSError as e:
                print(f"Error eliminando checkpoint: {e}")


if __name__ == "__main__":
    # Ejemplo de uso
    checkpoint = OptimizationCheckpoint()
    
    # Crear checkpoint
    checkpoint_path = checkpoint.create_checkpoint()
    
    # Simular aplicación de optimizaciones
    print("\nAplicando optimizaciones...")
    time.sleep(1)
    
    # Si algo falla, hacer rollback
    print("\nSimulando fallo, haciendo rollback...")
    checkpoint.rollback(checkpoint_path)
    
    # Listar checkpoints disponibles
    print("\nCheckpoints disponibles:")
    for cp in checkpoint.list_checkpoints():
        print(f"  - {cp['timestamp_readable']} ({cp['process_count']} procesos)")
    
    # Limpiar checkpoints antiguos
    checkpoint.cleanup_old_checkpoints(keep_last=3)
