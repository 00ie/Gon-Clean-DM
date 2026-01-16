import customtkinter as ctk
from tkinter import messagebox, Toplevel, filedialog
from PIL import ImageTk, Image, ImageDraw
import io
import requests
import hashlib
import csv
import time
import threading
from datetime import datetime
from src.core.discord_api import get_user_info, get_dm_channels, fetch_messages, delete_message
from src.core.utils import discord_timestamp_from_id
from src.core.config import ICON_ICO_PATH, ICON_PATH, THEME, PALETTE, AVATAR_CACHE_DIR, EXPORTS_DIR

ctk.set_appearance_mode(THEME["appear"])
ctk.set_default_color_theme(THEME["color"])

def ensure_rounded_icon(size: int = 256, radius: int = 56) -> None:
    try:
        if ICON_ICO_PATH.exists():
            icon = Image.open(ICON_ICO_PATH).convert("RGBA").resize((size, size), Image.LANCZOS)
            mask = Image.new("L", (size, size), 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle((0, 0, size, size), radius=radius, fill=255)
            icon.putalpha(mask)
            ICON_PATH.parent.mkdir(exist_ok=True)
            icon.save(ICON_PATH, format="PNG")
            icon.save(ICON_ICO_PATH, format="ICO", sizes=[(64, 64), (128, 128), (256, 256)])
    except Exception:
        pass

class GonCleanDMGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gon Clean DM - Gon")
        self.geometry("1250x770")
        self.configure(fg_color=PALETTE["bg"])
        ensure_rounded_icon()
        try:
            if ICON_ICO_PATH.exists():
                self.iconbitmap(ICON_ICO_PATH)
            self.iconphoto(True, ImageTk.PhotoImage(Image.open(ICON_PATH)))
        except Exception:
            pass
        self.token = None
        self.my_id = None
        self.username = None
        self.discriminator = None
        self.avatar_hash = None
        self.email = None
        self.phone = None
        self.created_at = None
        self.channels = []
        self.filtered_channels = []
        self.channel_selection = {}
        self.channel_rows = []
        self.channel_row_by_id = {}
        self.channel_check_vars = []
        self.channel_avatar_images = {}
        self.active_channel_index = None
        self.active_channel_id = None
        self.show_ids_var = ctk.BooleanVar(value=True)
        self.select_all_var = ctk.BooleanVar(value=False)
        self.avatar_session = requests.Session()
        self.avatar_session.headers.update({"User-Agent": "GonCleanDM/1.0"})
        self.messages = []
        self.auto_delete_active = False
        self.auto_delete_thread = None
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.frame_top = ctk.CTkFrame(self, corner_radius=10, fg_color=PALETTE["panel"])
        self.frame_top.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(self.frame_top, text="🔑 Token Discord:", font=("Segoe UI", 13, "bold"), text_color=PALETTE["text"]).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_token = ctk.CTkEntry(self.frame_top, width=400, show="*", fg_color=PALETTE["panel_soft"], text_color=PALETTE["text"], placeholder_text_color=PALETTE["muted"], border_color=PALETTE["panel_soft_alt"])
        self.entry_token.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.btn_login = ctk.CTkButton(self.frame_top, text="Login", command=self.login, fg_color=PALETTE["success"], hover_color=PALETTE["success_hover"])
        self.btn_login.grid(row=0, column=2, padx=10, pady=10)
        self.btn_about = ctk.CTkButton(self.frame_top, text="Sobre", command=self.show_about, width=80, fg_color=PALETTE["accent"], hover_color=PALETTE["accent_hover"])
        self.btn_about.grid(row=0, column=3, padx=10)
        self.lbl_user_info = ctk.CTkLabel(self.frame_top, text="Desconectado", font=("Arial", 12), text_color="red")
        self.lbl_user_info.grid(row=0, column=4, padx=20, pady=10)
        self.frame_sidebar = ctk.CTkFrame(self, corner_radius=10, fg_color=PALETTE["panel_alt"], width=340)
        self.frame_sidebar.grid(row=1, column=0, padx=(10, 5), pady=(0, 10), sticky="nsew")
        self.frame_sidebar.grid_columnconfigure(0, minsize=320)
        self.frame_sidebar.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(self.frame_sidebar, text="Canais DM/Grupos", font=("Segoe UI", 16, "bold"), text_color=PALETTE["text"]).grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

        self.frame_channel_tools = ctk.CTkFrame(self.frame_sidebar, fg_color=PALETTE["panel_alt"], corner_radius=10)
        self.frame_channel_tools.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        self.frame_channel_tools.grid_columnconfigure(0, weight=1)
        self.entry_search_channels = ctk.CTkEntry(self.frame_channel_tools, placeholder_text="Buscar chats...", fg_color=PALETTE["panel_soft"], text_color=PALETTE["text"], placeholder_text_color=PALETTE["muted"], border_color=PALETTE["panel_soft_alt"])
        self.entry_search_channels.grid(row=0, column=0, padx=8, pady=(8, 6), sticky="ew")
        self.entry_search_channels.bind("<KeyRelease>", self.filter_channels)

        self.show_ids_switch = ctk.CTkSwitch(self.frame_channel_tools, text="Mostrar IDs", variable=self.show_ids_var, command=self.toggle_show_ids, fg_color=PALETTE["accent"], progress_color=PALETTE["accent"], button_color=PALETTE["panel_soft_alt"], button_hover_color=PALETTE["accent_hover"], text_color=PALETTE["muted"])
        self.show_ids_switch.grid(row=1, column=0, padx=8, pady=(0, 6), sticky="w")

        self.select_all_switch = ctk.CTkSwitch(self.frame_channel_tools, text="Selecionar visíveis", variable=self.select_all_var, command=self.toggle_select_all, fg_color=PALETTE["accent"], progress_color=PALETTE["accent"], button_color=PALETTE["panel_soft_alt"], button_hover_color=PALETTE["accent_hover"], text_color=PALETTE["muted"])
        self.select_all_switch.grid(row=2, column=0, padx=8, pady=(0, 8), sticky="w")

        self.channels_container = ctk.CTkScrollableFrame(self.frame_sidebar, corner_radius=10, fg_color=PALETTE["panel_soft"], width=320)
        self.channels_container.grid(row=2, column=0, padx=12, pady=(0, 10), sticky="nsew")
        self.channels_container.grid_columnconfigure(2, weight=1)
        self.avatar_placeholder = self.create_avatar_placeholder(32)
        self.btn_backup_selected = ctk.CTkButton(self.frame_sidebar, text="Backup Selecionados (TXT)", command=self.threaded_backup_selected, fg_color=PALETTE["info"], hover_color=PALETTE["info_hover"])
        self.btn_backup_selected.grid(row=3, column=0, padx=10, pady=3, sticky="ew")
        self.btn_backup_csv = ctk.CTkButton(self.frame_sidebar, text="Exportar CSV", command=self.threaded_csv_selected, fg_color=PALETTE["accent"], hover_color=PALETTE["accent_hover"])
        self.btn_backup_csv.grid(row=4, column=0, padx=10, pady=3, sticky="ew")
        self.btn_delete_selected = ctk.CTkButton(self.frame_sidebar, text="Deletar em Selecionados", command=self.threaded_delete_selected_confirm, fg_color=PALETTE["danger"], hover_color=PALETTE["danger_hover"])
        self.btn_delete_selected.grid(row=5, column=0, padx=10, pady=(3, 8), sticky="ew")
        self.frame_center = ctk.CTkFrame(self, corner_radius=10, fg_color=PALETTE["panel"])
        self.frame_center.grid(row=1, column=1, padx=(5, 10), pady=(0, 10), sticky="nsew")
        self.frame_center.grid_rowconfigure(1, weight=1)
        self.frame_center.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.frame_center, text="Mensagens", font=("Segoe UI", 16, "bold"), text_color=PALETTE["text"]).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.txt_messages = ctk.CTkTextbox(self.frame_center, width=800, height=27, fg_color=PALETTE["panel_soft"], text_color=PALETTE["text"])
        self.txt_messages.grid(row=1, column=0, padx=10, pady=(0,5), sticky="nsew")
        self.entry_search = ctk.CTkEntry(self.frame_center, width=800, placeholder_text="Buscar termo nas mensagens...", fg_color=PALETTE["panel_soft"], text_color=PALETTE["text"], placeholder_text_color=PALETTE["muted"], border_color=PALETTE["panel_soft_alt"])
        self.entry_search.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.entry_search.bind("<Return>", self.search_messages)
        self.frame_filters = ctk.CTkFrame(self.frame_center, corner_radius=10, fg_color=PALETTE["panel_soft_alt"])
        self.frame_filters.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.frame_filters.grid_columnconfigure(4, weight=1)
        ctk.CTkLabel(self.frame_filters, text="Limite (n°/all):", text_color=PALETTE["muted"]).grid(row=0, column=0, sticky="w")
        self.entry_limit = ctk.CTkEntry(self.frame_filters, width=60, fg_color=PALETTE["panel_soft"], text_color=PALETTE["text"], placeholder_text_color=PALETTE["muted"], border_color=PALETTE["panel_soft_alt"])
        self.entry_limit.insert(0, "all")
        self.entry_limit.grid(row=0, column=1, padx=5)
        ctk.CTkLabel(self.frame_filters, text="Palavras-chave (| separar):", text_color=PALETTE["muted"]).grid(row=0, column=2, sticky="w")
        self.entry_keywords = ctk.CTkEntry(self.frame_filters, width=120, fg_color=PALETTE["panel_soft"], text_color=PALETTE["text"], placeholder_text_color=PALETTE["muted"], border_color=PALETTE["panel_soft_alt"])
        self.entry_keywords.grid(row=0, column=3, padx=5)
        ctk.CTkLabel(self.frame_filters, text="Início (YYYY-MM-DD):", text_color=PALETTE["muted"]).grid(row=1, column=0, sticky="w")
        self.entry_date_start = ctk.CTkEntry(self.frame_filters, width=80, fg_color=PALETTE["panel_soft"], text_color=PALETTE["text"], placeholder_text_color=PALETTE["muted"], border_color=PALETTE["panel_soft_alt"])
        self.entry_date_start.grid(row=1, column=1)
        ctk.CTkLabel(self.frame_filters, text="Fim (YYYY-MM-DD):", text_color=PALETTE["muted"]).grid(row=1, column=2, sticky="w")
        self.entry_date_end = ctk.CTkEntry(self.frame_filters, width=80, fg_color=PALETTE["panel_soft"], text_color=PALETTE["text"], placeholder_text_color=PALETTE["muted"], border_color=PALETTE["panel_soft_alt"])
        self.entry_date_end.grid(row=1, column=3)
        self.content_filter_var = ctk.StringVar(value="1")
        ctk.CTkLabel(self.frame_filters, text="Conteúdo:", text_color=PALETTE["muted"]).grid(row=2, column=0, sticky="w")
        ctk.CTkRadioButton(self.frame_filters, text="Nenhum", variable=self.content_filter_var, value="1").grid(row=2, column=1, sticky="w")
        ctk.CTkRadioButton(self.frame_filters, text="Anexos", variable=self.content_filter_var, value="2").grid(row=2, column=2, sticky="w")
        ctk.CTkRadioButton(self.frame_filters, text="Links", variable=self.content_filter_var, value="3").grid(row=2, column=3, sticky="w")
        self.btn_backup = ctk.CTkButton(self.frame_filters, text="Backup deste canal", command=self.threaded_backup, fg_color=PALETTE["info"], hover_color=PALETTE["info_hover"])
        self.btn_backup.grid(row=3, column=1, padx=6, pady=7, sticky="ew")
        self.btn_delete_confirm = ctk.CTkButton(self.frame_filters, text="Deletar neste canal", command=self.threaded_delete_confirm, fg_color=PALETTE["danger"], hover_color=PALETTE["danger_hover"])
        self.btn_delete_confirm.grid(row=3, column=2, padx=6, pady=7, sticky="ew")
        self.frame_auto_delete = ctk.CTkFrame(self.frame_filters, corner_radius=10, fg_color=PALETTE["panel_soft_alt"])
        self.frame_auto_delete.grid(row=4, column=0, columnspan=5, pady=10, sticky="ew")
        ctk.CTkLabel(self.frame_auto_delete, text="Agendamento automático:", font=("Segoe UI", 12, "bold"), text_color=PALETTE["text"]).grid(row=0, column=0, padx=10, pady=6)
        ctk.CTkLabel(self.frame_auto_delete, text="Hora do dia (HH:MM):", text_color=PALETTE["muted"]).grid(row=1, column=0, sticky="w", padx=10)
        self.entry_auto_time = ctk.CTkEntry(self.frame_auto_delete, width=60, fg_color=PALETTE["panel_soft"], text_color=PALETTE["text"], placeholder_text_color=PALETTE["muted"], border_color=PALETTE["panel_soft_alt"])
        self.entry_auto_time.insert(0, "00:00")
        self.entry_auto_time.grid(row=1, column=1, padx=5)
        ctk.CTkLabel(self.frame_auto_delete, text="Frequência (minutos):", text_color=PALETTE["muted"]).grid(row=1, column=2, sticky="w", padx=10)
        self.entry_auto_freq = ctk.CTkEntry(self.frame_auto_delete, width=60, fg_color=PALETTE["panel_soft"], text_color=PALETTE["text"], placeholder_text_color=PALETTE["muted"], border_color=PALETTE["panel_soft_alt"])
        self.entry_auto_freq.insert(0, "60")
        self.entry_auto_freq.grid(row=1, column=3, padx=5)
        self.btn_toggle_auto = ctk.CTkButton(self.frame_auto_delete, text="Ativar Deleção Automática", fg_color=PALETTE["info"], hover_color=PALETTE["info_hover"], command=self.toggle_auto_delete)
        self.btn_toggle_auto.grid(row=1, column=4, padx=15)
        self.frame_status = ctk.CTkFrame(self, corner_radius=10, fg_color=PALETTE["panel"])
        self.frame_status.grid(row=2, column=0, columnspan=2, padx=10, pady=4, sticky="ew")
        self.lbl_status = ctk.CTkLabel(self.frame_status, text="Pronto", font=("Consolas", 12), text_color=PALETTE["text"], bg_color=PALETTE["panel"])
        self.lbl_status.pack(side="left", padx=12)
        self.progress = ctk.CTkProgressBar(self.frame_status, width=240, height=18, fg_color=PALETTE["panel_soft"], progress_color=PALETTE["info"])
        self.progress.pack(side="left", padx=14)
        ctk.CTkLabel(self.frame_status, text="Criador: Gon | GitHub: 00ie | Telegram: @feicoes | Discord: tlwm", font=("Arial", 12), text_color=PALETTE["link"], bg_color=PALETTE["panel"]).pack(side="right", padx=10)

    def set_status(self, msg: str, color: str = "white", progress: float = None):
        self.lbl_status.configure(text=msg, text_color=color)
        if progress is not None:
            self.progress.set(min(1.0, max(0.0, progress)))
        self.update_idletasks()

    def login(self):
        token = self.entry_token.get().strip()
        if not token:
            messagebox.showwarning("Aviso", "Digite seu token do Discord!")
            return
        self.token = token
        user = get_user_info(token)
        if not user:
            messagebox.showerror("Erro", "Token inválido ou falha na API.")
            self.set_status("Login falhou.", "red")
            return
        self.my_id = user["id"]
        self.username = user.get("username","")
        self.discriminator = user.get("discriminator","")
        self.avatar_hash = user.get("avatar","")
        self.email = user.get("email", "")
        self.phone = user.get("phone", "")
        self.created_at = discord_timestamp_from_id(self.my_id)
        self.lbl_user_info.configure(
            text=f"Logado: {self.username}#{self.discriminator} | ID: {self.my_id}",
            text_color="#87ff77"
        )
        self.set_status("Autenticado!", "#77FFC4")
        self.load_channels()

    def load_channels(self):
        data = get_dm_channels(self.token)
        self.channels = []
        if not data:
            self.set_status("Falha ao carregar canais", "red")
            return
        for idx, c in enumerate(data):
            if c["type"] == 1:
                recipient = c.get("recipients", [])
                if recipient:
                    name = f"{recipient[0]['username']}"
                    avatar_url = self.get_avatar_url(recipient[0])
                else:
                    name = "DM"
                    avatar_url = None
            elif c["type"] == 3:
                name = f"{c.get('name', 'Grupo')}"
                avatar_url = self.get_group_icon_url(c)
            else:
                name = "Outro"
                avatar_url = None
            channel_item = {"id": c["id"], "name": name, "avatar_url": avatar_url}
            self.channels.append(channel_item)
            if channel_item["id"] not in self.channel_selection:
                self.channel_selection[channel_item["id"]] = False
        self.filtered_channels = list(self.channels)
        self.build_channel_rows()
        threading.Thread(target=self.load_channel_avatars, daemon=True).start()

    def set_active_channel(self, idx: int):
        if idx < 0 or idx >= len(self.filtered_channels):
            return
        channel = self.filtered_channels[idx]
        self.active_channel_id = channel["id"]
        self.active_channel_index = idx
        for row_index, row in enumerate(self.channel_rows):
            row_id = row["channel_id"]
            fg = PALETTE["panel_soft_alt"] if row_id == self.active_channel_id else PALETTE["panel_soft"]
            row["frame"].configure(fg_color=fg)
        self.current_channel_id = channel["id"]
        self.set_status(f"Carregando canal: {channel['name']}")
        self.load_messages(channel["id"])

    def load_messages(self, channel_id: str):
        self.txt_messages.configure(state="normal")
        self.txt_messages.delete("1.0", "end")
        self.txt_messages.insert("end", "Carregando mensagens...\n")
        threading.Thread(target=self.load_messages_thread, args=(channel_id,), daemon=True).start()

    def load_messages_thread(self, channel_id):
        all_msgs = []
        before = None
        while True:
            messages = fetch_messages(self.token, channel_id, 50, before)
            if not messages: break
            all_msgs.extend(messages)
            before = messages[-1]["id"]
            if len(all_msgs) >= 200: break
            time.sleep(0.5)
        self.messages = list(reversed(all_msgs))
        self.show_messages()

    def show_messages(self):
        self.txt_messages.configure(state="normal")
        self.txt_messages.delete("1.0", "end")
        for msg in self.messages:
            author = msg["author"]
            timestamp = msg["timestamp"][:19].replace("T", " ")
            line = f"[{timestamp}] {author['username']}#{author['discriminator']}: {msg.get('content', '')}\n"
            self.txt_messages.insert("end", line)
        self.set_status(f"{len(self.messages)} mensagens carregadas.", "#87ff77")

    def search_messages(self, event=None):
        term = self.entry_search.get().strip().lower()
        if not term:
            self.show_messages()
            return
        self.txt_messages.configure(state="normal")
        self.txt_messages.delete("1.0", "end")
        matches = 0
        for msg in self.messages:
            content = msg.get("content", "").lower()
            if term in content:
                author = msg["author"]
                timestamp = msg["timestamp"][:19].replace("T", " ")
                line = f"[{timestamp}] {author['username']}#{author['discriminator']}: {msg.get('content', '')}\n"
                self.txt_messages.insert("end", line)
                matches += 1
        self.set_status(f"{matches} mensagens encontradas para '{term}'.", "#22bbff")
        self.txt_messages.configure(state="disabled")

    def threaded_backup(self):
        if not self.current_channel_id:
            messagebox.showwarning("Aviso", "Selecione um canal para backup.")
            return
        threading.Thread(target=self.backup_thread, daemon=True).start()

    def backup_thread(self):
        all_messages = []
        before = None
        self.set_status("Iniciando backup...", "#17a2b8")
        while True:
            messages = fetch_messages(self.token, self.current_channel_id, 100, before)
            if not messages: break
            all_messages.extend(messages)
            before = messages[-1]["id"]
            time.sleep(1)
        all_messages.reverse()
        filename = EXPORTS_DIR / f"backup_{self.current_channel_id}_{int(time.time())}.txt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"Canal: {self.current_channel_id}\n")
                f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-" * 60 + "\n")
                for msg in all_messages:
                    author = msg["author"]
                    line = f"[{msg['timestamp']}] {author['id']} ({author['username']}#{author['discriminator']}): {msg.get('content','').replace(chr(10),' ')}"
                    f.write(line + "\n")
            messagebox.showinfo("Backup", f"Backup salvo em: {filename}")
            self.set_status("Backup concluído!", "#2ddfff")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro backup: {str(e)}")
            self.set_status("Erro backup!", "red")

    def threaded_delete_confirm(self):
        if not self.current_channel_id:
            messagebox.showwarning("Aviso", "Selecione um canal para deletar.")
            return
        if messagebox.askyesno("Confirme deleção", "Está certo que deseja deletar todas as mensagens deste canal?"):
            self.threaded_delete()

    def threaded_delete(self):
        threading.Thread(target=self.delete_thread, daemon=True).start()

    def delete_thread(self):
        limit_str = self.entry_limit.get().strip().lower()
        limit = -1 if limit_str == 'all' else int(limit_str) if limit_str.isdigit() else -1
        keywords = self.entry_keywords.get().strip().split('|') if self.entry_keywords.get().strip() else None
        start_date = self.entry_date_start.get().strip()
        end_date = self.entry_date_end.get().strip()
        start_ts = None
        end_ts = None
        import time
        try:
            if start_date:
                start_ts = int(time.mktime(time.strptime(start_date, "%Y-%m-%d"))) * 1000
            if end_date:
                end_ts = int(time.mktime(time.strptime(end_date, "%Y-%m-%d"))) * 1000
        except:
            pass
        content_filter = self.content_filter_var.get()
        count = 0
        before = None
        self.set_status("Deletando mensagens...", "#dc3545")
        while True:
            fetch_limit = 100 if limit==-1 else min(100, limit-count)
            if fetch_limit <= 0:
                break
            messages = fetch_messages(self.token, self.current_channel_id, fetch_limit, before)
            if not messages:
                break
            for msg in messages:
                try:
                    if msg["author"]["id"] != self.my_id: continue
                    content = msg.get("content", "").lower()
                    ts = 0
                    try:
                        ts = int(time.mktime(time.strptime(msg["timestamp"][:19], "%Y-%m-%dT%H:%M:%S"))) * 1000
                    except:
                        pass
                    if keywords and not any(k.lower() in content for k in keywords): continue
                    if start_ts and end_ts and not (start_ts <= ts <= end_ts): continue
                    if content_filter == "2" and not msg["attachments"]: continue
                    if content_filter == "3" and "http" not in content: continue
                    if delete_message(self.token, self.current_channel_id, msg["id"]):
                        count += 1
                        self.set_status(f"Deletadas: {count}", "#dc3545")
                        time.sleep(1.2)
                        if limit!=-1 and count >= limit: break
                except Exception as e:
                    self.set_status(f"Erro deletando msg: {str(e)}", "red")
            if len(messages)<100 or (limit!=-1 and count >= limit): break
            before = messages[-1]["id"]
        messagebox.showinfo("Finalizado", f"Deletadas {count} mensagens.")
        self.set_status("Deleção finalizada!", "#55FF55")

    def get_selected_channels(self):
        selected = []
        for channel in self.channels:
            if self.channel_selection.get(channel["id"], False):
                selected.append(channel)
        return selected

    def build_channel_rows(self):
        for child in self.channels_container.winfo_children():
            child.destroy()
        self.channel_rows = []
        self.channel_row_by_id = {}
        self.channel_check_vars = []
        for idx, channel in enumerate(self.filtered_channels):
            var = ctk.BooleanVar(value=self.channel_selection.get(channel["id"], False))
            row = ctk.CTkFrame(self.channels_container, fg_color=PALETTE["panel_soft"], corner_radius=10)
            row.grid(row=idx, column=0, columnspan=3, padx=6, pady=4, sticky="ew")
            row.grid_columnconfigure(2, weight=1)

            checkbox = ctk.CTkCheckBox(
                row,
                text="",
                variable=var,
                width=18,
                fg_color=PALETTE["accent"],
                hover_color=PALETTE["accent_hover"],
                border_color=PALETTE["panel_soft_alt"],
                command=lambda v=var, cid=channel["id"]: self.on_channel_check(cid, v)
            )
            checkbox.grid(row=0, column=0, rowspan=2, padx=(10, 6), pady=8, sticky="w")

            avatar = ctk.CTkLabel(row, text="", width=32, height=32, image=self.avatar_placeholder)
            avatar.grid(row=0, column=1, rowspan=2, padx=(0, 8), pady=6, sticky="w")

            name_label = ctk.CTkLabel(row, text=f"{idx + 1}. {channel['name']}", text_color=PALETTE["text"], font=("Segoe UI", 12, "bold"))
            name_label.grid(row=0, column=2, sticky="w", padx=(0, 10))

            id_label = ctk.CTkLabel(row, text=f"ID: {channel['id']}", text_color=PALETTE["muted"], font=("Segoe UI", 10))
            id_label.grid(row=1, column=2, sticky="w", padx=(0, 10))
            id_label.configure(wraplength=260)
            if not self.show_ids_var.get():
                id_label.grid_remove()

            for widget in (row, name_label, id_label, avatar):
                widget.bind("<Button-1>", lambda e, i=idx: self.set_active_channel(i))

            if channel["id"] == self.active_channel_id:
                row.configure(fg_color=PALETTE["panel_soft_alt"])

            self.channel_rows.append({
                "frame": row,
                "checkbox": checkbox,
                "avatar": avatar,
                "name": name_label,
                "id": id_label,
                "channel_id": channel["id"]
            })
            self.channel_row_by_id[channel["id"]] = self.channel_rows[-1]
            self.channel_check_vars.append(var)

            cached_avatar = self.channel_avatar_images.get(channel["id"])
            if cached_avatar:
                avatar.configure(image=cached_avatar)

    def filter_channels(self, event=None):
        term = self.entry_search_channels.get().strip().lower()
        if term:
            self.filtered_channels = [
                c for c in self.channels
                if term in c["name"].lower() or term in c["id"]
            ]
        else:
            self.filtered_channels = list(self.channels)
        self.select_all_var.set(False)
        self.build_channel_rows()

    def toggle_show_ids(self):
        self.build_channel_rows()

    def toggle_select_all(self):
        value = self.select_all_var.get()
        for channel in self.filtered_channels:
            self.channel_selection[channel["id"]] = value
        for var in self.channel_check_vars:
            var.set(value)

    def on_channel_check(self, channel_id: str, var: ctk.BooleanVar):
        self.channel_selection[channel_id] = var.get()
        if not var.get():
            self.select_all_var.set(False)
        else:
            all_selected = all(
                self.channel_selection.get(c["id"], False) for c in self.filtered_channels
            )
            self.select_all_var.set(all_selected)

    def create_avatar_placeholder(self, size: int):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((0, 0, size, size), fill=PALETTE["panel_soft_alt"], outline=PALETTE["accent"])
        return ImageTk.PhotoImage(img)

    def load_channel_avatars(self):
        AVATAR_CACHE_DIR.mkdir(exist_ok=True)
        for channel in self.channels:
            url = channel.get("avatar_url")
            if not url:
                continue
            try:
                cache_path = self.get_avatar_cache_path(url)
                if cache_path.exists():
                    img = Image.open(cache_path).convert("RGBA").resize((32, 32), Image.LANCZOS)
                else:
                    response = self.avatar_session.get(url, timeout=6)
                    response.raise_for_status()
                    img = Image.open(io.BytesIO(response.content)).convert("RGBA")
                    img.save(cache_path, format="PNG")
                    img = img.resize((32, 32), Image.LANCZOS)
                mask = Image.new("L", (32, 32), 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, 32, 32), fill=255)
                img.putalpha(mask)
                avatar_img = ImageTk.PhotoImage(img)
                channel_id = channel["id"]
                self.channel_avatar_images[channel_id] = avatar_img
                self.after(0, lambda cid=channel_id, im=avatar_img: self.update_avatar_image(cid, im))
            except Exception:
                continue

    def get_avatar_cache_path(self, url: str):
        digest = hashlib.md5(url.encode("utf-8")).hexdigest()
        return AVATAR_CACHE_DIR / f"{digest}.png"

    def update_avatar_image(self, channel_id: str, image):
        row = self.channel_row_by_id.get(channel_id)
        if row:
            row["avatar"].configure(image=image)

    def get_avatar_url(self, user: dict):
        avatar_hash = user.get("avatar")
        user_id = user.get("id")
        if avatar_hash and user_id:
            return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png?size=64"
        discriminator = user.get("discriminator") or "0"
        try:
            default_index = int(discriminator) % 5
        except Exception:
            default_index = 0
        return f"https://cdn.discordapp.com/embed/avatars/{default_index}.png"

    def get_group_icon_url(self, channel: dict):
        icon_hash = channel.get("icon")
        channel_id = channel.get("id")
        if icon_hash and channel_id:
            return f"https://cdn.discordapp.com/channel-icons/{channel_id}/{icon_hash}.png?size=64"
        return None

    def threaded_backup_selected(self):
        selected = self.get_selected_channels()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione ao menos um canal para backup.")
            return
        threading.Thread(target=self.backup_selected_channels_thread, args=(selected,), daemon=True).start()

    def backup_selected_channels_thread(self, channels):
        self.set_status("Iniciando backup...", "#17a2b8")
        for channel in channels:
            all_messages = []
            before = None
            count = 0
            self.set_status(f"Backup canal: {channel['name']} 0 mensagens", "#17a2b8")
            while True:
                messages = fetch_messages(self.token, channel['id'], 100, before)
                if not messages: break
                all_messages.extend(messages)
                before = messages[-1]["id"]
                count += len(messages)
                self.set_status(f"Backup canal: {channel['name']} {count} mensagens", "#17a2b8")
                time.sleep(0.5)
            all_messages.reverse()
            filename = EXPORTS_DIR / f"backup_{channel['id']}_{int(time.time())}.txt"
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"Canal: {channel['name']} ({channel['id']})\n")
                    f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("-" * 60 + "\n")
                    for msg in all_messages:
                        author = msg["author"]
                        line = f"[{msg['timestamp']}] {author['id']} ({author['username']}#{author['discriminator']}): {msg.get('content','').replace(chr(10),' ')}"
                        f.write(line + "\n")
                self.set_status(f"Backup salvo: {filename}", "#55FF55")
            except Exception as e:
                self.set_status(f"Erro no backup: {str(e)}", "red")
        messagebox.showinfo("Backup", "Backup finalizado para os canais selecionados.")

    def threaded_delete_selected_confirm(self):
        selected = self.get_selected_channels()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione ao menos um canal para deletar mensagens.")
            return
        if messagebox.askyesno("Confirmar", "Deseja realmente DELETAR mensagens dos canais selecionados? Esta ação é irreversível!"):
            threading.Thread(target=self.delete_selected_channels_thread, args=(selected,), daemon=True).start()

    def delete_selected_channels_thread(self, channels):
        limit_str = self.entry_limit.get().strip().lower()
        limit = -1 if limit_str == 'all' else int(limit_str) if limit_str.isdigit() else -1
        keywords_str = self.entry_keywords.get().strip()
        keywords = [k.strip() for k in keywords_str.split('|')] if keywords_str else None
        start_date = self.entry_date_start.get().strip()
        end_date = self.entry_date_end.get().strip()
        start_ts = None
        end_ts = None
        try:
            if start_date:
                start_ts = int(time.mktime(time.strptime(start_date, "%Y-%m-%d"))) * 1000
            if end_date:
                end_ts = int(time.mktime(time.strptime(end_date, "%Y-%m-%d"))) * 1000
        except:
            pass
        content_filter = self.content_filter_var.get()
        for channel in channels:
            count = 0
            before = None
            self.set_status(f"Deletando no canal: {channel['name']}", "#dc3545")
            while True:
                fetch_limit = 100 if limit == -1 else min(100, limit - count)
                if fetch_limit <= 0:
                    break
                messages = fetch_messages(self.token, channel['id'], fetch_limit, before)
                if not messages:
                    break
                for msg in messages:
                    try:
                        if msg["author"]["id"] != self.my_id:
                            continue
                        content = msg.get("content", "").lower()
                        ts = 0
                        try:
                            ts = int(time.mktime(time.strptime(msg["timestamp"][:19], "%Y-%m-%dT%H:%M:%S"))) * 1000
                        except:
                            pass
                        if keywords and not any(k.lower() in content for k in keywords):
                            continue
                        if start_ts and end_ts and not (start_ts <= ts <= end_ts):
                            continue
                        if content_filter == "2" and not msg["attachments"]:
                            continue
                        if content_filter == "3" and "http" not in content:
                            continue
                        if delete_message(self.token, channel['id'], msg["id"]):
                            count += 1
                            self.set_status(f"Deletadas: {count} no canal {channel['name']}", "#dc3545")
                            time.sleep(1)
                            if limit != -1 and count >= limit:
                                break
                    except Exception as e:
                        self.set_status(f"Erro msg: {str(e)}", "red")
                if len(messages) < 100 or (limit != -1 and count >= limit):
                    break
                before = messages[-1]["id"]
            self.set_status(f"Finalizado canal {channel['name']}, mensagens deletadas: {count}", "#55FF55")
        messagebox.showinfo("Deleção", "Deleção finalizada nos canais selecionados.")

    def threaded_csv_selected(self):
        selected = self.get_selected_channels()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione ao menos um canal para exportar CSV.")
            return
        threading.Thread(target=self.csv_selected_channels_thread, args=(selected,), daemon=True).start()

    def csv_selected_channels_thread(self, channels):
        for channel in channels:
            all_messages = []
            before = None
            count = 0
            self.set_status(f"Exportando CSV de: {channel['name']}", "#17a2b8", 0)
            while True:
                messages = fetch_messages(self.token, channel['id'], 100, before)
                if not messages:
                    break
                all_messages.extend(messages)
                before = messages[-1]["id"]
                count += len(messages)
                self.set_status(f"Exportando CSV de: {channel['name']} ({count})", "#17a2b8", count / 1000.0)
                time.sleep(0.5)
            all_messages.reverse()
            filename = filedialog.asksaveasfilename(initialdir=EXPORTS_DIR, initialfile=f"backup_{channel['id']}_{int(time.time())}.csv", defaultextension=".csv")
            if filename:
                try:
                    with open(filename, "w", encoding="utf-8", newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(["Data", "Autor", "ID", "Conteúdo"])
                        for msg in all_messages:
                            author = msg["author"]
                            data = msg['timestamp']
                            autor = f"{author['username']}#{author['discriminator']}"
                            uid = author["id"]
                            conteudo = msg.get("content", "").replace("\n", " ")
                            writer.writerow([data, autor, uid, conteudo])
                    self.set_status(f"CSV salvo: {filename}", "#55FF55")
                except Exception as e:
                    self.set_status(f"Erro no CSV ({str(e)})", "red")
        messagebox.showinfo("CSV", "Exportação CSV(s) concluída.")

    def toggle_auto_delete(self):
        if self.auto_delete_active:
            self.auto_delete_active = False
            if self.auto_delete_thread and self.auto_delete_thread.is_alive():
                self.set_status("Deleção automática desativada", "#d9534f")
            self.btn_toggle_auto.configure(text="Ativar Deleção Automática", fg_color=PALETTE["info"], hover_color=PALETTE["info_hover"])
        else:
            t = self.entry_auto_time.get()
            f = self.entry_auto_freq.get()
            try:
                datetime.strptime(t, "%H:%M")
                freq = int(f)
                if freq <= 0:
                    raise ValueError()
            except Exception:
                self.set_status("Erro: horário inválido ou frequência inválida", "red")
                return
            self.auto_delete_active = True
            self.btn_toggle_auto.configure(text="Desativar Deleção Automática", fg_color=PALETTE["danger"], hover_color=PALETTE["danger_hover"])
            self.auto_delete_thread = threading.Thread(target=self.auto_delete_loop, args=(t, freq,), daemon=True)
            self.auto_delete_thread.start()
            self.set_status(f"Deleção automática ativada - hora: {t} freq: {freq}min", "#5cb85c")

    def auto_delete_loop(self, target_time:str, frequency:int):
        while self.auto_delete_active:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            if current_time == target_time:
                self.set_status("Executando deleção automática...", "#337ab7")
                self.threaded_delete()
                self.set_status("Deleção automática concluída, aguardando próximo ciclo...", "#5bc0de")
                time.sleep(frequency*60)
            else:
                time.sleep(30)
        self.set_status("Deleção automática parada", "#d9534f")

    def show_about(self):
        win = Toplevel(self)
        win.title("Sobre - Gon Clean DM")
        win.geometry("430x540")
        win.configure(bg=PALETTE["panel"])
        try:
            win.iconphoto(True, ImageTk.PhotoImage(Image.open(ICON_PATH)))
        except Exception:
            pass
        ctk.CTkLabel(win, text="Gon Clean DM", font=("Segoe UI SemiBold", 22, "bold"), text_color=PALETTE["danger"], bg_color=PALETTE["panel"]).pack(pady=(16,0))
        if self.avatar_hash:
            avatar_url = f"https://cdn.discordapp.com/avatars/{self.my_id}/{self.avatar_hash}.png?size=128"
            try:
                import io, requests
                avatar_bytes = requests.get(avatar_url).content
                img = Image.open(io.BytesIO(avatar_bytes)).resize((80,80))
                avatar_img = ImageTk.PhotoImage(img)
                avatar_frame = ctk.CTkFrame(win, fg_color=PALETTE["panel_soft"], corner_radius=30)
                avatar_frame.pack(pady=7)
                ctk.CTkLabel(avatar_frame, image=avatar_img, text="", bg_color=PALETTE["panel_soft"]).pack(padx=10, pady=5)
                avatar_frame.image = avatar_img
            except Exception:
                pass
        user_card = ctk.CTkFrame(win, fg_color=PALETTE["panel_soft"], corner_radius=15)
        user_card.pack(padx=16, pady=10, fill="x")
        userinfo = (
            f"Usuário: {self.username}#{self.discriminator}\n"
            f"ID: {self.my_id}\n"
            f"Email: {self.email or 'Desconhecido'}\n"
            f"Telefone: {self.phone or 'Desconhecido'}\n"
            f"Avatar: {self.avatar_hash or 'Desconhecido'}\n"
            f"Conta criada: {self.created_at}\n"
        )
        self.info_label = ctk.CTkLabel(user_card, text=userinfo, justify="left", font=("Consolas", 13), text_color=PALETTE["muted"], bg_color=PALETTE["panel_soft"])
        self.info_label.pack()
        def toggle_info():
            if self.info_label.winfo_ismapped():
                self.info_label.pack_forget()
                btn_toggle.configure(text="Exibir informações")
            else:
                self.info_label.pack(padx=10, pady=10, anchor="center")
                btn_toggle.configure(text="Ocultar informações")
        btn_toggle = ctk.CTkButton(win, text="Ocultar informações", command=toggle_info, width=170, fg_color=PALETTE["panel_soft_alt"], hover_color=PALETTE["panel_soft"])
        btn_toggle.pack(pady=6)
        ctk.CTkLabel(win, text="─"*52, font=("Segoe UI", 10), text_color=PALETTE["panel_soft_alt"], bg_color=PALETTE["panel"]).pack(pady=8)
        dev_card = ctk.CTkFrame(win, fg_color=PALETTE["panel_soft_alt"], corner_radius=13)
        dev_card.pack(fill="x", padx=17, pady=4)
        devtext = (
            "Criador: Gon\n"
            "GitHub: https://github.com/00ie\n"
            "Telegram: @feicoes\n"
            "Discord: tlwm\n\n"
            "Ferramenta para remover, fazer backup e gerenciar\n"
            "mensagens do Discord via DM/Grupo com segurança."
        )
        ctk.CTkLabel(dev_card, text=devtext, font=("Segoe UI", 12), text_color=PALETTE["accent"], justify="center", bg_color=PALETTE["panel_soft_alt"]).pack(padx=8, pady=11)
        ctk.CTkLabel(win, text="© 2025 Gon Clean DM", font=("Arial", 10), text_color=PALETTE["muted"], bg_color=PALETTE["panel"]).pack(pady=8)

if __name__ == "__main__":
    GonCleanDMGUI().mainloop()
