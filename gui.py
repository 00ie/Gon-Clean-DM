import customtkinter as ctk
from tkinter import messagebox, Listbox, Scrollbar, END, Toplevel, filedialog
from PIL import ImageTk, Image
import csv
import time
import threading
from datetime import datetime
from discord_api import get_user_info, get_dm_channels, fetch_messages, delete_message
from utils import discord_timestamp_from_id
from config import ICON_PATH, THEME

ctk.set_appearance_mode(THEME["appear"])
ctk.set_default_color_theme(THEME["color"])

class GonCleanDMGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gon Clean DM - Yankkj (Gon)")
        self.geometry("1250x770")
        try:
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
        self.messages = []
        self.auto_delete_active = False
        self.auto_delete_thread = None
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.frame_top = ctk.CTkFrame(self, corner_radius=10, fg_color="#181825")
        self.frame_top.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(self.frame_top, text="🔑 Token Discord:", font=("Arial", 13, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_token = ctk.CTkEntry(self.frame_top, width=400, show="*")
        self.entry_token.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.btn_login = ctk.CTkButton(self.frame_top, text="🔓 Login", command=self.login, fg_color="#28a745", hover_color="#218838")
        self.btn_login.grid(row=0, column=2, padx=10, pady=10)
        self.btn_about = ctk.CTkButton(self.frame_top, text="Sobre", command=self.show_about, width=80, fg_color="#2288FF", hover_color="#3344bb")
        self.btn_about.grid(row=0, column=3, padx=10)
        self.lbl_user_info = ctk.CTkLabel(self.frame_top, text="Desconectado", font=("Arial", 12), text_color="red")
        self.lbl_user_info.grid(row=0, column=4, padx=20, pady=10)
        self.frame_sidebar = ctk.CTkFrame(self, corner_radius=10, fg_color="#191924")
        self.frame_sidebar.grid(row=1, column=0, padx=(10, 5), pady=(0, 10), sticky="nsew")
        self.frame_sidebar.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self.frame_sidebar, text="📂 Canais DM/Grupos", font=("Arial", 16, "bold")).grid(row=0, column=0, padx=10, pady=10)
        self.listbox_channels = Listbox(self.frame_sidebar, selectmode="extended", bg="#232334", fg="white", activestyle="none", highlightcolor="#FF5555", relief="flat")
        self.listbox_channels.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.listbox_channels.bind("<<ListboxSelect>>", self.channel_selected)
        scrollbar = Scrollbar(self.frame_sidebar, command=self.listbox_channels.yview)
        scrollbar.grid(row=1, column=1, sticky='ns')
        self.listbox_channels.config(yscrollcommand=scrollbar.set)
        self.btn_backup_selected = ctk.CTkButton(self.frame_sidebar, text="💾 Backup Selecionados (TXT)", command=self.threaded_backup_selected, fg_color="#17a2b8", hover_color="#138496")
        self.btn_backup_selected.grid(row=2, column=0, padx=10, pady=3, sticky="ew")
        self.btn_backup_csv = ctk.CTkButton(self.frame_sidebar, text="Exportar CSV", command=self.threaded_csv_selected, fg_color="#116ec7", hover_color="#104095")
        self.btn_backup_csv.grid(row=3, column=0, padx=10, pady=3, sticky="ew")
        self.btn_delete_selected = ctk.CTkButton(self.frame_sidebar, text="🗑️ Deletar em Selecionados", command=self.threaded_delete_selected_confirm, fg_color="#dc3545", hover_color="#c82333")
        self.btn_delete_selected.grid(row=4, column=0, padx=10, pady=3, sticky="ew")
        self.frame_center = ctk.CTkFrame(self, corner_radius=10, fg_color="#181825")
        self.frame_center.grid(row=1, column=1, padx=(5, 10), pady=(0, 10), sticky="nsew")
        self.frame_center.grid_rowconfigure(1, weight=1)
        self.frame_center.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.frame_center, text="💬 Mensagens", font=("Arial", 16, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.txt_messages = ctk.CTkTextbox(self.frame_center, width=800, height=27, fg_color="#232334", text_color="#eaeaea")
        self.txt_messages.grid(row=1, column=0, padx=10, pady=(0,5), sticky="nsew")
        self.entry_search = ctk.CTkEntry(self.frame_center, width=800, placeholder_text="Buscar termo nas mensagens...")
        self.entry_search.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.entry_search.bind("<Return>", self.search_messages)
        self.frame_filters = ctk.CTkFrame(self.frame_center, corner_radius=10, fg_color="#24243a")
        self.frame_filters.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.frame_filters.grid_columnconfigure(4, weight=1)
        ctk.CTkLabel(self.frame_filters, text="Limite (n°/all):").grid(row=0, column=0, sticky="w")
        self.entry_limit = ctk.CTkEntry(self.frame_filters, width=60)
        self.entry_limit.insert(0, "all")
        self.entry_limit.grid(row=0, column=1, padx=5)
        ctk.CTkLabel(self.frame_filters, text="Palavras-chave (| separar):").grid(row=0, column=2, sticky="w")
        self.entry_keywords = ctk.CTkEntry(self.frame_filters, width=120)
        self.entry_keywords.grid(row=0, column=3, padx=5)
        ctk.CTkLabel(self.frame_filters, text="Início (YYYY-MM-DD):").grid(row=1, column=0, sticky="w")
        self.entry_date_start = ctk.CTkEntry(self.frame_filters, width=80)
        self.entry_date_start.grid(row=1, column=1)
        ctk.CTkLabel(self.frame_filters, text="Fim (YYYY-MM-DD):").grid(row=1, column=2, sticky="w")
        self.entry_date_end = ctk.CTkEntry(self.frame_filters, width=80)
        self.entry_date_end.grid(row=1, column=3)
        self.content_filter_var = ctk.StringVar(value="1")
        ctk.CTkLabel(self.frame_filters, text="Conteúdo:").grid(row=2, column=0, sticky="w")
        ctk.CTkRadioButton(self.frame_filters, text="Nenhum", variable=self.content_filter_var, value="1").grid(row=2, column=1, sticky="w")
        ctk.CTkRadioButton(self.frame_filters, text="Anexos", variable=self.content_filter_var, value="2").grid(row=2, column=2, sticky="w")
        ctk.CTkRadioButton(self.frame_filters, text="Links", variable=self.content_filter_var, value="3").grid(row=2, column=3, sticky="w")
        self.btn_backup = ctk.CTkButton(self.frame_filters, text="Backup deste canal", command=self.threaded_backup, fg_color="#17a2b8")
        self.btn_backup.grid(row=3, column=1, padx=6, pady=7, sticky="ew")
        self.btn_delete_confirm = ctk.CTkButton(self.frame_filters, text="Deletar neste canal", command=self.threaded_delete_confirm, fg_color="#dc3545")
        self.btn_delete_confirm.grid(row=3, column=2, padx=6, pady=7, sticky="ew")
        # Agendamento automação deletar
        self.frame_auto_delete = ctk.CTkFrame(self.frame_filters, corner_radius=10, fg_color="#24243a")
        self.frame_auto_delete.grid(row=4, column=0, columnspan=5, pady=10, sticky="ew")
        ctk.CTkLabel(self.frame_auto_delete, text="Agendamento automático:", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=10, pady=6)
        ctk.CTkLabel(self.frame_auto_delete, text="Hora do dia (HH:MM):").grid(row=1, column=0, sticky="w", padx=10)
        self.entry_auto_time = ctk.CTkEntry(self.frame_auto_delete, width=60)
        self.entry_auto_time.insert(0, "00:00")
        self.entry_auto_time.grid(row=1, column=1, padx=5)
        ctk.CTkLabel(self.frame_auto_delete, text="Frequência (minutos):").grid(row=1, column=2, sticky="w", padx=10)
        self.entry_auto_freq = ctk.CTkEntry(self.frame_auto_delete, width=60)
        self.entry_auto_freq.insert(0, "60")
        self.entry_auto_freq.grid(row=1, column=3, padx=5)
        self.btn_toggle_auto = ctk.CTkButton(self.frame_auto_delete, text="Ativar Deleção Automática", fg_color="#17a2b8", command=self.toggle_auto_delete)
        self.btn_toggle_auto.grid(row=1, column=4, padx=15)
        self.frame_status = ctk.CTkFrame(self, corner_radius=10, fg_color="#181825")
        self.frame_status.grid(row=2, column=0, columnspan=2, padx=10, pady=4, sticky="ew")
        self.lbl_status = ctk.CTkLabel(self.frame_status, text="Pronto", font=("Consolas", 12), text_color="#eaeaea", bg_color="#181825")
        self.lbl_status.pack(side="left", padx=12)
        self.progress = ctk.CTkProgressBar(self.frame_status, width=240, height=18, fg_color="#232334", progress_color="#20d0bb")
        self.progress.pack(side="left", padx=14)
        ctk.CTkLabel(self.frame_status, text="Desenvolvido por: methzzy (Gon) [GitHub] [Telegram: @methzzy]", font=("Arial", 12), text_color="#55dfff", bg_color="#181825").pack(side="right", padx=10)

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
        self.listbox_channels.delete(0, END)
        if not data:
            self.set_status("Falha ao carregar canais", "red")
            return
        for idx, c in enumerate(data):
            if c["type"] == 1:
                recipient = c.get("recipients", [])
                if recipient:
                    name = f"💬 {recipient[0]['username']}"
                else:
                    name = "💬 DM"
            elif c["type"] == 3:
                name = f"👥 {c.get('name', 'Grupo')}"
            else:
                name = "Outro"
            self.channels.append({"id": c["id"], "name": name})
            self.listbox_channels.insert(END, f"[{idx + 1}] {name} ({c['id']})")

    def channel_selected(self, event):
        selected_indices = self.listbox_channels.curselection()
        if len(selected_indices) == 1:
            idx = selected_indices[0]
            channel = self.channels[idx]
            self.current_channel_id = channel['id']
            self.set_status(f"Carregando canal: {channel['name']}")
            self.load_messages(channel['id'])
        else:
            self.current_channel_id = None
            self.txt_messages.delete("1.0", "end")
            self.set_status("Selecione apenas 1 canal para visualizar mensagens.")

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
        filename = f"backup_{self.current_channel_id}_{int(time.time())}.txt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
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
        selected_indices = self.listbox_channels.curselection()
        if not selected_indices:
            return []
        return [self.channels[i] for i in selected_indices]

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
            filename = f"backup_{channel['id']}_{int(time.time())}.txt"
            try:
                with open(filename, "w", encoding="utf-8") as f:
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
            filename = filedialog.asksaveasfilename(initialfile=f"backup_{channel['id']}_{int(time.time())}.csv", defaultextension=".csv")
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
            self.btn_toggle_auto.configure(text="Ativar Deleção Automática", fg_color="#17a2b8")
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
            self.btn_toggle_auto.configure(text="Desativar Deleção Automática", fg_color="#d9534f")
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
        win.configure(bg="#181825")
        try:
            win.iconphoto(True, ImageTk.PhotoImage(Image.open(ICON_PATH)))
        except Exception:
            pass
        ctk.CTkLabel(win, text="Gon Clean DM", font=("Segoe UI SemiBold", 22, "bold"), text_color="#FF6565", bg_color="#181825").pack(pady=(16,0))
        if self.avatar_hash:
            avatar_url = f"https://cdn.discordapp.com/avatars/{self.my_id}/{self.avatar_hash}.png?size=128"
            try:
                import io, requests
                avatar_bytes = requests.get(avatar_url).content
                img = Image.open(io.BytesIO(avatar_bytes)).resize((80,80))
                avatar_img = ImageTk.PhotoImage(img)
                avatar_frame = ctk.CTkFrame(win, fg_color="#232334", corner_radius=30)
                avatar_frame.pack(pady=7)
                ctk.CTkLabel(avatar_frame, image=avatar_img, text="", bg_color="#232334").pack(padx=10, pady=5)
                avatar_frame.image = avatar_img
            except Exception:
                pass
        user_card = ctk.CTkFrame(win, fg_color="#232334", corner_radius=15)
        user_card.pack(padx=16, pady=10, fill="x")
        userinfo = (
            f"Usuário: {self.username}#{self.discriminator}\n"
            f"ID: {self.my_id}\n"
            f"Email: {self.email or 'Desconhecido'}\n"
            f"Telefone: {self.phone or 'Desconhecido'}\n"
            f"Avatar: {self.avatar_hash or 'Desconhecido'}\n"
            f"Conta criada: {self.created_at}\n"
        )
        self.info_label = ctk.CTkLabel(user_card, text=userinfo, justify="left", font=("Consolas", 13), text_color="#cccccc", bg_color="#232334")
        self.info_label.pack()
        def toggle_info():
            if self.info_label.winfo_ismapped():
                self.info_label.pack_forget()
                btn_toggle.configure(text="Exibir informações")
            else:
                self.info_label.pack(padx=10, pady=10, anchor="center")
                btn_toggle.configure(text="Ocultar informações")
        btn_toggle = ctk.CTkButton(win, text="Ocultar informações", command=toggle_info, width=170, fg_color="#394362", hover_color="#556")
        btn_toggle.pack(pady=6)
        ctk.CTkLabel(win, text="─"*52, font=("Segoe UI", 10), text_color="#272739", bg_color="#181825").pack(pady=8)
        dev_card = ctk.CTkFrame(win, fg_color="#202127", corner_radius=13)
        dev_card.pack(fill="x", padx=17, pady=4)
        devtext = (
            "Criador: methzzy (Gon)\n"
            "GitHub: https://github.com/methzzy\n"
            "Telegram: @methzzy\n\n"
            "Ferramenta para remover, fazer backup e gerenciar\n"
            "mensagens do Discord via DM/Grupo com segurança."
        )
        ctk.CTkLabel(dev_card, text=devtext, font=("Segoe UI", 12), text_color="#42c5ff", justify="center", bg_color="#202127").pack(padx=8, pady=11)
        ctk.CTkLabel(win, text="© 2025 Gon Clean DM", font=("Arial", 10), text_color="#808080", bg_color="#181825").pack(pady=8)

if __name__ == "__main__":
    GonCleanDMGUI().mainloop()
