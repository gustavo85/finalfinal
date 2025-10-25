"""
LIMPIEZA.PY - Sistema de Limpieza Agresiva y Segura para Windows
Versión mejorada con notificaciones coordinadas y cierre forzado
Autor: gustavo85
Fecha: 2025-10-24
"""

import tkinter as tk
from tkinter import font
import os
import sys
import shutil
import glob
import ctypes
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
import winreg
import logging
import threading

# ============================================================================
# OCULTAR CONSOLA
# ============================================================================

def hide_console():
    """Oculta la ventana de consola en Windows."""
    try:
        whnd = ctypes.windll.kernel32.GetConsoleWindow()
        if whnd != 0:
            ctypes.windll.user32.ShowWindow(whnd, 0)  # 0 = SW_HIDE
    except Exception:
        pass

# Ocultar consola al inicio
if os.name == 'nt':
    hide_console()

# ============================================================================
# CONFIGURACIÓN Y LOGGING
# ============================================================================

log_file = os.path.join(os.path.expanduser("~"), 'limpieza_log.txt')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
    ]
)

# ============================================================================
# NOTIFICACIONES VISUALES (COORDINADAS + FAILSAFE)
# ============================================================================

# Eventos globales para coordinar notificaciones y evitar superposiciones
_last_notification_done = None
_last_notification_mutex = threading.Lock()

def show_notification(message, bg_color="#006400", duration=5000, wait_for_previous=True, max_wait_previous=12):
    """
    Muestra una notificación deslizante en Windows.
    - Coordina con notificaciones previas para no superponer.
    - Devuelve un threading.Event que se setea cuando la notificación terminó.
    - Usa hilo daemon para no bloquear el proceso en caso de cuelgue.
    - Programa un destroy forzado por si el slide_out no ocurre.
    """
    global _last_notification_done

    # Esperar (opcionalmente) a que la notificación anterior finalice, con timeout
    try:
        if wait_for_previous and _last_notification_done and not _last_notification_done.is_set():
            _last_notification_done.wait(timeout=max_wait_previous)
    except Exception:
        pass

    done_event = threading.Event()

    def create_notification():
        try:
            root = tk.Tk()
            root.title("")
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            root.configure(bg=bg_color)
            root.resizable(False, False)

            # Configurar geometría inicial
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            window_width = 500
            window_height = 150

            initial_x = screen_width
            initial_y = 50

            root.geometry(f"{window_width}x{window_height}+{initial_x}+{initial_y}")

            # Crear label con el mensaje
            label = tk.Label(
                root,
                text=message,
                fg="white",
                bg=bg_color,
                font=font.Font(family="Segoe UI", size=12, weight="bold"),
                wraplength=480,
                justify="center",
                padx=10,
                pady=10
            )
            label.pack(expand=True, fill="both")

            # Variables de control
            is_closing = [False]  # lista para mutabilidad en nested functions

            def slide_in():
                """Deslizar la ventana hacia dentro."""
                try:
                    if is_closing[0]:
                        return

                    current_x = root.winfo_x()
                    target_x = screen_width - window_width - 20

                    if current_x > target_x:
                        new_x = max(current_x - 30, target_x)
                        root.geometry(f"{window_width}x{window_height}+{new_x}+{initial_y}")
                        root.after(10, slide_in)
                    else:
                        # Una vez dentro, esperar y luego deslizar fuera
                        root.after(duration, slide_out)
                except tk.TclError:
                    pass  # Ventana destruida

            def slide_out():
                """Deslizar la ventana hacia fuera."""
                try:
                    if is_closing[0]:
                        return

                    is_closing[0] = True
                    current_x = root.winfo_x()

                    if current_x < screen_width:
                        new_x = current_x + 30
                        root.geometry(f"{window_width}x{window_height}+{new_x}+{initial_y}")
                        root.after(10, slide_out)
                    else:
                        try:
                            root.destroy()
                        except Exception:
                            pass
                        finally:
                            done_event.set()
                except tk.TclError:
                    done_event.set()

            # Permitir cerrar haciendo clic
            def on_click(event):
                is_closing[0] = True
                slide_out()

            root.bind("<Button-1>", on_click)
            label.bind("<Button-1>", on_click)

            # Failsafe: destruir aunque algo falle (duración + margen)
            def force_destroy():
                try:
                    if not done_event.is_set():
                        try:
                            root.destroy()
                        except Exception:
                            pass
                        finally:
                            done_event.set()
                except Exception:
                    done_event.set()

            # Iniciar la animación después de que la ventana esté lista
            root.update_idletasks()
            root.after(100, slide_in)
            root.after(duration + 9000, force_destroy)  # margen de 9s posterior a duration

            # Iniciar el mainloop
            root.mainloop()

            # Si se sale del loop sin setear done_event, setearlo
            if not done_event.is_set():
                done_event.set()

        except Exception as e:
            logging.warning(f"Error mostrando notificación: {e}")
            done_event.set()

    # Hilo daemon para que no bloquee la terminación del proceso
    notification_thread = threading.Thread(target=create_notification, daemon=True)
    notification_thread.start()

    # Registrar este evento como la última notificación activa
    with _last_notification_mutex:
        _last_notification_done = done_event

    return done_event

# ============================================================================
# UTILIDADES DE SISTEMA
# ============================================================================

def is_admin():
    """Detecta si el script corre con privilegios de administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def bytes_to_mb(bytes_size):
    """Convierte bytes a MB."""
    return bytes_size / (1024 * 1024)

def bytes_to_gb(bytes_size):
    """Convierte bytes a GB."""
    return bytes_size / (1024 * 1024 * 1024)

def format_size(bytes_size):
    """Formatea el tamaño en la unidad más apropiada."""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.2f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_to_mb(bytes_size):.2f} MB"
    else:
        return f"{bytes_to_gb(bytes_size):.2f} GB"

# ============================================================================
# FUNCIONES DE CÁLCULO Y ELIMINACIÓN
# ============================================================================

def get_folder_size(folder_path):
    """Calcula el tamaño total de una carpeta en bytes."""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
                except (OSError, PermissionError, FileNotFoundError):
                    continue
    except Exception as e:
        logging.debug(f"Error calculando tamaño de {folder_path}: {e}")
    return total_size

def clean_directory(path, total_freed):
    """Limpia un directorio y devuelve el espacio liberado."""
    try:
        if os.path.exists(path):
            size_before = get_folder_size(path)
            logging.info(f"Limpiando: {path} ({format_size(size_before)})")
            shutil.rmtree(path, ignore_errors=True)
            os.makedirs(path, exist_ok=True)
            return total_freed + size_before
    except (PermissionError, OSError) as e:
        logging.warning(f"No se pudo limpiar {path}: {e}")
    return total_freed

def clean_files(pattern, total_freed):
    """Elimina archivos según un patrón y devuelve el espacio liberado."""
    try:
        files_found = glob.glob(pattern, recursive=True)
        for file_path in files_found:
            try:
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    os.remove(file_path)
                    total_freed += size
                    logging.debug(f"Eliminado archivo: {file_path}")
                elif os.path.isdir(file_path):
                    size = get_folder_size(file_path)
                    shutil.rmtree(file_path, ignore_errors=True)
                    total_freed += size
                    logging.debug(f"Eliminado directorio: {file_path}")
            except (PermissionError, OSError, FileNotFoundError):
                continue
    except Exception as e:
        logging.debug(f"Error con patrón {pattern}: {e}")
    return total_freed

def remove_empty_dirs(root_path):
    """Elimina directorios vacíos recursivamente."""
    removed = 0
    try:
        for dirpath, dirnames, filenames in os.walk(root_path, topdown=False):
            try:
                if not dirnames and not filenames and dirpath != root_path:
                    os.rmdir(dirpath)
                    removed += 1
                    logging.debug(f"Directorio vacío eliminado: {dirpath}")
            except (OSError, PermissionError):
                continue
    except Exception as e:
        logging.debug(f"Error removiendo directorios vacíos en {root_path}: {e}")
    return removed

# ============================================================================
# LIMPIEZA AVANZADA - ARCHIVOS ANTIGUOS Y GRANDES
# ============================================================================

def clean_old_large_files(path, days=60, min_size_mb=100):
    """
    Elimina archivos grandes y antiguos de Downloads y Desktop.
    """
    removed_size = 0
    cutoff_time = time.time() - (days * 86400)
    min_size_bytes = min_size_mb * 1024 * 1024

    extensions_to_clean = [
        '.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm',  # Instaladores
        '.iso', '.img', '.vhd', '.vmdk',  # Imágenes de disco
        '.tmp', '.temp', '.bak', '.old',  # Temporales
    ]

    if not os.path.exists(path):
        return removed_size

    for root, _, files in os.walk(path):
        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                file_stat = os.stat(filepath)
                file_ext = os.path.splitext(filename)[1].lower()

                if (file_stat.st_mtime < cutoff_time and 
                    file_stat.st_size >= min_size_bytes and
                    file_ext in extensions_to_clean):

                    removed_size += file_stat.st_size
                    os.remove(filepath)
                    logging.info(f"Archivo antiguo eliminado: {filepath} ({format_size(file_stat.st_size)})")

            except (OSError, PermissionError, FileNotFoundError):
                continue

    return removed_size

# ============================================================================
# LIMPIEZA AVANZADA - ARCHIVOS DE 0 BYTES
# ============================================================================

def clean_zero_byte_files(root_path):
    """Elimina archivos de 0 bytes."""
    removed_count = 0

    for root, _, files in os.walk(root_path):
        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                if os.path.getsize(filepath) == 0:
                    os.remove(filepath)
                    removed_count += 1
                    logging.debug(f"Archivo 0 bytes eliminado: {filepath}")
            except (OSError, PermissionError, FileNotFoundError):
                continue

    return removed_count

# ============================================================================
# LIMPIEZA DE REGISTROS DE WINDOWS
# ============================================================================

def clean_windows_registry():
    """
    Limpia entradas obsoletas del registro de Windows.
    PRECAUCIÓN: Solo limpia ubicaciones seguras y conocidas.
    """
    if not is_admin():
        logging.warning("Se requieren permisos de administrador para limpiar el registro.")
        return 0

    cleaned_keys = 0

    # Rutas seguras para limpiar en el registro
    safe_registry_paths = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs"),
    ]

    for hkey, subkey_path in safe_registry_paths:
        try:
            key = winreg.OpenKey(hkey, subkey_path, 0, winreg.KEY_SET_VALUE)

            # Enumerar y eliminar valores (excepto "MRUList" y "(Default)")
            i = 0
            while True:
                try:
                    value_name, _, _ = winreg.EnumValue(key, i)
                    if value_name not in ["MRUList", ""]:
                        winreg.DeleteValue(key, value_name)
                        cleaned_keys += 1
                    else:
                        i += 1
                except OSError:
                    break

            winreg.CloseKey(key)
            logging.debug(f"Registro limpiado: {subkey_path}")

        except (WindowsError, OSError) as e:
            logging.debug(f"No se pudo limpiar {subkey_path}: {e}")

    return cleaned_keys

# ============================================================================
# LIMPIEZA DE DNS Y CACHÉ DE RED
# ============================================================================

def flush_dns_cache():
    """Limpia la caché DNS de Windows."""
    try:
        subprocess.run(["ipconfig", "/flushdns"], 
                      capture_output=True, 
                      check=False,
                      creationflags=subprocess.CREATE_NO_WINDOW)
        logging.info("Caché DNS limpiada exitosamente")
        return True
    except Exception as e:
        logging.warning(f"Error al limpiar caché DNS: {e}")
        return False

def reset_network_stack():
    """Reinicia la pila de red de Windows."""
    if not is_admin():
        logging.warning("Se requieren permisos de administrador para reiniciar la pila de red.")
        return False

    commands = [
        ["netsh", "winsock", "reset"],
        ["netsh", "int", "ip", "reset"],
    ]

    for cmd in commands:
        try:
            subprocess.run(cmd, 
                          capture_output=True, 
                          check=False,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            logging.info(f"Ejecutado: {' '.join(cmd)}")
        except Exception as e:
            logging.warning(f"Error ejecutando {' '.join(cmd)}: {e}")

    return True

# ============================================================================
# LIMPIEZA DE EVENT LOGS
# ============================================================================

def clear_event_logs():
    """Limpia los logs de eventos de Windows."""
    if not is_admin():
        logging.warning("Se requieren permisos de administrador para limpiar event logs.")
        return 0

    event_logs = [
        "Application", "System", "Security", "Setup",
        "Microsoft-Windows-Store/Operational",
        "Microsoft-Windows-TWinUI/Operational"
    ]

    cleared = 0
    for log_name in event_logs:
        try:
            subprocess.run(["wevtutil", "cl", log_name],
                          capture_output=True,
                          check=False,
                          creationflags=subprocess.CREATE_NO_WINDOW)
            cleared += 1
            logging.debug(f"Event log limpiado: {log_name}")
        except Exception as e:
            logging.debug(f"No se pudo limpiar {log_name}: {e}")

    return cleared

# ============================================================================
# PAPELERA DE RECICLAJE
# ============================================================================

def empty_recycle_bin():
    """Vacía la papelera de reciclaje usando API nativa de Windows."""
    try:
        # Flags: SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
        flags = 0x00000001 | 0x00000002 | 0x00000004
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
        logging.info("Papelera de reciclaje vaciada")
        return True
    except Exception as e:
        logging.warning(f"Error al vaciar papelera: {e}")
        return False

# ============================================================================
# LIMPIEZA DE WINDOWS UPDATE
# ============================================================================

def clean_windows_update():
    """Limpia archivos antiguos de Windows Update usando DISM."""
    if not is_admin():
        logging.warning("Se requieren permisos de administrador para limpiar Windows Update.")
        return 0

    total_freed = 0

    update_paths = [
        r"C:\Windows\SoftwareDistribution\Download",
        r"C:\Windows\SoftwareDistribution\DataStore\Logs",
    ]

    for path in update_paths:
        if os.path.exists(path):
            total_freed = clean_directory(path, total_freed)

    # Usar DISM para limpiar componentes de Windows
    try:
        logging.info("Ejecutando DISM /Cleanup-Image...")
        subprocess.run([
            "DISM.exe",
            "/Online",
            "/Cleanup-Image",
            "/StartComponentCleanup",
            "/ResetBase"
        ], capture_output=True, check=False, creationflags=subprocess.CREATE_NO_WINDOW, timeout=300)
        logging.info("DISM cleanup completado")
    except subprocess.TimeoutExpired:
        logging.warning("DISM timeout - operación muy larga, continuando...")
    except Exception as e:
        logging.debug(f"Error ejecutando DISM: {e}")

    return total_freed

# ============================================================================
# LIMPIEZA DE THUMBNAILS Y CACHÉ DE ICONOS
# ============================================================================

def clean_thumbnail_cache():
    """Limpia la caché de miniaturas e iconos de Windows."""
    total_freed = 0

    thumbcache_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 
                                   'Microsoft', 'Windows', 'Explorer')

    if os.path.exists(thumbcache_path):
        patterns = [
            os.path.join(thumbcache_path, 'thumbcache_*.db'),
            os.path.join(thumbcache_path, 'iconcache_*.db'),
        ]

        for pattern in patterns:
            total_freed = clean_files(pattern, total_freed)

    return total_freed

# ============================================================================
# OPTIMIZACIÓN DE PREFETCH
# ============================================================================

def optimize_prefetch():
    """
    Limpia archivos de prefetch antiguos (mantiene los recientes para rendimiento).
    """
    prefetch_path = r"C:\Windows\Prefetch"

    if not os.path.exists(prefetch_path):
        return 0

    total_freed = 0
    cutoff_time = time.time() - (30 * 86400)  # 30 días

    for filename in os.listdir(prefetch_path):
        filepath = os.path.join(prefetch_path, filename)
        try:
            if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff_time:
                size = os.path.getsize(filepath)
                os.remove(filepath)
                total_freed += size
        except (OSError, PermissionError):
            continue

    return total_freed

# ============================================================================
# LIMPIEZA DE WINDOWS DEFENDER
# ============================================================================

def clean_windows_defender():
    """Limpia archivos temporales y logs de Windows Defender."""
    total_freed = 0

    defender_paths = [
        r"C:\ProgramData\Microsoft\Windows Defender\Scans\History\Results",
        r"C:\ProgramData\Microsoft\Windows Defender\Scans\History\Service",
        os.path.join(os.environ.get('PROGRAMDATA', ''), 'Microsoft', 'Windows Defender', 'Support'),
    ]

    for path in defender_paths:
        if os.path.exists(path):
            total_freed = clean_directory(path, total_freed)

    return total_freed

# ============================================================================
# LIMPIEZA DE LOGS DEL SISTEMA
# ============================================================================

def clean_system_logs():
    """Limpia logs del sistema de Windows."""
    total_freed = 0

    log_patterns = [
        r"C:\Windows\Logs\**\*.log",
        r"C:\Windows\Logs\**\*.etl",
        r"C:\Windows\System32\LogFiles\**\*.log",
        r"C:\Windows\Panther\*.log",
    ]

    for pattern in log_patterns:
        total_freed = clean_files(pattern, total_freed)

    return total_freed

# ============================================================================
# FUNCIÓN PRINCIPAL DE LIMPIEZA
# ============================================================================

def system_maintenance():
    """Realiza el mantenimiento completo del sistema."""

    start_time = time.time()
    total_freed = 0

    # Mostrar notificación de inicio
    show_notification("🔧 Iniciando limpieza profunda del sistema...\nPor favor espere...", bg_color="#0066CC", duration=3000)

    logging.info("=" * 70)
    logging.info("INICIANDO LIMPIEZA PROFUNDA DEL SISTEMA")
    logging.info(f"Usuario: gustavo85")
    logging.info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("=" * 70)

    # ========================================================================
    # 1. LIMPIEZA DE ARCHIVOS TEMPORALES DEL SISTEMA
    # ========================================================================
    logging.info("\n[1/14] Limpiando archivos temporales del sistema...")
    temp_paths = [
        os.environ.get('TEMP', ''),
        os.environ.get('TMP', ''),
        r"C:\Windows\Temp",
        r"C:\Windows\Logs",
        r"C:\Windows\Minidump",
        r"C:\Windows\Downloaded Program Files",
        r"C:\Windows\System32\LogFiles",
    ]

    for path in temp_paths:
        if path and os.path.exists(path):
            total_freed = clean_directory(path, total_freed)

    # ========================================================================
    # 2. LIMPIEZA DE PREFETCH (OPTIMIZADO)
    # ========================================================================
    logging.info("\n[2/14] Optimizando Prefetch...")
    if is_admin():
        total_freed += optimize_prefetch()

    # ========================================================================
    # 3. LIMPIEZA DE WINDOWS UPDATE (CON DISM)
    # ========================================================================
    logging.info("\n[3/14] Limpiando archivos de Windows Update...")
    total_freed += clean_windows_update()

    # ========================================================================
    # 4. LIMPIEZA DE CACHÉ DEL SISTEMA
    # ========================================================================
    logging.info("\n[4/14] Limpiando caché del sistema...")
    cache_paths = [
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'INetCache'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'History'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'WebCache'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'Caches'),
    ]

    for path in cache_paths:
        if os.path.exists(path):
            total_freed = clean_directory(path, total_freed)

    # ========================================================================
    # 5. LIMPIEZA DE NAVEGADORES
    # ========================================================================
    logging.info("\n[5/14] Limpiando caché de navegadores...")
    browsers_cache = [
        # Google Chrome
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data', 'Default', 'Cache'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data', 'Default', 'Code Cache'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data', 'Default', 'GPUCache'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data', 'Default', 'Service Worker', 'CacheStorage'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data', 'ShaderCache'),

        # Mozilla Firefox
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Mozilla', 'Firefox', 'Profiles'),

        # Microsoft Edge
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data', 'Default', 'Cache'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data', 'Default', 'Code Cache'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data', 'Default', 'GPUCache'),

        # Opera
        os.path.join(os.environ.get('APPDATA', ''), 'Opera Software', 'Opera Stable', 'Cache'),
        os.path.join(os.environ.get('APPDATA', ''), 'Opera Software', 'Opera Stable', 'GPUCache'),

        # Brave
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'BraveSoftware', 'Brave-Browser', 'User Data', 'Default', 'Cache'),

        # Vivaldi
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Vivaldi', 'User Data', 'Default', 'Cache'),

        # Internet Explorer
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'INetCache', 'IE'),
    ]

    for cache_path in browsers_cache:
        if os.path.exists(cache_path):
            total_freed = clean_directory(cache_path, total_freed)

    # ========================================================================
    # 6. LIMPIEZA DE APLICACIONES COMUNES
    # ========================================================================
    logging.info("\n[6/14] Limpiando caché de aplicaciones...")
    programs_cache = [
        # Adobe
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Adobe', 'Common', 'Media Cache'),
        os.path.join(os.environ.get('APPDATA', ''), 'Adobe', 'Common', 'Media Cache Files'),

        # Discord
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Discord', 'Cache'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Discord', 'Code Cache'),
        os.path.join(os.environ.get('APPDATA', ''), 'discord', 'Cache'),

        # Spotify
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Spotify', 'Data'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Spotify', 'Storage'),

        # Steam
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Steam', 'htmlcache'),

        # Zoom
        os.path.join(os.environ.get('APPDATA', ''), 'Zoom', 'data', 'caches'),

        # Slack
        os.path.join(os.environ.get('APPDATA', ''), 'Slack', 'Cache'),
        os.path.join(os.environ.get('APPDATA', ''), 'Slack', 'Code Cache'),

        # Microsoft Teams
        os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Teams', 'Cache'),
        os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Teams', 'tmp'),
        os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Teams', 'Service Worker', 'CacheStorage'),

        # VS Code
        os.path.join(os.environ.get('APPDATA', ''), 'Code', 'Cache'),
        os.path.join(os.environ.get('APPDATA', ''), 'Code', 'CachedData'),
        os.path.join(os.environ.get('APPDATA', ''), 'Code', 'Code Cache'),

        # Telegram
        os.path.join(os.environ.get('APPDATA', ''), 'Telegram Desktop', 'tdata', 'user_data', 'cache'),

        # WhatsApp
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'WhatsApp', 'Cache'),

        # Skype
        os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Skype for Desktop', 'Cache'),

        # Microsoft Office
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Office', '16.0', 'OfficeFileCache'),

        # Node.js
        os.path.join(os.environ.get('APPDATA', ''), 'npm-cache'),

        # Python pip
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'pip', 'cache'),
    ]

    for program_path in programs_cache:
        if os.path.exists(program_path):
            total_freed = clean_directory(program_path, total_freed)

    # ========================================================================
    # 7. LIMPIEZA DE CACHÉ DE GPU Y DRIVERS
    # ========================================================================
    logging.info("\n[7/14] Limpiando caché de GPU y drivers...")
    gpu_cache_paths = [
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'D3DSCache'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'NVIDIA', 'DXCache'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'NVIDIA', 'GLCache'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'AMD', 'DxCache'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'AMD', 'GLCache'),
        r'C:\ProgramData\NVIDIA Corporation\NV_Cache',
    ]

    for path in gpu_cache_paths:
        if os.path.exists(path):
            total_freed = clean_directory(path, total_freed)

    # ========================================================================
    # 8. LIMPIEZA DE ERROR REPORTS Y DUMPS
    # ========================================================================
    logging.info("\n[8/14] Limpiando reportes de errores...")
    error_report_paths = [
        os.path.join(os.environ.get('PROGRAMDATA', ''), 'Microsoft', 'Windows', 'WER', 'ReportArchive'),
        os.path.join(os.environ.get('PROGRAMDATA', ''), 'Microsoft', 'Windows', 'WER', 'ReportQueue'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'WER'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'CrashDumps'),
    ]

    for path in error_report_paths:
        if os.path.exists(path):
            total_freed = clean_directory(path, total_freed)

    # ========================================================================
    # 9. LIMPIEZA DE THUMBNAILS E ICONOS
    # ========================================================================
    logging.info("\n[9/14] Limpiando caché de miniaturas e iconos...")
    total_freed += clean_thumbnail_cache()

    # ========================================================================
    # 10. LIMPIEZA DE WINDOWS DEFENDER
    # ========================================================================
    logging.info("\n[10/14] Limpiando archivos de Windows Defender...")
    total_freed += clean_windows_defender()

    # ========================================================================
    # 11. LIMPIEZA DE LOGS DEL SISTEMA
    # ========================================================================
    logging.info("\n[11/14] Limpiando logs del sistema...")
    total_freed += clean_system_logs()

    # ========================================================================
    # 12. LIMPIEZA DE ARCHIVOS TEMPORALES GLOBALES
    # ========================================================================
    logging.info("\n[12/14] Limpiando archivos temporales globales...")
    global_patterns = [
        os.path.join(os.environ.get('USERPROFILE', ''), '**', '*.tmp'),
        os.path.join(os.environ.get('USERPROFILE', ''), '**', '*.temp'),
        r'C:\*.dmp',
        r'C:\Windows\*.log',
    ]

    for pattern in global_patterns:
        total_freed = clean_files(pattern, total_freed)

    # Limpiar archivos de 0 bytes
    user_home = os.path.expanduser("~")
    zero_count = clean_zero_byte_files(user_home)
    logging.info(f"Archivos de 0 bytes eliminados: {zero_count}")

    # ========================================================================
    # 13. LIMPIEZA DE ARCHIVOS ANTIGUOS EN DOWNLOADS Y DESKTOP
    # ========================================================================
    logging.info("\n[13/14] Limpiando archivos antiguos de Downloads y Desktop...")
    downloads_path = os.path.join(user_home, "Downloads")
    desktop_path = os.path.join(user_home, "Desktop")

    total_freed += clean_old_large_files(downloads_path, days=60, min_size_mb=100)
    total_freed += clean_old_large_files(desktop_path, days=90, min_size_mb=100)

    # ========================================================================
    # 14. LIMPIEZA DEL SISTEMA
    # ========================================================================
    logging.info("\n[14/14] Limpieza del sistema...")

    # Vaciar papelera
    empty_recycle_bin()

    # Limpiar DNS
    flush_dns_cache()

    # Limpiar Event Logs
    if is_admin():
        clear_event_logs()

    # Limpiar registro (solo áreas seguras)
    if is_admin():
        clean_windows_registry()

    # Eliminar directorios vacíos
    removed_dirs = remove_empty_dirs(user_home)
    logging.info(f"Directorios vacíos eliminados: {removed_dirs}")

    # ========================================================================
    # RESUMEN FINAL
    # ========================================================================
    end_time = time.time()
    elapsed_time = end_time - start_time

    freed_mb = bytes_to_mb(total_freed)
    freed_gb = bytes_to_gb(total_freed)

    logging.info("\n" + "=" * 70)
    logging.info("LIMPIEZA COMPLETADA")
    logging.info("=" * 70)
    logging.info(f"Espacio liberado: {format_size(total_freed)}")
    logging.info(f"Tiempo transcurrido: {elapsed_time:.2f} segundos")
    logging.info(f"Log guardado en: {log_file}")
    logging.info("=" * 70)

    # Esperar 10s antes de mostrar el resultado final para evitar solapamiento
    time.sleep(10)

    # Mostrar notificación de finalización (con más duración)
    if freed_gb >= 1:
        message = f"✅ Limpieza completada con éxito\n\n💾 Espacio liberado: {freed_gb:.2f} GB\n⏱️ Tiempo: {elapsed_time:.1f}s"
    else:
        message = f"✅ Limpieza completada con éxito\n\n💾 Espacio liberado: {freed_mb:.2f} MB\n⏱️ Tiempo: {elapsed_time:.1f}s"

    # Mostrar notificación final coordinada y esperar a que termine (con timeout)
    final_event = show_notification(message, bg_color="#006400", duration=6000)
    # Esperar a que termine (duración + margen). Si algo falla, continuamos.
    try:
        final_event.wait(timeout=8)
    except Exception:
        pass

    return total_freed

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    try:
        # Verificar si se ejecuta con privilegios de administrador
        if is_admin():
            logging.info("✓ Ejecutando con privilegios de administrador")
        else:
            logging.warning("⚠ Ejecutando sin privilegios de administrador. Algunas operaciones pueden fallar.")
            logging.warning("  Recomendación: Ejecutar como administrador para limpieza completa.")

        # Ejecutar limpieza
        system_maintenance()

    except KeyboardInterrupt:
        logging.info("\n\nLimpieza interrumpida por el usuario.")
        show_notification("⚠️ Limpieza interrumpida por el usuario", bg_color="#FF8C00", duration=3000)
        time.sleep(4)
        sys.exit(0)
    except Exception as e:
        logging.error(f"Error crítico durante la limpieza: {e}", exc_info=True)
        show_notification(f"❌ Error durante la limpieza:\n{str(e)[:100]}", bg_color="#8B0000", duration=5000)
        time.sleep(6)
        sys.exit(1)