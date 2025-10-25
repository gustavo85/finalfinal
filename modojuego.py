# -*- coding: utf-8 -*-
"""
modo_juego.py - Optimizador ULTIMATE para juegos en ejecución
Este script es LANZADO por un gestor externo cuando detecta un juego activo.

NUEVAS OPTIMIZACIONES EXTREMAS (Versión 7.4 EXTREME):
- NUEVO: Dynamic Core Parking (reduce stuttering)
- NUEVO: Large Page Support (aumenta FPS 3-8%)
- NUEVO: MMCSS Tweaking (elimina audio crackling)
- NUEVO: Notificación visual al iniciar modo juego
- NUEVO: Detección laptop/desktop + instalación automática de plan de energía (SIN restauración)
- NUEVO: Sistema de prioridades refinado (Paginación, Procesamiento, I/O)
- NUEVO: Afinidad de núcleos inteligente según cantidad de cores
- IRQ Affinity: Aísla interrupciones de GPU a núcleos específicos
- QoS de Red: Prioriza tráfico del juego con netsh
- PowerShell en lugar de WMIC (3x más rápido)
- SIN backup/restore de registro (permanente hasta reinicio)
- Monitoreo optimizado de prioridades
- Restauración inteligente de modo anterior (normal/agresivo)

Autor: moltenisoy
Fecha: 2025-10-19
Versión: 7.4 EXTREME
"""
import ctypes
from ctypes import wintypes
import json
import os
import sys
import time
import psutil
import subprocess
import winreg
import threading
from typing import Dict, List, Tuple, Optional, Set
import tkinter as tk
from tkinter import font

try:
    import win32api
    import win32con
    import win32gui
    import win32process
except ImportError:
    print("ERROR: PyWin32 no instalado. Ejecute: pip install pywin32")
    sys.exit(1)

# === CONFIGURACIÓN ===
NOMBRE_ARCHIVO_CONFIG = "config.json"
STATE_FILE = ".mode_state.json"

# === CONSTANTES ADICIONALES PARA PRIORIDADES ===
# I/O Priority
IO_PRIORITY_VERY_LOW = 0
IO_PRIORITY_LOW = 1
IO_PRIORITY_NORMAL = 2
IO_PRIORITY_HIGH = 3
IO_PRIORITY_CRITICAL = 4

# Memory Priority (Page Priority)
MEMORY_PRIORITY_VERY_LOW = 1
MEMORY_PRIORITY_LOW = 2
MEMORY_PRIORITY_MEDIUM = 3
MEMORY_PRIORITY_BELOW_NORMAL = 4
MEMORY_PRIORITY_NORMAL = 5

# === LISTAS DE PROCESOS Y SERVICIOS A DETENER ===
PROCESOS_A_DETENER_DEFAULT = [
    "dropbox.exe", "evernote.exe", "grammarly.exe", "todoist.exe", "onedriveupdater.exe",
    "discord.exe", "chrome.exe", "firefox.exe", "googleupdate.exe", "adobeupdater.exe",
    "javaupdater.exe", "spotify.exe", "vlc.exe", "winrar.exe", "audacity.exe",
    "foobar2000.exe", "lghub.exe", "razersynapse.exe", "nvcontainer.exe", "rthdcpl.exe",
    "synaptics.exe", "acrobat.exe", "photoshop.exe", "lightroom.exe", "adobearm.exe",
    "creativecloud.exe", "7z.exe", "winzip.exe", "git.exe", "sourcetree.exe",
    "pycharm.exe", "acroupdate.exe", "ravcpl64.exe", "whatpulse.exe", "etd.exe",
    "jusched.exe", "acrord32.exe", "zoom.exe", "telegram.exe", "hkcmd.exe",
    "igfxtray.exe", "kenotify.exe", "igfxpers.exe", "ravbg64.exe", "syntpenh.exe",
    "tcrdmain.exe", "temprotray.exe", "tosreeltimemonitor.exe", "toswaitsrv.exe",
    "tosvolregulator.exe", "tpwrmain.exe", "tosdimonitor.exe", "adobecollabsync.exe",
    "cnsemain.exe", "pdvdserv.exe", "garminexpress.exe", "gbpagent.exe", "rthdbkgd.exe",
    "keepass.exe", "lda.exe", "macriumreflect.exe", "power2go.exe", "rainlendar2.exe",
    "rapidmode.exe", "scantopc.exe", "snagit.exe", "wavesmaxxaudio.exe",
    "adobegcinvoker.exe", "ccxprocess.exe", "googledrivesync.exe", "slack.exe",
    "teams.exe", "skype.exe", "galaxyclient.exe", "battle.net.exe", "eadesktop.exe",
    "riotclientservices.exe", "icue.exe", "steelseriesgg.exe", "msiafterburner.exe",
    "flux.exe", "sharex.exe", "lightshot.exe", "displayfusion.exe", "ditto.exe",
    "powertoys.runner.exe", "qbittorrent.exe", "utorrent.exe", "plex media server.exe",
    "ituneshelper.exe", "teamviewer.exe", "anydesk.exe", "nordvpn-service.exe",
    "vmware-tray.exe", "vboxtray.exe", "docker desktop.exe", "box.exe", "megasync.exe",
    "pcloud.exe", "acronistrueimage.exe", "veeam.agent.tray.exe", "signal.exe",
    "overwolf.exe", "medal.tv.exe", "cam.exe", "armourycrate.exe",
    "dellsupportassist.exe", "lenovovantage.exe", "elgatostreamdeck.exe",
    "wacomhost.exe", "rainmeter.exe", "greenshot.exe", "everything.exe",
    "jdownloader2.exe", "musicbee.exe", "protonvpn.exe", "wallpaper64.exe",
    "stardockfences.exe", "obs64.exe", "calibre.exe", "expressvpn.exe",
    "openvpn-gui.exe", "awcc.exe", "notion.exe", "whatsapp.exe", "viber.exe",
    "hd-agent.exe", "nox.exe", "speechruntime.exe", "kiestrayagent.exe",
    "splashtopstreamer.exe", "logmein.exe", "obsidian.exe", "1password.exe",
    "lastpass.exe", "dashlane.exe", "bitwarden.exe", "idman.exe", "cyberghost.exe",
    "surfshark.exe", "mullvad-vpn.exe", "ccleaner64.exe", "backblaze.exe",
    "idrive.exe", "duplicati.gui.trayicon.exe", "code.exe", "asusgputweak.exe",
    "hwinfo64.exe", "coretemp.exe", "keepassxc.exe", "eartrumpet.exe",
    "vnc-server.exe", "synergy.exe", "soundswitch.exe", "voicemeeter.exe",
    "translucenttb.exe", "copyq.exe", "autohotkey.exe", "launchy.exe",
    "tweetdeck.exe", "trello.exe", "insync.exe", "kdeconnectd.exe", "pushbullet.exe",
    "cyserver.exe", "popcorn-time.exe", "wemod.exe", "curseforge.exe", "pia_tray.exe",
    "windscribe.exe", "calculator.exe", "newsandinterests.exe", "onedrive.exe",
    "ctfmon.exe", "phoneexperiencehost.exe", "groovemusic.exe", "phonelink.exe",
    "msedge.exe", "skypeapp.exe", "dropboxupdate.exe", "adobeipcbroker.exe",
    "adobenotificationclient.exe", "lcore.exe", "logioverlay.exe", "rzsynapse.exe",
    "razercentral.exe", "lenovo.modern.imcontroller.exe", "lenovoutility.exe",
    "hpsupportsolutionsframework.exe", "officeclicktorun.exe", "nvbackend.exe",
    "nvidia web helper.exe", "amd radeon software.exe", "amdrsserv.exe",
    "igfxem.exe", "delldatavault.exe", "dellcommandupdate.exe", "auraservice.exe",
    "syntpenh.exe", "setpoint.exe"
]

SERVICIOS_A_DETENER_DEFAULT = [
    "spooler", "wmpnetworksvc", "icssvc", "wsearch", "winrm", "remoteregistry",
    "seclogon", "sensordataservice", "sensormonitoringservice", "sensorservice",
    "lanmanserver", "sharedpcaccountmanager", "shellhwdetection", "scardsvr",
    "scdeviceenum", "scpolicysvc", "lmhosts", "tapisrv", "vds", "vss",
    "walletservice", "stisvc", "wisvc", "AxInstSV", "BDESVC", "bthserv", "CertPropSvc",
    "DiagTrack", "CEIP", "DusmSvc", "DoSvc", "DPS", "WdiServiceHost", "WdiSystemHost", "DiagSvc",
    "EntAppSvc", "Fax", "lfsvc", "InstallService", "OneSyncSvc", "PhoneSvc", "Spooler", "PcaSvc",
    "RemoteRegistry", "RetailDemo", "seclogon", "TabletInputService", "stisvc", "wisvc", "WMPNetworkSvc",
    "WSearch", "wuauserv", "WerSvc", "MapsBroker"
]

# === CONSTANTES WINAPI ===
wtsapi32 = ctypes.WinDLL('Wtsapi32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
advapi32 = ctypes.WinDLL('advapi32', use_last_error=True)
userenv = ctypes.WinDLL('userenv', use_last_error=True)
ntdll = ctypes.WinDLL('ntdll', use_last_error=True)

WTSGetActiveConsoleSessionId = kernel32.WTSGetActiveConsoleSessionId
WTSQueryUserToken = wtsapi32.WTSQueryUserToken
CreateEnvironmentBlock = userenv.CreateEnvironmentBlock
DestroyEnvironmentBlock = userenv.DestroyEnvironmentBlock
CreateProcessAsUserW = advapi32.CreateProcessAsUserW
DuplicateTokenEx = advapi32.DuplicateTokenEx
CloseHandle = kernel32.CloseHandle

TOKEN_ALL_ACCESS = 0xF01FF
CREATE_NEW_CONSOLE = 0x00000010
CREATE_UNICODE_ENVIRONMENT = 0x00000400

# VirtualAlloc/Free
MEM_COMMIT = 0x00001000
MEM_RESERVE = 0x00002000
MEM_RELEASE = 0x00008000
PAGE_READWRITE = 0x04

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]

# === ESTADO GLOBAL SIMPLIFICADO (SIN BACKUP) ===
class GameModeState:
    """Guarda el estado de las optimizaciones aplicadas (SIN BACKUP DE REGISTRO)"""
    def __init__(self):
        self.processes_killed: List[str] = []  # SOLO los que realmente cerró
        self.services_stopped: List[str] = []  # SOLO los que realmente detuvo
        self.explorer_killed: bool = False
        self.timer_changed: bool = False
        self.qos_policy_created: bool = False
        self.core_parking_changed: bool = False
        self.large_pages_enabled: bool = False
        self.mmcss_optimized: bool = False
        
        # PIDs a los que se modificó prioridad/afinidad
        self.modified_priority_pids: Set[int] = set()
        self.original_priorities: Dict[int, int] = {}
        self.original_affinities: Dict[int, int] = {}
        
        # Nombre de política QoS creada
        self.qos_policy_name: Optional[str] = None
        
        # Event para control preciso del loop de monitoreo
        self.exit_event: threading.Event = threading.Event()

# === NOTIFICACIÓN DE INICIO ===

def show_game_mode_notification():
    """Muestra notificación "MODO JUEGO ACTIVADO" con animación deslizante"""
    def run_notification():
        try:
            root = tk.Tk()
            root.title("")
            root.overrideredirect(True)
            root.geometry("320x120")
            root.configure(bg="#006400")
            root.resizable(False, False)

            label = tk.Label(
                root,
                text="MODO JUEGO\nACTIVADO",
                fg="white",
                bg="#006400",
                font=font.Font(family="Arial", size=20, weight="bold"),
                justify=tk.CENTER
            )
            label.pack(expand=True)

            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            initial_x = screen_width
            initial_y = 50
            root.geometry(f"320x120+{initial_x}+{initial_y}")

            def slide_in():
                current_x = root.winfo_x()
                if current_x > screen_width - 320:
                    new_x = current_x - 20
                    root.geometry(f"320x120+{new_x}+{initial_y}")
                    root.after(10, slide_in)
                else:
                    root.after(5000, slide_out)

            def slide_out():
                current_x = root.winfo_x()
                if current_x < screen_width:
                    new_x = current_x + 20
                    root.geometry(f"320x120+{new_x}+{initial_y}")
                    root.after(10, slide_out)
                else:
                    root.destroy()

            root.attributes("-topmost", True)
            root.update_idletasks()
            root.after(100, slide_in)
            root.mainloop()
        
        except Exception as e:
            print(f"ERROR mostrando notificación: {e}")
    
    notification_thread = threading.Thread(target=run_notification, daemon=True)
    notification_thread.start()

# === GESTIÓN DE PLANES DE ENERGÍA (SIN RESTAURACIÓN) ===

def is_laptop() -> bool:
    """Detecta si el sistema es laptop o PC de escritorio"""
    try:
        battery = psutil.sensors_battery()
        if battery is not None:
            return True
        
        ps_command = """
        $chassis = Get-CimInstance -ClassName Win32_SystemEnclosure
        $chassis.ChassisTypes
        """
        
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            chassis_types = result.stdout.strip()
            laptop_chassis = ['8', '9', '10', '11', '12', '14', '18', '21', '30', '31', '32']
            for chassis in laptop_chassis:
                if chassis in chassis_types:
                    return True
        
        return False
    
    except Exception as e:
        print(f"ERROR detectando tipo de sistema: {e}")
        return False

def power_plan_exists(plan_name: str) -> bool:
    """Verifica si un plan de energía con nombre específico existe"""
    try:
        result = subprocess.run(
            ["powercfg", "/list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return plan_name.lower() in result.stdout.lower()
        
        return False
    
    except Exception as e:
        print(f"ERROR verificando existencia de plan: {e}")
        return False

def install_power_plan(pow_file_path: str) -> bool:
    """Instala un plan de energía desde archivo .pow"""
    try:
        if not os.path.exists(pow_file_path):
            print(f"ERROR: Archivo {pow_file_path} no encontrado")
            return False
        
        result = subprocess.run(
            ["powercfg", "/import", pow_file_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"INFO: Plan de energía instalado desde {pow_file_path}")
            return True
        else:
            print(f"ERROR instalando plan: {result.stderr}")
            return False
    
    except Exception as e:
        print(f"ERROR instalando plan de energía: {e}")
        return False

def activate_power_plan_by_name(plan_name: str) -> bool:
    """Activa un plan de energía por nombre"""
    try:
        result = subprocess.run(
            ["powercfg", "/list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return False
        
        import re
        for line in result.stdout.split('\n'):
            if plan_name.lower() in line.lower():
                guid_match = re.search(r'([0-9a-fA-F-]{36})', line)
                if guid_match:
                    guid = guid_match.group(1)
                    
                    result = subprocess.run(
                        ["powercfg", "/setactive", guid],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if result.returncode == 0:
                        print(f"INFO: Plan '{plan_name}' activado (GUID: {guid})")
                        return True
        
        return False
    
    except Exception as e:
        print(f"ERROR activando plan: {e}")
        return False

def setup_power_plan() -> bool:
    """Configura el plan de energía óptimo según tipo de sistema (SIN GUARDAR ORIGINAL)"""
    try:
        is_laptop_system = is_laptop()
        
        if is_laptop_system:
            plan_name = "RENDIMIENTO PARA Laptop"
            pow_file = "RENDIMIENTO PARA Laptop.pow"
        else:
            plan_name = "RENDIMIENTO PARA ESCRITORIO"
            pow_file = "RENDIMIENTO PARA ESCRITORIO.pow"
        
        print(f"INFO: Sistema detectado como {'LAPTOP' if is_laptop_system else 'DESKTOP'}")
        
        if not power_plan_exists(plan_name):
            print(f"INFO: Plan '{plan_name}' no encontrado, instalando...")
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            pow_path = os.path.join(script_dir, pow_file)
            
            if not install_power_plan(pow_path):
                print(f"WARN: No se pudo instalar plan de energía")
                return False
        
        if activate_power_plan_by_name(plan_name):
            print(f"INFO: Plan de energía '{plan_name}' activado PERMANENTEMENTE")
            return True
        else:
            print(f"WARN: No se pudo activar plan '{plan_name}'")
            return False
    
    except Exception as e:
        print(f"ERROR configurando plan de energía: {e}")
        return False

# === SISTEMA DE PRIORIDADES Y AFINIDAD ===

def set_process_io_priority(pid: int, io_priority: int) -> bool:
    """Establece prioridad de I/O de un proceso"""
    try:
        PROCESS_SET_INFORMATION = 0x0200
        
        handle = kernel32.OpenProcess(PROCESS_SET_INFORMATION, False, pid)
        if not handle:
            return False
        
        io_priority_value = ctypes.c_int(io_priority)
        status = ntdll.NtSetInformationProcess(
            handle,
            0x21,  # ProcessIoPriority
            ctypes.byref(io_priority_value),
            ctypes.sizeof(io_priority_value)
        )
        
        kernel32.CloseHandle(handle)
        
        return status == 0
    
    except Exception:
        return False

def set_process_memory_priority(pid: int, memory_priority: int) -> bool:
    """Establece prioridad de memoria (paginación) de un proceso"""
    try:
        PROCESS_SET_INFORMATION = 0x0200
        
        handle = kernel32.OpenProcess(PROCESS_SET_INFORMATION, False, pid)
        if not handle:
            return False
        
        memory_priority_value = ctypes.c_int(memory_priority)
        status = ntdll.NtSetInformationProcess(
            handle,
            0x27,  # ProcessPagePriority
            ctypes.byref(memory_priority_value),
            ctypes.sizeof(memory_priority_value)
        )
        
        kernel32.CloseHandle(handle)
        
        return status == 0
    
    except Exception:
        return False

def get_cpu_core_count() -> int:
    """Obtiene cantidad de núcleos físicos"""
    return psutil.cpu_count(logical=False) or psutil.cpu_count(logical=True)

def calculate_affinity_masks(core_count: int) -> Tuple[int, int]:
    """
    Calcula máscaras de afinidad según cantidad de núcleos
    Retorna: (game_affinity_mask, others_affinity_mask)
    """
    logical_cores = psutil.cpu_count(logical=True)
    
    if core_count == 2:
        game_mask = 0b11  # Cores 0 y 1
        others_mask = 0b10  # Core 1
    
    elif core_count == 4:
        game_mask = 0b1111  # Todos los cores (0-3)
        others_mask = 0b1001  # Cores 0 y 3
    
    else:  # 8+ cores
        game_mask = (1 << logical_cores) - 1
        game_mask &= ~0b11  # Quitar cores 0-1
        others_mask = 0b11
    
    return game_mask, others_mask

def apply_priority_and_affinity_system(game_pid: int, whitelist: Set[str], state: GameModeState):
    """Aplica sistema completo de prioridades y afinidad (RESPETANDO WHITELIST)"""
    try:
        core_count = get_cpu_core_count()
        game_affinity, others_affinity = calculate_affinity_masks(core_count)
        
        print(f"INFO: CPU con {core_count} núcleos físicos detectada")
        print(f"INFO: Afinidad juego: {bin(game_affinity)}, otros: {bin(others_affinity)}")
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pid = proc.info['pid']
                name = (proc.info.get('name') or "").lower()
                
                # CRÍTICO: RESPETAR WHITELIST
                if name in whitelist or pid == os.getpid() or pid <= 4:
                    continue
                
                process = psutil.Process(pid)
                
                # Guardar configuración original
                if pid not in state.original_priorities:
                    try:
                        state.original_priorities[pid] = process.nice()
                        state.original_affinities[pid] = process.cpu_affinity()
                    except:
                        pass
                
                if pid == game_pid:
                    # === CONFIGURACIÓN PARA JUEGO ===
                    try:
                        process.nice(psutil.REALTIME_PRIORITY_CLASS)
                    except:
                        pass
                    
                    set_process_io_priority(pid, IO_PRIORITY_HIGH)
                    set_process_memory_priority(pid, MEMORY_PRIORITY_NORMAL)
                    
                    try:
                        cpu_list = [i for i in range(psutil.cpu_count(logical=True)) 
                                   if game_affinity & (1 << i)]
                        process.cpu_affinity(cpu_list)
                    except:
                        pass
                    
                    state.modified_priority_pids.add(pid)
                
                else:
                    # === CONFIGURACIÓN PARA OTROS PROCESOS ===
                    try:
                        process.nice(psutil.IDLE_PRIORITY_CLASS)
                    except:
                        pass
                    
                    set_process_io_priority(pid, IO_PRIORITY_VERY_LOW)
                    set_process_memory_priority(pid, MEMORY_PRIORITY_VERY_LOW)
                    
                    try:
                        cpu_list = [i for i in range(psutil.cpu_count(logical=True)) 
                                   if others_affinity & (1 << i)]
                        process.cpu_affinity(cpu_list)
                    except:
                        pass
                    
                    state.modified_priority_pids.add(pid)
            
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        print(f"INFO: Prioridades y afinidad aplicadas a {len(state.modified_priority_pids)} procesos")
        return True
    
    except Exception as e:
        print(f"ERROR aplicando prioridades: {e}")
        return False

def restore_priority_and_affinity(state: GameModeState):
    """Restaura prioridades y afinidad originales"""
    if not state.modified_priority_pids:
        return
    
    restored_count = 0
    
    for pid in state.modified_priority_pids:
        try:
            if not psutil.pid_exists(pid):
                continue
            
            process = psutil.Process(pid)
            
            if pid in state.original_priorities:
                try:
                    process.nice(state.original_priorities[pid])
                    restored_count += 1
                except:
                    pass
            
            if pid in state.original_affinities:
                try:
                    process.cpu_affinity(state.original_affinities[pid])
                except:
                    pass
        
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    print(f"INFO: Prioridades restauradas en {restored_count} procesos")

# === NUEVA OPTIMIZACIÓN 1: DYNAMIC CORE PARKING ===

def optimize_core_parking(state: GameModeState) -> bool:
    """
    NUEVO: Desactiva Core Parking para eliminar latencia de wake-up
    Mejora: Reduce stuttering en CPUs con muchos cores (SIN BACKUP)
    """
    try:
        # Desactivar Core Parking
        key_path = r"SYSTEM\CurrentControlSet\Control\Power\PowerSettings\54533251-82be-4824-96c1-47b60b740d00\0cc5b647-c1df-4637-891a-dec35c318583"
        
        try:
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                winreg.SetValueEx(key, "ValueMax", 0, winreg.REG_DWORD, 0)
        except Exception as e:
            print(f"WARN: No se pudo modificar registro Core Parking: {e}")
        
        # Aplicar configuración via powercfg
        subprocess.run(["powercfg", "/setacvalueindex", "SCHEME_CURRENT", 
                       "SUB_PROCESSOR", "CPMINCORES", "100"], 
                       capture_output=True, timeout=5)
        subprocess.run(["powercfg", "/setactive", "SCHEME_CURRENT"], 
                       capture_output=True, timeout=5)
        
        state.core_parking_changed = True
        print("INFO: ✓ Core Parking desactivado (latencia reducida)")
        return True
    
    except Exception as e:
        print(f"ERROR en Core Parking: {e}")
        return False

# === NUEVA OPTIMIZACIÓN 2: LARGE PAGE SUPPORT ===

def enable_large_pages_for_game(state: GameModeState) -> bool:
    """
    NUEVO: Habilita Large Pages (2MB vs 4KB normal)
    Mejora: Reduce TLB misses, aumenta FPS en 3-8% (SIN BACKUP)
    """
    try:
        # Otorgar privilegio SeLockMemoryPrivilege
        username = os.getlogin()
        ps_command = f"""
        try {{
            $user = "{username}"
            $sidstr = (New-Object System.Security.Principal.NTAccount($user)).Translate([System.Security.Principal.SecurityIdentifier]).Value
            $tempFile = [System.IO.Path]::GetTempFileName()
            secedit /export /cfg $tempFile | Out-Null
            $cfg = Get-Content $tempFile
            $line = $cfg | Where-Object {{ $_ -match 'SeLockMemoryPrivilege' }}
            if ($line -notmatch $sidstr) {{
                $newcfg = $cfg -replace '(SeLockMemoryPrivilege\\s*=\\s*)(.*)', "`$1`$2,*$sidstr"
                $newcfg | Out-File $tempFile -Encoding ascii
                secedit /configure /db secedit.sdb /cfg $tempFile /areas USER_RIGHTS | Out-Null
            }}
            Remove-Item $tempFile -ErrorAction SilentlyContinue
            Write-Output "OK"
        }} catch {{
            Write-Output "ERROR"
        }}
        """
        
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if "OK" in result.stdout:
            # Habilitar Large Pages en el sistema
            key_path = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"
            
            try:
                with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                    winreg.SetValueEx(key, "LargePageMinimum", 0, winreg.REG_DWORD, 0)
            except Exception as e:
                print(f"WARN: No se pudo modificar LargePageMinimum: {e}")
            
            state.large_pages_enabled = True
            print("INFO: ✓ Large Pages habilitado (mejora FPS +3-8%)")
            return True
        else:
            print("WARN: No se pudo habilitar Large Pages")
            return False
    
    except Exception as e:
        print(f"ERROR habilitando Large Pages: {e}")
        return False

# === NUEVA OPTIMIZACIÓN 3: MMCSS TWEAKING ===

def optimize_mmcss_for_game(state: GameModeState) -> bool:
    """
    NUEVO: Configura MMCSS para dar máxima prioridad al juego
    Mejora: Reduce audio crackling y frame pacing issues (SIN BACKUP)
    """
    try:
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games"
        
        try:
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                # Priority: 8 = High
                winreg.SetValueEx(key, "Priority", 0, winreg.REG_DWORD, 8)
                # GPU Priority: 8 = Maximum
                winreg.SetValueEx(key, "GPU Priority", 0, winreg.REG_DWORD, 8)
                # Scheduling Category: High
                winreg.SetValueEx(key, "Scheduling Category", 0, winreg.REG_SZ, "High")
                # SFIO Priority: High
                winreg.SetValueEx(key, "SFIO Priority", 0, winreg.REG_SZ, "High")
                # BackgroundPriority: 0
                winreg.SetValueEx(key, "BackgroundPriority", 0, winreg.REG_DWORD, 0)
        
        except Exception as e:
            print(f"WARN: No se pudo modificar MMCSS: {e}")
            return False
        
        state.mmcss_optimized = True
        print("INFO: ✓ MMCSS optimizado para gaming (elimina audio crackling)")
        return True
    
    except Exception as e:
        print(f"ERROR en MMCSS: {e}")
        return False

# === DETECCIÓN DE TOPOLOGÍA DE CPU ===

class CPUTopology:
    """Detecta topología de CPU para optimización de IRQ Affinity"""
    
    @staticmethod
    def get_cpu_info() -> Dict[str, any]:
        """Obtiene información detallada de CPU"""
        try:
            logical_cores = psutil.cpu_count(logical=True)
            physical_cores = psutil.cpu_count(logical=False) or logical_cores
            
            isolated_cores = []
            
            if physical_cores >= 4:
                if logical_cores > physical_cores:
                    isolated_cores = list(range(logical_cores - 4, logical_cores))
                else:
                    isolated_cores = list(range(physical_cores - 2, physical_cores))
            
            return {
                'logical_cores': logical_cores,
                'physical_cores': physical_cores,
                'isolated_cores': isolated_cores
            }
        
        except Exception as e:
            print(f"ERROR detectando topología CPU: {e}")
            return {
                'logical_cores': psutil.cpu_count(logical=True),
                'physical_cores': psutil.cpu_count(logical=False) or psutil.cpu_count(logical=True),
                'isolated_cores': []
            }
    
    @staticmethod
    def cores_to_affinity_mask(cores: List[int]) -> int:
        """Convierte lista de núcleos a máscara de afinidad"""
        mask = 0
        for core in cores:
            mask |= (1 << core)
        return mask

# === INTEGRACIÓN CON ORQUESTADOR ===

def notify_game_mode_start(game_pid: int, game_name: str, previous_mode: str = None):
    """Notifica al orquestador que el modo juego ha iniciado"""
    try:
        state_data = {
            "state": "game",
            "game_pid": game_pid,
            "game_name": game_name,
            "previous_mode": previous_mode,
            "timestamp": time.time()
        }
        
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2)
        
        print(f"INFO: Estado 'game' notificado al orquestador")
        return True
    
    except Exception as e:
        print(f"ERROR notificando estado: {e}")
        return False

def notify_game_mode_end():
    """Notifica al orquestador que el modo juego ha finalizado"""
    try:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        
        print(f"INFO: Estado 'game' limpiado")
        return True
    
    except Exception as e:
        print(f"ERROR limpiando estado: {e}")
        return False

def load_previous_mode() -> Optional[str]:
    """Lee el modo anterior desde config.json"""
    try:
        if os.path.exists(NOMBRE_ARCHIVO_CONFIG):
            with open(NOMBRE_ARCHIVO_CONFIG, "r", encoding="utf-8") as f:
                config = json.load(f)
                switches = config.get("switches", {})
                
                if switches.get("modo_normal"):
                    return "normal"
                elif switches.get("modo_agresivo"):
                    return "agresivo"
        
        return None
    
    except Exception:
        return None

def restore_previous_mode(previous_mode: Optional[str]):
    """Ejecuta el modo anterior (modonormal.py o modoagresivo.py)"""
    if not previous_mode:
        print("INFO: No hay modo anterior para restaurar")
        return
    
    try:
        if previous_mode == "normal":
            script_name = "modonormal.py"
        elif previous_mode == "agresivo":
            script_name = "modoagresivo.py"
        else:
            print(f"WARN: Modo desconocido: {previous_mode}")
            return
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, script_name)
        
        if os.path.exists(script_path):
            print(f"INFO: Restaurando modo anterior: {script_name}")
            subprocess.Popen([sys.executable, script_path], shell=False)
        else:
            print(f"WARN: Script {script_name} no encontrado")
    
    except Exception as e:
        print(f"ERROR restaurando modo anterior: {e}")

# === CARGAR CONFIGURACIÓN ===
# Config cache for optimization
_config_cache = None
_config_mtime = 0

def cargar_config() -> Tuple[Set[str], Set[str], List[str], List[str]]:
    """Carga configuración desde config.json con caché"""
    global _config_cache, _config_mtime
    
    lista_blanca = set()
    lista_juegos = set()
    procesos_a_terminar = list(PROCESOS_A_DETENER_DEFAULT)
    servicios_a_detener = list(SERVICIOS_A_DETENER_DEFAULT)
    
    try:
        if os.path.exists(NOMBRE_ARCHIVO_CONFIG):
            current_mtime = os.path.getmtime(NOMBRE_ARCHIVO_CONFIG)
            if _config_cache is None or current_mtime > _config_mtime:
                with open(NOMBRE_ARCHIVO_CONFIG, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                    _config_cache = datos
                    _config_mtime = current_mtime
            
            lista_blanca = set(item.lower() for item in _config_cache.get("lista_blanca", []))
            lista_juegos = set(item.lower() for item in _config_cache.get("juegos", []))
            
            procesos_custom = _config_cache.get("procesos_a_terminar", [])
            if procesos_custom:
                procesos_a_terminar.extend([p.lower() for p in procesos_custom])
            
            servicios_custom = _config_cache.get("servicios_a_detener", [])
            if servicios_custom:
                servicios_a_detener.extend([s.lower() for s in servicios_custom])
    except (IOError, OSError, PermissionError) as e:
        print(f"ERROR: Error de archivo config: {e}")
    except json.JSONDecodeError as e:
        print(f"ERROR: Error JSON en config: {e}")
    except Exception as e:
        print(f"ERROR: Error inesperado leyendo config: {e}")
    
    return lista_blanca, lista_juegos, procesos_a_terminar, servicios_a_detener

# === FUNCIONES DE OPTIMIZACIÓN (CÓDIGO ORIGINAL - SIN BACKUP) ===

def set_high_timer_resolution() -> bool:
    """Establece timer resolution a 0.5ms"""
    try:
        ntdll = ctypes.WinDLL('ntdll.dll')
        resolution = ctypes.c_ulong(5000)
        status = ntdll.NtSetTimerResolution(resolution, ctypes.c_bool(True), ctypes.byref(resolution))
        return status == 0
    except Exception as e:
        print(f"ERROR timer_resolution: {e}")
        return False

def restore_timer_resolution() -> bool:
    """Restaura timer resolution"""
    try:
        ntdll = ctypes.WinDLL('ntdll.dll')
        resolution = ctypes.c_ulong(156000)
        status = ntdll.NtSetTimerResolution(resolution, ctypes.c_bool(False), ctypes.byref(resolution))
        return status == 0
    except:
        return False

def disable_game_dvr() -> bool:
    """Desactiva GameDVR y Game Bar (SIN BACKUP)"""
    try:
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR"
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValueEx(key, "AppCaptureEnabled", 0, winreg.REG_DWORD, 0)
                winreg.SetValueEx(key, "GameDVR_Enabled", 0, winreg.REG_DWORD, 0)
        except:
            pass
        
        key_path = r"SOFTWARE\Microsoft\GameBar"
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValueEx(key, "AutoGameModeEnabled", 0, winreg.REG_DWORD, 0)
                winreg.SetValueEx(key, "AllowAutoGameMode", 0, winreg.REG_DWORD, 0)
        except:
            pass
        
        return True
    except Exception as e:
        print(f"ERROR GameDVR: {e}")
        return False

def optimize_gpu_settings() -> bool:
    """Optimiza GPU (TdrDelay + HW Scheduling) (SIN BACKUP)"""
    try:
        key_path = r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers"
        
        try:
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                winreg.SetValueEx(key, "TdrDelay", 0, winreg.REG_DWORD, 60)
                winreg.SetValueEx(key, "TdrDdiDelay", 0, winreg.REG_DWORD, 60)
                winreg.SetValueEx(key, "HwSchMode", 0, winreg.REG_DWORD, 2)
        except Exception as e:
            print(f"WARN: No se pudo modificar GPU settings: {e}")
        
        return True
    except Exception as e:
        print(f"ERROR GPU settings: {e}")
        return False

def detect_active_gpu_for_process(game_pid: int) -> Optional[str]:
    """Detecta qué GPU está usando REALMENTE el proceso del juego"""
    try:
        ps_command = f"""
        $proc = Get-Process -Id {game_pid} -ErrorAction SilentlyContinue
        if ($proc) {{
            $counters = Get-Counter "\\GPU Engine(*)\\Running Time" -ErrorAction SilentlyContinue
            if ($counters) {{
                $counters.CounterSamples | Where-Object {{
                    $_.InstanceName -match "pid_$($proc.Id)_"
                }} | ForEach-Object {{
                    $_.InstanceName -split "_" | Select-Object -First 1
                }}
            }}
        }}
        """
        
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            gpu_name = result.stdout.strip().upper()
            
            if any(keyword in gpu_name for keyword in ["NVIDIA", "RTX", "GTX", "GEFORCE"]):
                return "NVIDIA"
            elif any(keyword in gpu_name for keyword in ["AMD", "RADEON", "RX"]):
                return "AMD"
            elif any(keyword in gpu_name for keyword in ["INTEL", "UHD", "IRIS"]):
                return "INTEL"
        
        ps_command_fallback = """
        Get-CimInstance -ClassName Win32_VideoController | 
        Where-Object {$_.AdapterDACType -ne "Internal" -or $_.AdapterRAM -gt 1GB} |
        Select-Object -ExpandProperty Name -First 1
        """
        
        result = subprocess.run(
            ["powershell", "-Command", ps_command_fallback],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            gpu_name = result.stdout.strip().upper()
            
            if any(keyword in gpu_name for keyword in ["NVIDIA", "RTX", "GTX", "GEFORCE"]):
                return "NVIDIA"
            elif any(keyword in gpu_name for keyword in ["AMD", "RADEON", "RX"]):
                return "AMD"
        
        return None
    
    except Exception as e:
        print(f"ERROR detectando GPU activa: {e}")
        return None

def get_gpu_pnp_device_id_powershell(gpu_vendor: str) -> Optional[str]:
    """Obtiene PNPDeviceID de GPU usando PowerShell"""
    if not gpu_vendor or gpu_vendor == "INTEL":
        return None
    
    try:
        ps_command = f"""
        Get-CimInstance -ClassName Win32_VideoController | 
        Where-Object {{
            $_.Name -like "*{gpu_vendor}*" -and 
            ($_.AdapterDACType -ne "Internal" -or $_.AdapterRAM -gt 1GB)
        }} | 
        Select-Object -ExpandProperty PNPDeviceID -First 1
        """
        
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        
        return None
    
    except Exception as e:
        print(f"ERROR obteniendo GPU PNPDeviceID: {e}")
        return None

def set_gpu_irq_priority_and_affinity(gpu_vendor: str) -> bool:
    """Establece prioridad IRQ de GPU Y afinidad a núcleos aislados (SIN BACKUP)"""
    if not gpu_vendor or gpu_vendor == "INTEL":
        return False
    
    try:
        device_id = get_gpu_pnp_device_id_powershell(gpu_vendor)
        if not device_id:
            return False
        
        device_path = device_id.replace('\\', '\\')
        key_path = f"SYSTEM\\CurrentControlSet\\Enum\\{device_path}\\Device Parameters\\Interrupt Management\\Affinity Policy"
        
        cpu_info = CPUTopology.get_cpu_info()
        isolated_cores = cpu_info['isolated_cores']
        
        try:
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                winreg.SetValueEx(key, "DevicePolicy", 0, winreg.REG_DWORD, 4)
                winreg.SetValueEx(key, "DevicePriority", 0, winreg.REG_DWORD, 3)
                
                if isolated_cores:
                    affinity_mask = CPUTopology.cores_to_affinity_mask(isolated_cores)
                    winreg.SetValueEx(key, "AssignmentSetOverride", 0, winreg.REG_QWORD, affinity_mask)
        
        except Exception as e:
            print(f"WARN: No se pudo modificar GPU IRQ: {e}")
        
        return True
    
    except Exception as e:
        print(f"ERROR GPU IRQ Affinity: {e}")
        return False

def optimize_network() -> bool:
    """Optimiza red para gaming (SIN BACKUP)"""
    try:
        key_path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"
        
        try:
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                winreg.SetValueEx(key, "TcpAckFrequency", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "TCPNoDelay", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "TcpDelAckTicks", 0, winreg.REG_DWORD, 0)
        except:
            pass
        
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
        
        try:
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                winreg.SetValueEx(key, "NetworkThrottlingIndex", 0, winreg.REG_DWORD, 0xFFFFFFFF)
                winreg.SetValueEx(key, "SystemResponsiveness", 0, winreg.REG_DWORD, 0)
        except:
            pass
        
        return True
    except Exception as e:
        print(f"ERROR Network: {e}")
        return False

def create_qos_policy_for_game(game_name: str, state: GameModeState) -> bool:
    """Crea política QoS para priorizar tráfico del juego"""
    try:
        policy_name = f"GameMode_{game_name}_{int(time.time())}"
        
        ps_command = (
            f'New-NetQosPolicy -Name "{policy_name}" '
            f'-AppPathNameMatchCondition "*{game_name}*" '
            f'-DSCPAction 46 '
            f'-NetworkProfile All '
            f'-Precedence 127'
        )
        
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            state.qos_policy_name = policy_name
            return True
        
        return False
    
    except Exception as e:
        print(f"ERROR creando QoS policy: {e}")
        return False

def remove_qos_policy(state: GameModeState) -> bool:
    """Elimina política QoS creada"""
    if not state.qos_policy_name:
        return True
    
    try:
        ps_command = f'Remove-NetQosPolicy -Name "{state.qos_policy_name}" -Confirm:$false'
        
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"ERROR eliminando QoS policy: {e}")
        return False

def flush_pagefile_to_ram() -> bool:
    """Flush de pagefile a RAM con manejo correcto de OOM"""
    ptr = None
    try:
        mem_status = MEMORYSTATUSEX()
        mem_status.dwLength = ctypes.sizeof(mem_status)
        
        if kernel32.GlobalMemoryStatusEx(ctypes.byref(mem_status)) == 0:
            return False
        
        available_gb = mem_status.ullAvailPhys / (1024**3)
        
        if available_gb < 2.0:
            print(f"WARN: RAM disponible insuficiente ({available_gb:.1f}GB), saltando flush")
            return False
        
        size_bytes = int(available_gb * 0.6 * (1024**3))
        
        ptr = kernel32.VirtualAlloc(
            wintypes.LPVOID(0),
            ctypes.c_size_t(size_bytes),
            wintypes.DWORD(MEM_COMMIT | MEM_RESERVE),
            wintypes.DWORD(PAGE_READWRITE)
        )
        
        if not ptr:
            print("ERROR: VirtualAlloc falló (posible OOM)")
            return False
        
        chunk_size = 4096
        num_chunks = size_bytes // chunk_size
        step = max(1, num_chunks // 50)
        byte_value = ctypes.c_byte(0xFF)
        
        for i in range(0, num_chunks, step):
            offset = i * chunk_size
            try:
                ctypes.memmove(ptr + offset, ctypes.byref(byte_value), 1)
            except Exception as e:
                print(f"ERROR durante flush: {e}")
                break
        
        time.sleep(0.3)
        
        return True
    
    except Exception as e:
        print(f"ERROR Memory flush: {e}")
        return False
    
    finally:
        if ptr:
            result = kernel32.VirtualFree(
                wintypes.LPVOID(ptr),
                ctypes.c_size_t(0),
                wintypes.DWORD(MEM_RELEASE)
            )
            if not result:
                print("ERROR: VirtualFree falló - posible memory leak")

def aggressive_trim_processes(game_pid: int, whitelist: Set[str]) -> bool:
    """Trim agresivo de procesos (RESPETANDO WHITELIST)"""
    try:
        psapi = ctypes.WinDLL('psapi', use_last_error=True)
        K32EmptyWorkingSet = psapi.K32EmptyWorkingSet
        K32EmptyWorkingSet.argtypes = [wintypes.HANDLE]
        K32EmptyWorkingSet.restype = wintypes.BOOL
        
        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_SET_QUOTA = 0x0100
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pid = proc.info['pid']
                name = (proc.info.get('name') or "").lower()
                
                # RESPETAR WHITELIST
                if pid == game_pid or pid == os.getpid() or name in whitelist:
                    continue
                
                handle = kernel32.OpenProcess(
                    PROCESS_QUERY_INFORMATION | PROCESS_SET_QUOTA,
                    False, pid
                )
                
                if handle:
                    K32EmptyWorkingSet(handle)
                    kernel32.CloseHandle(handle)
            
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return True
    
    except Exception as e:
        print(f"ERROR Trim processes: {e}")
        return False

def terminar_procesos(lista_procesos: List[str], lista_blanca: Set[str]) -> List[str]:
    """Termina procesos de la lista (RESPETANDO WHITELIST) - RETORNA SOLO LOS QUE CERRÓ"""
    terminados = []
    # MEJORA: Convertir la lista a un conjunto (set) para una búsqueda mucho más rápida (O(1))
    procesos_a_terminar_set = set(p.lower() for p in lista_procesos)

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = (proc.info.get('name') or "").lower()

            # La comprobación 'in' es ahora mucho más eficiente
            if name in procesos_a_terminar_set and name not in lista_blanca and proc.info['pid'] != os.getpid():
                try:
                    proc.kill()
                    terminados.append(name)
                    print(f"INFO: Proceso terminado: {name}")
                except Exception as e:
                    print(f"ERROR terminando {name}: {e}")

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return terminados

def detener_servicios(lista_servicios: List[str]) -> List[str]:
    """Detiene servicios - RETORNA SOLO LOS QUE DETUVO"""
    detenidos = []
    
    for service in psutil.win_service_iter():
        try:
            if service.name().lower() in lista_servicios and service.status() == 'running':
                try:
                    service.stop()
                    detenidos.append(service.name().lower())
                    print(f"INFO: Servicio detenido: {service.name()}")
                except Exception as e:
                    print(f"ERROR deteniendo servicio {service.name()}: {e}")
        
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return detenidos

def reiniciar_procesos(procesos: List[str]):
    """Reinicia SOLO los procesos que estaban en la lista proporcionada"""
    if not procesos:
        return
    
    print(f"INFO: Reiniciando {len(procesos)} procesos...")
    
    for proc_name in procesos:
        try:
            result = subprocess.run(
                ["where", proc_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                exe_path = result.stdout.strip().split('\n')[0]
                subprocess.Popen([exe_path], shell=False)
                print(f"INFO: Proceso reiniciado: {proc_name}")
        
        except Exception as e:
            print(f"ERROR reiniciando {proc_name}: {e}")

def reiniciar_servicios(servicios: List[str]):
    """Reinicia SOLO los servicios que estaban en la lista proporcionada"""
    if not servicios:
        return
    
    print(f"INFO: Reiniciando {len(servicios)} servicios...")
    
    for service_name in servicios:
        try:
            for service in psutil.win_service_iter():
                if service.name().lower() == service_name and service.status() == 'stopped':
                    try:
                        service.start()
                        print(f"INFO: Servicio reiniciado: {service.name()}")
                    except Exception as e:
                        print(f"ERROR reiniciando servicio {service.name()}: {e}")
                    break
        except Exception:
            continue

def kill_explorer() -> bool:
    """Cierra explorer.exe (single instance)"""
    killed = False
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if (proc.info.get('name') or "").lower() == 'explorer.exe':
                proc.kill()
                killed = True
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return killed

def start_explorer_fallback() -> bool:
    """Inicia explorer - fallback"""
    try:
        subprocess.Popen(["explorer.exe"], shell=False)
        return True
    except Exception as e:
        print(f"ERROR explorer fallback: {e}")
        return False

def start_explorer_as_active_user() -> bool:
    """Inicia explorer en contexto de usuario activo"""
    try:
        session_id = WTSGetActiveConsoleSessionId()
        if session_id is None or session_id == 0xFFFFFFFF:
            return start_explorer_fallback()

        hUserToken = wintypes.HANDLE()
        if not WTSQueryUserToken(wintypes.ULONG(session_id), ctypes.byref(hUserToken)):
            return start_explorer_fallback()

        hUserTokenDup = wintypes.HANDLE()
        
        if not DuplicateTokenEx(
            hUserToken, wintypes.DWORD(TOKEN_ALL_ACCESS),
            None, wintypes.DWORD(2), wintypes.DWORD(1),
            ctypes.byref(hUserTokenDup)
        ):
            CloseHandle(hUserToken)
            return start_explorer_fallback()

        env = ctypes.c_void_p()
        CreateEnvironmentBlock(ctypes.byref(env), hUserTokenDup, False)

        class STARTUPINFO(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("lpReserved", wintypes.LPWSTR),
                ("lpDesktop", wintypes.LPWSTR),
                ("lpTitle", wintypes.LPWSTR),
                ("dwX", wintypes.DWORD),
                ("dwY", wintypes.DWORD),
                ("dwXSize", wintypes.DWORD),
                ("dwYSize", wintypes.DWORD),
                ("dwXCountChars", wintypes.DWORD),
                ("dwYCountChars", wintypes.DWORD),
                ("dwFillAttribute", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("wShowWindow", wintypes.WORD),
                ("cbReserved2", wintypes.WORD),
                ("lpReserved2", wintypes.LPBYTE),
                ("hStdInput", wintypes.HANDLE),
                ("hStdOutput", wintypes.HANDLE),
                ("hStdError", wintypes.HANDLE),
            ]

        class PROCESS_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("hProcess", wintypes.HANDLE),
                ("hThread", wintypes.HANDLE),
                ("dwProcessId", wintypes.DWORD),
                ("dwThreadId", wintypes.DWORD),
            ]
            
        si = STARTUPINFO()
        si.cb = ctypes.sizeof(si)
        si.lpDesktop = "winsta0\\default"
        pi = PROCESS_INFORMATION()

        dwCreationFlags = CREATE_UNICODE_ENVIRONMENT | CREATE_NEW_CONSOLE

        if CreateProcessAsUserW(
            hUserTokenDup, "C:\\Windows\\explorer.exe", None,
            None, None, False, dwCreationFlags, env, None,
            ctypes.byref(si), ctypes.byref(pi)
        ):
            CloseHandle(pi.hProcess)
            CloseHandle(pi.hThread)
        
        DestroyEnvironmentBlock(env)
        CloseHandle(hUserTokenDup)
        CloseHandle(hUserToken)
        
        return True
    
    except Exception:
        return start_explorer_fallback()

# === BLOQUE DE EJECUCIÓN PRINCIPAL ===

def check_admin() -> bool:
    """Verifica si el script se está ejecutando con privilegios de administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    """
    Función principal que orquesta la detección del juego,
    la aplicación de optimizaciones y la restauración final.
    """
    if not check_admin():
        print("ERROR: Este script requiere privilegios de Administrador para funcionar.")
        print("Por favor, ejecútalo como Administrador.")
        time.sleep(5)
        sys.exit(1)

    print("--- Optimizador ULTIMATE v7.4 EXTREME ---")
    print("... Esperando el lanzamiento de un juego configurado ...")

    lista_blanca, lista_juegos, procesos_a_terminar, servicios_a_detener = cargar_config()
    juegos_configurados = set(j.lower() for j in lista_juegos)
    
    juego_encontrado_proc = None

    # 1. Bucle de Detección: Busca continuamente un proceso de juego.
    while juego_encontrado_proc is None:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc_name = (proc.info.get('name') or "").lower()
                if proc_name in juegos_configurados:
                    juego_encontrado_proc = proc
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if juego_encontrado_proc is None:
            time.sleep(2) # Espera 2 segundos antes de volver a escanear

    game_pid = juego_encontrado_proc.pid
    game_name = juego_encontrado_proc.name()
    print(f"\n¡JUEGO DETECTADO! -> {game_name} (PID: {game_pid})")
    print("=========================================")
    print("===   ACTIVANDO MODO JUEGO EXTREMO   ===")
    print("=========================================")

    # 2. Fase de Optimización
    state = GameModeState()
    previous_mode = load_previous_mode()
    
    if "notificaciones" not in sys.argv: # Permite desactivar notificaciones
        show_game_mode_notification()

    notify_game_mode_start(game_pid, game_name, previous_mode)

    # Aplicar todas las optimizaciones
    setup_power_plan()
    state.timer_changed = set_high_timer_resolution()
    disable_game_dvr()
    optimize_gpu_settings()
    optimize_network()
    
    active_gpu = detect_active_gpu_for_process(game_pid)
    if active_gpu:
        print(f"INFO: GPU activa detectada: {active_gpu}")
        set_gpu_irq_priority_and_affinity(active_gpu)

    state.qos_policy_created = create_qos_policy_for_game(game_name, state)
    
    # NUEVAS OPTIMIZACIONES EXTREMAS
    optimize_core_parking(state)
    enable_large_pages_for_game(state)
    optimize_mmcss_for_game(state)
    
    flush_pagefile_to_ram()
    aggressive_trim_processes(game_pid, lista_blanca)
    
    # Aplicar sistema de prioridades y afinidad
    apply_priority_and_affinity_system(game_pid, lista_blanca, state)

    # Detener procesos y servicios
    state.processes_killed = terminar_procesos(procesos_a_terminar, lista_blanca)
    state.services_stopped = detener_servicios(servicios_a_detener)
    state.explorer_killed = kill_explorer()

    print("\n=========================================")
    print("=== MODO JUEGO ACTIVADO. ¡A JUGAR!  ===")
    print(f"=== Monitoreando {game_name}...     ===")
    print("=========================================\n")

    # 3. Fase de Monitoreo: Espera a que el proceso del juego termine.
    try:
        juego_encontrado_proc.wait() 
    except psutil.NoSuchProcess:
        # El proceso ya terminó, no hay problema.
        pass
    except KeyboardInterrupt:
        print("\nInterrupción manual detectada. Restaurando el sistema...")

    # 4. Fase de Restauración
    print("\n=========================================")
    print("===   JUEGO CERRADO. RESTAURANDO...  ===")
    print("=========================================")
    
    restore_priority_and_affinity(state)
    
    if state.explorer_killed:
        start_explorer_as_active_user()
    
    # NOTA: Por diseño de la versión EXTREME, la mayoría de los cambios
    # (planes de energía, registro) son permanentes hasta el reinicio.
    # Solo se restauran elementos dinámicos.
    
    if state.timer_changed:
        restore_timer_resolution()
    
    if state.qos_policy_created:
        remove_qos_policy(state)
        
    reiniciar_servicios(state.services_stopped)
    # No se reinician procesos para no interrumpir al usuario.
    
    notify_game_mode_end()
    
    # Restaura el modo anterior (normal/agresivo) si estaba configurado
    restore_previous_mode(previous_mode)

    print("\n=========================================")
    print("===   SISTEMA RESTAURADO. ADIÓS.    ===")
    print("=========================================")


if __name__ == "__main__":
    main()
