import winreg
import os
import time
import json
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import sys
import subprocess
from datetime import datetime
import logging

# Configuración de logging
logging.basicConfig(
    filename='autoinicio_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuración
SCAN_INTERVAL = 60
KNOWN_ENTRIES_FILE = 'entradas_conocidas.json'
CONFIG_FILE = 'config.json'

# Claves de registro a escanear
REGISTRY_PATHS = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
]

# Carpeta de inicio
STARTUP_FOLDER = os.path.join(os.getenv('APPDATA'), r"Microsoft\Windows\Start Menu\Programs\Startup")

# Colores - Diseño Moderno Minimalista
COLOR_PRIMARY = "#6C63FF"
COLOR_SECONDARY = "#4CAF50"
COLOR_DANGER = "#FF6B6B"
COLOR_WARNING = "#FFA726"
COLOR_BG = "#F5F7FA"
COLOR_CARD = "#FFFFFF"
COLOR_TEXT = "#2D3436"
COLOR_TEXT_LIGHT = "#636E72"
COLOR_SHADOW = "#B2BEC3"

class AnimatedButton(tk.Canvas):
    def __init__(self, parent, text, command, bg_color, hover_color, width=150, height=45, **kwargs):
        super().__init__(parent, width=width, height=height, bg=COLOR_CARD, highlightthickness=0)
        self.text = text
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.width = width
        self.height = height
        self.current_color = bg_color
        self.is_hovered = False
        self.animation_id = None
        
        self.draw_button()
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        
    def draw_button(self):
        self.delete("all")
        # Sombra
        self.create_oval(5, 5, self.width-5, self.height-5, 
                        fill=COLOR_SHADOW, outline="", tags="shadow")
        # Botón principal
        self.create_oval(2, 2, self.width-2, self.height-2, 
                        fill=self.current_color, outline="", tags="button")
        # Texto
        self.create_text(self.width//2, self.height//2, 
                        text=self.text, fill="white", 
                        font=("Segoe UI", 11, "bold"), tags="text")
        
    def hex_to_rgb(self, hex_color):
        return tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
    
    def rgb_to_hex(self, rgb):
        return f"#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}"
    
    def animate_color(self, target_color, step=0):
        if not self.winfo_exists():
            return
            
        current = self.hex_to_rgb(self.current_color)
        target = self.hex_to_rgb(target_color)
        
        steps = 10
        if step <= steps:
            r = current[0] + (target[0] - current[0]) * step / steps
            g = current[1] + (target[1] - current[1]) * step / steps
            b = current[2] + (target[2] - current[2]) * step / steps
            self.current_color = self.rgb_to_hex((r, g, b))
            self.draw_button()
            
            self.animation_id = self.after(20, lambda: self.animate_color(target_color, step + 1))
        else:
            self.current_color = target_color
            self.draw_button()
    
    def on_enter(self, event):
        if self.animation_id:
            self.after_cancel(self.animation_id)
        self.is_hovered = True
        self.animate_color(self.hover_color)
        
    def on_leave(self, event):
        if self.animation_id:
            self.after_cancel(self.animation_id)
        self.is_hovered = False
        self.animate_color(self.bg_color)
        
    def on_click(self, event):
        if self.command:
            # Animación de click
            original_width = self.width
            original_height = self.height
            self.config(width=self.width-5, height=self.height-5)
            self.draw_button()
            self.update()
            self.after(100, lambda: [
                self.config(width=original_width, height=original_height),
                self.draw_button(),
                self.command()
            ])

class ModernAlertWindow:
    def __init__(self, entrada):
        self.entrada = entrada
        self.respuesta = None
        self.window = tk.Toplevel()
        self.window.overrideredirect(True)
        self.window.configure(bg=COLOR_BG)
        
        # Tamaño y posición
        width, height = 700, 550
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
        self.window.attributes('-alpha', 0.0)
        self.window.attributes('-topmost', True)
        
        self.create_ui()
        self.fade_in()
        
        self.window.transient()
        self.window.grab_set()
        self.window.focus_force()
        
    def create_ui(self):
        # Frame principal con sombra
        shadow_frame = tk.Frame(self.window, bg=COLOR_SHADOW)
        shadow_frame.place(x=5, y=5, width=690, height=540)
        
        main_frame = tk.Frame(self.window, bg=COLOR_CARD)
        main_frame.place(x=0, y=0, width=690, height=540)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=COLOR_PRIMARY, height=80)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Icono animado
        self.icon_canvas = tk.Canvas(header_frame, width=60, height=60, 
                                     bg=COLOR_PRIMARY, highlightthickness=0)
        self.icon_canvas.pack(pady=10)
        self.icon_size = 40
        self.icon_growing = True
        self.animate_icon()
        
        # Título
        title_label = tk.Label(header_frame, text="🔔 ALERTA DE SEGURIDAD",
                              font=("Segoe UI", 16, "bold"), 
                              fg="white", bg=COLOR_PRIMARY)
        title_label.pack()
        
        # Contenedor de contenido
        content_frame = tk.Frame(main_frame, bg=COLOR_CARD)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Subtítulo
        subtitle = tk.Label(content_frame, 
                           text="Se detectó un nuevo elemento de autoinicio",
                           font=("Segoe UI", 12), fg=COLOR_TEXT_LIGHT, bg=COLOR_CARD)
        subtitle.pack(pady=(0, 20))
        
        # Card de información
        info_card = tk.Frame(content_frame, bg=COLOR_BG, relief=tk.FLAT)
        info_card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Información detallada
        details = [
            ("Tipo", self.entrada['tipo']),
            ("Nombre", self.entrada['nombre']),
            ("Ubicación", self.entrada['ubicacion']),
        ]
        
        if self.entrada.get('valor'):
            details.append(("Valor", self.entrada['valor']))
        
        for i, (label, value) in enumerate(details):
            detail_frame = tk.Frame(info_card, bg=COLOR_BG)
            detail_frame.pack(fill=tk.X, padx=15, pady=8)
            
            tk.Label(detail_frame, text=f"{label}:", 
                    font=("Segoe UI", 10, "bold"), 
                    fg=COLOR_TEXT, bg=COLOR_BG).pack(anchor="w")
            
            value_label = tk.Label(detail_frame, text=str(value), 
                                  font=("Segoe UI", 9), 
                                  fg=COLOR_TEXT_LIGHT, bg=COLOR_BG,
                                  wraplength=600, justify="left")
            value_label.pack(anchor="w", padx=(10, 0))
        
        # Botones
        button_frame = tk.Frame(content_frame, bg=COLOR_CARD)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Botón Mantener
        btn_keep = AnimatedButton(button_frame, "✓ MANTENER", 
                                 self.mantener, COLOR_SECONDARY, "#45A049")
        btn_keep.pack(side=tk.RIGHT, padx=5)
        
        # Botón Eliminar
        btn_delete = AnimatedButton(button_frame, "✗ ELIMINAR", 
                                   self.eliminar, COLOR_DANGER, "#E85555")
        btn_delete.pack(side=tk.RIGHT, padx=5)
        
        # Botón Preguntar después
        btn_later = AnimatedButton(button_frame, "⏰ MÁS TARDE", 
                                  self.preguntar_despues, COLOR_WARNING, "#FB8C00",
                                  width=180)
        btn_later.pack(side=tk.LEFT, padx=5)
        
    def animate_icon(self):
        if not self.icon_canvas.winfo_exists():
            return
            
        self.icon_canvas.delete("all")
        x, y = 30, 30
        
        # Círculo externo pulsante
        self.icon_canvas.create_oval(x-self.icon_size//2, y-self.icon_size//2, 
                                     x+self.icon_size//2, y+self.icon_size//2,
                                     fill="white", outline="")
        # Círculo interno
        inner_size = self.icon_size // 2
        self.icon_canvas.create_oval(x-inner_size//2, y-inner_size//2, 
                                     x+inner_size//2, y+inner_size//2,
                                     fill=COLOR_WARNING, outline="")
        
        # Animar pulso
        if self.icon_growing:
            self.icon_size += 2
            if self.icon_size >= 50:
                self.icon_growing = False
        else:
            self.icon_size -= 2
            if self.icon_size <= 30:
                self.icon_growing = True
        
        self.icon_canvas.after(50, self.animate_icon)
        
    def fade_in(self, alpha=0.0):
        if alpha < 1.0:
            alpha += 0.1
            self.window.attributes('-alpha', alpha)
            self.window.after(30, lambda: self.fade_in(alpha))
        
    def fade_out(self, callback, alpha=1.0):
        if alpha > 0.0:
            alpha -= 0.1
            self.window.attributes('-alpha', alpha)
            self.window.after(30, lambda: self.fade_out(callback, alpha))
        else:
            callback()
        
    def mantener(self):
        self.respuesta = "MANTENER"
        self.guardar_decision()
        self.fade_out(self.window.destroy)
        
    def eliminar(self):
        self.respuesta = "ELIMINAR"
        eliminar_entrada(self.entrada['raw'])
        self.guardar_decision()
        self.fade_out(self.window.destroy)
        
    def preguntar_despues(self):
        self.respuesta = "PREGUNTAR_DESPUES"
        self.fade_out(self.window.destroy)
        
    def guardar_decision(self):
        if self.respuesta == "MANTENER":
            entradas_conocidas = cargar_entradas_conocidas()
            entradas_conocidas.append(self.entrada['raw'])
            guardar_entradas_conocidas(entradas_conocidas)
            
    def show(self):
        self.window.wait_window(self.window)
        return self.respuesta

def instalar_pyinstaller():
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        logging.info("PyInstaller instalado correctamente.")
    except Exception as e:
        logging.error(f"Error instalando PyInstaller: {e}")

def cargar_entradas_conocidas():
    try:
        if not os.path.exists(KNOWN_ENTRIES_FILE):
            return []
        with open(KNOWN_ENTRIES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error cargando entradas conocidas: {e}")
        return []

def guardar_entradas_conocidas(entradas):
    try:
        with open(KNOWN_ENTRIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(entradas, f, indent=2, ensure_ascii=False)
        logging.info(f"Entradas conocidas guardadas: {len(entradas)}")
    except Exception as e:
        logging.error(f"Error guardando entradas conocidas: {e}")

def obtener_autoinicios_actuales():
    entradas = []
    
    for root, path in REGISTRY_PATHS:
        try:
            with winreg.OpenKey(root, path) as key:
                for i in range(0, winreg.QueryInfoKey(key)[1]):
                    try:
                        nombre, valor, _ = winreg.EnumValue(key, i)
                        entradas.append({
                            'tipo': 'REGISTRO',
                            'ubicacion': path,
                            'nombre': nombre,
                            'valor': str(valor),
                            'raw': f"REG:{path} -> {nombre} => {valor}"
                        })
                    except Exception as e:
                        logging.warning(f"Error leyendo valor de registro: {e}")
        except FileNotFoundError:
            logging.warning(f"Ruta de registro no encontrada: {path}")
        except Exception as e:
            logging.error(f"Error accediendo a registro {path}: {e}")

    try:
        if os.path.exists(STARTUP_FOLDER):
            for file in os.listdir(STARTUP_FOLDER):
                if file.lower() not in ['desktop.ini', 'thumbs.db']:
                    file_path = os.path.join(STARTUP_FOLDER, file)
                    entradas.append({
                        'tipo': 'ARCHIVO',
                        'ubicacion': STARTUP_FOLDER,
                        'nombre': file,
                        'valor': file_path,
                        'raw': f"FILE:{STARTUP_FOLDER} -> {file}"
                    })
    except Exception as e:
        logging.error(f"Error escaneando carpeta de inicio: {e}")

    return entradas

def eliminar_entrada(entrada):
    try:
        if entrada.startswith("REG:"):
            _, resto = entrada.split(":", 1)
            path, datos = resto.split("->")
            path = path.strip()
            nombre = datos.split("=>")[0].strip()
            
            for root, reg_path in REGISTRY_PATHS:
                if reg_path == path:
                    try:
                        with winreg.OpenKey(root, reg_path, 0, winreg.KEY_SET_VALUE) as key:
                            winreg.DeleteValue(key, nombre)
                        logging.info(f"Entrada de registro eliminada: {nombre}")
                        return True
                    except Exception as e:
                        logging.error(f"Error eliminando entrada de registro: {e}")
                        
        elif entrada.startswith("FILE:"):
            _, resto = entrada.split(":", 1)
            folder, file = resto.split("->")
            archivo = os.path.join(folder.strip(), file.strip())
            
            if os.path.exists(archivo):
                os.remove(archivo)
                logging.info(f"Archivo eliminado: {archivo}")
                return True
    except Exception as e:
        logging.error(f"Error eliminando entrada: {e}")
        return False

if __name__ == '__main__':
    try:
        import PyInstaller
    except ImportError:
        instalar_pyinstaller()

    root = tk.Tk()
    root.withdraw()

    entradas_conocidas = cargar_entradas_conocidas()
    nuevas_detectadas = False

    try:
        actuales = obtener_autoinicios_actuales()
        nuevas = [e for e in actuales if e['raw'] not in entradas_conocidas]

        if nuevas:
            nuevas_detectadas = True
            logging.info(f"Nuevas entradas detectadas: {len(nuevas)}")
            
            for nueva in nuevas:
                alert = ModernAlertWindow(nueva)
                respuesta = alert.show()
                logging.info(f"Respuesta para {nueva['nombre']}: {respuesta}")
        else:
            logging.info("No se detectaron nuevas entradas")
        
        if not nuevas_detectadas or not nuevas:
            root.after(100, root.destroy)
            
    except Exception as e:
        logging.error(f"Error durante la ejecución: {e}")
        root.after(100, root.destroy)
    
    root.mainloop()