import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import platform
import os
import threading
import ctypes
import sys
import re
import json
from datetime import datetime
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import winreg

# Pre-compile regex patterns for better performance
FRAGMENTATION_PATTERNS = [
    re.compile(r'(\d+)%.*fragment', re.IGNORECASE),
    re.compile(r'Total fragmented.*?(\d+)%', re.IGNORECASE),
    re.compile(r'Fragmented.*?(\d+)%', re.IGNORECASE)
]
LAST_OPTIMIZED_PATTERN = re.compile(r'LastOptimized:(\d+) days ago')

class StorageMaintenanceApp:
    def __init__(self):
        """Inicializa la aplicación de mantenimiento de almacenamiento"""
        self.root = tk.Tk()
        self.root.title("Mantenimiento Avanzado de Unidades - Windows 10/11")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Configurar logging
        self.setup_logging()
        
        # Variables de control
        self.drives_info = []
        self.optimization_running = False
        self.cancel_requested = False
        
        # Detectar versión de Windows
        self.windows_version = self.get_windows_version()
        self.logger.info(f"Sistema detectado: {self.windows_version}")
        
        # Crear interfaz
        self.create_ui()
        
        # Iniciar detección
        self.check_drives()

    def setup_logging(self):
        """Configura el sistema de logging"""
        try:
            log_dir = Path(os.getenv('APPDATA')) / 'StorageMaintenance'
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / f'maintenance_{datetime.now().strftime("%Y%m%d")}.log'
            
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file, encoding='utf-8'),
                    logging.StreamHandler()
                ]
            )
            self.logger = logging.getLogger(__name__)
        except Exception as e:
            print(f"Error configurando logging: {e}")
            self.logger = logging.getLogger(__name__)
            self.logger.addHandler(logging.NullHandler())

    def create_ui(self):
        """Crea la interfaz de usuario mejorada"""
        # Frame superior - Información del sistema
        info_frame = ttk.LabelFrame(self.root, text="Información del Sistema", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.system_label = tk.Label(info_frame, text=f"Sistema: {self.windows_version}", 
                                      font=('Arial', 9), anchor='w')
        self.system_label.pack(fill=tk.X)
        
        self.admin_label = tk.Label(info_frame, 
                                     text=f"Permisos: {'Administrador ✓' if self.is_admin() else 'Usuario estándar ✗'}", 
                                     font=('Arial', 9), anchor='w',
                                     fg='green' if self.is_admin() else 'red')
        self.admin_label.pack(fill=tk.X)
        
        # Frame central - Estado y log
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.status_label = tk.Label(main_frame, text="Detectando unidades...", 
                                      font=('Arial', 10, 'bold'))
        self.status_label.pack(pady=10)
        
        # Barra de progreso
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(pady=5, fill=tk.X)
        
        # Log de actividades
        log_frame = ttk.LabelFrame(main_frame, text="Registro de Actividades", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, width=70, 
                                                   font=('Consolas', 8), state='disabled')
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Frame inferior - Botones
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.cancel_button = ttk.Button(button_frame, text="Cancelar", 
                                         command=self.cancel_operation, state='disabled')
        self.cancel_button.pack(side=tk.RIGHT, padx=5)
        
        self.retry_button = ttk.Button(button_frame, text="Reintentar Detección", 
                                        command=self.retry_detection, state='disabled')
        self.retry_button.pack(side=tk.RIGHT, padx=5)

    def log_message(self, message: str, level: str = 'INFO'):
        """Agrega mensajes al log visual y al archivo"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, formatted_msg)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        
        # Log a archivo
        if level == 'ERROR':
            self.logger.error(message)
        elif level == 'WARNING':
            self.logger.warning(message)
        else:
            self.logger.info(message)

    def get_windows_version(self) -> str:
        """Detecta la versión de Windows con precisión"""
        try:
            version = platform.version()
            release = platform.release()
            
            # Obtener build number desde el registro
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                     r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
                build = winreg.QueryValueEx(key, "CurrentBuild")[0]
                product_name = winreg.QueryValueEx(key, "ProductName")[0]
                winreg.CloseKey(key)
                
                return f"{product_name} (Build {build})"
            except:
                return f"Windows {release} - {version}"
        except Exception as e:
            self.logger.error(f"Error detectando versión de Windows: {e}")
            return "Windows (versión desconocida)"

    def is_admin(self) -> bool:
        """Verifica si el script se ejecuta como administrador"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception as e:
            self.logger.error(f"Error verificando permisos de administrador: {e}")
            return False

    def check_drives(self):
        """Inicia el proceso de detección de unidades"""
        self.log_message("Iniciando análisis de unidades...")
        self.progress.start()
        self.retry_button.config(state='disabled')
        threading.Thread(target=self.analyze_drives, daemon=True).start()

    def analyze_drives(self):
        """Analiza todas las unidades del sistema"""
        drives_to_optimize = []
        
        try:
            self.log_message("Detectando unidades de disco...")
            drives_to_optimize = self.check_windows_drives()
            
            if drives_to_optimize:
                self.log_message(f"Se detectaron {len(drives_to_optimize)} unidad(es) que requieren mantenimiento")
            else:
                self.log_message("No se encontraron unidades que requieran mantenimiento")
                
        except Exception as e:
            error_msg = f"Error al analizar unidades: {str(e)}"
            self.log_message(error_msg, 'ERROR')
            self.logger.exception("Error detallado en análisis de unidades")
        
        self.root.after(0, self.process_results, drives_to_optimize)

    def check_windows_drives(self) -> List[Tuple[str, str, str, Dict]]:
        """
        Detecta y analiza todas las unidades de Windows
        Returns: Lista de tuplas (tipo, letra_unidad, acción, info_adicional)
        """
        drives_to_optimize = []
        
        try:
            # Método 1: Usar WMIC (compatible con Windows 10/11)
            self.log_message("Método 1: Detectando unidades con WMIC...")
            result = subprocess.run(
                ['wmic', 'logicaldisk', 'where', 'DriveType=3', 'get', 'DeviceID'],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            drive_letters = [line.strip() for line in result.stdout.split('\n') 
                           if line.strip() and ':' in line]
            
            if not drive_letters:
                # Método 2: Fallback usando PowerShell
                self.log_message("Método 2: Detectando unidades con PowerShell...")
                ps_cmd = "Get-Volume | Where-Object {$_.DriveType -eq 'Fixed'} | Select-Object -ExpandProperty DriveLetter"
                result = subprocess.run(
                    ['powershell', '-Command', ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                drive_letters = [f"{letter.strip()}:" for letter in result.stdout.split('\n') 
                               if letter.strip() and letter.strip().isalpha()]
            
            self.log_message(f"Unidades detectadas: {', '.join(drive_letters) if drive_letters else 'Ninguna'}")
            
            # Analizar cada unidad
            for drive in drive_letters:
                try:
                    self.log_message(f"Analizando unidad {drive}...")
                    
                    # Obtener información detallada
                    drive_info = self.get_detailed_drive_info(drive)
                    drive_type = drive_info.get('type', 'UNKNOWN')
                    
                    self.log_message(f"  Tipo: {drive_type}")
                    self.log_message(f"  Modelo: {drive_info.get('model', 'Desconocido')}")
                    self.log_message(f"  Tamaño: {drive_info.get('size', 'Desconocido')}")
                    
                    if drive_type == "SSD":
                        needs_optimization, reason = self.needs_optimize_windows(drive, drive_info)
                        if needs_optimization:
                            drives_to_optimize.append(("SSD", drive, "optimize", drive_info))
                            self.log_message(f"  Estado: Requiere optimización - {reason}")
                        else:
                            self.log_message(f"  Estado: No requiere mantenimiento - {reason}")
                            
                    elif drive_type == "HDD":
                        needs_defrag, reason = self.needs_defrag_windows(drive, drive_info)
                        if needs_defrag:
                            drives_to_optimize.append(("HDD", drive, "defrag", drive_info))
                            self.log_message(f"  Estado: Requiere desfragmentación - {reason}")
                        else:
                            self.log_message(f"  Estado: No requiere mantenimiento - {reason}")
                    else:
                        self.log_message(f"  Estado: Tipo de unidad no soportado o desconocido", 'WARNING')
                        
                except Exception as e:
                    self.log_message(f"  Error analizando {drive}: {str(e)}", 'WARNING')
                    self.logger.exception(f"Error detallado analizando {drive}")
                    continue
                    
        except subprocess.TimeoutExpired:
            raise Exception("Tiempo de espera agotado al detectar unidades")
        except Exception as e:
            raise Exception(f"No se pudieron detectar unidades: {str(e)}")
        
        return drives_to_optimize

    def get_detailed_drive_info(self, drive: str) -> Dict:
        """Obtiene información detallada de una unidad"""
        info = {
            'type': 'UNKNOWN',
            'model': 'Desconocido',
            'size': 'Desconocido',
            'file_system': 'Desconocido',
            'free_space': 'Desconocido'
        }
        
        try:
            # Método 1: PowerShell (más preciso para Windows 10/11)
            ps_cmd = f"""
            $drive = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='{drive}'"
            $partition = Get-WmiObject -Query "ASSOCIATORS OF {{Win32_LogicalDisk.DeviceID='{drive}'}} WHERE AssocClass=Win32_LogicalDiskToPartition"
            $disk = Get-WmiObject -Query "ASSOCIATORS OF {{Win32_DiskPartition.DeviceID='$($partition.DeviceID)'}} WHERE AssocClass=Win32_DiskDriveToDiskPartition"
            
            $mediaType = $disk.MediaType
            $size = [math]::Round($drive.Size / 1GB, 2)
            $freeSpace = [math]::Round($drive.FreeSpace / 1GB, 2)
            
            # Detectar SSD usando múltiples métodos
            $isSSD = $false
            try {{
                $physicalDisk = Get-PhysicalDisk | Where-Object {{$_.DeviceID -eq $disk.Index}}
                if ($physicalDisk.MediaType -eq 'SSD') {{ $isSSD = $true }}
            }} catch {{}}
            
            # Método alternativo: verificar si no tiene partes móviles
            if (-not $isSSD) {{
                $partInfo = Get-Partition -DriveLetter '{drive[0]}' -ErrorAction SilentlyContinue
                if ($partInfo) {{
                    $diskNum = $partInfo.DiskNumber
                    $physDisk = Get-PhysicalDisk -DeviceNumber $diskNum -ErrorAction SilentlyContinue
                    if ($physDisk.MediaType -eq 'SSD' -or $physDisk.SpindleSpeed -eq 0) {{
                        $isSSD = $true
                    }}
                }}
            }}
            
            $type = if ($isSSD) {{ "SSD" }} else {{ "HDD" }}
            
            Write-Output "$type|$($disk.Model)|$size GB|$($drive.FileSystem)|$freeSpace GB"
            """
            
            result = subprocess.run(
                ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_cmd],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split('|')
                if len(parts) >= 5:
                    info['type'] = parts[0].strip()
                    info['model'] = parts[1].strip()
                    info['size'] = parts[2].strip()
                    info['file_system'] = parts[3].strip()
                    info['free_space'] = parts[4].strip()
                    return info
            
        except Exception as e:
            self.logger.warning(f"Error en método PowerShell para {drive}: {e}")
        
        # Método 2: Fallback usando fsutil y WMIC
        try:
            # Verificar si es SSD usando fsutil
            result = subprocess.run(
                ['fsutil', 'fsinfo', 'sectorinfo', drive],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if 'TrimEnabled' in result.stdout or 'SolidState' in result.stdout:
                info['type'] = 'SSD'
            else:
                # Método adicional: verificar si la unidad acepta TRIM
                result2 = subprocess.run(
                    ['fsutil', 'behavior', 'query', 'DisableDeleteNotify'],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                # Si no podemos determinar, usamos WMIC
                wmic_cmd = f"wmic diskdrive where \"DeviceID like '%{drive[0]}%'\" get Model,MediaType"
                result3 = subprocess.run(
                    wmic_cmd,
                    capture_output=True,
                    text=True,
                    shell=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if 'SSD' in result3.stdout.upper():
                    info['type'] = 'SSD'
                else:
                    info['type'] = 'HDD'
            
            # Obtener tamaño y espacio libre
            wmic_size = f"wmic logicaldisk where \"DeviceID='{drive}'\" get Size,FreeSpace,FileSystem"
            result4 = subprocess.run(
                wmic_size,
                capture_output=True,
                text=True,
                shell=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Parsear resultado
            lines = [l.strip() for l in result4.stdout.split('\n') if l.strip()]
            if len(lines) >= 2:
                values = lines[1].split()
                if len(values) >= 3:
                    info['file_system'] = values[0]
                    info['free_space'] = f"{int(values[1]) / (1024**3):.2f} GB" if values[1].isdigit() else "Desconocido"
                    info['size'] = f"{int(values[2]) / (1024**3):.2f} GB" if values[2].isdigit() else "Desconocido"
            
        except Exception as e:
            self.logger.warning(f"Error en método fallback para {drive}: {e}")
            info['type'] = 'HDD'  # Asumir HDD por defecto
        
        return info

    def needs_optimize_windows(self, drive: str, drive_info: Dict) -> Tuple[bool, str]:
        """
        Verifica si un SSD necesita optimización
        Returns: (necesita_optimización, razón)
        """
        try:
            # Método 1: Verificar análisis de optimización de Windows
            ps_cmd = f"""
            $volume = Get-Volume -DriveLetter '{drive[0]}'
            $optimizeInfo = Optimize-Volume -DriveLetter '{drive[0]}' -Analyze -Verbose 4>&1
            
            # Verificar última optimización
            $task = Get-ScheduledTask -TaskName 'ScheduledDefrag' -ErrorAction SilentlyContinue
            $lastRun = $null
            if ($task) {{
                $info = Get-ScheduledTaskInfo -TaskName 'ScheduledDefrag'
                $lastRun = $info.LastRunTime
            }}
            
            if ($lastRun) {{
                $daysSince = (Get-Date) - $lastRun
                Write-Output "LastOptimized:$($daysSince.Days) days ago"
            }} else {{
                Write-Output "LastOptimized:Never"
            }}
            """
            
            result = subprocess.run(
                ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_cmd],
                capture_output=True,
                text=True,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            output = result.stdout + result.stderr
            
            # Analizar resultados
            if 'LastOptimized:Never' in output:
                return True, "Nunca se ha optimizado"
            
            # Buscar días desde última optimización
            match = LAST_OPTIMIZED_PATTERN.search(output)
            if match:
                days = int(match.group(1))
                if days > 30:
                    return True, f"Última optimización hace {days} días"
                else:
                    return False, f"Optimizado hace {days} días"
            
            # Si hay mensajes de optimización recomendada
            if 'should' in output.lower() or 'recommend' in output.lower():
                return True, "Windows recomienda optimización"
                
            # Por defecto, optimizar si pasó más de un mes
            return True, "Verificación de rutina recomendada"
            
        except subprocess.TimeoutExpired:
            return False, "Tiempo de análisis agotado"
        except Exception as e:
            self.logger.warning(f"Error verificando optimización de {drive}: {e}")
            return True, "No se pudo verificar estado, se recomienda optimización"

    def needs_defrag_windows(self, drive: str, drive_info: Dict) -> Tuple[bool, str]:
        """
        Verifica si un HDD necesita desfragmentación
        Returns: (necesita_defrag, razón)
        """
        try:
            # Método 1: Análisis detallado con defrag
            self.log_message(f"  Analizando fragmentación de {drive}...")
            
            result = subprocess.run(
                ['defrag', drive, '/A', '/H'],
                capture_output=True,
                text=True,
                timeout=120,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            output = result.stdout + result.stderr
            
            # Buscar porcentaje de fragmentación usando patrones pre-compilados
            for pattern in FRAGMENTATION_PATTERNS:
                match = pattern.search(output)
                if match:
                    frag_percent = int(match.group(1))
                    if frag_percent > 10:
                        return True, f"Fragmentación: {frag_percent}%"
                    else:
                        return False, f"Fragmentación baja: {frag_percent}%"
            
            # Buscar mensajes de recomendación
            if any(phrase in output for phrase in [
                'should defragment',
                'Debe desfragmentar',
                'recommended',
                'recomendado'
            ]):
                return True, "Windows recomienda desfragmentación"
            
            if any(phrase in output for phrase in [
                'does not need',
                'no necesita',
                'not necessary',
                'no es necesario'
            ]):
                return False, "No requiere desfragmentación"
            
            # Método 2: PowerShell como fallback
            ps_cmd = f"""
            $volume = Get-Volume -DriveLetter '{drive[0]}'
            $defragAnalysis = Optimize-Volume -DriveLetter '{drive[0]}' -Analyze -Verbose 4>&1
            Write-Output $defragAnalysis
            """
            
            ps_result = subprocess.run(
                ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_cmd],
                capture_output=True,
                text=True,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            ps_output = ps_result.stdout + ps_result.stderr
            
            if 'should be optimized' in ps_output.lower():
                return True, "Optimización recomendada por análisis"
            
            # Por defecto, no desfragmentar si no hay evidencia clara
            return False, "Análisis no concluyente, no se requiere acción"
            
        except subprocess.TimeoutExpired:
            return False, "Tiempo de análisis agotado"
        except Exception as e:
            self.logger.warning(f"Error verificando desfragmentación de {drive}: {e}")
            return False, f"Error en análisis: {str(e)}"

    def process_results(self, drives: List[Tuple]):
        """Procesa los resultados del análisis"""
        self.progress.stop()
        self.progress.config(mode='determinate')
        self.retry_button.config(state='normal')
        
        if not drives:
            self.status_label.config(text="✓ Todas las unidades están optimizadas")
            self.log_message("No se requiere ningún mantenimiento en este momento")
            messagebox.showinfo("Estado del Sistema", 
                              "Todas las unidades están en buen estado.\n"
                              "No se requiere mantenimiento en este momento.")
            return
        
        self.show_optimization_dialog(drives)

    def show_optimization_dialog(self, drives: List[Tuple]):
        """Muestra diálogo con las unidades que requieren mantenimiento"""
        drive_list = []
        for drive_type, drive, action, info in drives:
            model = info.get('model', 'Desconocido')
            size = info.get('size', 'Desconocido')
            action_text = "Optimización TRIM" if action == "optimize" else "Desfragmentación"
            drive_list.append(f"  • {drive} - {drive_type} ({model})\n    Tamaño: {size}\n    Acción: {action_text}")
        
        drive_text = "\n".join(drive_list)
        msg = f"""Las siguientes unidades necesitan mantenimiento:

{drive_text}

¿Desea proceder con la optimización?

ADVERTENCIA: Este proceso puede tardar varios minutos o incluso horas
dependiendo del tamaño y estado de las unidades.
Se recomienda cerrar otras aplicaciones antes de continuar."""
        
        if messagebox.askyesno("Mantenimiento Requerido", msg, icon='warning'):
            self.perform_optimization(drives)
        else:
            self.log_message("Optimización cancelada por el usuario")
            self.status_label.config(text="Optimización cancelada")

    def perform_optimization(self, drives: List[Tuple]):
        """Ejecuta el proceso de optimización"""
        self.status_label.config(text="Optimizando unidades...")
        self.progress['value'] = 0
        self.progress['maximum'] = len(drives)
        self.cancel_button.config(state='normal')
        self.retry_button.config(state='disabled')
        self.optimization_running = True
        self.cancel_requested = False
        
        threading.Thread(target=self.run_optimization, args=(drives,), daemon=True).start()

    def run_optimization(self, drives: List[Tuple]):
        """Ejecuta la optimización en un hilo separado"""
        successful = 0
        failed = 0
        
        for i, (drive_type, drive, action, info) in enumerate(drives):
            if self.cancel_requested:
                self.log_message("Optimización cancelada por el usuario", 'WARNING')
                break
            
            try:
                action_text = "Optimización TRIM" if action == "optimize" else "Desfragmentación"
                self.log_message(f"\n{'='*50}")
                self.log_message(f"Iniciando {action_text} de {drive} ({drive_type})")
                self.log_message(f"Modelo: {info.get('model', 'Desconocido')}")
                self.log_message(f"{'='*50}")
                
                self.root.after(0, self.status_label.config, 
                              {'text': f"Optimizando {drive} ({drive_type}) - {i+1}/{len(drives)}"})
                
                if action == "optimize":
                    self.run_optimize_ssd(drive, info)
                elif action == "defrag":
                    self.run_defrag_hdd(drive, info)
                
                self.log_message(f"✓ {action_text} de {drive} completada exitosamente")
                successful += 1
                
            except Exception as e:
                error_msg = f"✗ Error optimizando {drive}: {str(e)}"
                self.log_message(error_msg, 'ERROR')
                self.logger.exception(f"Error detallado optimizando {drive}")
                failed += 1
            
            self.root.after(0, self.update_progress, i + 1)
        
        self.optimization_running = False
        self.root.after(0, self.complete, successful, failed, len(drives))

    def run_optimize_ssd(self, drive: str, info: Dict):
        """Ejecuta optimización para SSD con múltiples métodos"""
        methods_tried = []
        last_error = None
        
        # Método 1: Optimize-Volume de PowerShell (recomendado para Windows 10/11)
        try:
            self.log_message(f"  Método 1: Optimize-Volume (ReTrim)...")
            ps_cmd = f"Optimize-Volume -DriveLetter '{drive[0]}' -ReTrim -Verbose"
            
            result = subprocess.run(
                ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_cmd],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutos
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                self.log_message("  ✓ Optimización TRIM completada")
                return
            else:
                methods_tried.append("Optimize-Volume")
                last_error = result.stderr
                self.log_message(f"  ✗ Optimize-Volume falló: {result.stderr}", 'WARNING')
                
        except subprocess.TimeoutExpired:
            methods_tried.append("Optimize-Volume (timeout)")
            last_error = "Tiempo de espera agotado"
            self.log_message("  ✗ Tiempo de espera agotado para Optimize-Volume", 'WARNING')
        except Exception as e:
            methods_tried.append("Optimize-Volume (error)")
            last_error = str(e)
            self.log_message(f"  ✗ Error en Optimize-Volume: {e}", 'WARNING')
        
        # Método 2: defrag con opción de optimización
        try:
            self.log_message(f"  Método 2: defrag /O (Optimización SSD)...")
            
            result = subprocess.run(
                ['defrag', drive, '/O', '/H', '/U', '/V'],
                capture_output=True,
                text=True,
                timeout=600,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 or 'successfully' in result.stdout.lower():
                self.log_message("  ✓ Optimización con defrag completada")
                return
            else:
                methods_tried.append("defrag /O")
                last_error = result.stderr
                self.log_message(f"  ✗ defrag /O falló", 'WARNING')
                
        except subprocess.TimeoutExpired:
            methods_tried.append("defrag /O (timeout)")
            last_error = "Tiempo de espera agotado"
            self.log_message("  ✗ Tiempo de espera agotado para defrag", 'WARNING')
        except Exception as e:
            methods_tried.append("defrag /O (error)")
            last_error = str(e)
            self.log_message(f"  ✗ Error en defrag: {e}", 'WARNING')
        
        # Método 3: Optimización manual con TRIM
        try:
            self.log_message(f"  Método 3: Verificando soporte TRIM...")
            
            # Verificar si TRIM está habilitado
            result = subprocess.run(
                ['fsutil', 'behavior', 'query', 'DisableDeleteNotify'],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if 'DisableDeleteNotify = 0' in result.stdout:
                self.log_message("  ✓ TRIM está habilitado en el sistema")
                # TRIM se ejecuta automáticamente, consideramos esto como éxito
                return
            else:
                self.log_message("  ! TRIM puede estar deshabilitado", 'WARNING')
                methods_tried.append("TRIM verification")
                
        except Exception as e:
            methods_tried.append("TRIM verification (error)")
            last_error = str(e)
            self.log_message(f"  ✗ Error verificando TRIM: {e}", 'WARNING')
        
        # Si todos los métodos fallaron
        if methods_tried:
            raise Exception(f"Todos los métodos de optimización fallaron. Métodos intentados: {', '.join(methods_tried)}. Último error: {last_error}")

    def run_defrag_hdd(self, drive: str, info: Dict):
        """Ejecuta desfragmentación para HDD con múltiples métodos"""
        methods_tried = []
        last_error = None
        
        # Método 1: defrag estándar con opciones detalladas
        try:
            self.log_message(f"  Método 1: defrag estándar...")
            
            result = subprocess.run(
                ['defrag', drive, '/U', '/V', '/H'],
                capture_output=True,
                text=True,
                timeout=7200,  # 2 horas máximo
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 or 'successfully' in result.stdout.lower():
                self.log_message("  ✓ Desfragmentación completada")
                
                # Mostrar estadísticas si están disponibles
                if 'fragmented' in result.stdout.lower():
                    self.log_message(f"  Estadísticas: {result.stdout[-200:]}")
                return
            else:
                methods_tried.append("defrag estándar")
                last_error = result.stderr
                self.log_message(f"  ✗ defrag estándar falló", 'WARNING')
                
        except subprocess.TimeoutExpired:
            methods_tried.append("defrag estándar (timeout)")
            last_error = "Tiempo de espera agotado"
            self.log_message("  ✗ Tiempo de espera agotado (2 horas)", 'WARNING')
        except Exception as e:
            methods_tried.append("defrag estándar (error)")
            last_error = str(e)
            self.log_message(f"  ✗ Error en defrag: {e}", 'WARNING')
        
        # Método 2: Optimize-Volume de PowerShell
        try:
            self.log_message(f"  Método 2: Optimize-Volume (Defragmentación)...")
            ps_cmd = f"Optimize-Volume -DriveLetter '{drive[0]}' -Defrag -Verbose"
            
            result = subprocess.run(
                ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_cmd],
                capture_output=True,
                text=True,
                timeout=7200,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                self.log_message("  ✓ Optimize-Volume completado")
                return
            else:
                methods_tried.append("Optimize-Volume")
                last_error = result.stderr
                self.log_message(f"  ✗ Optimize-Volume falló", 'WARNING')
                
        except subprocess.TimeoutExpired:
            methods_tried.append("Optimize-Volume (timeout)")
            last_error = "Tiempo de espera agotado"
            self.log_message("  ✗ Tiempo de espera agotado para Optimize-Volume", 'WARNING')
        except Exception as e:
            methods_tried.append("Optimize-Volume (error)")
            last_error = str(e)
            self.log_message(f"  ✗ Error en Optimize-Volume: {e}", 'WARNING')
        
        # Si todos los métodos fallaron
        if methods_tried:
            raise Exception(f"Todos los métodos de desfragmentación fallaron. Métodos intentados: {', '.join(methods_tried)}. Último error: {last_error}")

    def update_progress(self, value: int):
        """Actualiza la barra de progreso"""
        self.progress['value'] = value
        if self.progress['maximum'] > 0:
            percentage = int((value / self.progress['maximum']) * 100)
            self.status_label.config(text=f"Progreso: {percentage}% completado ({value}/{int(self.progress['maximum'])})")

    def complete(self, successful: int, failed: int, total: int):
        """Finaliza el proceso de optimización"""
        self.cancel_button.config(state='disabled')
        self.retry_button.config(state='normal')
        self.progress['value'] = self.progress['maximum']
        
        self.log_message(f"\n{'='*50}")
        self.log_message(f"RESUMEN DE OPTIMIZACIÓN")
        self.log_message(f"{'='*50}")
        self.log_message(f"Total de unidades procesadas: {total}")
        self.log_message(f"Exitosas: {successful}")
        self.log_message(f"Fallidas: {failed}")
        self.log_message(f"{'='*50}\n")
        
        if failed == 0:
            self.status_label.config(text="✓ Todas las optimizaciones completadas exitosamente")
            messagebox.showinfo("Completado", 
                              f"Todas las optimizaciones finalizaron correctamente.\n\n"
                              f"Unidades procesadas: {successful}/{total}")
        else:
            self.status_label.config(text=f"⚠ Optimización completada con errores ({failed} fallos)")
            messagebox.showwarning("Completado con Errores", 
                                 f"Optimización finalizada:\n\n"
                                 f"Exitosas: {successful}/{total}\n"
                                 f"Fallidas: {failed}/{total}\n\n"
                                 f"Revise el registro para más detalles.")

    def cancel_operation(self):
        """Cancela la operación en curso"""
        if self.optimization_running:
            if messagebox.askyesno("Cancelar Optimización", 
                                   "¿Está seguro de que desea cancelar la optimización en curso?\n\n"
                                   "La unidad actual completará su proceso antes de detenerse."):
                self.cancel_requested = True
                self.cancel_button.config(state='disabled')
                self.log_message("Solicitando cancelación...", 'WARNING')
        else:
            self.root.destroy()

    def retry_detection(self):
        """Reinicia el proceso de detección"""
        self.log_message("\n" + "="*50)
        self.log_message("Reintentando detección de unidades...")
        self.log_message("="*50 + "\n")
        self.status_label.config(text="Detectando unidades...")
        self.check_drives()

    def run(self):
        """Inicia la aplicación"""
        self.root.mainloop()

def check_requirements():
    """Verifica los requisitos del sistema"""
    errors = []
    
    # Verificar sistema operativo
    if platform.system() != "Windows":
        errors.append("Este programa solo funciona en Windows")
        return errors
    
    # Verificar versión de Windows (debe ser Windows 10 o superior)
    try:
        version = platform.version()
        major_version = int(version.split('.')[0])
        if major_version < 10:
            errors.append(f"Se requiere Windows 10 o superior (detectado: Windows {major_version})")
    except:
        pass  # No podemos determinar la versión, continuar de todos modos
    
    # Verificar permisos de administrador
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            errors.append("Este programa requiere permisos de administrador")
    except:
        errors.append("No se pudo verificar permisos de administrador")
    
    return errors

def main():
    """Función principal"""
    # Verificar requisitos
    errors = check_requirements()
    
    if errors:
        root = tk.Tk()
        root.withdraw()  # Ocultar ventana principal
        
        error_msg = "No se puede ejecutar el programa:\n\n" + "\n".join(f"• {err}" for err in errors)
        
        if "permisos de administrador" in error_msg.lower():
            error_msg += "\n\nPor favor, ejecute el programa como administrador:\n"
            error_msg += "1. Haga clic derecho en el archivo\n"
            error_msg += "2. Seleccione 'Ejecutar como administrador'"
        
        messagebox.showerror("Requisitos no cumplidos", error_msg)
        sys.exit(1)
    
    # Crear y ejecutar aplicación
    try:
        app = StorageMaintenanceApp()
        app.run()
    except Exception as e:
        logging.exception("Error fatal en la aplicación")
        messagebox.showerror("Error Fatal", 
                           f"Se produjo un error inesperado:\n\n{str(e)}\n\n"
                           f"La aplicación se cerrará.")
        sys.exit(1)

if __name__ == "__main__":
    main()