import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import threading
import ctypes
import json
import shutil
from datetime import datetime

class BackupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Herramienta de Backup Completa")
        self.color_fondo_progreso = "#D8BFD8"
        self.color_fondo_finalizado = "#28a745"
        self.color_boton_salir = "#dc3545"

        window_width = 500
        window_height = 180
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        self.root.protocol("WM_DELETE_WINDOW", self.disable_close)
        self.root.config(bg=self.color_fondo_progreso)

        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure("TFrame", background=self.color_fondo_progreso)
        style.configure("TLabel", background=self.color_fondo_progreso, foreground="black")
        style.configure("TButton", background="#f0f0f0", foreground="black")
        style.configure("Violet.Horizontal.TProgressbar", troughcolor=self.color_fondo_progreso, background='purple')

        self.main_frame = ttk.Frame(self.root, padding="20", style="TFrame")
        self.main_frame.pack(expand=True, fill=tk.BOTH)

        self.progress_label = ttk.Label(self.main_frame, text="Iniciando backup completo del sistema...", font=("Segoe UI", 10))
        self.progress_label.pack(pady=(0, 5))

        self.detail_label = ttk.Label(self.main_frame, text="", font=("Segoe UI", 8))
        self.detail_label.pack(pady=(0, 5))

        self.progress_bar = ttk.Progressbar(self.main_frame, orient='horizontal', length=400, mode='determinate', style="Violet.Horizontal.TProgressbar")
        self.progress_bar.pack(pady=10)

        self.start_backup_thread()

    def disable_close(self):
        pass

    def start_backup_thread(self):
        backup_thread = threading.Thread(target=self.run_backup_process)
        backup_thread.daemon = True
        backup_thread.start()

    def update_progress(self, value, text, detail=""):
        self.progress_bar['value'] = value
        self.progress_label['text'] = text
        self.detail_label['text'] = detail
        self.root.update_idletasks()

    def show_completion_window(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.main_frame.destroy()

        self.root.overrideredirect(True)
        self.root.config(bg=self.color_fondo_finalizado)
        
        window_width = 400
        window_height = 150
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        completion_label = tk.Label(
            self.root,
            text="✓ Copia de seguridad completada",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg=self.color_fondo_finalizado
        )
        completion_label.pack(pady=(25, 10))

        exit_button = tk.Button(
            self.root,
            text="Salir",
            font=("Segoe UI", 10, "bold"),
            fg="white",
            bg=self.color_boton_salir,
            command=self.root.destroy,
            relief=tk.FLAT,
            activebackground="#c82333",
            activeforeground="white",
            padx=15,
            pady=5
        )
        exit_button.pack(pady=10)

    def run_command(self, command):
        try:
            subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        except:
            return False

    def backup_drivers(self, backup_dir):
        drivers_dir = os.path.join(backup_dir, "drivers")
        try:
            os.makedirs(drivers_dir, exist_ok=True)
            self.run_command(f'dism /online /export-driver /destination:"{drivers_dir}"')
        except:
            pass

    def backup_network_profiles(self, backup_dir):
        network_dir = os.path.join(backup_dir, "network_profiles")
        try:
            os.makedirs(network_dir, exist_ok=True)
            result = subprocess.run('netsh wlan show profiles', capture_output=True, text=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            profiles = [line.split(":")[1].strip() for line in result.stdout.split('\n') if "All User Profile" in line]
            for profile in profiles:
                safe_name = "".join(c for c in profile if c.isalnum() or c in (' ', '-', '_')).strip()
                self.run_command(f'netsh wlan export profile name="{profile}" folder="{network_dir}" key=clear')
        except:
            pass

    def backup_installed_programs(self, backup_dir):
        try:
            programs = []
            keys = [
                r'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
                r'HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall',
                r'HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'
            ]
            for key in keys:
                try:
                    result = subprocess.run(f'reg query "{key}"', capture_output=True, text=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    for line in result.stdout.split('\n'):
                        if 'HKEY_' in line:
                            subkey = line.strip()
                            name_result = subprocess.run(f'reg query "{subkey}" /v DisplayName', capture_output=True, text=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                            if name_result.returncode == 0:
                                for name_line in name_result.stdout.split('\n'):
                                    if 'DisplayName' in name_line and 'REG_SZ' in name_line:
                                        program_name = name_line.split('REG_SZ')[-1].strip()
                                        if program_name:
                                            programs.append(program_name)
                except:
                    pass
            with open(os.path.join(backup_dir, "installed_programs.txt"), 'w', encoding='utf-8') as f:
                for program in sorted(set(programs)):
                    f.write(f"{program}\n")
        except:
            pass

    def backup_environment_variables(self, backup_dir):
        try:
            self.run_command(f'reg export "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment" "{os.path.join(backup_dir, "env_system.reg")}" /y')
            self.run_command(f'reg export "HKCU\\Environment" "{os.path.join(backup_dir, "env_user.reg")}" /y')
        except:
            pass

    def backup_startup_programs(self, backup_dir):
        try:
            startup_keys = [
                (r'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run', 'startup_system_run.reg'),
                (r'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce', 'startup_system_runonce.reg'),
                (r'HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run', 'startup_user_run.reg'),
                (r'HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce', 'startup_user_runonce.reg'),
            ]
            for key, filename in startup_keys:
                self.run_command(f'reg export "{key}" "{os.path.join(backup_dir, filename)}" /y')
        except:
            pass

    def backup_taskbar_settings(self, backup_dir):
        try:
            self.run_command(f'reg export "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Taskband" "{os.path.join(backup_dir, "taskbar_taskband.reg")}" /y')
            self.run_command(f'reg export "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" "{os.path.join(backup_dir, "explorer_advanced.reg")}" /y')
            self.run_command(f'reg export "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StuckRects3" "{os.path.join(backup_dir, "taskbar_position.reg")}" /y')
        except:
            pass

    def backup_file_associations(self, backup_dir):
        try:
            self.run_command(f'reg export "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FileExts" "{os.path.join(backup_dir, "file_associations.reg")}" /y')
            self.run_command(f'reg export "HKLM\\SOFTWARE\\Classes" "{os.path.join(backup_dir, "file_classes_system.reg")}" /y')
        except:
            pass

    def backup_desktop_settings(self, backup_dir):
        try:
            self.run_command(f'reg export "HKCU\\Control Panel\\Desktop" "{os.path.join(backup_dir, "desktop_settings.reg")}" /y')
            self.run_command(f'reg export "HKCU\\Control Panel\\Colors" "{os.path.join(backup_dir, "desktop_colors.reg")}" /y')
            self.run_command(f'reg export "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes" "{os.path.join(backup_dir, "themes.reg")}" /y')
        except:
            pass

    def backup_fonts(self, backup_dir):
        try:
            self.run_command(f'reg export "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts" "{os.path.join(backup_dir, "fonts_registry.reg")}" /y')
        except:
            pass

    def backup_mouse_keyboard(self, backup_dir):
        try:
            self.run_command(f'reg export "HKCU\\Control Panel\\Mouse" "{os.path.join(backup_dir, "mouse_settings.reg")}" /y')
            self.run_command(f'reg export "HKCU\\Control Panel\\Keyboard" "{os.path.join(backup_dir, "keyboard_settings.reg")}" /y')
            self.run_command(f'reg export "HKCU\\Control Panel\\Accessibility" "{os.path.join(backup_dir, "accessibility.reg")}" /y')
        except:
            pass

    def backup_sound_settings(self, backup_dir):
        try:
            self.run_command(f'reg export "HKCU\\AppEvents\\Schemes" "{os.path.join(backup_dir, "sound_schemes.reg")}" /y')
            self.run_command(f'reg export "HKCU\\Software\\Microsoft\\Multimedia\\Audio" "{os.path.join(backup_dir, "audio_settings.reg")}" /y')
        except:
            pass

    def backup_windows_update(self, backup_dir):
        try:
            self.run_command(f'reg export "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate" "{os.path.join(backup_dir, "windows_update.reg")}" /y')
            self.run_command(f'reg export "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate" "{os.path.join(backup_dir, "windows_update_policies.reg")}" /y')
        except:
            pass

    def backup_firewall_rules(self, backup_dir):
        try:
            self.run_command(f'netsh advfirewall export "{os.path.join(backup_dir, "firewall_rules.wfw")}"')
        except:
            pass

    def backup_dns_cache(self, backup_dir):
        try:
            result = subprocess.run('ipconfig /displaydns', capture_output=True, text=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            with open(os.path.join(backup_dir, "dns_cache.txt"), 'w', encoding='utf-8') as f:
                f.write(result.stdout)
        except:
            pass

    def backup_hosts_file(self, backup_dir):
        try:
            hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
            if os.path.exists(hosts_path):
                shutil.copy2(hosts_path, os.path.join(backup_dir, "hosts"))
        except:
            pass

    def backup_power_scheme(self, backup_dir):
        try:
            result = subprocess.run('powercfg /getactivescheme', capture_output=True, text=True, shell=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            line = result.stdout.strip()
            guid = line.split(' ')[3]
            self.run_command(f'powercfg /export "{os.path.join(backup_dir, "power_scheme_backup.pow")}" {guid}')
            result = subprocess.run('powercfg /list', capture_output=True, text=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            with open(os.path.join(backup_dir, "power_schemes_list.txt"), 'w', encoding='utf-8') as f:
                f.write(result.stdout)
        except:
            pass

    def backup_system_info(self, backup_dir):
        try:
            commands = [
                ('systeminfo', 'system_info.txt'),
                ('driverquery', 'drivers_list.txt'),
                ('wmic os get /format:list', 'os_info.txt'),
                ('wmic cpu get /format:list', 'cpu_info.txt'),
                ('wmic baseboard get /format:list', 'motherboard_info.txt'),
                ('wmic memorychip get /format:list', 'memory_info.txt'),
                ('wmic diskdrive get /format:list', 'disk_info.txt'),
            ]
            for cmd, filename in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
                    with open(os.path.join(backup_dir, filename), 'w', encoding='utf-8') as f:
                        f.write(result.stdout)
                except:
                    pass
        except:
            pass

    def backup_printer_settings(self, backup_dir):
        try:
            self.run_command(f'reg export "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Print" "{os.path.join(backup_dir, "printer_settings.reg")}" /y')
            result = subprocess.run('wmic printer get /format:list', capture_output=True, text=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            with open(os.path.join(backup_dir, "printers_list.txt"), 'w', encoding='utf-8') as f:
                f.write(result.stdout)
        except:
            pass

    def backup_windows_features(self, backup_dir):
        try:
            result = subprocess.run('dism /online /get-features /format:table', capture_output=True, text=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            with open(os.path.join(backup_dir, "windows_features.txt"), 'w', encoding='utf-8') as f:
                f.write(result.stdout)
        except:
            pass

    def create_backup_manifest(self, backup_dir):
        try:
            manifest = {
                "backup_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "computer_name": os.environ.get('COMPUTERNAME', 'Unknown'),
                "username": os.environ.get('USERNAME', 'Unknown'),
                "os_version": os.sys.platform,
                "backup_version": "2.0_ULTRA_ROBUST"
            }
            with open(os.path.join(backup_dir, "backup_manifest.json"), 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=4)
        except:
            pass

    def run_backup_process(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(base_dir, "backup")

        try:
            os.makedirs(backup_dir, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Error", f"No se pudo crear el directorio de backup: {e}")
            self.root.destroy()
            return

        tasks = [
            ("Sistema: Servicios", lambda: self.run_command(f'reg export "HKLM\\SYSTEM\\CurrentControlSet\\Services" "{os.path.join(backup_dir, "services_backup.reg")}" /y')),
            ("Sistema: Tareas Programadas", lambda: self.run_command(f'reg export "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Schedule" "{os.path.join(backup_dir, "scheduled_tasks_backup.reg")}" /y')),
            ("Red: TCP/IP", lambda: self.run_command(f'reg export "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" "{os.path.join(backup_dir, "network_tcpip_params.reg")}" /y')),
            ("Red: Perfiles WiFi", lambda: self.backup_network_profiles(backup_dir)),
            ("Red: Firewall", lambda: self.backup_firewall_rules(backup_dir)),
            ("Red: DNS Cache", lambda: self.backup_dns_cache(backup_dir)),
            ("Red: Hosts File", lambda: self.backup_hosts_file(backup_dir)),
            ("Red: QoS", lambda: self.run_command(f'reg export "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\QoS" "{os.path.join(backup_dir, "network_qos.reg")}" /y')),
            ("Rendimiento: IFEO", lambda: self.run_command(f'reg export "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options" "{os.path.join(backup_dir, "process_priorities_ifeo.reg")}" /y')),
            ("Rendimiento: Memoria", lambda: self.run_command(f'reg export "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" "{os.path.join(backup_dir, "memory_management.reg")}" /y')),
            ("Explorador: Sistema", lambda: self.run_command(f'reg export "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer" "{os.path.join(backup_dir, "explorer_lm.reg")}" /y')),
            ("Explorador: Usuario", lambda: self.run_command(f'reg export "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer" "{os.path.join(backup_dir, "explorer_cu.reg")}" /y')),
            ("Privacidad: Telemetría", lambda: self.run_command(f'reg export "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" "{os.path.join(backup_dir, "telemetry.reg")}" /y')),
            ("Sistema: Control", lambda: self.run_command(f'reg export "HKLM\\SYSTEM\\CurrentControlSet\\Control" "{os.path.join(backup_dir, "system_control.reg")}" /y')),
            ("Usuario: Configuraciones", lambda: self.run_command(f'reg export "HKCU" "{os.path.join(backup_dir, "user_hkcu.reg")}" /y')),
            ("Sistema: BCD", lambda: self.run_command(f'bcdedit /export "{os.path.join(backup_dir, "bcd_backup")}"')),
            ("Energía: Plan Activo", lambda: self.backup_power_scheme(backup_dir)),
            ("Drivers: Exportar", lambda: self.backup_drivers(backup_dir)),
            ("Programas: Lista Instalados", lambda: self.backup_installed_programs(backup_dir)),
            ("Sistema: Variables de Entorno", lambda: self.backup_environment_variables(backup_dir)),
            ("Inicio: Programas", lambda: self.backup_startup_programs(backup_dir)),
            ("Interfaz: Barra de Tareas", lambda: self.backup_taskbar_settings(backup_dir)),
            ("Sistema: Asociaciones de Archivos", lambda: self.backup_file_associations(backup_dir)),
            ("Interfaz: Escritorio", lambda: self.backup_desktop_settings(backup_dir)),
            ("Sistema: Fuentes", lambda: self.backup_fonts(backup_dir)),
            ("Dispositivos: Mouse y Teclado", lambda: self.backup_mouse_keyboard(backup_dir)),
            ("Audio: Configuraciones", lambda: self.backup_sound_settings(backup_dir)),
            ("Sistema: Windows Update", lambda: self.backup_windows_update(backup_dir)),
            ("Información: Sistema", lambda: self.backup_system_info(backup_dir)),
            ("Dispositivos: Impresoras", lambda: self.backup_printer_settings(backup_dir)),
            ("Sistema: Características", lambda: self.backup_windows_features(backup_dir)),
            ("Manifest: Crear", lambda: self.create_backup_manifest(backup_dir))
        ]
        
        total_tasks = len(tasks)
        for i, (message, task_func) in enumerate(tasks):
            try:
                self.update_progress((i / total_tasks) * 100, f"[{i+1}/{total_tasks}] {message}", f"Procesando...")
                task_func()
            except:
                pass

        self.update_progress(100, "✓ Backup completado", f"Archivos guardados en: {backup_dir}")
        self.show_completion_window()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    if is_admin():
        root = tk.Tk()
        app = BackupApp(root)
        root.mainloop()
    else:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Permiso Requerido", "Este script debe ser ejecutado como Administrador.")
        root.destroy()