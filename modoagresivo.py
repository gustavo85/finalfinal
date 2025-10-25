# -*- coding: utf-8 -*-
import ctypes
import json
import os
import sys
import time
import psutil
import threading
import subprocess
import tkinter as tk
from tkinter import font
from pathlib import Path
import shutil
import winreg

try:
    import win32api
    import win32con
    import win32gui
    import win32process
except ImportError:
    sys.exit(1)

STATE_FILE = ".mode_state.json"
CURRENT_MODE = "aggressive"
NOMBRE_ARCHIVO_CONFIG = "config.json"
PROCESS_SET_INFORMATION = 0x0200
LIMITE_RAM_PORCENTAJE = 80.0
INTERVALO_MONITOREO_RAM_SEGUNDOS = 60
TIEMPO_ESPERA_POST_LIMPIEZA_MINUTOS = 60
TIEMPO_INACTIVIDAD_PARA_CIERRE_MINUTOS = 60
CPU_UMBRAL_INACTIVIDAD_PORCENTAJE = 1.0

# Constantes para gestión de energía
POWER_PLATFORM_ROLE_MOBILE = 3
POWER_PLATFORM_ROLE_SLATE = 4

class MEMORY_PRIORITY_INFORMATION(ctypes.Structure):
    _fields_ = [("MemoryPriority", ctypes.c_ulong)]

class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ('ACLineStatus', ctypes.c_byte),
        ('BatteryFlag', ctypes.c_byte),
        ('BatteryLifePercent', ctypes.c_byte),
        ('SystemStatusFlag', ctypes.c_byte),
        ('BatteryLifeTime', ctypes.c_ulong),
        ('BatteryFullLifeTime', ctypes.c_ulong),
    ]

def check_shutdown_signal():
    if not os.path.exists(STATE_FILE):
        return False
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
            return state.get("state") == "game"
    except:
        return False

def es_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def solicitar_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit(0)

def es_laptop():
    """
    Detecta si el equipo es una laptop/portátil.
    Retorna True si es laptop, False si es PC de escritorio.
    """
    try:
        # Método 1: Verificar si hay batería
        battery = psutil.sensors_battery()
        if battery is None:
            return False
        
        # Método 2: Verificar el rol de la plataforma en Windows
        PwrGetPlatformRole = ctypes.windll.powrprof.PowerDeterminePlatformRole
        role = PwrGetPlatformRole()
        
        # Roles 3 y 4 corresponden a laptops/tablets
        if role in [POWER_PLATFORM_ROLE_MOBILE, POWER_PLATFORM_ROLE_SLATE]:
            return True
        
        return True  # Si tiene batería, es laptop
    except:
        return False

def obtener_estado_bateria():
    """
    Obtiene el estado actual de la batería.
    Retorna: (porcentaje, está_conectada)
    """
    try:
        status = SYSTEM_POWER_STATUS()
        ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status))
        
        porcentaje = status.BatteryLifePercent
        conectada = status.ACLineStatus == 1
        
        return porcentaje, conectada
    except:
        try:
            battery = psutil.sensors_battery()
            if battery:
                return battery.percent, battery.power_plugged
        except:
            pass
    return 100, True

def _crear_ventana_notificacion(texto, duracion_ms=5000, color_fondo="#006400"):
    """Versión mejorada que acepta color de fondo personalizado"""
    root = tk.Tk()
    root.title("")
    root.overrideredirect(True)
    root.geometry("320x120")
    root.configure(bg=color_fondo)
    root.resizable(False, False)
    label = tk.Message(root, text=texto, fg="white", bg=color_fondo, 
                      font=font.Font(family="Arial", size=11, weight="bold"), 
                      width=300, justify='center')
    label.pack(expand=True, padx=10, pady=10)
    screen_width = root.winfo_screenwidth()
    initial_x = screen_width
    initial_y = 50
    root.geometry(f"320x120+{initial_x}+{initial_y}")
    
    def slide_in():
        current_x = root.winfo_x()
        target_x = screen_width - 330
        if current_x > target_x:
            new_x = max(current_x - 20, target_x)
            root.geometry(f"320x120+{new_x}+{initial_y}")
            root.after(10, slide_in)
        else:
            root.after(duracion_ms, slide_out)
    
    def slide_out():
        current_x = root.winfo_x()
        if current_x < screen_width:
            new_x = current_x + 20
            root.geometry(f"320x120+{new_x}+{initial_y}")
            root.after(10, slide_out)
        else:
            root.destroy()
    
    root.attributes("-topmost", True)
    root.after(100, slide_in)
    root.mainloop()

def mostrar_notificacion_energia(tipo_plan):
    """Muestra notificación de cambio de plan de energía con color azul claro"""
    textos = {
        "eficiencia_adaptativa": "PLAN DE ENERGÍA: EFICIENCIA ADAPTATIVA\nBaja latencia con ahorro inteligente",
        "ahorro_bateria": "PLAN DE ENERGÍA: AHORRO DE BATERÍA\nBatería ≤20% - Ahorro agresivo activado",
        "eficiencia_laptop": "PLAN DE ENERGÍA: EFICIENCIA ADAPTATIVA\nOptimizado para portátil con batería >20%"
    }
    texto = textos.get(tipo_plan, "Plan de energía personalizado activado")
    threading.Thread(target=_crear_ventana_notificacion, 
                    args=(texto, 5000, "#4A90E2"), daemon=True).start()

def aplicar_plan_energia_profesional(tipo_plan="eficiencia_adaptativa"):
    """
    Aplica un plan de energía personalizado y profesional.
    
    Tipos de plan:
    - eficiencia_adaptativa: Prioriza baja latencia con ahorro inteligente
    - ahorro_bateria: Ahorro agresivo cuando batería ≤20%
    - eficiencia_laptop: Igual que adaptativa pero optimizado para laptop
    """
    try:
        # Rutas del registro para configuración de energía
        base_key = r"SYSTEM\CurrentControlSet\Control\Power\PowerSettings"
        
        # GUIDs importantes para la configuración
        configs = {
            # Procesador
            "cpu_min": {
                "guid": "54533251-82be-4824-96c1-47b60b740d00\\bc5038f7-23e0-4960-96da-33abaf5935ec",
                "eficiencia_adaptativa": 5,    # Mínimo 5% - respuesta rápida en demanda
                "ahorro_bateria": 0,             # Mínimo 0% - máximo ahorro
                "eficiencia_laptop": 5
            },
            "cpu_max": {
                "guid": "54533251-82be-4824-96c1-47b60b740d00\\bc5038f7-23e0-4960-96da-33abaf5935ed",
                "eficiencia_adaptativa": 95,    # Máximo 95% - evita throttling térmico
                "ahorro_bateria": 50,            # Máximo 50% - ahorro significativo
                "eficiencia_laptop": 90
            },
            # Latencia del sistema (procesamiento)
            "latencia_sistema": {
                "guid": "54533251-82be-4824-96c1-47b60b740d00\\5d76a2ca-e8c0-402f-a133-2158492d58ad",
                "eficiencia_adaptativa": 0,      # Sin tolerancia a latencia
                "ahorro_bateria": 1,              # Tolerancia alta para ahorrar
                "eficiencia_laptop": 0
            },
            # Boost del procesador
            "cpu_boost": {
                "guid": "54533251-82be-4824-96c1-47b60b740d00\\be337238-0d82-4146-a960-4f3749d470c7",
                "eficiencia_adaptativa": 2,      # Eficiente y agresivo (boost adaptativo)
                "ahorro_bateria": 0,              # Desactivado
                "eficiencia_laptop": 2
            },
            # Política de enfriamiento
            "enfriamiento": {
                "guid": "54533251-82be-4824-96c1-47b60b740d00\\94d3a615-a899-4ac5-ae2b-e4d8f634367f",
                "eficiencia_adaptativa": 1,      # Activo - mejor rendimiento
                "ahorro_bateria": 0,              # Pasivo - ahorro de energía
                "eficiencia_laptop": 1
            },
            # Ahorro de energía del procesador
            "cpu_ahorro": {
                "guid": "54533251-82be-4824-96c1-47b60b740d00\\68dd2f27-a4ce-4e11-8487-3794e4135dfa",
                "eficiencia_adaptativa": 50,     # Balance
                "ahorro_bateria": 100,            # Máximo ahorro
                "eficiencia_laptop": 60
            },
            # Disco duro - tiempo antes de apagar
            "disco_timeout": {
                "guid": "0012ee47-9041-4b5d-9b77-535fba8b1442\\6738e2c4-e8a5-4a42-b16a-e040e769756e",
                "eficiencia_adaptativa": 0,      # Nunca apagar - baja latencia
                "ahorro_bateria": 300,            # 5 minutos
                "eficiencia_laptop": 600          # 10 minutos
            },
            # USB - suspensión selectiva
            "usb_suspend": {
                "guid": "2a737441-1930-4402-8d77-b2bebba308a3\\48e6b7a6-50f5-4782-a5d4-53bb8f07e226",
                "eficiencia_adaptativa": 0,      # Desactivado - sin latencia USB
                "ahorro_bateria": 1,              # Activado
                "eficiencia_laptop": 0
            },
            # PCI Express - gestión de energía de enlaces
            "pcie_power": {
                "guid": "501a4d13-42af-4429-9fd1-a8218c268e20\\ee12f906-d277-404b-b6da-e5fa1a576df5",
                "eficiencia_adaptativa": 0,      # Desactivado - máxima velocidad PCIe
                "ahorro_bateria": 3,              # Ahorro agresivo
                "eficiencia_laptop": 1            # Ahorro moderado
            },
            # Pantalla - tiempo antes de apagar
            "pantalla_timeout": {
                "guid": "7516b95f-f776-4464-8c53-06167f40cc99\\3c0bc021-c8a8-4e07-a973-6b14cbcb2b7e",
                "eficiencia_adaptativa": 600,    # 10 minutos
                "ahorro_bateria": 120,            # 2 minutos
                "eficiencia_laptop": 300          # 5 minutos
            },
            # Brillo adaptativo
            "brillo_adaptativo": {
                "guid": "7516b95f-f776-4464-8c53-06167f40cc99\\fbd9aa66-9553-4097-ba44-ed6e9d65eab8",
                "eficiencia_adaptativa": 1,      # Activado
                "ahorro_bateria": 1,              # Activado
                "eficiencia_laptop": 1
            },
            # Nivel de brillo
            "brillo_nivel": {
                "guid": "7516b95f-f776-4464-8c53-06167f40cc99\\aded5e82-b909-4619-9949-f5d71dac0bcb",
                "eficiencia_adaptativa": 80,     # 80%
                "ahorro_bateria": 40,             # 40% - ahorro significativo
                "eficiencia_laptop": 70           # 70%
            },
        }
        
        # Obtener el GUID del plan de energía activo
        plan_guid = obtener_plan_energia_activo()
        
        if not plan_guid:
            return False
        
        # Aplicar cada configuración
        for nombre, config in configs.items():
            try:
                valor = config.get(tipo_plan, config["eficiencia_adaptativa"])
                guid_parts = config["guid"].split("\\")
                
                if len(guid_parts) == 2:
                    subgroup_guid = guid_parts[0]
                    setting_guid = guid_parts[1]
                    
                    # Usar powercfg para aplicar configuraciones
                    # AC (conectado a corriente)
                    subprocess.run(
                        ["powercfg", "/setacvalueindex", plan_guid, 
                         subgroup_guid, setting_guid, str(valor)],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    # DC (en batería)
                    subprocess.run(
                        ["powercfg", "/setdcvalueindex", plan_guid, 
                         subgroup_guid, setting_guid, str(valor)],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
            except:
                continue
        
        # Aplicar el esquema para que los cambios tengan efecto
        subprocess.run(
            ["powercfg", "/setactive", plan_guid],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        return True
    except:
        return False

def obtener_plan_energia_activo():
    """Obtiene el GUID del plan de energía actualmente activo"""
    try:
        result = subprocess.run(
            ["powercfg", "/getactivescheme"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode == 0:
            # El formato es: "Power Scheme GUID: {guid} (nombre)"
            output = result.stdout.strip()
            start = output.find("{")
            end = output.find("}")
            if start != -1 and end != -1:
                return output[start+1:end]
    except:
        pass
    return None

def calcular_demanda_sistema():
    """
    Calcula la demanda actual del sistema.
    Retorna un valor entre 0 (sin demanda) y 100 (demanda máxima)
    """
    try:
        # Factores de demanda
        cpu_percent = psutil.cpu_percent(interval=0.5)
        
        # Uso de disco (IO)
        disk_io = psutil.disk_io_counters()
        disk_usage = 0
        if hasattr(disk_io, 'read_bytes') and hasattr(disk_io, 'write_bytes'):
            # Simplificación: si hay actividad reciente de disco
            disk_usage = min((disk_io.read_bytes + disk_io.write_bytes) / (100 * 1024 * 1024), 100)
        
        # Uso de red
        net_io = psutil.net_io_counters()
        net_usage = 0
        if hasattr(net_io, 'bytes_sent') and hasattr(net_io, 'bytes_recv'):
            net_usage = min((net_io.bytes_sent + net_io.bytes_recv) / (50 * 1024 * 1024), 100)
        
        # Ponderación: CPU es el factor más importante
        demanda = (cpu_percent * 0.7) + (disk_usage * 0.2) + (net_usage * 0.1)
        
        return min(demanda, 100)
    except:
        return 50  # Valor por defecto en caso de error

def monitor_energia():
    """
    Monitorea el estado del sistema y ajusta el plan de energía dinámicamente.
    """
    is_laptop = es_laptop()
    plan_actual = None
    ultimo_cambio = time.time()
    TIEMPO_MIN_ENTRE_CAMBIOS = 30  # Segundos mínimos entre cambios de plan
    
    # Esperar 10 segundos antes de comenzar
    time.sleep(10)
    
    # Aplicar plan inicial
    if is_laptop:
        porcentaje_bat, conectada = obtener_estado_bateria()
        if porcentaje_bat <= 20 and not conectada:
            aplicar_plan_energia_profesional("ahorro_bateria")
            mostrar_notificacion_energia("ahorro_bateria")
            plan_actual = "ahorro_bateria"
        else:
            aplicar_plan_energia_profesional("eficiencia_laptop")
            mostrar_notificacion_energia("eficiencia_laptop")
            plan_actual = "eficiencia_laptop"
    else:
        aplicar_plan_energia_profesional("eficiencia_adaptativa")
        mostrar_notificacion_energia("eficiencia_adaptativa")
        plan_actual = "eficiencia_adaptativa"
    
    while True:
        try:
            if check_shutdown_signal():
                break
            
            tiempo_actual = time.time()
            
            if is_laptop:
                porcentaje_bat, conectada = obtener_estado_bateria()
                
                # Lógica para laptop
                if porcentaje_bat <= 20 and not conectada:
                    if plan_actual != "ahorro_bateria" and (tiempo_actual - ultimo_cambio) > TIEMPO_MIN_ENTRE_CAMBIOS:
                        aplicar_plan_energia_profesional("ahorro_bateria")
                        mostrar_notificacion_energia("ahorro_bateria")
                        plan_actual = "ahorro_bateria"
                        ultimo_cambio = tiempo_actual
                elif plan_actual != "eficiencia_laptop" and (tiempo_actual - ultimo_cambio) > TIEMPO_MIN_ENTRE_CAMBIOS:
                    aplicar_plan_energia_profesional("eficiencia_laptop")
                    mostrar_notificacion_energia("eficiencia_laptop")
                    plan_actual = "eficiencia_laptop"
                    ultimo_cambio = tiempo_actual
            
            # Pequeña pausa antes del siguiente chequeo
            time.sleep(15)  # Verificar cada 15 segundos
        except:
            time.sleep(30)

# Config cache for optimization
_config_cache = None
_config_mtime = 0

def cargar_config():
    """
    Carga la configuración desde config.json con caché.
    Retorna:
        - lista_blanca: procesos ignorados en ajustes de prioridad
        - lista_juegos: lista de juegos
        - ignorar: procesos que NO se deben cerrar por inactividad
    """
    global _config_cache, _config_mtime
    
    if not os.path.exists(NOMBRE_ARCHIVO_CONFIG):
        return set(), set(), set()
    
    try:
        current_mtime = os.path.getmtime(NOMBRE_ARCHIVO_CONFIG)
        if _config_cache is None or current_mtime > _config_mtime:
            with open(NOMBRE_ARCHIVO_CONFIG, "r") as f:
                datos = json.load(f)
                _config_cache = datos
                _config_mtime = current_mtime
        
        lista_blanca = set(item.lower() for item in _config_cache.get("lista_blanca", []))
        lista_juegos = set(item.lower() for item in _config_cache.get("juegos", []))
        ignorar = set(item.lower() for item in _config_cache.get("ignorar", []))
        return lista_blanca, lista_juegos, ignorar
    except (IOError, OSError, PermissionError) as e:
        print(f"Error de archivo config: {e}")
        return set(), set(), set()
    except json.JSONDecodeError as e:
        print(f"Error JSON en config: {e}")
        return set(), set(), set()
    except Exception as e:
        print(f"Error inesperado cargando config: {e}")
        return set(), set(), set()

def obtener_pid_primer_plano():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid
    except:
        return None

def obtener_todos_hijos_recursivo(pid, hijos_set=None):
    """
    Obtiene todos los procesos hijos de un PID de forma recursiva.
    Retorna un set con todos los PIDs hijos (incluyendo nietos, bisnietos, etc.)
    """
    if hijos_set is None:
        hijos_set = set()
    
    try:
        proceso_padre = psutil.Process(pid)
        hijos_directos = proceso_padre.children(recursive=False)
        
        for hijo in hijos_directos:
            if hijo.pid not in hijos_set:
                hijos_set.add(hijo.pid)
                # Recursión para obtener todos los descendientes
                obtener_todos_hijos_recursivo(hijo.pid, hijos_set)
    except:
        pass
    
    return hijos_set

def obtener_todas_instancias_proceso(nombre_proceso):
    """
    Obtiene todos los PIDs de procesos con el mismo nombre.
    Ejemplo: todos los chrome.exe, todos los svchost.exe, etc.
    """
    pids = set()
    nombre_lower = nombre_proceso.lower()
    
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() == nombre_lower:
                    pids.add(proc.pid)
            except:
                continue
    except:
        pass
    
    return pids

def obtener_grupo_completo_proceso(pid):
    """
    Obtiene el grupo completo de un proceso:
    1. Todos los procesos hijos (recursivo)
    2. Todas las instancias con el mismo nombre
    3. Los hijos de todas esas instancias
    
    Retorna: (set de PIDs, nombre del proceso)
    """
    grupo_pids = set()
    nombre_proceso = None
    
    try:
        proceso = psutil.Process(pid)
        nombre_proceso = proceso.name()
        
        # 1. Agregar el PID principal
        grupo_pids.add(pid)
        
        # 2. Obtener todos los hijos recursivamente
        hijos = obtener_todos_hijos_recursivo(pid)
        grupo_pids.update(hijos)
        
        # 3. Obtener todas las instancias con el mismo nombre
        instancias_mismo_nombre = obtener_todas_instancias_proceso(nombre_proceso)
        
        # 4. Para cada instancia, obtener también sus hijos
        for instancia_pid in instancias_mismo_nombre:
            grupo_pids.add(instancia_pid)
            hijos_instancia = obtener_todos_hijos_recursivo(instancia_pid)
            grupo_pids.update(hijos_instancia)
    except:
        pass
    
    return grupo_pids, nombre_proceso

def proceso_en_lista(pid, lista):
    """
    Verifica si un proceso está en una lista específica.
    """
    try:
        proceso = psutil.Process(pid)
        nombre = proceso.name().lower()
        
        # Verificar si el proceso principal está en la lista
        if nombre in lista:
            return True
        
        # Verificar si algún padre está en la lista
        try:
            padre = proceso.parent()
            while padre is not None:
                if padre.name().lower() in lista:
                    return True
                padre = padre.parent()
        except:
            pass
            
    except:
        pass
    
    return False

def establecer_prioridad_memoria(pid, prioridad):
    try:
        h_proceso = win32api.OpenProcess(PROCESS_SET_INFORMATION, False, pid)
        if h_proceso:
            info_prioridad = MEMORY_PRIORITY_INFORMATION(prioridad)
            ctypes.windll.kernel32.SetProcessInformation(
                int(h_proceso),
                win32process.ProcessMemoryPriority,
                ctypes.byref(info_prioridad),
                ctypes.sizeof(info_prioridad)
            )
            win32api.CloseHandle(h_proceso)
    except:
        pass

def establecer_prioridad_io(pid, prioridad_io):
    try:
        proceso = psutil.Process(pid)
        proceso.ionice(prioridad_io)
    except:
        pass

def aplicar_configuracion_a_grupo(pids_grupo, es_primer_plano, nucleos_totales):
    """
    Aplica configuración de prioridad a un grupo completo de procesos.
    """
    MEMORY_PRIORITY_LOW = 1
    MEMORY_PRIORITY_NORMAL = 3
    
    for pid in pids_grupo:
        try:
            proc = psutil.Process(pid)
            
            if es_primer_plano:
                # Configuración para primer plano
                proc.nice(psutil.HIGH_PRIORITY_CLASS)
                establecer_prioridad_memoria(pid, MEMORY_PRIORITY_NORMAL)
                establecer_prioridad_io(pid, psutil.IOPRIO_NORMAL)
                if nucleos_totales >= 8:
                    proc.cpu_affinity(list(range(1, nucleos_totales)))
                else:
                    proc.cpu_affinity(list(range(nucleos_totales)))
            else:
                # Configuración para segundo plano
                proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                establecer_prioridad_memoria(pid, MEMORY_PRIORITY_LOW)
                establecer_prioridad_io(pid, psutil.IOPRIO_VERYLOW)
                if nucleos_totales >= 8:
                    proc.cpu_affinity([0] + list(range(nucleos_totales - 3, nucleos_totales)))
                elif nucleos_totales >= 4:
                    proc.cpu_affinity([0, 3])
                elif nucleos_totales >= 2:
                    proc.cpu_affinity([1])
        except:
            continue

def mostrar_notificacion_inicio():
    """Notificación de inicio del modo agresivo"""
    texto_notificacion = "OPTIMIZACION AGRESIVA ACTIVADA"
    _crear_ventana_notificacion(texto_notificacion, duracion_ms=5000)

def mostrar_notificacion_limpieza():
    texto_notificacion = "se realizo una limpieza de memoria ram y ram en cache para reducir su porcentaje de consumo"
    _crear_ventana_notificacion(texto_notificacion, duracion_ms=6000)

def mostrar_notificacion_cierre(nombre_proceso):
    texto_notificacion = f"Se detuvo la ejecución de\n'{nombre_proceso}'\npor inactividad prolongada."
    _crear_ventana_notificacion(texto_notificacion, duracion_ms=5000)

def monitor_y_limpieza_ram():
    while True:
        try:
            if check_shutdown_signal():
                break
            uso_ram = psutil.virtual_memory().percent
            if uso_ram > LIMITE_RAM_PORCENTAJE:
                if not os.path.exists("emptystandbylist.exe"):
                    time.sleep(TIEMPO_ESPERA_POST_LIMPIEZA_MINUTOS * 60)
                    continue
                try:
                    comandos = [
                        ["emptystandbylist.exe", "workingsets"], 
                        ["emptystandbylist.exe", "standbylist"],
                        ["emptystandbylist.exe", "modifiedpagelist"], 
                        ["emptystandbylist.exe", "workingsets"]
                    ]
                    for cmd in comandos:
                        subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    threading.Thread(target=mostrar_notificacion_limpieza, daemon=True).start()
                    time.sleep(TIEMPO_ESPERA_POST_LIMPIEZA_MINUTOS * 60)
                except:
                    time.sleep(TIEMPO_ESPERA_POST_LIMPIEZA_MINUTOS * 60)
            else:
                time.sleep(INTERVALO_MONITOREO_RAM_SEGUNDOS)
        except:
            time.sleep(INTERVALO_MONITOREO_RAM_SEGUNDOS)

def monitorear_y_terminar_inactivos(ignorar):
    """
    Monitorea y termina grupos completos de procesos inactivos.
    Solo respeta la lista_ignorados para NO cerrar procesos.
    """
    procesos_inactivos = {}
    grupos_procesados = {}
    
    while True:
        try:
            if check_shutdown_signal():
                break
            
            pid_primer_plano = obtener_pid_primer_plano()
            
            # Obtener grupo del proceso en primer plano
            grupo_primer_plano = set()
            if pid_primer_plano:
                grupo_primer_plano, _ = obtener_grupo_completo_proceso(pid_primer_plano)
            
            # Limpiar PIDs que ya no existen
            pids_actuales = {p.pid for p in psutil.process_iter(['pid'])}
            pids_a_eliminar = set(procesos_inactivos.keys()) - pids_actuales
            for pid in pids_a_eliminar:
                del procesos_inactivos[pid]
            
            # Agrupar procesos por nombre para procesarlos juntos
            procesos_por_nombre = {}
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    nombre = proc.info['name'].lower()
                    if nombre not in procesos_por_nombre:
                        procesos_por_nombre[nombre] = []
                    procesos_por_nombre[nombre].append(proc)
                except:
                    continue
            
            # Procesar cada grupo de procesos con el mismo nombre
            for nombre_proc, lista_procs in procesos_por_nombre.items():
                try:
                    # Verificar si está en ignorar (NO cerrar por inactividad)
                    if nombre_proc in ignorar:
                        for proc in lista_procs:
                            if proc.pid in procesos_inactivos:
                                del procesos_inactivos[proc.pid]
                        continue
                    
                    # Verificar si alguno está en primer plano
                    alguno_en_primer_plano = any(proc.pid in grupo_primer_plano for proc in lista_procs)
                    if alguno_en_primer_plano:
                        for proc in lista_procs:
                            if proc.pid in procesos_inactivos:
                                del procesos_inactivos[proc.pid]
                        continue
                    
                    # Verificar si es el proceso propio
                    if any(proc.pid == os.getpid() for proc in lista_procs):
                        continue
                    
                    # Calcular CPU promedio del grupo
                    cpu_total = sum(proc.info['cpu_percent'] for proc in lista_procs)
                    cpu_promedio = cpu_total / len(lista_procs)
                    
                    # Usar el primer PID como representante del grupo
                    pid_representante = lista_procs[0].pid
                    
                    if cpu_promedio < CPU_UMBRAL_INACTIVIDAD_PORCENTAJE:
                        if pid_representante not in procesos_inactivos:
                            procesos_inactivos[pid_representante] = time.time()
                        else:
                            tiempo_inactivo = time.time() - procesos_inactivos[pid_representante]
                            if tiempo_inactivo > TIEMPO_INACTIVIDAD_PARA_CIERRE_MINUTOS * 60:
                                # Terminar todo el grupo
                                for proc in lista_procs:
                                    try:
                                        proc.terminate()
                                    except:
                                        pass
                                
                                threading.Thread(
                                    target=mostrar_notificacion_cierre, 
                                    args=(f"{nombre_proc} (todas las instancias)",), 
                                    daemon=True
                                ).start()
                                
                                if pid_representante in procesos_inactivos:
                                    del procesos_inactivos[pid_representante]
                    else:
                        if pid_representante in procesos_inactivos:
                            del procesos_inactivos[pid_representante]
                
                except:
                    continue
            
            time.sleep(30)
        except:
            time.sleep(60)

def monitorear_y_ajustar_base_agresivo():
    """
    Monitorea y ajusta prioridades considerando grupos completos de procesos.
    Solo ignora ajustes de prioridad para procesos en lista_blanca.
    """
    lista_blanca, _, ignorar = cargar_config()
    nucleos_totales = psutil.cpu_count()
    ultimo_pid_primer_plano = None
    procesos_ya_configurados = set()
    
    try:
        while True:
            if check_shutdown_signal():
                break
            
            pid_actual_primer_plano = obtener_pid_primer_plano()
            
            if pid_actual_primer_plano != ultimo_pid_primer_plano and pid_actual_primer_plano is not None:
                ultimo_pid_primer_plano = pid_actual_primer_plano
                procesos_ya_configurados.clear()
                
                # Obtener grupo completo del proceso en primer plano
                grupo_primer_plano, nombre_primer_plano = obtener_grupo_completo_proceso(pid_actual_primer_plano)
                
                # Verificar si el proceso en primer plano está en lista blanca
                proceso_fg_en_lista_blanca = False
                if nombre_primer_plano:
                    proceso_fg_en_lista_blanca = nombre_primer_plano.lower() in lista_blanca
                
                # Aplicar configuración al grupo de primer plano (solo si NO está en lista_blanca)
                if not proceso_fg_en_lista_blanca and grupo_primer_plano:
                    aplicar_configuracion_a_grupo(grupo_primer_plano, True, nucleos_totales)
                    procesos_ya_configurados.update(grupo_primer_plano)
                
                # Agrupar todos los demás procesos por nombre
                procesos_por_nombre = {}
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if proc.pid in procesos_ya_configurados:
                            continue
                        
                        nombre_proceso = proc.info['name'].lower()
                        
                        # Ignorar solo lista_blanca para ajustes de prioridad
                        # (NO ignorar ignorar aquí, solo en cierre por inactividad)
                        if nombre_proceso in lista_blanca or proc.pid == os.getpid():
                            continue
                        
                        if nombre_proceso not in procesos_por_nombre:
                            procesos_por_nombre[nombre_proceso] = set()
                        procesos_por_nombre[nombre_proceso].add(proc.pid)
                    except:
                        continue
                
                # Aplicar configuración de segundo plano a cada grupo
                for nombre_proc, pids_grupo in procesos_por_nombre.items():
                    # Expandir grupo con todos los hijos
                    grupo_completo = set()
                    for pid in pids_grupo:
                        grupo_completo.add(pid)
                        hijos = obtener_todos_hijos_recursivo(pid)
                        grupo_completo.update(hijos)
                    
                    # Aplicar configuración al grupo completo
                    aplicar_configuracion_a_grupo(grupo_completo, False, nucleos_totales)
                    procesos_ya_configurados.update(grupo_completo)
            
            time.sleep(0.75)
    except KeyboardInterrupt:
        pass
    finally:
        os._exit(0)

def crear_acceso_directo(carpeta_destino, nombre_acceso):
    escritorio = Path.home() / 'Desktop'
    ruta_acceso = escritorio / f"{nombre_acceso}.lnk"
    script_vbs = f'''
    Set oWS = WScript.CreateObject("WScript.Shell")
    sLinkFile = "{ruta_acceso}"
    Set oLink = oWS.CreateShortcut(sLinkFile)
    oLink.TargetPath = "{carpeta_destino}"
    oLink.Save
    '''
    temp_vbs = escritorio / "temp_shortcut.vbs"
    with open(temp_vbs, 'w') as f:
        f.write(script_vbs)
    os.system(f'wscript "{temp_vbs}"')
    time.sleep(1)
    if temp_vbs.exists():
        temp_vbs.unlink()

def refrescar_escritorio():
    ctypes.windll.user32.SystemParametersInfoW(0x0014, 0, None, 0)

def organizar_escritorio_main():
    if check_shutdown_signal():
        return
    desktop = Path.home() / 'Desktop'
    library = Path('C:/') / 'BIBLIOTECA DE ESCRITORIO'
    files = [f for f in desktop.iterdir() if f.is_file() and not f.name.endswith('.lnk')]
    if len(files) < 15:
        return
    library.mkdir(exist_ok=True)
    acceso_directo = desktop / 'BIBLIOTECA DE ESCRITORIO.lnk'
    if not acceso_directo.exists():
        crear_acceso_directo(str(library), 'BIBLIOTECA DE ESCRITORIO')
    categories = {
        'ejecutables': {'.exe', '.msi', '.bat', '.sh', '.com', '.cmd', '.ps1'},
        'comprimidos': {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.iso'},
        'imagenes': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp', '.ico', '.psd'},
        'videos': {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v', '.mpg', '.mpeg'},
        'audios': {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.mid', '.midi'},
        'documentos': {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt', '.ods', '.odp', '.csv', '.xml', '.json'}
    }
    archivos_movidos = 0
    for file in files:
        extension = file.suffix.lower()
        folder_name = 'otros'
        for category, extensions in categories.items():
            if extension in extensions:
                folder_name = category
                break
        subfolder = library / folder_name
        subfolder.mkdir(exist_ok=True)
        destino = subfolder / file.name
        contador = 1
        nombre_base = file.stem
        while destino.exists():
            nuevo_nombre = f"{nombre_base}_{contador}{file.suffix}"
            destino = subfolder / nuevo_nombre
            contador += 1
        shutil.move(str(file), str(destino))
        archivos_movidos += 1
    if archivos_movidos > 0:
        refrescar_escritorio()
        texto_notif = "para optimizar el rendimiento del sistema y ademas una mejor gestion se reubicaron archivos presentes en el escritorio organizados por categorias.para facilitar su acceso se creo un link en el escritorio"
        threading.Thread(target=_crear_ventana_notificacion, args=(texto_notif, 8000), daemon=True).start()

def ejecutar_tarea_programada(delay, tarea):
    time.sleep(delay)
    tarea()

if __name__ == "__main__":
    if es_admin():
        # Mostrar notificación de inicio
        threading.Thread(target=mostrar_notificacion_inicio, daemon=True).start()
        
        lista_blanca_global, _, ignorar_global = cargar_config()
        
        # Iniciar monitor de energía
        hilo_energia = threading.Thread(target=monitor_energia, daemon=True)
        hilo_energia.start()
        
        hilo_escritorio = threading.Thread(target=ejecutar_tarea_programada, args=(60, organizar_escritorio_main), daemon=True)
        hilo_escritorio.start()
        hilo_ram = threading.Thread(target=monitor_y_limpieza_ram, daemon=True)
        hilo_ram.start()
        hilo_cierre = threading.Thread(target=monitorear_y_terminar_inactivos, args=(ignorar_global,), daemon=True)
        hilo_cierre.start()
        monitorear_y_ajustar_base_agresivo()
    else:
        solicitar_admin()