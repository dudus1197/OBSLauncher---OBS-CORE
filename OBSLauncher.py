import customtkinter as ctk
import minecraft_launcher_lib
import subprocess
import threading
import os
from tkinter import messagebox

class ProLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("OBS CORE v4.0 | Minecraft Launcher")
        self.geometry("900x650")
        
        # Katalog gry
        self.mc_dir = os.path.join(os.getenv('APPDATA'), ".obs_launcher")
        if not os.path.exists(self.mc_dir): os.makedirs(self.mc_dir)

        # UI Setup
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar & Container
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="OBS CORE", font=("Segoe UI", 24, "bold")).pack(pady=30)

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)

        # Wersja i Silnik
        ctk.CTkLabel(self.container, text="Wybierz Wersję:").pack()
        self.version_list = [v['id'] for v in minecraft_launcher_lib.utils.get_version_list()]
        self.ver_select = ctk.CTkComboBox(self.container, values=self.version_list, width=350)
        self.ver_select.set("1.20.1")
        self.ver_select.pack(pady=10)

        self.engine_select = ctk.CTkOptionMenu(self.container, values=["Vanilla", "Fabric"], width=350)
        self.engine_select.pack(pady=10)

        self.nick_entry = ctk.CTkEntry(self.container, placeholder_text="Twój Nick", width=350)
        self.nick_entry.pack(pady=15)

        # RAM
        self.ram_slider = ctk.CTkSlider(self.container, from_=2, to=16, number_of_steps=14)
        self.ram_slider.set(4)
        self.ram_slider.pack(pady=5)
        self.ram_label = ctk.CTkLabel(self.container, text="RAM: 4 GB")
        self.ram_label.pack()
        self.ram_slider.configure(command=lambda v: self.ram_label.configure(text=f"RAM: {int(v)} GB"))

        # Przycisk
        self.btn_play = ctk.CTkButton(self.container, text="GRAJ", height=60, width=350,
                                       fg_color="#2ecc71", hover_color="#27ae60",
                                       font=("Segoe UI", 20, "bold"),
                                       command=self.launch_handler)
        self.btn_play.pack(pady=40)

        self.status = ctk.CTkLabel(self, text="Gotowy", fg_color="#111")
        self.status.grid(row=1, column=0, columnspan=2, sticky="we")

    def log(self, text):
        self.status.configure(text=f"STATUS: {text}")

    def is_version_installed(self, version_id):
        """Sprawdza czy folder wersji i plik json istnieją."""
        version_path = os.path.join(self.mc_dir, "versions", version_id)
        json_path = os.path.join(version_path, f"{version_id}.json")
        return os.path.exists(json_path)

    def launch_handler(self):
        self.btn_play.configure(state="disabled")
        threading.Thread(target=self.run_process, daemon=True).start()

    def run_process(self):
        try:
            nick = self.nick_entry.get() or "Player"
            ver = self.ver_select.get()
            engine = self.engine_select.get()
            ram = int(self.ram_slider.get())

            current_ver_id = ver

            # --- LOGIKA FABRIC ---
            if engine == "Fabric":
                # Sprawdź czy Fabric dla tej wersji jest już zainstalowany
                installed_versions = [v['id'] for v in minecraft_launcher_lib.utils.get_installed_versions(self.mc_dir)]
                fabric_id = next((v for v in installed_versions if "fabric" in v and ver in v), None)
                
                if not fabric_id:
                    self.log(f"Instalowanie Fabric dla {ver}...")
                    minecraft_launcher_lib.fabric.install_fabric(ver, self.mc_dir)
                    # Ponowne sprawdzenie ID po instalacji
                    installed_versions = [v['id'] for v in minecraft_launcher_lib.utils.get_installed_versions(self.mc_dir)]
                    fabric_id = next((v for v in installed_versions if "fabric" in v and ver in v), None)
                
                current_ver_id = fabric_id

            # --- LOGIKA VANILLA / SPRAWDZANIE PLIKÓW ---
            if not self.is_version_installed(current_ver_id):
                self.log(f"Pobieranie brakujących plików ({current_ver_id})...")
                # Ta funkcja sama sprawdzi co brakuje i pobierze tylko to
                minecraft_launcher_lib.install.install_minecraft_version(current_ver_id, self.mc_dir)
            else:
                self.log("Pliki znalezione! Weryfikacja i uruchamianie...")

            # Opcje startu
            options = {
                "username": nick,
                "uuid": "0",
                "token": "0",
                "jvmArguments": [f"-Xmx{ram}G", "-XX:+UseG1GC", "-Dminecraft.launcher.brand=OBSLauncher"]
            }

            cmd = minecraft_launcher_lib.command.get_minecraft_command(current_ver_id, self.mc_dir, options)
            
            self.log("Gra uruchomiona!")
            subprocess.Popen(cmd)
            
            # Zamknięcie launchera po 5 sekundach od startu gry
            self.after(5000, self.destroy)

        except Exception as e:
            messagebox.showerror("Błąd", f"Problem podczas startu: {e}")
            self.btn_play.configure(state="normal")
            self.log("Błąd startu")

if __name__ == "__main__":
    app = ProLauncher()
    app.mainloop()