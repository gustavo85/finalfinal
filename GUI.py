import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import psutil
import json
import os
import subprocess
import sys
import ctypes
import threading
import importlib
import runpy
from pathlib import Path

try:
    from pystray import Icon, Menu, MenuItem
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False

# Pistas para PyInstaller (hidden imports) sin ejecutar nada:
if False:
    import entradas, entrada, LIMPIEZA, limpia, DISCOS, discos  # noqa: F401

COLOR_BG = "#0b0f1a"
COLOR_PANEL = "#0f1724"
COLOR_ACCENT = "#00e5ff"
COLOR_ACCENT2 = "#b388ff"
COLOR_ACCENT_RED = "#ff4d6d"
COLOR_NEUTRO = "#1f2937"
COLOR_TEXT = "#e6eef8"
COLOR_LIST_BG = "#08111a"
COLOR_LIST_FG = "#e6eef8"
COLOR_BLANCO_PAGINA = COLOR_PANEL
COLOR_ROJO_PAGINA = "#17060a"
COLOR_AZUL_PAGINA = "#071022"
COLOR_VERDE_PAGINA = "#07120a"

NOMBRE_ARCHIVO_CONFIG = "config.json"

proceso_modo_normal = None
proceso_modo_agresivo = None
proceso_modo_juego = None
modo_juego_activo = False

ventana = None
icono_bandeja = None
tray_icon = None
tray_thread_running = False
es_laptop = False

# Flags de tareas programadas
limpieza_en_ejecucion = False
discos_en_ejecucion = False

switches_config = {
    "modo_normal": False,
    "modo_agresivo": False,
    "notificaciones": False,
    "freno_termico": False,
    "autoinicio_windows": False,
    "optimizador_sesion": False
}

# ----------------- Utilidad rutas compatible con PyInstaller -----------------
def resource_path(relative_path: str) -> str:
    """
    Devuelve la ruta a un recurso, compatible tanto en desarrollo como en EXE de PyInstaller.
    """
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def is_frozen() -> bool:
    return getattr(sys, "frozen", False) is True

# -----------------------------------------------------------------------------


def detectar_laptop():
    global es_laptop
    try:
        battery = psutil.sensors_battery()
        if battery is not None:
            es_laptop = True
            return True
        
        if sys.platform == 'win32':
            try:
                result = subprocess.run(
                    ['wmic', 'systemenclosure', 'get', 'chassistypes'],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                laptop_types = ['8', '9', '10', '11', '14']
                for tipo in laptop_types:
                    if tipo in result.stdout:
                        es_laptop = True
                        return True
            except:
                pass
        es_laptop = False
        return False
    except:
        es_laptop = False
        return False

def desactivar_power_throttling():
    """
    Eliminado: instalación/gestión de planes/ajustes de energía.
    No-op para mantener la interfaz y lógica sin tocar el sistema.
    """
    return True

def activar_power_throttling():
    """
    Eliminado: instalación/gestión de planes/ajustes de energía.
    No-op para mantener la interfaz y lógica sin tocar el sistema.
    """
    return True

def _spawn_self_with_flag(flag: str):
    """
    Lanza este mismo ejecutable con una bandera (solo para EXE).
    """
    try:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        subprocess.Popen([sys.executable, flag], creationflags=flags)
    except Exception:
        pass

def _resolver_script(*nombres_posibles):
    base = Path(__file__).parent
    for nombre in nombres_posibles:
        p = base / nombre
        if p.exists():
            return p
    return None

def _mod_disponible(nombre: str) -> bool:
    try:
        spec = importlib.util.find_spec(nombre)
        return spec is not None
    except Exception:
        return False

def iniciar_modo_normal():
    global proceso_modo_normal
    if proceso_modo_normal:
        return True
    try:
        # Para EXE: podría implementarse como bandera interna si fuera necesario.
        script_path = _resolver_script("modonormal.py")
        if not script_path:
            messagebox.showerror("Error", "No se encontró modonormal.py")
            return False
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        proceso_modo_normal = subprocess.Popen([sys.executable, str(script_path)], creationflags=flags)
        return True
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo iniciar modo normal:\n{e}")
        return False

def detener_modo_normal():
    global proceso_modo_normal
    if not proceso_modo_normal:
        return
    try:
        proceso_modo_normal.terminate()
        proceso_modo_normal.wait(timeout=3)
    except:
        try:
            proceso_modo_normal.kill()
        except:
            pass
    finally:
        proceso_modo_normal = None

def iniciar_modo_agresivo():
    global proceso_modo_agresivo
    if proceso_modo_agresivo:
        return True
    try:
        script_path = _resolver_script("modoagresivo.py")
        if not script_path:
            messagebox.showerror("Error", "No se encontró modoagresivo.py")
            return False
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        proceso_modo_agresivo = subprocess.Popen([sys.executable, str(script_path)], creationflags=flags)
        return True
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo iniciar modo agresivo:\n{e}")
        return False

def detener_modo_agresivo():
    global proceso_modo_agresivo
    if not proceso_modo_agresivo:
        return
    try:
        proceso_modo_agresivo.terminate()
        proceso_modo_agresivo.wait(timeout=3)
    except:
        try:
            proceso_modo_agresivo.kill()
        except:
            pass
    finally:
        proceso_modo_agresivo = None

def iniciar_modo_juego():
    global proceso_modo_juego, modo_juego_activo
    if proceso_modo_juego:
        return True
    try:
        script_path = _resolver_script("modojuego.py")
        if not script_path:
            messagebox.showerror("Error", "No se encontró modojuego.py")
            return False
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        proceso_modo_juego = subprocess.Popen([sys.executable, str(script_path)], creationflags=flags)
        modo_juego_activo = True
        if interruptor_modo_normal:
            interruptor_modo_normal.set_enabled(False)
        if interruptor_modo_agresivo:
            interruptor_modo_agresivo.set_enabled(False)
        return True
    except:
        modo_juego_activo = False
        return False

def detener_modo_juego():
    global proceso_modo_juego, modo_juego_activo
    if not proceso_modo_juego:
        return
    try:
        proceso_modo_juego.terminate()
        proceso_modo_juego.wait(timeout=3)
    except:
        try:
            proceso_modo_juego.kill()
        except:
            pass
    finally:
        proceso_modo_juego = None
        modo_juego_activo = False
        if interruptor_modo_normal:
            interruptor_modo_normal.set_enabled(True)
        if interruptor_modo_agresivo:
            interruptor_modo_agresivo.set_enabled(True)

def verificar_juegos_activos():
    global modo_juego_activo
    if not ventana or not ventana.winfo_exists():
        return
    try:
        juegos_lista = set(lista_juegos.get(0, tk.END))
        if not juegos_lista:
            ventana.after(2000, verificar_juegos_activos)
            return
        juego_encontrado = False
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] in juegos_lista:
                    juego_encontrado = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        if juego_encontrado and not modo_juego_activo:
            if switches_config["modo_normal"]:
                detener_modo_normal()
                switches_config["modo_normal"] = False
                if interruptor_modo_normal:
                    interruptor_modo_normal.set_state(False)
            if switches_config["modo_agresivo"]:
                detener_modo_agresivo()
                switches_config["modo_agresivo"] = False
                if interruptor_modo_agresivo:
                    interruptor_modo_agresivo.set_state(False)
            iniciar_modo_juego()
            guardar_switches()
        elif not juego_encontrado and modo_juego_activo:
            detener_modo_juego()
            guardar_switches()
    except:
        pass
    ventana.after(2000, verificar_juegos_activos)

def crear_tarea_programada(task_name, description, command, arguments, delay=None):
    try:
        workdir = os.path.dirname(sys.executable) if is_frozen() else os.path.dirname(os.path.abspath(__file__))
        task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>{description}</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      {f'<Delay>{delay}</Delay>' if delay else ''}
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>"{command}"</Command>
      <Arguments>{arguments}</Arguments>
      <WorkingDirectory>{workdir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''
        temp_xml = os.path.join(workdir, "temp_task.xml")
        with open(temp_xml, 'w', encoding='utf-16') as f:
            f.write(task_xml)
        cmd = f'schtasks /Create /TN "{task_name}" /XML "{temp_xml}" /F'
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        try:
            os.remove(temp_xml)
        except:
            pass
        return result.returncode == 0
    except:
        return False

def eliminar_tarea_programada(task_name):
    try:
        cmd = f'schtasks /Delete /TN "{task_name}" /F'
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return result.returncode == 0
    except:
        return False

def crear_icono_neon():
    try:
        ico_path = resource_path("1.ico")
        if os.path.exists(ico_path):
            try:
                return Image.open(ico_path)
            except:
                pass
        img = Image.new('RGBA', (64, 64), (11, 15, 26, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([8, 8, 56, 56], outline=(0, 229, 255, 255), width=3)
        draw.ellipse([20, 20, 44, 44], fill=(179, 136, 255, 255), outline=(0, 229, 255, 255), width=2)
        draw.ellipse([10, 10, 15, 15], fill=(0, 229, 255, 255))
        draw.ellipse([49, 10, 54, 15], fill=(255, 77, 109, 255))
        draw.ellipse([10, 49, 15, 54], fill=(255, 77, 109, 255))
        draw.ellipse([49, 49, 54, 54], fill=(0, 229, 255, 255))
        return img
    except:
        return None

def restaurar_ventana(icon=None, item=None):
    try:
        if ventana and ventana.winfo_exists():
            ventana.after(0, lambda: [ventana.deiconify(), ventana.lift(), ventana.focus_force()])
    except:
        pass

def minimizar_ventana_bandeja():
    try:
        if ventana and ventana.winfo_exists():
            ventana.withdraw()
    except:
        pass

def cerrar_optimizador_completo(icon=None, item=None):
    global tray_icon, tray_thread_running
    detener_modo_normal()
    detener_modo_agresivo()
    detener_modo_juego()
    tray_thread_running = False
    if tray_icon and PYSTRAY_AVAILABLE:
        try:
            tray_icon.stop()
        except:
            pass
    if ventana and ventana.winfo_exists():
        try:
            ventana.after(0, ventana.destroy)
        except:
            pass
    try:
        sys.exit(0)
    except:
        os._exit(0)

def setup_tray_icon():
    global tray_icon, tray_thread_running
    if not PYSTRAY_AVAILABLE:
        return False
    try:
        menu = Menu(
            MenuItem("Restaurar", restaurar_ventana, default=True),
            MenuItem("Minimizar", minimizar_ventana_bandeja),
            Menu.SEPARATOR,
            MenuItem("Salir", cerrar_optimizador_completo)
        )
        icono_img = crear_icono_neon()
        if icono_img:
            tray_icon = Icon("GamingOptimizer", icono_img, "Gaming Optimizer", menu=menu)
            tray_thread_running = True
            def run_tray():
                try:
                    tray_icon.run()
                except:
                    pass
            threading.Thread(target=run_tray, daemon=True).start()
            return True
    except:
        pass
    return False

class InterruptorAnimado(tk.Canvas):
    def __init__(self, parent, command=None, **kwargs):
        super().__init__(parent, width=80, height=36, bg=parent['bg'], highlightthickness=0, **kwargs)
        self.command = command
        self.estado_on = False
        self.is_enabled = True
        self.color_off = "#2a2f3a"
        self.borde_off = "#20252e"
        self.color_on = COLOR_ACCENT
        self.borde_on = COLOR_ACCENT2
        self.color_circulo = "#ffffff"
        self.color_disabled = "#1a1e26"
        self.pill_left = self.create_oval(2, 2, 36, 34, fill=self.color_off, outline=self.borde_off, width=1)
        self.pill_center = self.create_rectangle(18, 2, 62, 34, fill=self.color_off, outline=self.borde_off, width=0)
        self.pill_right = self.create_oval(44, 2, 78, 34, fill=self.color_off, outline=self.borde_off, width=1)
        self.shadow = self.create_oval(6, 8, 38, 30, fill="#000000", outline="", stipple="gray25")
        self.circulo = self.create_oval(6, 6, 38, 30, fill=self.color_circulo, outline=self.borde_off, width=1)
        self.bind("<Button-1>", self.toggle)
        
    def set_state(self, state):
        self.estado_on = state
        self.animar(force=True)

    def set_enabled(self, enabled_state):
        self.is_enabled = enabled_state
        if not self.is_enabled:
            for item in (self.pill_left, self.pill_center, self.pill_right):
                self.itemconfig(item, fill=self.color_disabled)
            self.itemconfig(self.circulo, fill="#555555")
        else:
            self.animar(force=True)

    def toggle(self, event=None):
        if not self.is_enabled:
            return
        self.estado_on = not self.estado_on
        self.animar()
        if self.command:
            try:
                self.command(self.estado_on)
            except:
                pass

    def animar(self, force=False):
        destino_x = 40 if self.estado_on else 0
        new_fill = self.color_on if self.estado_on else self.color_off
        new_outline = self.borde_on if self.estado_on else self.borde_off
        if not self.is_enabled:
            new_fill = self.color_disabled
        for item in (self.pill_left, self.pill_center, self.pill_right):
            self.itemconfig(item, fill=new_fill, outline=new_outline)
        curr_x = self.coords(self.circulo)[0] - 6
        if force:
            self.move(self.circulo, destino_x - curr_x, 0)
            self.move(self.shadow, destino_x - curr_x, 0)
            return
        dist = destino_x - curr_x
        steps = 8
        for i in range(steps):
            self.move(self.circulo, dist / steps, 0)
            self.move(self.shadow, dist / steps, 0)
            self.update()
            self.after(10)

def toggle_modo_normal(estado):
    global switches_config
    if estado:
        if switches_config["modo_agresivo"]:
            detener_modo_agresivo()
            switches_config["modo_agresivo"] = False
            if interruptor_modo_agresivo:
                interruptor_modo_agresivo.set_state(False)
        if iniciar_modo_normal():
            switches_config["modo_normal"] = True
        else:
            switches_config["modo_normal"] = False
            interruptor_modo_normal.set_state(False)
    else:
        detener_modo_normal()
        switches_config["modo_normal"] = False
    guardar_switches()

def toggle_modo_agresivo(estado):
    global switches_config
    if estado:
        if switches_config["modo_normal"]:
            detener_modo_normal()
            switches_config["modo_normal"] = False
            if interruptor_modo_normal:
                interruptor_modo_normal.set_state(False)
        if iniciar_modo_agresivo():
            switches_config["modo_agresivo"] = True
        else:
            switches_config["modo_agresivo"] = False
            interruptor_modo_agresivo.set_state(False)
    else:
        detener_modo_agresivo()
        switches_config["modo_agresivo"] = False
    guardar_switches()

def toggle_notificaciones(estado):
    switches_config["notificaciones"] = estado
    guardar_switches()

def toggle_freno_termico(estado):
    switches_config["freno_termico"] = estado
    if es_laptop:
        return
    if estado:
        if not activar_power_throttling():
            messagebox.showwarning(
                "Advertencia",
                "No se pudo activar el Freno Térmico.\nEs posible que necesite permisos de administrador."
            )
    else:
        if not desactivar_power_throttling():
            messagebox.showwarning(
                "Advertencia",
                "No se pudo desactivar el Freno Térmico.\nEs posible que necesite permisos de administrador."
            )
    guardar_switches()

def toggle_autoinicio_windows(estado):
    switches_config["autoinicio_windows"] = estado
    task_name = "GamingOptimizerAutostart"
    if estado:
        command = sys.executable
        # En EXE no hace falta pasar ruta del script, el EXE es auto-contenido
        arguments = f'"{os.path.abspath(__file__)}"' if not is_frozen() else ""
        if crear_tarea_programada(task_name, "Autoinicio Gaming Optimizer", command, arguments):
            messagebox.showinfo("Autoinicio", "✓ Autoinicio configurado.\n\nEl optimizador se iniciará con Windows.")
            interruptor_sesion.set_enabled(True)
        else:
            messagebox.showerror("Error", "No se pudo crear la tarea de autoinicio.")
            switches_config["autoinicio_windows"] = False
            interruptor_autoinicio.set_state(False)
    else:
        eliminar_tarea_programada(task_name)
        messagebox.showinfo("Autoinicio", "✓ Autoinicio desactivado.")
        interruptor_sesion.set_enabled(False)
        if switches_config["optimizador_sesion"]:
            interruptor_sesion.set_state(False)
            toggle_optimizador_sesion(False)
    guardar_switches()

def toggle_optimizador_sesion(estado):
    switches_config["optimizador_sesion"] = estado
    task_name = "GamingOptimizerSessionOptimizer"
    if estado:
        script_path = resource_path("sesion.bat")
        if not os.path.exists(script_path):
            messagebox.showerror("Error", f"No se encontró el archivo:\n{script_path}")
            interruptor_sesion.set_state(False)
            switches_config["optimizador_sesion"] = False
            return
        # Ejecutar como admin y sin ventana visible: usar PowerShell para lanzar cmd.exe oculto que corre el .bat
        command = "powershell.exe"
        arguments = (
            "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden "
            f"-Command \"Start-Process -FilePath cmd.exe -ArgumentList '/c','\\\"{script_path}\\\"' -WindowStyle Hidden\""
        )
        if crear_tarea_programada(
            task_name, 
            "Optimizador de Sesión de Gaming Optimizer", 
            command, 
            arguments,
            delay="PT5S"
        ):
            messagebox.showinfo(
                "Optimizador de Sesión",
                "✓ Tarea creada correctamente.\n\nSe ejecutará 5 segundos después de iniciar sesión."
            )
        else:
            messagebox.showerror("Error", "No se pudo crear la tarea del Optimizador de Sesión.")
            interruptor_sesion.set_state(False)
            switches_config["optimizador_sesion"] = False
    else:
        eliminar_tarea_programada(task_name)
    guardar_switches()

def guardar_switches():
    try:
        with open(NOMBRE_ARCHIVO_CONFIG, 'r') as f:
            datos = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        datos = {}
    datos["switches"] = switches_config
    with open(NOMBRE_ARCHIVO_CONFIG, 'w') as f:
        json.dump(datos, f, indent=4)

def cargar_switches():
    global switches_config
    if not os.path.exists(NOMBRE_ARCHIVO_CONFIG):
        return
    try:
        with open(NOMBRE_ARCHIVO_CONFIG, 'r') as f:
            datos = json.load(f)
            switches_config = datos.get("switches", switches_config)
    except json.JSONDecodeError:
        pass

def guardar_listas():
    datos = {
        "juegos": list(lista_juegos.get(0, tk.END)),
        "lista_blanca": list(lista_blanca.get(0, tk.END)),
        "ignorar": list(lista_ignorar.get(0, tk.END)),
        "switches": switches_config
    }
    with open(NOMBRE_ARCHIVO_CONFIG, "w") as f:
        json.dump(datos, f, indent=4)

def cargar_listas():
    if not os.path.exists(NOMBRE_ARCHIVO_CONFIG):
        return
    try:
        with open(NOMBRE_ARCHIVO_CONFIG, "r") as f:
            datos = json.load(f)
        for W, L in [(lista_juegos, "juegos"), (lista_blanca, "lista_blanca"), (lista_ignorar, "ignorar")]:
            W.delete(0, tk.END)
            [W.insert(tk.END, i) for i in datos.get(L, [])]
        switches_config.update(datos.get("switches", {}))
    except json.JSONDecodeError:
        pass

def refrescar_lista_procesos():
    sel, view = lista_procesos.curselection(), lista_procesos.yview()
    lista_procesos.delete(0, tk.END)
    listas = {
        "juegos": set(lista_juegos.get(0, tk.END)),
        "blanca": set(lista_blanca.get(0, tk.END)),
        "ignorar": set(lista_ignorar.get(0, tk.END))
    }
    excluidos = {"svchost.exe", "smss.exe", "sihost.exe", "wininit.exe"}
    idx = 0
    for p in psutil.process_iter(['pid', 'name']):
        try:
            name = p.info['name']
            if name and name.lower() not in excluidos:
                lista_procesos.insert(tk.END, f"{name} (PID: {p.info['pid']})")
                bg_color = None
                if name in listas["ignorar"] and name in listas["blanca"]:
                    bg_color = "#084447"
                elif name in listas["juegos"]:
                    bg_color = COLOR_ACCENT_RED
                elif name in listas["blanca"]:
                    bg_color = COLOR_ACCENT
                elif name in listas["ignorar"]:
                    bg_color = COLOR_ACCENT2
                if bg_color:
                    try:
                        lista_procesos.itemconfig(idx, {'bg': bg_color, 'fg': COLOR_LIST_FG})
                    except:
                        pass
                idx += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    if sel:
        lista_procesos.selection_set(sel)
    lista_procesos.yview_moveto(view[0])

def agregar_exe_desde_explorador(lista):
    ruta = filedialog.askopenfilename(title="Seleccionar ejecutable", filetypes=(("Ejecutables", "*.exe"), ("Todos", "*.*")))
    if ruta and (nombre := os.path.basename(ruta)) not in lista.get(0, tk.END):
        lista.insert(tk.END, nombre)
        guardar_listas()
        refrescar_lista_procesos()

def eliminar_seleccionado(lista):
    for i in reversed(lista.curselection()):
        lista.delete(i)
    guardar_listas()
    refrescar_lista_procesos()

def agregar_proceso_seleccionado(lista):
    if (sel := lista_procesos.curselection()) and (nombre := lista_procesos.get(sel[0]).split(" (PID:")[0]) not in lista.get(0, tk.END):
        lista.insert(tk.END, nombre)
        guardar_listas()
        refrescar_lista_procesos()

def agregar_proceso_a_juegos(): 
    agregar_proceso_seleccionado(lista_juegos)

def agregar_proceso_a_blanca(): 
    agregar_proceso_seleccionado(lista_blanca)

def agregar_proceso_a_ignorar(): 
    agregar_proceso_seleccionado(lista_ignorar)

def ejecutar_optimizacion_total():
    try:
        vbs_path = resource_path("o.vbs")
        if not os.path.exists(vbs_path):
            messagebox.showerror("Error", f"No se encontró el archivo:\n{vbs_path}")
            return
        if sys.platform == 'win32':
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "wscript.exe", f'"{vbs_path}"', None, 1)
        else:
            messagebox.showwarning("Advertencia", "Esta función solo está disponible en Windows")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo ejecutar la optimización:\n{e}")

def ejecutar_restaurar_sistema():
    try:
        from RECUPERA import RestoreApp
        restore_window = tk.Toplevel(ventana)
        RestoreApp(restore_window)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo ejecutar la restauración:\n{e}")

def ejecutar_copia_seguridad():
    try:
        from COPIA import BackupApp
        backup_window = tk.Toplevel(ventana)
        BackupApp(backup_window)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo ejecutar la copia de seguridad:\n{e}")

def crear_frame_lista(parent, titulo, bg_color):
    frame = ttk.Frame(parent)
    frame.pack(expand=True, fill="both", padx=10, pady=10)
    ttk.Label(frame, text=titulo, font=("Segoe UI", 10, "bold")).pack(pady=(0, 5))
    frame_lista = ttk.Frame(frame)
    frame_lista.pack(expand=True, fill="both")
    scrollbar = ttk.Scrollbar(frame_lista, orient=tk.VERTICAL)
    lista = tk.Listbox(frame_lista, yscrollcommand=scrollbar.set, selectmode=tk.EXTENDED,
                       bg=COLOR_LIST_BG, fg=COLOR_LIST_FG, selectbackground=COLOR_ACCENT,
                       font=("Segoe UI", 10), highlightthickness=0)
    scrollbar.config(command=lista.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    lista.pack(side=tk.LEFT, expand=True, fill="both")
    return frame, lista

def centrar_ventana(win):
    win.update_idletasks()
    width = win.winfo_width()
    height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f'{width}x{height}+{x}+{y}')

# ===================== NUEVAS FUNCIONES SOLICITADAS =====================

def leer_switches_de_config():
    if not os.path.exists(NOMBRE_ARCHIVO_CONFIG):
        return None
    try:
        with open(NOMBRE_ARCHIVO_CONFIG, 'r') as f:
            datos = json.load(f)
            return datos.get("switches", None)
    except Exception:
        return None

def determinar_inicio_minimizado_y_guardar():
    """
    - Si es primera ejecución o si NO quedó activo modo normal/agresivo:
      guarda switches y retorna False (no minimizado).
    - Si había quedado modo normal o agresivo activos: retorna True (minimizado).
    """
    global switches_config
    switches_archivo = leer_switches_de_config()
    iniciar_minimizado = False
    if switches_archivo is None:
        guardar_switches()
        iniciar_minimizado = False
    else:
        switches_config.update(switches_archivo)
        iniciar_minimizado = bool(switches_archivo.get("modo_normal") or switches_archivo.get("modo_agresivo"))
        guardar_switches()  # Guardar SIEMPRE al inicio
    return iniciar_minimizado

def reproducir_gif_pantalla_completa_dos_veces():
    try:
        gif_path = resource_path("1.gif")
        if not os.path.exists(gif_path):
            return
        top = tk.Toplevel(ventana)
        top.overrideredirect(True)
        try:
            top.attributes("-fullscreen", True)
        except:
            sw, sh = top.winfo_screenwidth(), top.winfo_screenheight()
            top.geometry(f"{sw}x{sh}+0+0")
        top.attributes("-topmost", True)
        top.configure(bg="black")

        lbl = tk.Label(top, bg="black")
        lbl.pack(expand=True, fill="both")

        frames = []
        idx = 0
        while True:
            try:
                frame = tk.PhotoImage(file=str(gif_path), format=f"gif -index {idx}")
                frames.append(frame)
                idx += 1
            except tk.TclError:
                break

        if not frames:
            top.destroy()
            return

        delay_ms = 50
        estado = {"frame": 0, "vueltas": 0}

        def avanzar():
            lbl.configure(image=frames[estado["frame"]])
            estado["frame"] = (estado["frame"] + 1) % len(frames)
            if estado["frame"] == 0:
                estado["vueltas"] += 1
                if estado["vueltas"] >= 2:
                    try:
                        top.destroy()
                    except:
                        pass
                    return
            try:
                top.after(delay_ms, avanzar)
            except tk.TclError:
                pass

        top.after(0, avanzar)
    except Exception:
        pass

def lanzar_entradas():
    """
    A los 10s: lanzar entrada/entradas.
    - En EXE (frozen): relanzar este EXE con bandera interna.
    - En .py: lanzar el script detectado.
    """
    try:
        if is_frozen():
            _spawn_self_with_flag("--run-entradas")
            return
        script_path = _resolver_script("entrada.py", "entradas.py")
        if not script_path:
            return
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        subprocess.Popen([sys.executable, str(script_path)], creationflags=flags)
    except Exception:
        pass

def condiciones_sistema_ok(umbral=70):
    try:
        if modo_juego_activo:
            return False
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        return cpu <= umbral and mem <= umbral
    except Exception:
        return False

def intentar_ejecutar_limpieza():
    """
    A los 10 minutos: LIMPIEZA/limpia si condiciones OK.
    Si no: reintento en 1 hora.
    Si ejecuta: reprograma 7 días.
    """
    global limpieza_en_ejecucion
    if limpieza_en_ejecucion:
        return
    if not condiciones_sistema_ok(70):
        if ventana and ventana.winfo_exists():
            ventana.after(60 * 60 * 1000, intentar_ejecutar_limpieza)
        return

    if is_frozen():
        # En EXE relanzamos con bandera
        limpieza_en_ejecucion = True
        def worker_frozen():
            global limpieza_en_ejecucion
            try:
                flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                result = subprocess.run([sys.executable, "--run-limpieza"], creationflags=flags)
                if ventana and ventana.winfo_exists():
                    if result.returncode == 0:
                        ventana.after(7 * 24 * 60 * 60 * 1000, intentar_ejecutar_limpieza)
                    else:
                        ventana.after(60 * 60 * 1000, intentar_ejecutar_limpieza)
            except Exception:
                if ventana and ventana.winfo_exists():
                    ventana.after(60 * 60 * 1000, intentar_ejecutar_limpieza)
            finally:
                limpieza_en_ejecucion = False
        threading.Thread(target=worker_frozen, daemon=True).start()
        return

    # Modo desarrollo .py
    modulo = None
    for nombre in ("LIMPIEZA", "limpia"):
        if _mod_disponible(nombre):
            modulo = nombre
            break

    if modulo is None:
        if ventana and ventana.winfo_exists():
            ventana.after(60 * 60 * 1000, intentar_ejecutar_limpieza)
        return

    def worker():
        global limpieza_en_ejecucion
        limpieza_en_ejecucion = True
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            result = subprocess.run([sys.executable, "-c", f"import {modulo}; {modulo}.system_maintenance()"], creationflags=flags)
            if ventana and ventana.winfo_exists():
                if result.returncode == 0:
                    ventana.after(7 * 24 * 60 * 60 * 1000, intentar_ejecutar_limpieza)
                else:
                    ventana.after(60 * 60 * 1000, intentar_ejecutar_limpieza)
        except Exception:
            if ventana and ventana.winfo_exists():
                ventana.after(60 * 60 * 1000, intentar_ejecutar_limpieza)
        finally:
            limpieza_en_ejecucion = False

    threading.Thread(target=worker, daemon=True).start()

def intentar_ejecutar_discos():
    """
    A los 30 minutos: DISCOS/discos si condiciones OK.
    Si no: reintento en 30 minutos.
    Si ejecuta: reprograma 14 días.
    """
    global discos_en_ejecucion
    if discos_en_ejecucion:
        return
    if not condiciones_sistema_ok(70):
        if ventana and ventana.winfo_exists():
            ventana.after(30 * 60 * 1000, intentar_ejecutar_discos)
        return

    if is_frozen():
        discos_en_ejecucion = True
        def worker_frozen():
            global discos_en_ejecucion
            try:
                flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                result = subprocess.run([sys.executable, "--run-discos"], creationflags=flags)
                if ventana and ventana.winfo_exists():
                    if result.returncode == 0:
                        ventana.after(14 * 24 * 60 * 60 * 1000, intentar_ejecutar_discos)
                    else:
                        ventana.after(30 * 60 * 1000, intentar_ejecutar_discos)
            except Exception:
                if ventana and ventana.winfo_exists():
                    ventana.after(30 * 60 * 1000, intentar_ejecutar_discos)
            finally:
                discos_en_ejecucion = False
        threading.Thread(target=worker_frozen, daemon=True).start()
        return

    modulo = None
    for nombre in ("DISCOS", "discos"):
        if _mod_disponible(nombre):
            modulo = nombre
            break

    if modulo is None:
        if ventana and ventana.winfo_exists():
            ventana.after(30 * 60 * 1000, intentar_ejecutar_discos)
        return

    def worker():
        global discos_en_ejecucion
        discos_en_ejecucion = True
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            result = subprocess.run([sys.executable, "-c", f"import {modulo}; {modulo}.main()"], creationflags=flags)
            if ventana and ventana.winfo_exists():
                if result.returncode == 0:
                    ventana.after(14 * 24 * 60 * 60 * 1000, intentar_ejecutar_discos)
                else:
                    ventana.after(30 * 60 * 1000, intentar_ejecutar_discos)
        except Exception:
            if ventana and ventana.winfo_exists():
                ventana.after(30 * 60 * 1000, intentar_ejecutar_discos)
        finally:
            discos_en_ejecucion = False

    threading.Thread(target=worker, daemon=True).start()

def programar_tareas_inicio():
    if ventana and ventana.winfo_exists():
        ventana.after(0, reproducir_gif_pantalla_completa_dos_veces)
        ventana.after(10 * 1000, lanzar_entradas)
        ventana.after(10 * 60 * 1000, intentar_ejecutar_limpieza)
        ventana.after(30 * 60 * 1000, intentar_ejecutar_discos)

# ===================== FIN NUEVAS FUNCIONES =====================

def crear_interfaz(iniciar_minimizado=False):
    global ventana
    global lista_procesos, lista_juegos, lista_blanca, lista_ignorar
    global interruptor_modo_normal, interruptor_modo_agresivo, interruptor_autoinicio, interruptor_sesion
    
    detectar_laptop()
    ventana = tk.Tk()
    ventana.title("Gaming Optimizer")
    ventana.geometry("1050x600")
    ventana.configure(bg=COLOR_BG)
    ventana.overrideredirect(True)

    style = ttk.Style(ventana)
    try:
        style.theme_use('clam')
    except:
        pass
    style.configure('Gamer.TButton',
                    background=COLOR_NEUTRO, foreground=COLOR_TEXT,
                    relief='flat', padding=(8, 6), font=('Segoe UI', 10, 'bold'))
    style.map('Gamer.TButton',
              background=[('active', COLOR_ACCENT)],
              foreground=[('active', COLOR_BG)])

    frame_titulo = tk.Frame(ventana, bg=COLOR_NEUTRO, height=35)
    frame_titulo.pack(side="top", fill="x")
    frame_titulo.pack_propagate(False)

    def on_drag_start(event):
        frame_titulo.x = event.x
        frame_titulo.y = event.y

    def on_drag_motion(event):
        dx = event.x - frame_titulo.x
        dy = event.y - frame_titulo.y
        x = ventana.winfo_x() + dx
        y = ventana.winfo_y() + dy
        ventana.geometry(f"+{x}+{y}")

    label_titulo = tk.Label(frame_titulo, text="⬢ Asistente de Procesos Gaming ⬢", bg=COLOR_NEUTRO, 
                            fg=COLOR_ACCENT, font=("Segoe UI", 11, "bold"))
    label_titulo.pack(side="left", padx=15, pady=7)
    label_titulo.bind("<Button-1>", on_drag_start)
    label_titulo.bind("<B1-Motion>", on_drag_motion)

    btn_cerrar = tk.Button(frame_titulo, text="✕", bg=COLOR_NEUTRO, fg=COLOR_ACCENT_RED, 
                           font=("Segoe UI", 16, "bold"), relief="flat", bd=0, 
                           command=cerrar_optimizador_completo, activebackground=COLOR_ACCENT_RED, 
                           activeforeground=COLOR_BG, cursor="hand2", width=3)
    btn_cerrar.pack(side="right", padx=5, pady=2)
    
    btn_minimizar = tk.Button(frame_titulo, text="─", bg=COLOR_NEUTRO, fg=COLOR_ACCENT, 
                              font=("Segoe UI", 16, "bold"), relief="flat", bd=0, 
                              command=minimizar_ventana_bandeja, activebackground=COLOR_ACCENT, 
                              activeforeground=COLOR_BG, cursor="hand2", width=3)
    btn_minimizar.pack(side="right", padx=5, pady=2)

    frame_principal = tk.Frame(ventana, bg=COLOR_BG)
    frame_principal.pack(side="top", fill="both", expand=True)
    frame_principal.grid_columnconfigure(0, weight=3, minsize=275)
    frame_principal.grid_columnconfigure(1, weight=7)
    frame_principal.grid_rowconfigure(0, weight=1)

    frame_sector_izquierdo = tk.Frame(frame_principal, bg=COLOR_BG)
    frame_sector_izquierdo.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
    frame_procesos = ttk.Frame(frame_sector_izquierdo)
    frame_procesos.pack(expand=True, fill="both", padx=5, pady=5)
    ttk.Label(frame_procesos, text="Procesos en Ejecución", font=("Segoe UI", 10, "bold")).pack(pady=(0, 5))
    frame_lista_procesos = ttk.Frame(frame_procesos)
    frame_lista_procesos.pack(expand=True, fill="both")
    scrollbar_procesos = ttk.Scrollbar(frame_lista_procesos, orient=tk.VERTICAL)
    lista_procesos = tk.Listbox(frame_lista_procesos, yscrollcommand=scrollbar_procesos.set,
                                bg=COLOR_LIST_BG, fg=COLOR_LIST_FG, selectbackground=COLOR_ACCENT, 
                                font=("Segoe UI", 10), highlightthickness=0)
    scrollbar_procesos.config(command=lista_procesos.yview)
    scrollbar_procesos.pack(side=tk.RIGHT, fill=tk.Y)
    lista_procesos.pack(side=tk.LEFT, expand=True, fill="both")
    frame_botones_procesos = ttk.Frame(frame_procesos)
    frame_botones_procesos.pack(fill="x", pady=10)
    ttk.Button(frame_botones_procesos, text="Refrescar Lista", command=refrescar_lista_procesos, style="Gamer.TButton").pack(fill="x", pady=6)
    ttk.Button(frame_botones_procesos, text="Agregar a JUEGOS", command=agregar_proceso_a_juegos, style="Gamer.TButton").pack(fill="x", pady=6)
    ttk.Button(frame_botones_procesos, text="Agregar a L. BLANCA", command=agregar_proceso_a_blanca, style="Gamer.TButton").pack(fill="x", pady=6)
    ttk.Button(frame_botones_procesos, text="Agregar a IGNORAR", command=agregar_proceso_a_ignorar, style="Gamer.TButton").pack(fill="x", pady=6)

    frame_pestanas_contenedor = tk.Frame(frame_principal, bg=COLOR_BG)
    frame_pestanas_contenedor.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
    frame_pestanas_contenedor.grid_rowconfigure(1, weight=1)
    frame_botones_pestanas = tk.Frame(frame_pestanas_contenedor, bg=COLOR_BG)
    frame_botones_pestanas.grid(row=0, column=0, sticky="ew")
    frame_botones_pestanas.grid_columnconfigure((0, 1, 2, 3), weight=1)
    frame_contenido = tk.Frame(frame_pestanas_contenedor, bg=COLOR_PANEL)
    frame_contenido.grid(row=1, column=0, sticky="nsew")
    frame_contenido.grid_rowconfigure(0, weight=1)
    frame_contenido.grid_columnconfigure(0, weight=1)

    pagina_controles = tk.Frame(frame_contenido, bg=COLOR_BLANCO_PAGINA)
    pagina_juegos = tk.Frame(frame_contenido, bg=COLOR_ROJO_PAGINA)
    pagina_blanca = tk.Frame(frame_contenido, bg=COLOR_AZUL_PAGINA)
    pagina_ignorar = tk.Frame(frame_contenido, bg=COLOR_VERDE_PAGINA)
    paginas = [pagina_controles, pagina_juegos, pagina_blanca, pagina_ignorar]
    for p in paginas: 
        p.grid(row=0, column=0, sticky="nsew")
    botones_pestana = []

    def mostrar_pagina(p_mostrar):
        p_mostrar.tkraise()
        for i, p in enumerate(paginas):
            botones_pestana[i].config(relief="sunken" if p == p_mostrar else "raised")

    btn_defs = [("Controles", COLOR_NEUTRO, pagina_controles), ("Juegos", COLOR_PANEL, pagina_juegos),
                ("Lista Blanca", COLOR_PANEL, pagina_blanca), ("Ignorar", COLOR_PANEL, pagina_ignorar)]
    for i, (txt, clr, pag) in enumerate(btn_defs):
        btn = tk.Button(frame_botones_pestanas, text=txt, bg=COLOR_NEUTRO, fg=COLOR_TEXT,
                        activebackground=COLOR_ACCENT, activeforeground=COLOR_BG,
                        relief="raised", bd=0, command=lambda p=pag: mostrar_pagina(p),
                        font=("Segoe UI", 9, "bold"))
        btn.grid(row=0, column=i, sticky="ew", padx=2, pady=2)
        botones_pestana.append(btn)

    frame_interruptores = tk.Frame(pagina_controles, bg=COLOR_BLANCO_PAGINA)
    frame_interruptores.pack(side="left", fill="y", padx=10, pady=10)
    
    interruptor_modo_normal = InterruptorAnimado(frame_interruptores, command=toggle_modo_normal)
    interruptor_modo_normal.grid(row=0, column=0, padx=10, pady=(5, 5), sticky="w")
    ttk.Label(frame_interruptores, text="Modo Normal", font=("Segoe UI", 9)).grid(row=0, column=1, sticky="w", padx=5)
    
    interruptor_modo_agresivo = InterruptorAnimado(frame_interruptores, command=toggle_modo_agresivo)
    interruptor_modo_agresivo.grid(row=1, column=0, padx=10, pady=5, sticky="w")
    ttk.Label(frame_interruptores, text="Modo Agresivo", font=("Segoe UI", 9)).grid(row=1, column=1, sticky="w", padx=5)
    
    interruptor_notif = InterruptorAnimado(frame_interruptores, command=toggle_notificaciones)
    interruptor_notif.grid(row=2, column=0, padx=10, pady=5, sticky="w")
    ttk.Label(frame_interruptores, text="Notificaciones", font=("Segoe UI", 9)).grid(row=2, column=1, sticky="w", padx=5)
    
    interruptor_termo = InterruptorAnimado(frame_interruptores, command=toggle_freno_termico)
    interruptor_termo.grid(row=3, column=0, padx=10, pady=5, sticky="w")
    label_termo = ttk.Label(frame_interruptores, text="Freno Térmico", font=("Segoe UI", 9))
    label_termo.grid(row=3, column=1, sticky="w", padx=5)
    
    if es_laptop:
        interruptor_termo.set_enabled(False)
        label_termo.config(text="Freno Térmico (Deshabilitado en Laptop)")
    
    interruptor_autoinicio = InterruptorAnimado(frame_interruptores, command=toggle_autoinicio_windows)
    interruptor_autoinicio.grid(row=4, column=0, padx=10, pady=5, sticky="w")
    ttk.Label(frame_interruptores, text="Autoinicio con Windows", font=("Segoe UI", 9)).grid(row=4, column=1, sticky="w", padx=5)
    
    interruptor_sesion = InterruptorAnimado(frame_interruptores, command=toggle_optimizador_sesion)
    interruptor_sesion.grid(row=5, column=0, padx=10, pady=5, sticky="w")
    ttk.Label(frame_interruptores, text="Optimizador de Sesión", font=("Segoe UI", 9)).grid(row=5, column=1, sticky="w", padx=5)

    frame_botones_accion = tk.Frame(pagina_controles, bg=COLOR_BLANCO_PAGINA)
    frame_botones_accion.pack(side="right", fill="y", padx=10, pady=10)
    ttk.Button(frame_botones_accion, text="⚡ Optimización Total", 
               command=ejecutar_optimizacion_total, style="Gamer.TButton").pack(fill='x', pady=5, ipady=8)
    ttk.Button(frame_botones_accion, text="🔄 Restaurar Sistema", 
               command=ejecutar_restaurar_sistema, style="Gamer.TButton").pack(fill='x', pady=5, ipady=8)
    ttk.Button(frame_botones_accion, text="💾 Copia de Seguridad", 
               command=ejecutar_copia_seguridad, style="Gamer.TButton").pack(fill='x', pady=5, ipady=8)

    frame_juegos, lista_juegos = crear_frame_lista(pagina_juegos, "Lista de Juegos", COLOR_ROJO_PAGINA)
    frame_botones_juegos = ttk.Frame(pagina_juegos)
    frame_botones_juegos.pack(fill="x", padx=10, pady=10)
    ttk.Button(frame_botones_juegos, text="Agregar desde explorador", 
               command=lambda: agregar_exe_desde_explorador(lista_juegos), style="Gamer.TButton").pack(side="left", padx=5, ipady=5)
    ttk.Button(frame_botones_juegos, text="Eliminar seleccionado", 
               command=lambda: eliminar_seleccionado(lista_juegos), style="Gamer.TButton").pack(side="left", padx=5, ipady=5)

    frame_blanca, lista_blanca = crear_frame_lista(pagina_blanca, "Lista Blanca (Protegidos)", COLOR_AZUL_PAGINA)
    frame_botones_blanca = ttk.Frame(pagina_blanca)
    frame_botones_blanca.pack(fill="x", padx=10, pady=10)
    ttk.Button(frame_botones_blanca, text="Agregar desde explorador", 
               command=lambda: agregar_exe_desde_explorador(lista_blanca), style="Gamer.TButton").pack(side="left", padx=5, ipady=5)
    ttk.Button(frame_botones_blanca, text="Eliminar seleccionado", 
               command=lambda: eliminar_seleccionado(lista_blanca), style="Gamer.TButton").pack(side="left", padx=5, ipady=5)

    frame_ignorar, lista_ignorar = crear_frame_lista(pagina_ignorar, "Lista a Ignorar", COLOR_VERDE_PAGINA)
    frame_botones_ignorar = ttk.Frame(pagina_ignorar)
    frame_botones_ignorar.pack(fill="x", padx=10, pady=10)
    ttk.Button(frame_botones_ignorar, text="Agregar desde explorador", 
               command=lambda: agregar_exe_desde_explorador(lista_ignorar), style="Gamer.TButton").pack(side="left", padx=5, ipady=5)
    ttk.Button(frame_botones_ignorar, text="Eliminar seleccionado", 
               command=lambda: eliminar_seleccionado(lista_ignorar), style="Gamer.TButton").pack(side="left", padx=5, ipady=5)

    cargar_listas()
    cargar_switches()
    refrescar_lista_procesos()
    mostrar_pagina(pagina_controles)

    if switches_config.get("modo_normal"): 
        interruptor_modo_normal.set_state(True)
    if switches_config.get("modo_agresivo"): 
        interruptor_modo_agresivo.set_state(True)
    if switches_config.get("notificaciones"): 
        interruptor_notif.set_state(True)
    if not es_laptop and switches_config.get("freno_termico"): 
        interruptor_termo.set_state(True)
    if switches_config.get("autoinicio_windows"): 
        interruptor_autoinicio.set_state(True)
    if switches_config.get("optimizador_sesion"): 
        interruptor_sesion.set_state(True)

    interruptor_sesion.set_enabled(switches_config.get("autoinicio_windows", False))

    tray_ok = setup_tray_icon()
    centrar_ventana(ventana)
    ventana.after(2000, verificar_juegos_activos)

    if iniciar_minimizado and tray_ok:
        minimizar_ventana_bandeja()
    else:
        try:
            ventana.deiconify()
            ventana.lift()
            ventana.focus_force()
        except:
            pass

    programar_tareas_inicio()
    return ventana

# ----------------- Entradas internas para EXE (banderas) ---------------------
def _run_entradas_main():
    # Ejecutar entradas o entrada como si fueran __main__
    for nombre in ("entradas", "entrada"):
        if _mod_disponible(nombre):
            try:
                runpy.run_module(nombre, run_name="__main__")
                return 0
            except SystemExit as se:
                return int(getattr(se, "code", 0) or 0)
            except Exception:
                pass
    return 1

def _run_limpieza_main():
    for nombre in ("LIMPIEZA", "limpia"):
        if _mod_disponible(nombre):
            try:
                mod = importlib.import_module(nombre)
                rc = 0
                try:
                    res = mod.system_maintenance()
                    rc = 0 if (res is None or res >= 0) else 1
                except Exception:
                    rc = 1
                return rc
            except Exception:
                pass
    return 1

def _run_discos_main():
    for nombre in ("DISCOS", "discos"):
        if _mod_disponible(nombre):
            try:
                mod = importlib.import_module(nombre)
                mod.main()
                return 0
            except SystemExit as se:
                return int(getattr(se, "code", 0) or 0)
            except Exception:
                pass
    return 1
# -----------------------------------------------------------------------------


if __name__ == "__main__":
    # Manejo de banderas internas para EXE
    if "--run-entradas" in sys.argv:
        sys.exit(_run_entradas_main())
    if "--run-limpieza" in sys.argv:
        sys.exit(_run_limpieza_main())
    if "--run-discos" in sys.argv:
        sys.exit(_run_discos_main())

    try:
        iniciar_minimizado = determinar_inicio_minimizado_y_guardar()

        if sys.platform == 'win32' and not ctypes.windll.shell32.IsUserAnAdmin():
            try:
                messagebox.showwarning("Permisos", "Se recomienda ejecutar como Administrador para un funcionamiento completo.")
            except:
                pass

        ventana = crear_interfaz(iniciar_minimizado)
        ventana.mainloop()
    except KeyboardInterrupt:
        cerrar_optimizador_completo()
    except Exception:
        import traceback
        traceback.print_exc()