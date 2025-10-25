import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import threading
import ctypes
import json
import shutil

class RestoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Herramienta de Restauración Completa")
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

        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(expand=True, fill=tk.BOTH)

        self.progress_label = ttk.Label(main_frame, text="Iniciando restauración completa...", font=("Segoe UI", 10))
        self.progress_label.pack(pady=(0, 5))

        self.detail_label = ttk.Label(main_frame, text="", font=("Segoe UI", 8))
        self.detail_label.pack(pady=(0, 5))

        self.progress_bar = ttk.Progressbar(main_frame, orient='horizontal', length=400, mode='determinate')
        self.progress_bar.pack(pady=10)

        self.completion_button = ttk.Button(main_frame, text="Restauración Finalizada. Salir", state=tk.DISABLED, command=self.root.destroy)
        self.completion_button.pack(pady=10)

        self.start_restore_thread()

    def disable_close(self):
        pass

    def start_restore_thread(self):
        restore_thread = threading.Thread(target=self.run_restore_process)
        restore_thread.daemon = True
        restore_thread.start()

    def update_progress(self, value, text, detail=""):
        self.progress_bar['value'] = value
        self.progress_label['text'] = text
        self.detail_label['text'] = detail
        self.root.update_idletasks()

    def show_completion(self):
        self.progress_label.pack_forget()
        self.detail_label.pack_forget()
        self.progress_bar.pack_forget()
        self.completion_button.config(state=tk.NORMAL)
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def run_command(self, command):
        try:
            subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        except:
            return False

    def restore_network_profiles(self, backup_dir):
        network_dir = os.path.join(backup_dir, "network_profiles")
        try:
            if os.path.exists(network_dir):
                for file in os.listdir(network_dir):
                    if file.endswith('.xml'):
                        filepath = os.path.join(network_dir, file)
                        self.run_command(f'netsh wlan add profile filename="{filepath}"')
        except:
            pass

    def restore_firewall_rules(self, backup_dir):
        firewall_file = os.path.join(backup_dir, "firewall_rules.wfw")
        try:
            if os.path.exists(firewall_file):
                self.run_command(f'netsh advfirewall import "{firewall_file}"')
        except:
            pass

    def restore_hosts_file(self, backup_dir):
        hosts_backup = os.path.join(backup_dir, "hosts")
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        try:
            if os.path.exists(hosts_backup):
                shutil.copy2(hosts_backup, hosts_path)
        except:
            pass

    def restore_power_scheme(self, backup_dir):
        power_file = os.path.join(backup_dir, "power_scheme_backup.pow")
        try:
            if os.path.exists(power_file):
                result = subprocess.run(f'powercfg /import "{power_file}"', capture_output=True, text=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'GUID' in line or len(line.strip()) == 36:
                            guid = line.strip().split()[-1]
                            if len(guid) == 36:
                                self.run_command(f'powercfg /setactive {guid}')
                                break
        except:
            pass

    def restore_drivers(self, backup_dir):
        drivers_dir = os.path.join(backup_dir, "drivers")
        try:
            if os.path.exists(drivers_dir):
                for inf_file in os.listdir(drivers_dir):
                    if inf_file.endswith('.inf'):
                        inf_path = os.path.join(drivers_dir, inf_file)
                        self.run_command(f'pnputil /add-driver "{inf_path}" /install')
        except:
            pass

    def run_restore_process(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        backup_dir = os.path.join(base_dir, "backup")

        if not os.path.exists(backup_dir):
            messagebox.showerror("Error", f"El directorio de backup '{backup_dir}' no fue encontrado.")
            self.root.destroy()
            return

        manifest_file = os.path.join(backup_dir, "backup_manifest.json")
        if os.path.exists(manifest_file):
            try:
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    backup_date = manifest.get("backup_date", "Desconocido")
                    self.update_progress(0, f"Restaurando backup del {backup_date}", "Verificando archivos...")
            except:
                pass

        restore_priority = [
            "services_backup.reg",
            "scheduled_tasks_backup.reg",
            "network_tcpip_params.reg",
            "network_qos.reg",
            "process_priorities_ifeo.reg",
            "memory_management.reg",
            "explorer_lm.reg",
            "telemetry.reg",
            "system_control.reg",
            "explorer_cu.reg",
            "user_hkcu.reg",
            "env_system.reg",
            "env_user.reg",
            "startup_system_run.reg",
            "startup_system_runonce.reg",
            "startup_user_run.reg",
            "startup_user_runonce.reg",
            "taskbar_taskband.reg",
            "explorer_advanced.reg",
            "taskbar_position.reg",
            "file_associations.reg",
            "file_classes_system.reg",
            "desktop_settings.reg",
            "desktop_colors.reg",
            "themes.reg",
            "fonts_registry.reg",
            "mouse_settings.reg",
            "keyboard_settings.reg",
            "accessibility.reg",
            "sound_schemes.reg",
            "audio_settings.reg",
            "windows_update.reg",
            "windows_update_policies.reg",
            "printer_settings.reg",
            "bcd_backup",
            "power_scheme_backup.pow",
            "firewall_rules.wfw",
            "hosts"
        ]

        all_backup_files = []
        try:
            all_backup_files = [f for f in os.listdir(backup_dir) if os.path.isfile(os.path.join(backup_dir, f))]
        except:
            pass

        tasks_to_run = sorted(all_backup_files, key=lambda x: restore_priority.index(x) if x in restore_priority else len(restore_priority))

        special_tasks = [
            ("Red: Perfiles WiFi", lambda: self.restore_network_profiles(backup_dir)),
            ("Red: Firewall", lambda: self.restore_firewall_rules(backup_dir)),
            ("Red: Hosts File", lambda: self.restore_hosts_file(backup_dir)),
            ("Energía: Plan", lambda: self.restore_power_scheme(backup_dir)),
        ]

        total_files = len(tasks_to_run)
        total_tasks = total_files + len(special_tasks)

        if total_files == 0:
            messagebox.showwarning("Advertencia", "No se encontraron archivos de backup para restaurar.")
            self.root.destroy()
            return

        current_task = 0

        for filename in tasks_to_run:
            filepath = os.path.join(backup_dir, filename)
            current_task += 1
            
            try:
                if filename.lower().endswith('.reg'):
                    message = f"[{current_task}/{total_tasks}] Registro: {filename}"
                    self.update_progress((current_task / total_tasks) * 100, message, "Importando...")
                    self.run_command(f'reg import "{filepath}"')
                
                elif filename.lower() == 'bcd_backup':
                    message = f"[{current_task}/{total_tasks}] BCD"
                    self.update_progress((current_task / total_tasks) * 100, message, "Importando configuración de arranque...")
                    self.run_command(f'bcdedit /import "{filepath}"')
            except:
                pass

        for task_name, task_func in special_tasks:
            current_task += 1
            try:
                message = f"[{current_task}/{total_tasks}] {task_name}"
                self.update_progress((current_task / total_tasks) * 100, message, "Procesando...")
                task_func()
            except:
                pass

        self.update_progress(100, "✓ Restauración completada", "Se recomienda reiniciar el equipo")
        self.show_completion()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    if is_admin():
        root = tk.Tk()
        app = RestoreApp(root)
        root.mainloop()
    else:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Permiso Requerido", "Este script debe ser ejecutado como Administrador.")
        root.destroy()