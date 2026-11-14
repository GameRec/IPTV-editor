"""M3U Playlist Category Cleaner & Manager

A lightweight desktop utility built with Python and Tkinter to parse, filter,
group, and clean M3U/M3U8 IPTV playlists with zero bloat.

Author: TRX / GameRec (https://gamerec.org)
Support: https://ko-fi.com/gamerec | https://github.com/sponsors/trx90th
"""

import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

# Configuration links for support
SUPPORT_URL = "https://ko-fi.com/gamerec"
GITHUB_SPONSORS_URL = "https://github.com/sponsors/trx90th"

# Localization dictionaries
LANGUAGES = {
    "EN": {
        "title": "M3U Playlist Category Cleaner",
        "load_btn": "📂 Load M3U File",
        "no_file": "No file selected",
        "loaded": (
            "Loaded: {file} ({count} categories, {channels} channels)"
        ),
        "sel_status": (
            "Selected: {sel_cats}/{total_cats} cats |"
            " {sel_chans}/{total_chans} chans"
        ),
        "tabs": ["Live TV", "Movies", "Series", "Other"],
        "select_all": "✅ Select All",
        "deselect_all": "❌ Deselect All",
        "save_btn": "💾 Save Filtered Playlist",
        "support_btn": "☕ Support Me",
        "group_frame": "Select categories to keep (grouped)",
        "warning": "Warning",
        "warning_load": "Please load an M3U file first!",
        "success": "Success",
        "success_msg": (
            "Done!\nFiltered playlist saved.\nSkipped entries from rejected"
            " categories: {skipped}"
        ),
        "error": "Error",
        "error_read": "Failed to read file:\n{e}",
        "error_save": "Failed to save file:\n{e}",
        "time_group": "24/7 (Time categories)",
        "other_group": "Other",
    },
    "PL": {
        "title": "M3U Playlist Category Cleaner",
        "load_btn": "📂 Wczytaj plik M3U",
        "no_file": "Nie wybrano pliku",
        "loaded": "Wczytano: {file} ({count} kategorii, {channels} kanałów)",
        "sel_status": (
            "Zaznaczone: {sel_cats}/{total_cats} kat. |"
            " {sel_chans}/{total_chans} kan."
        ),
        "tabs": ["Live TV", "Filmy", "Seriale", "Inne"],
        "select_all": "✅ Zaznacz wszystko",
        "deselect_all": "❌ Odznacz wszystko",
        "save_btn": "💾 Zapisz przefiltrowaną playlistę",
        "support_btn": "☕ Postaw kawę",
        "group_frame": "Wybierz kategorie do zachowania (zgrupowane)",
        "warning": "Uwaga",
        "warning_load": "Najpierw wczytaj plik M3U!",
        "success": "Sukces",
        "success_msg": (
            "Gotowe!\nZapisano przefiltrowaną playlistę.\nPominięto wpisów z"
            " odrzuconych kategorii: {skipped}"
        ),
        "error": "Błąd",
        "error_read": "Nie udało się odczytać pliku:\n{e}",
        "error_save": "Nie udało się zapisać pliku:\n{e}",
        "time_group": "24/7 (Kategorie czasowe)",
        "other_group": "Inne",
    },
}

# Common country codes and regional tags for intelligent grouping
COUNTRIES = [
    "SWEDEN",
    "ICELAND",
    "POLAND",
    "POLSKA",
    "NORWAY",
    "DENMARK",
    "FINLAND",
    "GERMANY",
    "UK",
    "UNITED KINGDOM",
    "USA",
    "US",
    "SPAIN",
    "ITALY",
    "FRANCE",
    "NETHERLANDS",
    "BELGIUM",
    "PORTUGAL",
    "GREECE",
    "TURKEY",
    "ROMANIA",
    "RUSSIA",
    "UKRAINE",
    "CZECH",
    "SLOVAKIA",
    "HUNGARY",
    "AUSTRIA",
    "SWITZERLAND",
    "IRELAND",
    "ESTONIA",
    "LATVIA",
    "LITHUANIA",
    "CANADA",
    "AUSTRALIA",
    "BRAZIL",
    "MEXICO",
    "ARGENTINA",
    "CHILE",
    "COLOMBIA",
    "INDIA",
    "PAKISTAN",
    "PHILIPPINES",
    "VIETNAM",
    "THAILAND",
    "CHINA",
    "JAPAN",
    "KOREA",
    "ARAB",
    "EX-YU",
    "BALKAN",
    "LATINO",
]


class CollapsibleGroup(ttk.Frame):
  """UI Component representing a collapsible category group with checkboxes."""

  def __init__(self, parent, title, categories_list, app_instance):
    super().__init__(parent)
    self.app = app_instance
    self.title = title
    self.categories_list = categories_list

    self.var_group = tk.BooleanVar(value=True)
    self.is_expanded = False

    header_frame = ttk.Frame(self)
    header_frame.pack(fill=tk.X, anchor="w", pady=2)

    self.btn_toggle = ttk.Button(
        header_frame, text="+", width=3, command=self.toggle_expand
    )
    self.btn_toggle.pack(side=tk.LEFT, padx=(0, 6))

    self.chk_group = ttk.Checkbutton(
        header_frame,
        text=f"{title} ({len(categories_list)})",
        variable=self.var_group,
        command=self.toggle_group_states,
    )
    self.chk_group.pack(side=tk.LEFT, fill=tk.X, expand=True)

    self.content_frame = ttk.Frame(self, padding=(28, 2, 0, 2))
    self.sub_vars = []

    for cat in sorted(categories_list):
      var = tk.BooleanVar(value=True)
      self.app.categories[cat] = var
      self.sub_vars.append(var)
      chk = ttk.Checkbutton(
          self.content_frame,
          text=cat,
          variable=var,
          command=self.update_group_checkbox,
      )
      chk.pack(anchor="w", pady=1)

  def toggle_expand(self):
    if self.is_expanded:
      self.content_frame.pack_forget()
      self.btn_toggle.config(text="+")
      self.is_expanded = False
    else:
      self.content_frame.pack(fill=tk.X, anchor="w", pady=2)
      self.btn_toggle.config(text="-")
      self.is_expanded = True
    self.app.update_active_scrollregion()

  def toggle_group_states(self):
    state = self.var_group.get()
    for var in self.sub_vars:
      var.set(state)
    self.app.update_selection_counters()

  def set_group_state(self, state):
    self.var_group.set(state)
    for var in self.sub_vars:
      var.set(state)
    self.app.update_selection_counters()

  def update_group_checkbox(self):
    any_checked = any(v.get() for v in self.sub_vars)
    self.var_group.set(any_checked)
    self.app.update_selection_counters()


class M3UFilterApp:
  """Main application window and logic controller."""

  def __init__(self, root):
    self.root = root
    self.current_lang = "EN"
    self.t = LANGUAGES[self.current_lang]

    # Borderless window configuration for modern look
    self.root.overrideredirect(True)
    self.root.geometry("920x780")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure(".", font=("Segoe UI", 10))
    style.configure("TButton", padding=6, relief="flat", background="#e1e1e1")
    style.configure(
        "TNotebook.Tab", padding=[12, 8], font=("Segoe UI", 10, "bold")
    )

    self.file_path = None
    self.playlist_lines = []
    self.categories = {}
    self.category_channel_counts = {}
    self.tab_scroll_frames = {}
    self.group_widgets_by_tab = {
        "Live TV": [],
        "Filmy": [],
        "Seriale": [],
        "Inne": [],
    }

    # Custom draggable title bar
    self.title_bar = tk.Frame(root, bg="#2b2b2b", relief="flat", height=36)
    self.title_bar.pack(fill=tk.X)
    self.title_bar.pack_propagate(False)

    self.title_bar.bind("<Button-1>", self.start_move)
    self.title_bar.bind("<B1-Motion>", self.do_move)

    self.title_label = tk.Label(
        self.title_bar,
        text=self.t["title"],
        bg="#2b2b2b",
        fg="#ffffff",
        font=("Segoe UI", 10, "bold"),
    )
    self.title_label.pack(side=tk.LEFT, padx=12)
    self.title_label.bind("<Button-1>", self.start_move)
    self.title_label.bind("<B1-Motion>", self.do_move)

    # Close button (X)
    self.btn_close = tk.Button(
        self.title_bar,
        text="✕",
        bg="#2b2b2b",
        fg="#ffffff",
        bd=0,
        font=("Segoe UI", 11, "bold"),
        activebackground="#e81123",
        activeforeground="#ffffff",
        command=self.root.destroy,
        width=4,
    )
    self.btn_close.pack(side=tk.RIGHT, fill=tk.Y)

    # Main container frame
    main_container = ttk.Frame(root)
    main_container.pack(fill=tk.BOTH, expand=True)

    # Top control panel
    top_frame = ttk.Frame(main_container, padding=12)
    top_frame.pack(fill=tk.X)

    self.btn_load = ttk.Button(
        top_frame, text=self.t["load_btn"], command=self.load_file
    )
    self.btn_load.pack(side=tk.LEFT)

    self.lbl_status = ttk.Label(
        top_frame, text=self.t["no_file"], font=("Segoe UI", 9, "italic")
    )
    self.lbl_status.pack(side=tk.LEFT, padx=12)

    # Language switcher
    lang_frame = ttk.Frame(top_frame)
    lang_frame.pack(side=tk.RIGHT)

    ttk.Label(lang_frame, text="Lang: ").pack(side=tk.LEFT, padx=2)
    self.lang_cb = ttk.Combobox(
        lang_frame, values=["EN", "PL"], width=5, state="readonly"
    )
    self.lang_cb.set(self.current_lang)
    self.lang_cb.pack(side=tk.LEFT)
    self.lang_cb.bind("<<ComboboxSelected>>", self.change_language)

    # Tabbed notebook panel
    self.notebook_frame = ttk.LabelFrame(
        main_container, text=self.t["group_frame"], padding=10
    )
    self.notebook_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=5)

    self.notebook = ttk.Notebook(self.notebook_frame)
    self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    self.tabs = {}
    self.tab_keys = ["Live TV", "Filmy", "Seriale", "Inne"]
    for i, name in enumerate(self.tab_keys):
      tab_frame = ttk.Frame(self.notebook)
      self.notebook.add(tab_frame, text=self.t["tabs"][i])
      self.tabs[name] = tab_frame
      self.setup_tab_canvas(tab_frame, name)

    self.root.bind_all("<MouseWheel>", self._on_mousewheel)

    # Bottom control panel
    bottom_frame = ttk.Frame(main_container, padding=12)
    bottom_frame.pack(fill=tk.X)

    self.btn_select_all = ttk.Button(
        bottom_frame,
        text=self.t["select_all"],
        command=lambda: self.toggle_all(True),
    )
    self.btn_select_all.pack(side=tk.LEFT, padx=4)

    self.btn_deselect_all = ttk.Button(
        bottom_frame,
        text=self.t["deselect_all"],
        command=lambda: self.toggle_all(False),
    )
    self.btn_deselect_all.pack(side=tk.LEFT, padx=4)

    # Support button (Ko-fi / Sponsors)
    self.btn_support = ttk.Button(
        bottom_frame, text=self.t["support_btn"], command=self.open_support
    )
    self.btn_support.pack(side=tk.LEFT, padx=10)

    # Selection counter label
    self.lbl_selection_info = ttk.Label(
        bottom_frame, text="", font=("Segoe UI", 9, "bold")
    )
    self.lbl_selection_info.pack(side=tk.LEFT, padx=5)

    self.btn_save = ttk.Button(
        bottom_frame, text=self.t["save_btn"], command=self.save_file
    )
    self.btn_save.pack(side=tk.RIGHT, padx=4)

  def start_move(self, event):
    self.x = event.x
    self.y = event.y

  def do_move(self, event):
    x = event.x_root - self.x
    y = event.y_root - self.y
    self.root.geometry(f"+{x}+{y}")

  def open_support(self):
    webbrowser.open(SUPPORT_URL)

  def change_language(self, event):
    self.current_lang = self.lang_cb.get()
    self.t = LANGUAGES[self.current_lang]

    self.title_label.config(text=self.t["title"])
    self.btn_load.config(text=self.t["load_btn"])
    self.btn_select_all.config(text=self.t["select_all"])
    self.btn_deselect_all.config(text=self.t["deselect_all"])
    self.btn_support.config(text=self.t["support_btn"])
    self.btn_save.config(text=self.t["save_btn"])
    self.notebook_frame.config(text=self.t["group_frame"])

    for i, name in enumerate(self.tab_keys):
      self.notebook.tab(i, text=self.t["tabs"][i])

    if not self.file_path:
      self.lbl_status.config(text=self.t["no_file"])
    else:
      file_name = os.path.basename(self.file_path)
      cat_count = len(self.categories)
      chan_count = sum(self.category_channel_counts.values())
      self.lbl_status.config(
          text=self.t["loaded"].format(
              file=file_name, count=cat_count, channels=chan_count
          )
      )
    self.update_selection_counters()

  def update_selection_counters(self):
    if not self.categories:
      self.lbl_selection_info.config(text="")
      return

    total_cats = len(self.categories)
    sel_cats = sum(1 for var in self.categories.values() if var.get())

    total_chans = sum(self.category_channel_counts.values())
    sel_chans = sum(
        self.category_channel_counts.get(cat, 0)
        for cat, var in self.categories.items()
        if var.get()
    )

    self.lbl_selection_info.config(
        text=self.t["sel_status"].format(
            sel_cats=sel_cats,
            total_cats=total_cats,
            sel_chans=sel_chans,
            total_chans=total_chans,
        )
    )

  def setup_tab_canvas(self, parent_tab, tab_name):
    container = ttk.Frame(parent_tab, padding=2)
    container.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(container, highlightthickness=0, background="#ffffff")
    scrollbar = ttk.Scrollbar(
        container, orient="vertical", command=canvas.yview
    )
    scrollable_frame = ttk.Frame(canvas, style="TFrame")

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
    )

    canvas_window = canvas.create_window(
        (0, 0), window=scrollable_frame, anchor="nw"
    )
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.bind(
        "<Configure>",
        lambda e: canvas.itemconfig(canvas_window, width=e.width),
    )

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    self.tab_scroll_frames[tab_name] = {
        "canvas": canvas,
        "frame": scrollable_frame,
    }

  def _on_mousewheel(self, event):
    try:
      current_tab_index = self.notebook.index(self.notebook.select())
      tab_name = self.tab_keys[current_tab_index]
      canvas = self.tab_scroll_frames[tab_name]["canvas"]
      canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    except Exception:
      pass

  def update_active_scrollregion(self):
    current_tab_index = self.notebook.index(self.notebook.select())
    tab_name = self.tab_keys[current_tab_index]
    canvas = self.tab_scroll_frames[tab_name]["canvas"]
    canvas.configure(scrollregion=canvas.bbox("all"))

  def load_file(self):
    file_path = filedialog.askopenfilename(
        filetypes=[
            ("Pliki M3U/M3U8", "*.m3u *.m3u8"),
            ("Wszystkie pliki", "*.*"),
        ]
    )
    if not file_path:
      return

    self.file_path = file_path
    try:
      with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        self.playlist_lines = f.readlines()
    except Exception as e:
      messagebox.showerror(self.t["error"], self.t["error_read"].format(e=e))
      return

    self.category_channel_counts = {}
    for line in self.playlist_lines:
      if line.startswith("#EXTINF"):
        match = re.search(r'group-title="([^"]*)"', line)
        cat = match.group(1) if match else "(Brak kategorii)"
        if cat not in self.category_channel_counts:
          self.category_channel_counts[cat] = 0
        self.category_channel_counts[cat] += 1

    self.parse_categories()
    file_name = os.path.basename(file_path)
    cat_count = len(self.categories)
    chan_count = sum(self.category_channel_counts.values())

    self.lbl_status.config(
        text=self.t["loaded"].format(
            file=file_name, count=cat_count, channels=chan_count
        )
    )
    self.update_selection_counters()

  def parse_categories(self):
    for tab_name in self.group_widgets_by_tab:
      for widget in self.tab_scroll_frames[tab_name][
          "frame"
      ].winfo_children():
        widget.destroy()
      self.group_widgets_by_tab[tab_name] = []

    self.categories = {}
    unique_cats = set(self.category_channel_counts.keys())

    tab_buckets = {"Live TV": {}, "Filmy": {}, "Seriale": {}, "Inne": {}}

    for cat in unique_cats:
      target_tab = self.detect_tab(cat)
      group_name = self.detect_group(cat)

      if group_name not in tab_buckets[target_tab]:
        tab_buckets[target_tab][group_name] = []
      tab_buckets[target_tab][group_name].append(cat)

    for tab_name, groups in tab_buckets.items():
      scroll_frame = self.tab_scroll_frames[tab_name]["frame"]
      for group_name in sorted(groups.keys()):
        g_widget = CollapsibleGroup(
            scroll_frame, group_name, groups[group_name], self
        )
        g_widget.pack(fill=tk.X, anchor="w", pady=2)
        self.group_widgets_by_tab[tab_name].append(g_widget)

    self.update_selection_counters()

  def detect_tab(self, cat):
    c = cat.upper()
    if any(
        k in c
        for k in [
            "SERIAL",
            "SERIES",
            "SEZON",
            "TV SHOW",
            "TELENOVELA",
            "NETFLIX SERIES",
        ]
    ):
      return "Seriale"
    if any(
        k in c
        for k in [
            "FILM",
            "MOVIE",
            "CINEMA",
            "KINO",
            "VOD",
            "PREMIERE",
            "PREMIERY",
            "NETFLIX MOVIES",
        ]
    ):
      return "Filmy"
    return "Live TV"

  def detect_group(self, cat):
    cat_upper = cat.upper()
    if cat_upper.startswith("24/7"):
      return self.t["time_group"]
    if "4K" in cat_upper:
      return "4K / Ultra HD"

    clean_str = re.sub(r"[^A-Z0-9 ]", " ", cat_upper)
    words = clean_str.split()
    if words and words[0] in COUNTRIES:
      return words[0]

    parts = [p.strip() for p in re.split(r"[|/:]", cat) if p.strip()]
    if parts:
      if len(parts[0]) <= 6 and parts[0].isupper():
        return parts[0]
      return parts[0]

    return self.t["other_group"]

  def toggle_all(self, state):
    for tab_name in self.group_widgets_by_tab:
      for gw in self.group_widgets_by_tab[tab_name]:
        gw.set_group_state(state)

  def save_file(self):
    if not self.file_path or not self.playlist_lines:
      messagebox.showwarning(self.t["warning"], self.t["warning_load"])
      return

    save_path = filedialog.asksaveasfilename(
        defaultextension=".m3u",
        filetypes=[("Plik M3U", "*.m3u"), ("Wszystkie pliki", "*.*")],
    )
    if not save_path:
      return

    new_lines = []
    i = 0
    skipped_groups = 0

    while i < len(self.playlist_lines):
      line = self.playlist_lines[i]

      if line.startswith("#EXTINF"):
        match = re.search(r'group-title="([^"]*)"', line)
        cat = match.group(1) if match else "(Brak kategorii)"

        if self.categories.get(cat, tk.BooleanVar(value=True)).get():
          new_lines.append(line)
          i += 1
          while (
              i < len(self.playlist_lines)
              and not self.playlist_lines[i].startswith("#EXTINF")
              and not self.playlist_lines[i].startswith("#EXTM3U")
          ):
            new_lines.append(self.playlist_lines[i])
            i += 1
        else:
          skipped_groups += 1
          i += 1
          while (
              i < len(self.playlist_lines)
              and not self.playlist_lines[i].startswith("#EXTINF")
              and not self.playlist_lines[i].startswith("#EXTM3U")
          ):
            i += 1
      else:
        new_lines.append(line)
        i += 1

    try:
      with open(save_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
      messagebox.showinfo(
          self.t["success"], self.t["success_msg"].format(skipped=skipped_groups)
      )
    except Exception as e:
      messagebox.showerror(self.t["error"], self.t["error_save"].format(e=e))


if __name__ == "__main__":
  root = tk.Tk()
  app = M3UFilterApp(root)
  root.mainloop()