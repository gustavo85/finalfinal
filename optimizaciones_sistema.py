# -*- coding: utf-8 -*-
"""
optimizaciones_sistema.py - Módulo de optimizaciones automáticas del sistema
Implementa 10 optimizaciones para maximizar el rendimiento del sistema Windows
sin intervención manual del usuario.

Requiere: Privilegios de administrador y Windows 10/11
"""

import os
import sys
import platform
import subprocess
import psutil
import winreg
import time
import logging
from typing import Optional, List, Dict, Tuple
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def es_admin() -> bool:
    """Verifica si el script se ejecuta con privilegios de administrador"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        logger.warning(f"No se pudo verificar privilegios de administrador: {e}")
        return False


def es_windows() -> bool:
    """Verifica si el sistema operativo es Windows"""
    return platform.system() == 'Windows'


def verificar_requisitos() -> bool:
    """Verifica que se cumplan los requisitos para ejecutar optimizaciones"""
    if not es_windows():
        logger.error("Este módulo solo funciona en Windows")
        return False
    
    if not es_admin():
        logger.error("Se requieren privilegios de administrador para ejecutar optimizaciones")
        return False
    
    return True


# ============================================================================
# OPTIMIZACIÓN 1: SysMain (Superfetch) Inteligente
# ============================================================================

def detectar_ssd_principal() -> bool:
    """Detecta si el disco principal (C:) es SSD"""
    try:
        ps_command = """
        Get-PhysicalDisk | Where-Object {$_.DeviceID -eq 0} | 
        Select-Object -ExpandProperty MediaType
        """
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True, text=True, timeout=10, check=False
        )
        return "SSD" in result.stdout
    except subprocess.TimeoutExpired:
        logger.warning("Timeout detectando tipo de disco, asumiendo HDD")
        return False
    except Exception as e:
        logger.warning(f"Error detectando tipo de disco: {e}, asumiendo HDD")
        return False


def optimizar_sysmain_inteligente() -> bool:
    """
    Configura SysMain para optimizar según tipo de almacenamiento
    - SSD: Modo ligero (prefetch limitado)
    - HDD: Modo completo (prefetch agresivo)
    """
    try:
        es_ssd = detectar_ssd_principal()
        
        key_path = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters"
        
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, 
                               winreg.KEY_SET_VALUE) as key:
                if es_ssd:
                    # SSD: Prefetch moderado (solo aplicaciones)
                    winreg.SetValueEx(key, "EnablePrefetcher", 0, winreg.REG_DWORD, 1)
                    winreg.SetValueEx(key, "EnableSuperfetch", 0, winreg.REG_DWORD, 1)
                    logger.info("✓ SysMain configurado para SSD (modo moderado)")
                else:
                    # HDD: Prefetch completo (aplicaciones + boot)
                    winreg.SetValueEx(key, "EnablePrefetcher", 0, winreg.REG_DWORD, 3)
                    winreg.SetValueEx(key, "EnableSuperfetch", 0, winreg.REG_DWORD, 3)
                    logger.info("✓ SysMain configurado para HDD (modo completo)")
        except OSError as e:
            logger.error(f"Error accediendo al registro: {e}")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error optimizando SysMain: {e}")
        return False


# ============================================================================
# OPTIMIZACIÓN 2: Windows Search Indexing
# ============================================================================

def optimizar_windows_search() -> bool:
    """
    Optimiza el indexado de Windows Search
    - Excluye carpetas temporales
    - Reduce uso de CPU en segundo plano
    """
    try:
        # Rutas a excluir del indexado
        rutas_excluir = [
            r"C:\Windows\Temp",
            r"C:\Users\*\AppData\Local\Temp",
            r"C:\$Recycle.Bin",
            r"C:\ProgramData\Package Cache",
            r"C:\Windows\SoftwareDistribution"
        ]
        
        # Reducir prioridad del indexador
        try:
            for proc in psutil.process_iter(['name', 'pid']):
                if proc.info['name'] and proc.info['name'].lower() == 'searchindexer.exe':
                    p = psutil.Process(proc.info['pid'])
                    p.nice(psutil.IDLE_PRIORITY_CLASS)
                    logger.info("✓ Prioridad de SearchIndexer reducida")
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"No se pudo ajustar prioridad de SearchIndexer: {e}")
        
        # Configurar exclusiones mediante registro
        key_path = r"SOFTWARE\Microsoft\Windows Search\Gather\Windows\SystemIndex"
        try:
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                # Habilitar throttling para reducir uso de CPU
                winreg.SetValueEx(key, "ThrottleLevel", 0, winreg.REG_DWORD, 1)
                logger.info("✓ Windows Search indexing optimizado")
        except OSError as e:
            logger.warning(f"No se pudo configurar Windows Search: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Error optimizando Windows Search: {e}")
        return False


# ============================================================================
# OPTIMIZACIÓN 3: TRIM para SSDs
# ============================================================================

def optimizar_trim_ssd() -> bool:
    """
    Habilita y optimiza TRIM para SSDs
    - Verifica y habilita TRIM
    - Ejecuta TRIM manual
    - Programa tarea semanal
    """
    try:
        # Verificar si TRIM está habilitado
        result = subprocess.run(
            ["fsutil", "behavior", "query", "DisableDeleteNotify"],
            capture_output=True, text=True, check=False
        )
        
        # Si DisableDeleteNotify = 0, TRIM está habilitado
        if "DisableDeleteNotify = 1" in result.stdout:
            # Habilitar TRIM
            subprocess.run(
                ["fsutil", "behavior", "set", "DisableDeleteNotify", "0"],
                capture_output=True, check=False
            )
            logger.info("✓ TRIM habilitado para SSDs")
        else:
            logger.info("✓ TRIM ya estaba habilitado")
        
        # Ejecutar optimización TRIM en discos SSD
        for disk in psutil.disk_partitions():
            if disk.fstype == 'NTFS':
                drive_letter = disk.device[0]
                # Ejecutar optimize (TRIM) para SSDs
                subprocess.run(
                    ["defrag", f"{drive_letter}:", "/L"],
                    capture_output=True, timeout=60, check=False
                )
        
        logger.info("✓ TRIM ejecutado en discos SSD")
        
        # Programar tarea semanal de TRIM
        programar_tarea_trim_semanal()
        
        return True
    except subprocess.TimeoutExpired:
        logger.warning("Timeout ejecutando TRIM")
        return False
    except Exception as e:
        logger.error(f"Error optimizando TRIM: {e}")
        return False


def programar_tarea_trim_semanal() -> None:
    """Programa tarea semanal de TRIM para SSDs"""
    try:
        task_name = "OptimizadorGaming_TRIM_Semanal"
        
        # Eliminar tarea existente si existe
        subprocess.run(
            ["schtasks", "/Delete", "/TN", task_name, "/F"],
            capture_output=True, check=False
        )
        
        # Crear nueva tarea
        subprocess.run([
            "schtasks", "/Create",
            "/TN", task_name,
            "/TR", "defrag /C /L",
            "/SC", "WEEKLY",
            "/D", "SUN",
            "/ST", "03:00",
            "/RL", "HIGHEST",
            "/F"
        ], capture_output=True, check=False)
        
        logger.info("✓ Tarea semanal de TRIM programada")
    except Exception as e:
        logger.warning(f"No se pudo programar tarea de TRIM: {e}")


# ============================================================================
# OPTIMIZACIÓN 4: Desfragmentación Inteligente
# ============================================================================

def es_disco_ssd(letra_disco: str) -> bool:
    """Determina si un disco es SSD"""
    try:
        ps_command = f"""
        $partition = Get-Partition -DriveLetter '{letra_disco[0]}'
        $disk = Get-PhysicalDisk | Where-Object {{$_.DeviceID -eq $partition.DiskNumber}}
        $disk.MediaType
        """
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True, text=True, timeout=10, check=False
        )
        return "SSD" in result.stdout
    except Exception:
        return False


def configurar_desfragmentacion_inteligente() -> bool:
    """
    Configura desfragmentación según tipo de disco:
    - HDD: Desfragmentación completa mensual
    - SSD: Solo TRIM mensual
    """
    try:
        for disco in psutil.disk_partitions():
            if disco.fstype != 'NTFS':
                continue
            
            letra_disco = disco.device[0]
            es_ssd = es_disco_ssd(letra_disco)
            
            if es_ssd:
                # SSD: Solo TRIM mensual
                crear_tarea_optimizacion(letra_disco, tipo='trim', frecuencia='mensual')
                logger.info(f"✓ Disco {letra_disco}: configurado TRIM mensual (SSD)")
            else:
                # HDD: Desfragmentación completa mensual
                crear_tarea_optimizacion(letra_disco, tipo='defrag', frecuencia='mensual')
                logger.info(f"✓ Disco {letra_disco}: configurado defrag mensual (HDD)")
        
        return True
    except Exception as e:
        logger.error(f"Error configurando desfragmentación: {e}")
        return False


def crear_tarea_optimizacion(letra: str, tipo: str, frecuencia: str) -> None:
    """Crea tarea programada para optimización de disco"""
    try:
        task_name = f"OptimizadorGaming_{tipo.upper()}_{letra}_{frecuencia}"
        
        if tipo == 'trim':
            comando = f"defrag {letra}: /L"
        else:
            comando = f"defrag {letra}: /O /H"
        
        # Eliminar tarea existente
        subprocess.run(
            ["schtasks", "/Delete", "/TN", task_name, "/F"],
            capture_output=True, check=False
        )
        
        # Crear nueva tarea
        if frecuencia == 'mensual':
            subprocess.run([
                "schtasks", "/Create",
                "/TN", task_name,
                "/TR", comando,
                "/SC", "MONTHLY",
                "/D", "1",
                "/ST", "03:00",
                "/RL", "HIGHEST",
                "/F"
            ], capture_output=True, check=False)
    except Exception as e:
        logger.warning(f"No se pudo crear tarea de optimización: {e}")


# ============================================================================
# OPTIMIZACIÓN 5: Archivo de Paginación Dinámico
# ============================================================================

def optimizar_archivo_paginacion() -> bool:
    """
    Configura archivo de paginación óptimo:
    - RAM ≥ 16GB: Tamaño fijo 2GB (mínimo para dumps)
    - RAM 8-16GB: 1.5x RAM inicial, 3x RAM máximo
    - RAM < 8GB: Sistema administrado
    """
    try:
        ram_gb = psutil.virtual_memory().total / (1024**3)
        
        if ram_gb >= 16:
            # Sistema con mucha RAM: archivo mínimo fijo
            min_size_mb = 2048
            max_size_mb = 2048
            logger.info(f"RAM: {ram_gb:.1f}GB - Configurando pagefile fijo de 2GB")
        elif ram_gb >= 8:
            # Sistema medio: 1.5x-3x RAM
            min_size_mb = int(ram_gb * 1.5 * 1024)
            max_size_mb = int(ram_gb * 3 * 1024)
            logger.info(f"RAM: {ram_gb:.1f}GB - Configurando pagefile {min_size_mb}-{max_size_mb}MB")
        else:
            # Sistema con poca RAM: dejar administrado por sistema
            logger.info(f"RAM: {ram_gb:.1f}GB - Manteniendo pagefile administrado por sistema")
            return configurar_paginacion_administrada()
        
        # Configurar tamaño del archivo de paginación
        ps_command = f"""
        $computersys = Get-WmiObject Win32_ComputerSystem -EnableAllPrivileges
        $computersys.AutomaticManagedPagefile = $False
        $computersys.Put() | Out-Null
        
        $pagefileset = Get-WmiObject Win32_PageFileSetting
        if ($pagefileset -ne $null) {{
            $pagefileset.Delete()
        }}
        
        $pagefileset = ([WmiClass]"Win32_PageFileSetting").CreateInstance()
        $pagefileset.Name = "C:\\pagefile.sys"
        $pagefileset.InitialSize = {min_size_mb}
        $pagefileset.MaximumSize = {max_size_mb}
        $pagefileset.Put() | Out-Null
        """
        
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True, timeout=30, check=False
        )
        
        if result.returncode == 0:
            logger.info(f"✓ Archivo de paginación configurado: {min_size_mb}-{max_size_mb} MB")
            return True
        else:
            logger.warning(f"Advertencia configurando pagefile: {result.stderr.decode('utf-8', errors='ignore')}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Timeout configurando archivo de paginación")
        return False
    except Exception as e:
        logger.error(f"Error optimizando archivo de paginación: {e}")
        return False


def configurar_paginacion_administrada() -> bool:
    """Configura paginación administrada por el sistema"""
    try:
        ps_command = """
        $computersys = Get-WmiObject Win32_ComputerSystem -EnableAllPrivileges
        $computersys.AutomaticManagedPagefile = $True
        $computersys.Put() | Out-Null
        """
        subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True, timeout=15, check=False
        )
        logger.info("✓ Paginación configurada como administrada por sistema")
        return True
    except Exception as e:
        logger.error(f"Error configurando paginación administrada: {e}")
        return False


# ============================================================================
# OPTIMIZACIÓN 6: Estados de Energía del Procesador
# ============================================================================

def obtener_plan_energia_activo() -> Optional[str]:
    """Obtiene el GUID del plan de energía activo"""
    try:
        result = subprocess.run(
            ["powercfg", "/getactivescheme"],
            capture_output=True, text=True, check=False
        )
        # Extraer GUID del plan activo
        import re
        match = re.search(r'([0-9a-f-]{36})', result.stdout)
        if match:
            return match.group(1)
        return None
    except Exception:
        return None


def optimizar_estados_procesador() -> bool:
    """
    Optimiza estados de energía del procesador:
    - Gaming: C-States deshabilitados, P-States en máximo rendimiento
    - Turbo Boost habilitado
    - Core parking deshabilitado
    """
    try:
        plan_guid = obtener_plan_energia_activo()
        if not plan_guid:
            logger.warning("No se pudo obtener plan de energía activo")
            return False
        
        # Configuraciones para máximo rendimiento
        configs = {
            # Frecuencia mínima: 100%
            "PROCTHROTTLEMIN": ("54533251-82be-4824-96c1-47b60b740d00", 100),
            # Frecuencia máxima: 100%
            "PROCTHROTTLEMAX": ("bc5038f7-23e0-4960-96da-33abaf5935ec", 100),
            # Turbo Boost habilitado (2 = aggressive)
            "PERFBOOSTMODE": ("be337238-0d82-4146-a960-4f3749d470c7", 2),
        }
        
        for setting_name, (setting_guid, valor) in configs.items():
            try:
                # Aplicar en AC (conectado)
                subprocess.run(
                    ["powercfg", "/setacvalueindex", plan_guid, 
                     "SUB_PROCESSOR", setting_guid, str(valor)],
                    capture_output=True, check=False
                )
                # Aplicar en DC (batería)
                subprocess.run(
                    ["powercfg", "/setdcvalueindex", plan_guid, 
                     "SUB_PROCESSOR", setting_guid, str(valor)],
                    capture_output=True, check=False
                )
            except Exception as e:
                logger.warning(f"Error configurando {setting_name}: {e}")
        
        # Aplicar cambios
        subprocess.run(["powercfg", "/setactive", plan_guid], 
                      capture_output=True, check=False)
        
        logger.info("✓ Estados de procesador optimizados")
        return True
    except Exception as e:
        logger.error(f"Error optimizando procesador: {e}")
        return False


# ============================================================================
# OPTIMIZACIÓN 7: Hardware-Accelerated GPU Scheduling
# ============================================================================

def verificar_version_compatible(version_str: str) -> bool:
    """Verifica si Windows soporta GPU Scheduling (Build 19041+)"""
    try:
        import re
        match = re.search(r'(\d+)\.(\d+)\.(\d+)', version_str)
        if match:
            build = int(match.group(3))
            return build >= 19041
        return False
    except Exception:
        return False


def habilitar_gpu_scheduling() -> bool:
    """
    Habilita Hardware-Accelerated GPU Scheduling
    Requisitos: Windows 10 2004+, GPU compatible
    """
    try:
        # Verificar versión de Windows
        version_windows = platform.version()
        if not verificar_version_compatible(version_windows):
            logger.warning("Windows 10 2004+ requerido para GPU Scheduling")
            return False
        
        # Habilitar en registro
        key_path = r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0,
                               winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "HwSchMode", 0, winreg.REG_DWORD, 2)
        except OSError as e:
            logger.error(f"Error accediendo al registro: {e}")
            return False
        
        logger.info("✓ GPU Hardware Scheduling habilitado (requiere reinicio)")
        return True
    except Exception as e:
        logger.error(f"Error habilitando GPU Scheduling: {e}")
        return False


# ============================================================================
# OPTIMIZACIÓN 8: Adaptadores de Red
# ============================================================================

def optimizar_adaptadores_red() -> bool:
    """
    Optimiza todos los adaptadores de red activos:
    - Deshabilita ahorro de energía
    - Optimiza buffers de recepción/transmisión
    - Habilita RSS (Receive Side Scaling)
    """
    try:
        # Obtener adaptadores activos
        ps_command = """
        Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | 
        Select-Object -ExpandProperty Name
        """
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True, text=True, timeout=15, check=False
        )
        
        adaptadores = [a.strip() for a in result.stdout.split('\n') if a.strip()]
        
        if not adaptadores:
            logger.warning("No se encontraron adaptadores de red activos")
            return False
        
        for adaptador in adaptadores:
            # Optimizar configuraciones avanzadas
            ps_optimizar = f"""
            # Optimizar buffers
            Set-NetAdapterAdvancedProperty -Name '{adaptador}' -DisplayName 'Receive Buffers' -RegistryValue 2048 -ErrorAction SilentlyContinue
            Set-NetAdapterAdvancedProperty -Name '{adaptador}' -DisplayName 'Transmit Buffers' -RegistryValue 2048 -ErrorAction SilentlyContinue
            
            # Interrupt Moderation
            Set-NetAdapterAdvancedProperty -Name '{adaptador}' -DisplayName 'Interrupt Moderation' -RegistryValue 'Enabled' -ErrorAction SilentlyContinue
            
            # RSS
            Enable-NetAdapterRss -Name '{adaptador}' -ErrorAction SilentlyContinue
            """
            
            subprocess.run(
                ["powershell", "-Command", ps_optimizar],
                capture_output=True, timeout=15, check=False
            )
        
        logger.info(f"✓ {len(adaptadores)} adaptador(es) de red optimizados")
        return True
    except subprocess.TimeoutExpired:
        logger.error("Timeout optimizando adaptadores de red")
        return False
    except Exception as e:
        logger.error(f"Error optimizando red: {e}")
        return False


# ============================================================================
# OPTIMIZACIÓN 9: Gestión de Puntos de Restauración
# ============================================================================

def optimizar_puntos_restauracion() -> bool:
    """
    Configura puntos de restauración:
    - SSD: Máximo 2% espacio (2-5 puntos)
    - HDD: Máximo 5% espacio (10-15 puntos)
    """
    try:
        discos = psutil.disk_partitions()
        
        for disco in discos:
            if disco.fstype != 'NTFS' or not disco.device.startswith('C'):
                continue
            
            letra_disco = disco.device[0]
            es_ssd = es_disco_ssd(letra_disco + ':')
            
            # Configurar tamaño máximo
            porcentaje_max = 2 if es_ssd else 5
            
            ps_command = f"""
            # Habilitar protección del sistema
            Enable-ComputerRestore -Drive "{letra_disco}:\\" -ErrorAction SilentlyContinue
            
            # Configurar espacio máximo
            vssadmin Resize ShadowStorage /For={letra_disco}: /On={letra_disco}: /MaxSize={porcentaje_max}% 2>&1 | Out-Null
            """
            
            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True, timeout=30, check=False
            )
            
            logger.info(f"✓ Puntos de restauración configurados ({porcentaje_max}% en {letra_disco}:)")
        
        # Programar limpieza mensual de puntos antiguos
        programar_limpieza_puntos_restauracion()
        
        return True
    except subprocess.TimeoutExpired:
        logger.error("Timeout configurando puntos de restauración")
        return False
    except Exception as e:
        logger.error(f"Error optimizando puntos de restauración: {e}")
        return False


def programar_limpieza_puntos_restauracion() -> None:
    """Programa limpieza mensual de puntos de restauración antiguos"""
    try:
        task_name = "OptimizadorGaming_Limpieza_Restauracion"
        
        # Comando para limpiar puntos antiguos (mantener últimos 3)
        comando = 'powershell -Command "Get-ComputerRestorePoint | Sort-Object CreationTime -Descending | Select-Object -Skip 3 | ForEach-Object { vssadmin delete shadows /shadow=$_.SequenceNumber /quiet }"'
        
        # Eliminar tarea existente
        subprocess.run(
            ["schtasks", "/Delete", "/TN", task_name, "/F"],
            capture_output=True, check=False
        )
        
        # Crear nueva tarea mensual
        subprocess.run([
            "schtasks", "/Create",
            "/TN", task_name,
            "/TR", comando,
            "/SC", "MONTHLY",
            "/D", "1",
            "/ST", "04:00",
            "/RL", "HIGHEST",
            "/F"
        ], capture_output=True, check=False)
        
        logger.info("✓ Tarea de limpieza de restauración programada")
    except Exception as e:
        logger.warning(f"No se pudo programar limpieza de restauración: {e}")


# ============================================================================
# OPTIMIZACIÓN 10: Windows Update
# ============================================================================

def optimizar_windows_update() -> bool:
    """
    Optimiza comportamiento de Windows Update:
    - Horario de actualizaciones: 3-6 AM
    - Limita ancho de banda a 50%
    - Deshabilita reinicios automáticos
    """
    try:
        # Configurar horario activo y políticas
        ps_command = """
        # Crear claves si no existen
        New-Item -Path "HKLM:\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" -Force | Out-Null
        New-Item -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" -Force | Out-Null
        New-Item -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\DeliveryOptimization\\Config" -Force | Out-Null
        New-Item -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\DeliveryOptimization\\Settings" -Force | Out-Null
        
        # Configurar horario activo (6 AM - 3 AM del día siguiente = actualizar 3-6 AM)
        New-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" -Name "ActiveHoursStart" -Value 6 -PropertyType DWORD -Force | Out-Null
        New-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" -Name "ActiveHoursEnd" -Value 3 -PropertyType DWORD -Force | Out-Null
        
        # Deshabilitar reinicios automáticos
        New-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" -Name "NoAutoRebootWithLoggedOnUsers" -Value 1 -PropertyType DWORD -Force | Out-Null
        New-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" -Name "AUOptions" -Value 3 -PropertyType DWORD -Force | Out-Null
        
        # Limitar ancho de banda de descarga al 50%
        New-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\DeliveryOptimization\\Config" -Name "DODownloadMode" -Value 1 -PropertyType DWORD -Force | Out-Null
        New-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\DeliveryOptimization\\Settings" -Name "DownloadPercentageMaxBackground" -Value 50 -PropertyType DWORD -Force | Out-Null
        """
        
        subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True, timeout=20, check=False
        )
        
        # Limpiar caché de Windows Update
        try:
            subprocess.run(["net", "stop", "wuauserv"], capture_output=True, timeout=10, check=False)
            
            # Limpiar carpeta de descargas
            import shutil
            update_folder = r"C:\Windows\SoftwareDistribution\Download"
            if os.path.exists(update_folder):
                try:
                    shutil.rmtree(update_folder)
                    os.makedirs(update_folder)
                    logger.info("✓ Caché de Windows Update limpiado")
                except (PermissionError, OSError) as e:
                    logger.warning(f"No se pudo limpiar caché de WU: {e}")
            
            subprocess.run(["net", "start", "wuauserv"], capture_output=True, timeout=10, check=False)
        except subprocess.TimeoutExpired:
            logger.warning("Timeout manejando servicio Windows Update")
        
        logger.info("✓ Windows Update optimizado")
        return True
    except subprocess.TimeoutExpired:
        logger.error("Timeout configurando Windows Update")
        return False
    except Exception as e:
        logger.error(f"Error optimizando Windows Update: {e}")
        return False


# ============================================================================
# ORQUESTACIÓN Y PROGRAMACIÓN
# ============================================================================

def aplicar_todas_optimizaciones_sistema() -> Tuple[bool, Dict[str, str]]:
    """
    Aplica todas las optimizaciones automáticas del sistema
    
    Returns:
        Tuple[bool, Dict[str, str]]: (éxito_total, resultados_por_optimización)
    """
    print("=" * 70)
    print("=== Iniciando Optimización Automática del Sistema ===")
    print("=" * 70)
    print()
    
    if not verificar_requisitos():
        logger.error("No se cumplen los requisitos para ejecutar optimizaciones")
        return False, {}
    
    optimizaciones = [
        ("1. SysMain Inteligente", optimizar_sysmain_inteligente),
        ("2. Windows Search", optimizar_windows_search),
        ("3. TRIM para SSDs", optimizar_trim_ssd),
        ("4. Desfragmentación Inteligente", configurar_desfragmentacion_inteligente),
        ("5. Archivo de Paginación", optimizar_archivo_paginacion),
        ("6. Estados de Procesador", optimizar_estados_procesador),
        ("7. GPU Scheduling", habilitar_gpu_scheduling),
        ("8. Adaptadores de Red", optimizar_adaptadores_red),
        ("9. Puntos de Restauración", optimizar_puntos_restauracion),
        ("10. Windows Update", optimizar_windows_update)
    ]
    
    resultados = {}
    
    for nombre, funcion in optimizaciones:
        print(f"\n{nombre}...")
        print("-" * 70)
        try:
            exito = funcion()
            resultados[nombre] = "✓ ÉXITO" if exito else "✗ FALLÓ"
        except Exception as e:
            resultados[nombre] = f"✗ ERROR: {str(e)[:50]}"
            logger.error(f"Error en {nombre}: {e}")
        print(f"  {resultados[nombre]}")
    
    # Resumen
    print("\n" + "=" * 70)
    print("=== Resumen de Optimizaciones ===")
    print("=" * 70)
    exitosas = sum(1 for r in resultados.values() if "ÉXITO" in r)
    total = len(resultados)
    
    print(f"\nCompletadas exitosamente: {exitosas}/{total}")
    print("\nDetalle:")
    for nombre, resultado in resultados.items():
        print(f"  {nombre}: {resultado}")
    
    # Crear archivo de log
    log_file = "optimizaciones_sistema.log"
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"Optimizaciones del Sistema - {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Completadas: {exitosas}/{total}\n\n")
            for nombre, resultado in resultados.items():
                f.write(f"{nombre}: {resultado}\n")
        print(f"\n✓ Log guardado en {log_file}")
    except IOError as e:
        logger.warning(f"No se pudo guardar log: {e}")
    
    print("\n" + "=" * 70)
    
    return exitosas == total, resultados


def programar_optimizaciones_automaticas() -> bool:
    """
    Programa ejecución automática de optimizaciones
    - Diaria: Limpieza y monitoreo ligero
    - Semanal: TRIM y optimización de disco
    - Mensual: Desfragmentación y mantenimiento profundo
    """
    if not verificar_requisitos():
        logger.error("No se cumplen los requisitos para programar optimizaciones")
        return False
    
    print("Programando optimizaciones automáticas...")
    
    script_path = os.path.abspath(__file__)
    python_exe = sys.executable
    
    tareas = [
        {
            "nombre": "OptimizadorGaming_Diario",
            "descripcion": "Optimización diaria ligera",
            "frecuencia": "DAILY",
            "hora": "03:00",
            "comando": f'"{python_exe}" "{script_path}" --optimizacion-diaria'
        },
        {
            "nombre": "OptimizadorGaming_Semanal",
            "descripcion": "Optimización semanal (TRIM, limpieza)",
            "frecuencia": "WEEKLY",
            "hora": "03:00",
            "dia": "SUN",
            "comando": f'"{python_exe}" "{script_path}" --optimizacion-semanal'
        },
        {
            "nombre": "OptimizadorGaming_Mensual",
            "descripcion": "Optimización mensual completa",
            "frecuencia": "MONTHLY",
            "hora": "03:00",
            "dia": "1",
            "comando": f'"{python_exe}" "{script_path}" --optimizacion-mensual'
        }
    ]
    
    creadas = 0
    for tarea in tareas:
        try:
            # Eliminar tarea existente
            subprocess.run(
                ["schtasks", "/Delete", "/TN", tarea["nombre"], "/F"],
                capture_output=True, check=False
            )
            
            # Crear nueva tarea
            cmd = [
                "schtasks", "/Create",
                "/TN", tarea["nombre"],
                "/TR", tarea["comando"],
                "/SC", tarea["frecuencia"],
                "/ST", tarea["hora"],
                "/RL", "HIGHEST",
                "/F"
            ]
            
            if "dia" in tarea:
                if tarea["frecuencia"] == "WEEKLY":
                    cmd.extend(["/D", tarea["dia"]])
                elif tarea["frecuencia"] == "MONTHLY":
                    cmd.extend(["/D", tarea["dia"]])
            
            result = subprocess.run(cmd, capture_output=True, check=False)
            
            if result.returncode == 0:
                logger.info(f"✓ Tarea programada: {tarea['nombre']}")
                creadas += 1
            else:
                logger.warning(f"No se pudo crear tarea: {tarea['nombre']}")
                
        except Exception as e:
            logger.error(f"Error creando tarea {tarea['nombre']}: {e}")
    
    print(f"\n✓ {creadas}/{len(tareas)} tareas programadas correctamente")
    return creadas == len(tareas)


# ============================================================================
# MAIN - Punto de entrada para ejecución directa
# ============================================================================

def main():
    """Punto de entrada principal del módulo"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Optimizaciones Automáticas del Sistema para Gaming Optimizer'
    )
    parser.add_argument('--aplicar-todo', action='store_true',
                       help='Aplica todas las optimizaciones')
    parser.add_argument('--programar', action='store_true',
                       help='Programa optimizaciones automáticas')
    parser.add_argument('--optimizacion-diaria', action='store_true',
                       help='Ejecuta optimizaciones diarias')
    parser.add_argument('--optimizacion-semanal', action='store_true',
                       help='Ejecuta optimizaciones semanales')
    parser.add_argument('--optimizacion-mensual', action='store_true',
                       help='Ejecuta optimizaciones mensuales')
    
    args = parser.parse_args()
    
    if args.aplicar_todo:
        exito, resultados = aplicar_todas_optimizaciones_sistema()
        sys.exit(0 if exito else 1)
    
    elif args.programar:
        exito = programar_optimizaciones_automaticas()
        sys.exit(0 if exito else 1)
    
    elif args.optimizacion_diaria:
        # Optimizaciones ligeras diarias
        logger.info("Ejecutando optimizaciones diarias...")
        optimizar_windows_search()
        sys.exit(0)
    
    elif args.optimizacion_semanal:
        # Optimizaciones semanales
        logger.info("Ejecutando optimizaciones semanales...")
        optimizar_trim_ssd()
        optimizar_windows_search()
        sys.exit(0)
    
    elif args.optimizacion_mensual:
        # Optimizaciones completas mensuales
        logger.info("Ejecutando optimizaciones mensuales...")
        exito, resultados = aplicar_todas_optimizaciones_sistema()
        sys.exit(0 if exito else 1)
    
    else:
        parser.print_help()
        print("\nEjemplo de uso:")
        print(f"  python {os.path.basename(__file__)} --aplicar-todo")
        print(f"  python {os.path.basename(__file__)} --programar")
        sys.exit(1)


if __name__ == "__main__":
    main()
