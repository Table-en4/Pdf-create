import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser, font
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, LETTER, LEGAL
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
import os
import json
import sys
from datetime import datetime
import math
from PIL import Image as PILImage, ImageTk

class AdvancedPDFEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Editor Pro")
        self.root.geometry("1400x900")
        self.root.configure(bg="#2c3e50")
        
        # Initialisation des variables avant la création de l'interface
        self.setup_variables()
        self.setup_styles()
        self.create_gui()
        self.bind_events()
        
    def setup_styles(self):
        self.colors = {
            'primary': '#3498db',
            'secondary': '#2ecc71',
            'accent': '#e74c3c',
            'dark': '#2c3e50',
            'light': '#ecf0f1',
            'warning': '#f39c12',
            'success': '#27ae60'
        }
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('Custom.TButton', padding=10, font=('Arial', 10, 'bold'))
        self.style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground=self.colors['primary'])
        
    def setup_variables(self):
        self.bg_color = "#FFFFFF"
        self.text_color = "#000000"
        self.font_family = "Helvetica"
        self.font_size = 12
        self.page_format = A4
        self.text_align = TA_LEFT
        self.line_spacing = 1.2
        self.margin_left = 50
        self.margin_right = 50
        self.margin_top = 50
        self.margin_bottom = 50
        
        self.shapes = []
        self.images = []
        self.tables = []
        self.current_tool = "text"
        self.drawing = False
        self.start_x = None
        self.start_y = None
        self.current_shape = None
        
        self.undo_stack = []
        self.redo_stack = []
        
        # Variables pour le canvas unifié
        self.is_drawing = False
        self.last_x = None
        self.last_y = None
        self.current_text_item = None
        self.text_entries = {}
        self.selected_item = None
        
        # Variables pour le mode d'édition
        self.edit_mode = tk.StringVar(value="text")
        self.text_font_var = tk.StringVar(value="Arial")
        self.text_size_var = tk.StringVar(value="12")
        self.brush_size_var = tk.StringVar(value="2")
        
        # Variables pour les combobox
        self.font_var = tk.StringVar(value="Helvetica")
        self.size_var = tk.StringVar(value="12")
        self.page_format_var = tk.StringVar(value="A4")
        self.orientation_var = tk.StringVar(value="Portrait")
        
        # Initialiser les spinboxes des marges
        self.margin_spinboxes = {}
        
    def create_gui(self):
        self.create_menu()
        self.create_toolbar()
        self.create_main_content()
        self.create_properties_panel()
        self.create_status_bar()
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Nouveau", command=self.new_document, accelerator="Ctrl+N")
        file_menu.add_command(label="Ouvrir Template", command=self.open_template, accelerator="Ctrl+O")
        file_menu.add_command(label="Sauvegarder Template", command=self.save_template, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exporter PDF", command=self.export_pdf, accelerator="Ctrl+E")
        file_menu.add_command(label="Aperçu", command=self.preview_pdf, accelerator="Ctrl+P")
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit, accelerator="Ctrl+Q")
        
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Édition", menu=edit_menu)
        edit_menu.add_command(label="Annuler", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Refaire", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Copier", command=self.copy_text, accelerator="Ctrl+C")
        edit_menu.add_command(label="Coller", command=self.paste_text, accelerator="Ctrl+V")
        edit_menu.add_command(label="Tout sélectionner", command=self.select_all, accelerator="Ctrl+A")
        
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Affichage", menu=view_menu)
        view_menu.add_command(label="Zoom +", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom -", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Ajuster à la fenêtre", command=self.fit_to_window, accelerator="Ctrl+0")
        
        # Raccourcis clavier
        self.root.bind('<Control-n>', lambda e: self.new_document())
        self.root.bind('<Control-o>', lambda e: self.open_template())
        self.root.bind('<Control-s>', lambda e: self.save_template())
        self.root.bind('<Control-e>', lambda e: self.export_pdf())
        self.root.bind('<Control-p>', lambda e: self.preview_pdf())
        self.root.bind('<Control-z>', lambda e: self.undo())
        self.root.bind('<Control-y>', lambda e: self.redo())
        
    def create_toolbar(self):
        toolbar_frame = tk.Frame(self.root, bg=self.colors['dark'], height=80)
        toolbar_frame.pack(fill="x", padx=5, pady=5)
        toolbar_frame.pack_propagate(False)
        
        tools_frame = tk.Frame(toolbar_frame, bg=self.colors['dark'])
        tools_frame.pack(side="left", fill="y", padx=10)
        
        self.create_tool_buttons(tools_frame)
        
        format_frame = tk.Frame(toolbar_frame, bg=self.colors['dark'])
        format_frame.pack(side="left", fill="y", padx=20)
        
        self.create_format_controls(format_frame)
        
        action_frame = tk.Frame(toolbar_frame, bg=self.colors['dark'])
        action_frame.pack(side="right", fill="y", padx=10)
        
        self.create_action_buttons(action_frame)
        
    def create_tool_buttons(self, parent):
        tk.Label(parent, text="Outils:", bg=self.colors['dark'], fg=self.colors['light'], font=('Arial', 10, 'bold')).pack(anchor="w")
        
        tools_container = tk.Frame(parent, bg=self.colors['dark'])
        tools_container.pack(fill="x", pady=5)
        
        self.tool_buttons = {}
        tools = [
            ("✏️", "text", "Texte"),
            ("📦", "rectangle", "Rectangle"),
            ("⭕", "circle", "Cercle"),
            ("📏", "line", "Ligne"),
            ("🖼️", "image", "Image"),
            ("📊", "table", "Tableau")
        ]
        
        for icon, tool, tooltip in tools:
            btn = tk.Button(tools_container, text=icon, width=3, height=2,
                          command=lambda t=tool: self.select_tool(t),
                          bg=self.colors['primary'] if tool == "text" else self.colors['light'],
                          fg='white' if tool == "text" else 'black',
                          relief="raised", bd=2, font=('Arial', 12))
            btn.pack(side="left", padx=2)
            self.tool_buttons[tool] = btn
            self.create_tooltip(btn, tooltip)
            
    def create_format_controls(self, parent):
        tk.Label(parent, text="Format:", bg=self.colors['dark'], fg=self.colors['light'], font=('Arial', 10, 'bold')).pack(anchor="w")
        
        format_container = tk.Frame(parent, bg=self.colors['dark'])
        format_container.pack(fill="x", pady=5)
        
        tk.Label(format_container, text="Police:", bg=self.colors['dark'], fg=self.colors['light']).pack(side="left", padx=5)
        font_combo = ttk.Combobox(format_container, textvariable=self.font_var, width=12, state="readonly")
        font_combo['values'] = ["Helvetica", "Times-Roman", "Courier", "Arial", "Verdana"]
        font_combo.pack(side="left", padx=5)
        font_combo.bind('<<ComboboxSelected>>', self.on_font_change)
        
        tk.Label(format_container, text="Taille:", bg=self.colors['dark'], fg=self.colors['light']).pack(side="left", padx=5)
        size_combo = ttk.Combobox(format_container, textvariable=self.size_var, width=6, state="readonly")
        size_combo['values'] = ["8", "10", "12", "14", "16", "18", "20", "24", "28", "32", "36", "48"]
        size_combo.pack(side="left", padx=5)
        size_combo.bind('<<ComboboxSelected>>', self.on_size_change)
        
        tk.Button(format_container, text="🎨", command=self.choose_bg_color, width=3, height=1,
                 bg=self.colors['warning'], fg='white', relief="raised", bd=2).pack(side="left", padx=5)
        
        tk.Button(format_container, text="A", command=self.choose_text_color, width=3, height=1,
                 bg=self.colors['accent'], fg='white', relief="raised", bd=2, font=('Arial', 12, 'bold')).pack(side="left", padx=5)
        
    def create_action_buttons(self, parent):
        tk.Label(parent, text="Actions:", bg=self.colors['dark'], fg=self.colors['light'], font=('Arial', 10, 'bold')).pack(anchor="w")
        
        action_container = tk.Frame(parent, bg=self.colors['dark'])
        action_container.pack(fill="x", pady=5)
        
        tk.Button(action_container, text="↶", command=self.undo, width=3, height=1,
                 bg=self.colors['secondary'], fg='white', relief="raised", bd=2, font=('Arial', 12, 'bold')).pack(side="left", padx=2)
        
        tk.Button(action_container, text="↷", command=self.redo, width=3, height=1,
                 bg=self.colors['secondary'], fg='white', relief="raised", bd=2, font=('Arial', 12, 'bold')).pack(side="left", padx=2)
        
        tk.Button(action_container, text="👁️", command=self.preview_pdf, width=3, height=1,
                 bg=self.colors['primary'], fg='white', relief="raised", bd=2, font=('Arial', 12)).pack(side="left", padx=2)
        
        tk.Button(action_container, text="💾", command=self.export_pdf, width=3, height=1,
                 bg=self.colors['success'], fg='white', relief="raised", bd=2, font=('Arial', 12)).pack(side="left", padx=2)
        
    def create_main_content(self):
        main_frame = tk.Frame(self.root, bg=self.colors['light'])
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Créer un panneau principal avec deux sections
        paned_window = tk.PanedWindow(main_frame, orient=tk.HORIZONTAL, bg=self.colors['light'])
        paned_window.pack(fill="both", expand=True)
        
        # Panneau gauche pour le canvas
        left_frame = tk.Frame(paned_window, bg=self.colors['light'])
        paned_window.add(left_frame, minsize=600)
        
        self.create_unified_canvas(left_frame)
        
        # Panneau droit pour l'éditeur de texte
        right_frame = tk.Frame(paned_window, bg=self.colors['light'])
        paned_window.add(right_frame, minsize=300)
        
        self.create_text_editor(right_frame)
        
    def create_unified_canvas(self, parent):
        canvas_frame = tk.LabelFrame(parent, text="Zone de création unifiée", bg=self.colors['light'], 
                                    fg=self.colors['dark'], font=('Arial', 12, 'bold'))
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Barre d'outils canvas
        canvas_toolbar = tk.Frame(canvas_frame, bg=self.colors['light'])
        canvas_toolbar.pack(fill="x", padx=5, pady=5)
        
        # Mode d'édition
        mode_frame = tk.Frame(canvas_toolbar, bg=self.colors['light'])
        mode_frame.pack(side="left")
        
        tk.Label(mode_frame, text="Mode:", bg=self.colors['light'], font=('Arial', 10, 'bold')).pack(side="left", padx=5)
        
        modes = [("✏️ Texte", "text"), ("🖊️ Dessin", "draw"), ("🖱️ Sélection", "select")]
        
        for text, mode in modes:
            rb = tk.Radiobutton(mode_frame, text=text, variable=self.edit_mode, value=mode,
                               bg=self.colors['light'], command=self.change_edit_mode, font=('Arial', 9))
            rb.pack(side="left", padx=5)
        
        # Outils de formatage texte
        text_tools_frame = tk.Frame(canvas_toolbar, bg=self.colors['light'])
        text_tools_frame.pack(side="left", padx=20)
        
        tk.Label(text_tools_frame, text="Texte:", bg=self.colors['light'], font=('Arial', 10, 'bold')).pack(side="left", padx=5)
        
        font_combo = ttk.Combobox(text_tools_frame, textvariable=self.text_font_var, width=10, state="readonly")
        font_combo['values'] = ["Arial", "Helvetica", "Times", "Courier", "Verdana"]
        font_combo.pack(side="left", padx=2)
        
        size_combo = ttk.Combobox(text_tools_frame, textvariable=self.text_size_var, width=5, state="readonly")
        size_combo['values'] = ["8", "10", "12", "14", "16", "18", "20", "24", "28"]
        size_combo.pack(side="left", padx=2)
        
        tk.Button(text_tools_frame, text="B", command=self.toggle_bold, width=3, height=1,
                 font=('Arial', 10, 'bold')).pack(side="left", padx=2)
        tk.Button(text_tools_frame, text="I", command=self.toggle_italic, width=3, height=1,
                 font=('Arial', 10, 'italic')).pack(side="left", padx=2)
        
        # Outils de dessin
        draw_tools_frame = tk.Frame(canvas_toolbar, bg=self.colors['light'])
        draw_tools_frame.pack(side="left", padx=20)
        
        tk.Label(draw_tools_frame, text="Dessin:", bg=self.colors['light'], font=('Arial', 10, 'bold')).pack(side="left", padx=5)
        
        tk.Label(draw_tools_frame, text="Taille:", bg=self.colors['light']).pack(side="left", padx=2)
        brush_scale = tk.Scale(draw_tools_frame, from_=1, to=10, orient="horizontal", 
                              variable=self.brush_size_var, length=80)
        brush_scale.pack(side="left", padx=2)
        
        tk.Button(draw_tools_frame, text="🗑️", command=self.clear_canvas, width=3, height=1).pack(side="left", padx=2)
        
        # Canvas principal
        canvas_container = tk.Frame(canvas_frame, bg=self.colors['light'])
        canvas_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(canvas_container, bg="white", relief="sunken", bd=2, 
                               highlightthickness=1, highlightcolor=self.colors['primary'])
        
        # Scrollbars
        v_scrollbar = tk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)
        h_scrollbar = tk.Scrollbar(canvas_container, orient="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)
        
        # Configuration de la zone de défilement
        self.canvas.configure(scrollregion=(0, 0, 2000, 2000))
        
        # Curseur par défaut
        self.canvas.configure(cursor="xterm")
        
    def create_text_editor(self, parent):
        """Créer l'éditeur de texte séparé"""
        text_frame = tk.LabelFrame(parent, text="Éditeur de texte", bg=self.colors['light'], 
                                  fg=self.colors['dark'], font=('Arial', 12, 'bold'))
        text_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Barre d'outils pour l'éditeur de texte
        text_toolbar = tk.Frame(text_frame, bg=self.colors['light'])
        text_toolbar.pack(fill="x", padx=5, pady=5)
        
        # Boutons d'alignement
        align_frame = tk.Frame(text_toolbar, bg=self.colors['light'])
        align_frame.pack(side="left")
        
        tk.Label(align_frame, text="Alignement:", bg=self.colors['light'], font=('Arial', 10, 'bold')).pack(side="left", padx=5)
        
        tk.Button(align_frame, text="⬅️", command=lambda: self.set_alignment(TA_LEFT), width=3, height=1).pack(side="left", padx=2)
        tk.Button(align_frame, text="🔹", command=lambda: self.set_alignment(TA_CENTER), width=3, height=1).pack(side="left", padx=2)
        tk.Button(align_frame, text="➡️", command=lambda: self.set_alignment(TA_RIGHT), width=3, height=1).pack(side="left", padx=2)
        tk.Button(align_frame, text="▦", command=lambda: self.set_alignment(TA_JUSTIFY), width=3, height=1).pack(side="left", padx=2)
        
        # Zone de texte avec scrollbars
        text_container = tk.Frame(text_frame, bg=self.colors['light'])
        text_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.text_widget = tk.Text(text_container, wrap=tk.WORD, font=(self.font_family, self.font_size),
                                  bg="white", fg=self.text_color, relief="sunken", bd=2)
        
        text_v_scrollbar = tk.Scrollbar(text_container, orient="vertical", command=self.text_widget.yview)
        text_h_scrollbar = tk.Scrollbar(text_container, orient="horizontal", command=self.text_widget.xview)
        
        self.text_widget.configure(yscrollcommand=text_v_scrollbar.set, xscrollcommand=text_h_scrollbar.set)
        
        # Grid layout pour le texte
        self.text_widget.grid(row=0, column=0, sticky="nsew")
        text_v_scrollbar.grid(row=0, column=1, sticky="ns")
        text_h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        text_container.grid_rowconfigure(0, weight=1)
        text_container.grid_columnconfigure(0, weight=1)
        
        # Texte d'exemple
        self.text_widget.insert("1.0", "Commencez à taper votre texte ici...\n\nUtilisez les outils pour formater votre document.")
        
    def create_properties_panel(self):
        properties_frame = tk.Frame(self.root, bg=self.colors['light'], width=300)
        properties_frame.pack(side="right", fill="y", padx=5, pady=5)
        properties_frame.pack_propagate(False)
        
        tk.Label(properties_frame, text="Propriétés", bg=self.colors['light'], 
                fg=self.colors['dark'], font=('Arial', 14, 'bold')).pack(pady=10)
        
        self.create_page_settings(properties_frame)
        self.create_margin_settings(properties_frame)
        self.create_layer_manager(properties_frame)
        
    def create_page_settings(self, parent):
        page_frame = tk.LabelFrame(parent, text="Page", bg=self.colors['light'], 
                                  fg=self.colors['dark'], font=('Arial', 10, 'bold'))
        page_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(page_frame, text="Format:", bg=self.colors['light']).pack(anchor="w", padx=5)
        page_combo = ttk.Combobox(page_frame, textvariable=self.page_format_var, state="readonly")
        page_combo['values'] = ["A4", "Letter", "Legal"]
        page_combo.pack(fill="x", padx=5, pady=2)
        page_combo.bind('<<ComboboxSelected>>', self.on_page_format_change)
        
        tk.Label(page_frame, text="Orientation:", bg=self.colors['light']).pack(anchor="w", padx=5)
        orientation_combo = ttk.Combobox(page_frame, textvariable=self.orientation_var, state="readonly")
        orientation_combo['values'] = ["Portrait", "Paysage"]
        orientation_combo.pack(fill="x", padx=5, pady=2)
        
    def create_margin_settings(self, parent):
        margin_frame = tk.LabelFrame(parent, text="Marges", bg=self.colors['light'], 
                                    fg=self.colors['dark'], font=('Arial', 10, 'bold'))
        margin_frame.pack(fill="x", padx=10, pady=5)
        
        margins = [("Gauche", "margin_left"), ("Droite", "margin_right"), 
                  ("Haut", "margin_top"), ("Bas", "margin_bottom")]
        
        for label, attr in margins:
            frame = tk.Frame(margin_frame, bg=self.colors['light'])
            frame.pack(fill="x", padx=5, pady=2)
            tk.Label(frame, text=f"{label}:", bg=self.colors['light'], width=8).pack(side="left")
            spinbox = tk.Spinbox(frame, from_=10, to=100, width=10, 
                               command=lambda a=attr: self.update_margin(a))
            spinbox.pack(side="right")
            spinbox.delete(0, "end")
            spinbox.insert(0, str(getattr(self, attr)))
            self.margin_spinboxes[attr] = spinbox
            
    def create_layer_manager(self, parent):
        layer_frame = tk.LabelFrame(parent, text="Calques", bg=self.colors['light'], 
                                   fg=self.colors['dark'], font=('Arial', 10, 'bold'))
        layer_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.layer_listbox = tk.Listbox(layer_frame, bg='white', height=8)
        self.layer_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        layer_buttons = tk.Frame(layer_frame, bg=self.colors['light'])
        layer_buttons.pack(fill="x", padx=5, pady=5)
        
        tk.Button(layer_buttons, text="➕", command=self.add_layer, width=3).pack(side="left", padx=2)
        tk.Button(layer_buttons, text="➖", command=self.remove_layer, width=3).pack(side="left", padx=2)
        tk.Button(layer_buttons, text="⬆️", command=self.move_layer_up, width=3).pack(side="left", padx=2)
        tk.Button(layer_buttons, text="⬇️", command=self.move_layer_down, width=3).pack(side="left", padx=2)
        
    def create_status_bar(self):
        self.status_bar = tk.Label(self.root, text="Prêt", bg=self.colors['dark'], 
                                  fg=self.colors['light'], relief="sunken", anchor="w")
        self.status_bar.pack(side="bottom", fill="x")
        
    def bind_events(self):
        # Événements du canvas
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Motion>", self.on_canvas_motion)
        self.canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
        
        # Raccourcis pour changer de mode
        self.root.bind("<Control-t>", lambda e: self.edit_mode.set("text") or self.change_edit_mode())
        self.root.bind("<Control-d>", lambda e: self.edit_mode.set("draw") or self.change_edit_mode())
        self.root.bind("<Control-Shift-L>", lambda e: self.edit_mode.set("select") or self.change_edit_mode())
        
        # Supprimer avec Delete
        self.root.bind("<Delete>", self.delete_selected)
        
    # === MÉTHODES D'INTERACTION CANVAS ===
    
    def change_edit_mode(self):
        mode = self.edit_mode.get()
        if mode == "text":
            self.canvas.configure(cursor="xterm")
            self.current_tool = "text"
        elif mode == "draw":
            self.canvas.configure(cursor="pencil")
            self.current_tool = "draw"
        elif mode == "select":
            self.canvas.configure(cursor="hand2")
            self.current_tool = "select"
        
        self.update_status(f"Mode: {mode}")
        
    def select_tool(self, tool):
        self.current_tool = tool
        for t, btn in self.tool_buttons.items():
            if t == tool:
                btn.configure(bg=self.colors['primary'], fg='white')
            else:
                btn.configure(bg=self.colors['light'], fg='black')
        self.update_status(f"Outil sélectionné: {tool}")
        
    def on_canvas_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        mode = self.edit_mode.get()
        
        if mode == "text":
            self.add_text_directly(x, y)
        elif mode == "draw":
            self.start_drawing(x, y)
        elif mode == "select":
            self.select_item(x, y)
        elif self.current_tool == "image":
            self.add_image_at_position(x, y)
        elif self.current_tool == "table":
            self.add_table_at_position(x, y)
        else:
            self.start_x = x
            self.start_y = y
            self.drawing = True
            
    def on_canvas_drag(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        mode = self.edit_mode.get()
        
        if mode == "draw" and self.is_drawing:
            self.continue_drawing(x, y)
        elif self.drawing and self.current_tool in ["rectangle", "circle", "line"]:
            if self.current_shape:
                self.canvas.delete(self.current_shape)
            
            if self.current_tool == "rectangle":
                self.current_shape = self.canvas.create_rectangle(
                    self.start_x, self.start_y, x, y, 
                    outline=self.text_color, width=int(self.brush_size_var.get()))
            elif self.current_tool == "circle":
                self.current_shape = self.canvas.create_oval(
                    self.start_x, self.start_y, x, y, 
                    outline=self.text_color, width=int(self.brush_size_var.get()))
            elif self.current_tool == "line":
                self.current_shape = self.canvas.create_line(
                    self.start_x, self.start_y, x, y, 
                    fill=self.text_color, width=int(self.brush_size_var.get()))
                    
    def on_canvas_release(self, event):
        mode = self.edit_mode.get()
        
        if mode == "draw":
            self.stop_drawing()
        elif self.drawing:
            self.drawing = False
            if self.current_shape:
                coords = self.canvas.coords(self.current_shape)
                self.shapes.append({
                    'type': self.current_tool,
                    'coords': coords,
                    'color': self.text_color,
                    'width': int(self.brush_size_var.get()),
                    'id': self.current_shape
                })
                self.update_layer_list()
                self.save_state()
            self.current_shape = None
            
    def on_canvas_motion(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.update_status(f"Position: ({int(x)}, {int(y)})")
        
    def on_canvas_double_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Double-clic pour éditer du texte existant
        item = self.canvas.find_closest(x, y)[0]
        if item and self.canvas.type(item) == "text":
            self.edit_text_item(item, x, y)
    
    # === MÉTHODES DE CRÉATION D'ÉLÉMENTS ===
    
    def add_text_directly(self, x, y):
        # Créer une zone de saisie temporaire
        entry = tk.Entry(self.canvas, font=(self.text_font_var.get(), int(self.text_size_var.get())), 
                        bg="white", fg=self.text_color, relief="solid", bd=1)
        entry_window = self.canvas.create_window(x, y, window=entry, anchor="nw")
        
        entry.focus_set()
        
        def on_entry_return(event):
            text = entry.get()
            if text.strip():
                self.canvas.delete(entry_window)
                text_id = self.canvas.create_text(x, y, text=text, 
                                                font=(self.text_font_var.get(), int(self.text_size_var.get())),
                                                fill=self.text_color, anchor="nw")
                self.shapes.append({
                    'type': 'text',
                    'coords': [x, y],
                    'text': text,
                    'font': (self.text_font_var.get(), int(self.text_size_var.get())),
                    'color': self.text_color,
                    'id': text_id
                })
                self.update_layer_list()
                self.save_state()
            else:
                self.canvas.delete(entry_window)
                
        def on_entry_escape(event):
            self.canvas.delete(entry_window)
            
        def on_entry_focus_out(event):
            on_entry_return(event)
            
        entry.bind("<Return>", on_entry_return)
        entry.bind("<Escape>", on_entry_escape)
        entry.bind("<FocusOut>", on_entry_focus_out)
        
        # Ajuster la taille de l'entry au contenu
        def adjust_entry_size(event):
            content = entry.get()
            if content:
                entry.configure(width=max(10, len(content) + 2))
        
        entry.bind("<KeyRelease>", adjust_entry_size)
        
    def edit_text_item(self, item, x, y):
        # Récupérer le texte actuel
        current_text = self.canvas.itemcget(item, "text")
        current_font = self.canvas.itemcget(item, "font")
        
        # Créer une zone d'édition
        entry = tk.Entry(self.canvas, font=current_font, bg="white", fg=self.text_color, 
                        relief="solid", bd=1)
        entry.insert(0, current_text)
        entry.select_range(0, tk.END)
        
        entry_window = self.canvas.create_window(x, y, window=entry, anchor="nw")
        entry.focus_set()
        
        def on_edit_return(event):
            new_text = entry.get()
            if new_text.strip():
                self.canvas.itemconfig(item, text=new_text)
                # Mettre à jour dans la liste des shapes
                for shape in self.shapes:
                    if shape.get('id') == item:
                        shape['text'] = new_text
                        break
                self.save_state()
            self.canvas.delete(entry_window)
            
        def on_edit_escape(event):
            self.canvas.delete(entry_window)
            
        entry.bind("<Return>", on_edit_return)
        entry.bind("<Escape>", on_edit_escape)
        entry.bind("<FocusOut>", on_edit_return)
        
    def start_drawing(self, x, y):
        self.is_drawing = True
        self.last_x = x
        self.last_y = y
        
    def continue_drawing(self, x, y):
        if self.last_x and self.last_y:
            line_id = self.canvas.create_line(self.last_x, self.last_y, x, y, 
                                            fill=self.text_color, 
                                            width=int(self.brush_size_var.get()),
                                            capstyle=tk.ROUND, 
                                            smooth=True)
            self.shapes.append({
                'type': 'freehand',
                'coords': [self.last_x, self.last_y, x, y],
                'color': self.text_color,
                'width': int(self.brush_size_var.get()),
                'id': line_id
            })
        self.last_x = x
        self.last_y = y
        
    def stop_drawing(self):
        self.is_drawing = False
        self.last_x = None
        self.last_y = None
        if self.shapes:
            self.update_layer_list()
            self.save_state()
            
    def select_item(self, x, y):
        # Déselectionner l'item précédent
        if self.selected_item:
            try:
                self.canvas.itemconfig(self.selected_item, outline="")
            except:
                pass
            
        # Trouver l'item le plus proche
        item = self.canvas.find_closest(x, y)[0]
        if item:
            self.selected_item = item
            # Mettre en évidence l'item sélectionné
            try:
                if self.canvas.type(item) in ["rectangle", "oval", "line"]:
                    self.canvas.itemconfig(item, outline=self.colors['primary'], width=3)
                elif self.canvas.type(item) == "text":
                    bbox = self.canvas.bbox(item)
                    if bbox:
                        x1, y1, x2, y2 = bbox
                        self.canvas.create_rectangle(x1-2, y1-2, x2+2, y2+2, 
                                                   outline=self.colors['primary'], 
                                                   width=2, tags="selection")
            except:
                pass
            self.update_status(f"Item sélectionné: {item}")
            
    def delete_selected(self, event=None):
        if self.selected_item:
            # Supprimer les marqueurs de sélection
            self.canvas.delete("selection")
            
            # Supprimer l'item
            self.canvas.delete(self.selected_item)
            
            # Supprimer de la liste des shapes
            self.shapes = [s for s in self.shapes if s.get('id') != self.selected_item]
            self.images = [i for i in self.images if i.get('id') != self.selected_item]
            
            self.selected_item = None
            self.update_layer_list()
            self.save_state()
            self.update_status("Item supprimé")
            
    def add_image_at_position(self, x, y):
        file_path = filedialog.askopenfilename(
            title="Sélectionner une image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff")]
        )
        if file_path:
            try:
                # Utiliser PIL pour redimensionner l'image si nécessaire
                pil_image = PILImage.open(file_path)
                
                # Redimensionner si l'image est trop grande
                max_size = (300, 300)
                pil_image.thumbnail(max_size, PILImage.Resampling.LANCZOS)
                
                # Convertir pour Tkinter
                img = ImageTk.PhotoImage(pil_image)
                
                img_id = self.canvas.create_image(x, y, image=img, anchor="nw")
                self.images.append({
                    'path': file_path,
                    'coords': [x, y],
                    'image': img,
                    'id': img_id,
                    'pil_image': pil_image
                })
                self.update_layer_list()
                self.save_state()
                self.update_status(f"Image ajoutée: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de charger l'image: {e}")
                
    def add_table_at_position(self, x, y):
        dialog = TableDialog(self.root)
        if dialog.result:
            rows, cols = dialog.result
            table_data = [[''] * cols for _ in range(rows)]
            
            cell_width = 80
            cell_height = 30
            
            table_items = []
            
            for i in range(rows):
                for j in range(cols):
                    cell_x = x + j * cell_width
                    cell_y = y + i * cell_height
                    
                    rect_id = self.canvas.create_rectangle(
                        cell_x, cell_y, cell_x + cell_width, cell_y + cell_height,
                        outline="black", fill="white", tags=f"table_{len(self.tables)}"
                    )
                    
                    text_id = self.canvas.create_text(
                        cell_x + cell_width//2, cell_y + cell_height//2,
                        text=f"Cellule {i+1},{j+1}", font=("Arial", 9),
                        tags=f"table_{len(self.tables)}"
                    )
                    
                    table_items.extend([rect_id, text_id])
                    
            self.tables.append({
                'coords': [x, y],
                'rows': rows,
                'cols': cols,
                'data': table_data,
                'cell_width': cell_width,
                'cell_height': cell_height,
                'items': table_items
            })
            self.update_layer_list()
            self.save_state()
            self.update_status(f"Tableau {rows}x{cols} ajouté")
    
    # === MÉTHODES DE FORMATAGE ===
    
    def toggle_bold(self):
        try:
            if self.text_widget.tag_ranges(tk.SEL):
                current_tags = self.text_widget.tag_names(tk.SEL_FIRST)
                if 'bold' in current_tags:
                    self.text_widget.tag_remove('bold', tk.SEL_FIRST, tk.SEL_LAST)
                else:
                    self.text_widget.tag_add('bold', tk.SEL_FIRST, tk.SEL_LAST)
                    self.text_widget.tag_config('bold', font=(self.font_family, self.font_size, 'bold'))
        except tk.TclError:
            pass
        
    def toggle_italic(self):
        try:
            if self.text_widget.tag_ranges(tk.SEL):
                current_tags = self.text_widget.tag_names(tk.SEL_FIRST)
                if 'italic' in current_tags:
                    self.text_widget.tag_remove('italic', tk.SEL_FIRST, tk.SEL_LAST)
                else:
                    self.text_widget.tag_add('italic', tk.SEL_FIRST, tk.SEL_LAST)
                    self.text_widget.tag_config('italic', font=(self.font_family, self.font_size, 'italic'))
        except tk.TclError:
            pass
        
    def clear_canvas(self):
        result = messagebox.askyesno("Confirmation", "Effacer tout le contenu du canvas ?")
        if result:
            self.canvas.delete("all")
            self.shapes.clear()
            self.images.clear()
            self.tables.clear()
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.selected_item = None
            self.update_layer_list()
            self.update_status("Canvas effacé")
    
    def choose_bg_color(self):
        color = colorchooser.askcolor(title="Couleur de fond")[1]
        if color:
            self.bg_color = color
            self.canvas.configure(bg=color)
            self.update_status(f"Couleur de fond: {color}")
            
    def choose_text_color(self):
        color = colorchooser.askcolor(title="Couleur du texte")[1]
        if color:
            self.text_color = color
            self.text_widget.configure(fg=color)
            self.update_status(f"Couleur du texte: {color}")
            
    def on_font_change(self, event):
        self.font_family = self.font_var.get()
        self.text_widget.configure(font=(self.font_family, self.font_size))
        self.update_status(f"Police: {self.font_family}")
        
    def on_size_change(self, event):
        self.font_size = int(self.size_var.get())
        self.text_widget.configure(font=(self.font_family, self.font_size))
        self.update_status(f"Taille: {self.font_size}")
        
    def on_page_format_change(self, event):
        format_map = {"A4": A4, "Letter": LETTER, "Legal": LEGAL}
        self.page_format = format_map[self.page_format_var.get()]
        self.update_status(f"Format: {self.page_format_var.get()}")
        
    def set_alignment(self, alignment):
        self.text_align = alignment
        align_names = {TA_LEFT: "Gauche", TA_CENTER: "Centre", TA_RIGHT: "Droite", TA_JUSTIFY: "Justifié"}
        self.update_status(f"Alignement: {align_names[alignment]}")
        
    def update_margin(self, margin_attr):
        try:
            spinbox = self.margin_spinboxes[margin_attr]
            value = int(spinbox.get())
            setattr(self, margin_attr, value)
            self.update_status(f"Marge mise à jour: {margin_attr} = {value}")
        except (ValueError, KeyError):
            pass
    
    # === MÉTHODES FICHIERS ===
    
    def new_document(self):
        """Créer un nouveau document"""
        result = messagebox.askyesno("Nouveau document", "Voulez-vous créer un nouveau document ? Les modifications non sauvegardées seront perdues.")
        if result:
            self.canvas.delete("all")
            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert("1.0", "Commencez à taper votre texte ici...\n\nUtilisez les outils pour formater votre document.")
            
            self.shapes.clear()
            self.images.clear()
            self.tables.clear()
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.selected_item = None
            
            # Réinitialiser les paramètres par défaut
            self.bg_color = "#FFFFFF"
            self.text_color = "#000000"
            self.font_family = "Helvetica"
            self.font_size = 12
            
            self.canvas.configure(bg=self.bg_color)
            self.text_widget.configure(fg=self.text_color, font=(self.font_family, self.font_size))
            
            self.update_layer_list()
            self.update_status("Nouveau document créé")
            
    def open_template(self):
        """Ouvrir un template sauvegardé"""
        file_path = filedialog.askopenfilename(
            title="Ouvrir un template",
            filetypes=[("Template JSON", "*.json"), ("Tous les fichiers", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Vérifier la version du template
                version = data.get('version', '1.0')
                if version != '2.0':
                    messagebox.showwarning("Version", "Ce template a été créé avec une version différente. Certaines fonctionnalités peuvent ne pas fonctionner correctement.")
                
                # Créer un nouveau document
                self.new_document()
                
                # Charger les données
                if 'text' in data:
                    self.text_widget.delete("1.0", tk.END)
                    self.text_widget.insert("1.0", data['text'])
                    
                self.bg_color = data.get('bg_color', '#FFFFFF')
                self.text_color = data.get('text_color', '#000000')
                self.font_family = data.get('font_family', 'Helvetica')
                self.font_size = data.get('font_size', 12)
                
                # Charger les marges
                margins = data.get('margins', {})
                self.margin_left = margins.get('left', 50)
                self.margin_right = margins.get('right', 50)
                self.margin_top = margins.get('top', 50)
                self.margin_bottom = margins.get('bottom', 50)
                
                # Mettre à jour les spinboxes des marges
                for attr, spinbox in self.margin_spinboxes.items():
                    spinbox.delete(0, tk.END)
                    spinbox.insert(0, str(getattr(self, attr)))
                
                # Charger les formes
                for shape_data in data.get('shapes', []):
                    shape = self._deserialize_shape(shape_data)
                    self.shapes.append(shape)
                    self.redraw_shape(shape)
                
                # Charger les images
                for img_data in data.get('images', []):
                    img = self._deserialize_image(img_data)
                    if img:
                        self.images.append(img)
                        self.redraw_image(img)
                
                # Charger les tableaux
                for table_data in data.get('tables', []):
                    table = self._deserialize_table(table_data)
                    self.tables.append(table)
                    self.redraw_table(table)
                    
                # Mettre à jour l'interface
                self.canvas.configure(bg=self.bg_color)
                self.text_widget.configure(fg=self.text_color, font=(self.font_family, self.font_size))
                self.font_var.set(self.font_family)
                self.size_var.set(str(self.font_size))
                
                self.update_layer_list()
                self.save_state()
                self.update_status(f"Template chargé: {os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors du chargement du template: {e}")
                
    def save_template(self):
        """Sauvegarder le template actuel"""
        file_path = filedialog.asksaveasfilename(
            title="Sauvegarder le template",
            defaultextension=".json",
            filetypes=[("Template JSON", "*.json"), ("Tous les fichiers", "*.*")]
        )
        if file_path:
            try:
                # Préparer les données à sauvegarder
                shapes_data = [self._serialize_shape(s) for s in self.shapes]
                images_data = [self._serialize_image(i) for i in self.images]
                tables_data = [self._serialize_table(t) for t in self.tables]
                
                data = {
                    'text': self.text_widget.get("1.0", tk.END),
                    'bg_color': self.bg_color,
                    'text_color': self.text_color,
                    'font_family': self.font_family,
                    'font_size': self.font_size,
                    'text_align': self.text_align,
                    'line_spacing': self.line_spacing,
                    'margins': {
                        'left': self.margin_left,
                        'right': self.margin_right,
                        'top': self.margin_top,
                        'bottom': self.margin_bottom
                    },
                    'shapes': shapes_data,
                    'images': images_data,
                    'tables': tables_data,
                    'created_at': datetime.now().isoformat(),
                    'version': '2.0'
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
                self.update_status(f"Template sauvegardé: {os.path.basename(file_path)}")
                messagebox.showinfo("Succès", "Template sauvegardé avec succès!")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde du template: {e}")
    
    # === MÉTHODES PDF ===
    
    def preview_pdf(self):
        """Générer un aperçu du PDF"""
        temp_path = os.path.join(os.path.expanduser("~"), "temp_preview.pdf")
        if self.generate_pdf_file(temp_path):
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(temp_path)
                elif os.name == 'posix':  # macOS/Linux
                    if sys.platform == 'darwin':  # macOS
                        os.system(f'open "{temp_path}"')
                    else:  # Linux
                        os.system(f'xdg-open "{temp_path}"')
                self.update_status("Aperçu généré")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'ouvrir l'aperçu: {e}")
                
    def export_pdf(self):
        """Exporter le document en PDF"""
        file_path = filedialog.asksaveasfilename(
            title="Exporter en PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("Tous les fichiers", "*.*")]
        )
        if file_path:
            if self.generate_pdf_file(file_path):
                messagebox.showinfo("Succès", f"PDF exporté avec succès:\n{file_path}")
                self.update_status(f"PDF exporté: {os.path.basename(file_path)}")
                
    def generate_pdf_file(self, file_path):
        """Générer le fichier PDF"""
        try:
            width, height = self.page_format
            
            # Créer le document PDF
            doc = SimpleDocTemplate(file_path, pagesize=self.page_format,
                                  leftMargin=self.margin_left, rightMargin=self.margin_right,
                                  topMargin=self.margin_top, bottomMargin=self.margin_bottom)
            
            # Contenu du document
            story = []
            
            # Ajouter le texte du widget de texte
            text_content = self.text_widget.get("1.0", tk.END).strip()
            if text_content and text_content != "Commencez à taper votre texte ici...\n\nUtilisez les outils pour formater votre document.":
                # Créer un style de paragraphe
                styles = getSampleStyleSheet()
                style = ParagraphStyle(
                    'CustomStyle',
                    parent=styles['Normal'],
                    fontName=self._get_reportlab_font(self.font_family),
                    fontSize=self.font_size,
                    textColor=HexColor(self.text_color),
                    alignment=self.text_align,
                    leading=self.font_size * self.line_spacing,
                    backColor=HexColor(self.bg_color) if self.bg_color != '#FFFFFF' else None
                )
                
                # Diviser le texte en paragraphes
                paragraphs = text_content.split('\n\n')
                for para_text in paragraphs:
                    if para_text.strip():
                        para = Paragraph(para_text.replace('\n', '<br/>'), style)
                        story.append(para)
                        story.append(Spacer(1, 12))
            
            # Créer un canvas pour dessiner les éléments graphiques
            def draw_graphics(canvas_obj, doc_obj):
                canvas_obj.setFillColor(HexColor(self.bg_color))
                canvas_obj.rect(0, 0, width, height, fill=1)
                
                # Dessiner les éléments du canvas
                if self.shapes or self.images or self.tables:
                    canvas_width = self.canvas.winfo_width()
                    canvas_height = self.canvas.winfo_height()
                    
                    if canvas_width > 0 and canvas_height > 0:
                        # Calculer l'échelle
                        content_width = width - self.margin_left - self.margin_right
                        content_height = height - self.margin_top - self.margin_bottom
                        scale_x = content_width / canvas_width
                        scale_y = content_height / canvas_height
                        scale = min(scale_x, scale_y, 1.0)  # Ne pas agrandir
                        
                        # Dessiner les formes
                        for shape in self.shapes:
                            self.draw_shape_on_pdf(canvas_obj, shape, scale, scale, width, height)
                        
                        # Dessiner les images
                        for img_data in self.images:
                            self.draw_image_on_pdf(canvas_obj, img_data, scale, width, height)
                        
                        # Dessiner les tableaux
                        for table_data in self.tables:
                            self.draw_table_on_pdf(canvas_obj, table_data, scale, width, height)
            
            # Construire le document
            if story:
                doc.build(story, onFirstPage=draw_graphics, onLaterPages=draw_graphics)
            else:
                # Si pas de texte, créer une page vide avec les graphiques
                story.append(Spacer(1, height - self.margin_top - self.margin_bottom))
                doc.build(story, onFirstPage=draw_graphics, onLaterPages=draw_graphics)
            
            return True
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la génération du PDF: {e}")
            return False
            
    def _get_reportlab_font(self, font_family):
        """Convertir le nom de police Tkinter vers ReportLab"""
        font_map = {
            'Arial': 'Helvetica',
            'Times': 'Times-Roman',
            'Courier': 'Courier',
            'Verdana': 'Helvetica',
            'Helvetica': 'Helvetica',
            'Times-Roman': 'Times-Roman'
        }
        return font_map.get(font_family, 'Helvetica')
            
    def draw_shape_on_pdf(self, c, shape, scale_x, scale_y, pdf_width, pdf_height):
        """Dessiner une forme sur le PDF"""
        try:
            # Vérifier que la couleur est valide
            color = shape.get('color', '#000000')
            if not color.startswith('#'):
                color = '#000000'
            
            c.setStrokeColor(HexColor(color))
            line_width = shape.get('width', 2) * min(scale_x, scale_y)
            c.setLineWidth(max(0.5, line_width))

            shape_type = shape['type']
            coords = shape['coords']

            if shape_type == 'rectangle' and len(coords) >= 4:
                x1, y1, x2, y2 = coords
                pdf_x1 = self.margin_left + x1 * scale_x
                pdf_y1 = pdf_height - self.margin_top - y1 * scale_y
                pdf_x2 = self.margin_left + x2 * scale_x
                pdf_y2 = pdf_height - self.margin_top - y2 * scale_y

                c.rect(min(pdf_x1, pdf_x2), min(pdf_y1, pdf_y2),
                      abs(pdf_x2 - pdf_x1), abs(pdf_y2 - pdf_y1), fill=0)

            elif shape_type == 'circle' and len(coords) >= 4:
                x1, y1, x2, y2 = coords
                center_x = self.margin_left + ((x1 + x2) / 2) * scale_x
                center_y = pdf_height - self.margin_top - ((y1 + y2) / 2) * scale_y
                radius_x = abs(x2 - x1) / 2 * scale_x
                radius_y = abs(y2 - y1) / 2 * scale_y

                c.ellipse(center_x - radius_x, center_y - radius_y,
                         center_x + radius_x, center_y + radius_y, fill=0)

            elif shape_type in ['line', 'freehand']:
                if len(coords) >= 4:
                    x1, y1, x2, y2 = coords[:4]
                    pdf_x1 = self.margin_left + x1 * scale_x
                    pdf_y1 = pdf_height - self.margin_top - y1 * scale_y
                    pdf_x2 = self.margin_left + x2 * scale_x
                    pdf_y2 = pdf_height - self.margin_top - y2 * scale_y

                    c.line(pdf_x1, pdf_y1, pdf_x2, pdf_y2)

            elif shape_type == 'text':
                if len(coords) >= 2:
                    x, y = coords[:2]
                    pdf_x = self.margin_left + x * scale_x
                    pdf_y = pdf_height - self.margin_top - y * scale_y

                    # Vérifier que la couleur est valide
                    color = shape.get('color', '#000000')
                    if not color.startswith('#'):
                        color = '#000000'
                    
                    c.setFillColor(HexColor(color))
                    font_name, font_size = shape.get('font', ('Helvetica', 12))
                    scaled_font_size = max(6, int(font_size * min(scale_x, scale_y)))
                    c.setFont(self._get_reportlab_font(font_name), scaled_font_size)
                    
                    # S'assurer que le texte n'est pas None
                    text = shape.get('text', '')
                    if text is None:
                        text = ''
                    c.drawString(pdf_x, pdf_y, str(text))

        except Exception as e:
            print(f"Erreur lors du dessin de la forme: {e}")
            
    def draw_image_on_pdf(self, c, img_data, scale, pdf_width, pdf_height):
        """Dessiner une image sur le PDF"""
        try:
            x, y = img_data['coords']
            img_path = img_data['path']
            
            if os.path.exists(img_path):
                pdf_x = self.margin_left + x * scale
                pdf_y = pdf_height - self.margin_top - y * scale
                
                # Taille par défaut de l'image
                img_width = 100 * scale
                img_height = 100 * scale
                
                c.drawImage(img_path, pdf_x, pdf_y - img_height, 
                           width=img_width, height=img_height, preserveAspectRatio=True)
                
        except Exception as e:
            print(f"Erreur lors du dessin de l'image: {e}")
            
    def draw_table_on_pdf(self, c, table_data, scale, pdf_width, pdf_height):
        """Dessiner un tableau sur le PDF"""
        try:
            x, y = table_data['coords']
            rows, cols = table_data['rows'], table_data['cols']
            cell_width, cell_height = table_data['cell_width'], table_data['cell_height']
            
            scaled_cell_width = cell_width * scale
            scaled_cell_height = cell_height * scale
            
            c.setStrokeColor(HexColor("#000000"))
            c.setFillColor(HexColor("#000000"))
            c.setLineWidth(1)
            
            for i in range(rows):
                for j in range(cols):
                    cell_x = self.margin_left + (x + j * cell_width) * scale
                    cell_y = pdf_height - self.margin_top - (y + (i + 1) * cell_height) * scale
                    
                    # Dessiner la cellule
                    c.rect(cell_x, cell_y, scaled_cell_width, scaled_cell_height, fill=0)
                    
                    # Dessiner le texte
                    cell_text = table_data['data'][i][j] if table_data['data'][i][j] else f"Cellule {i+1},{j+1}"
                    c.setFont("Helvetica", max(6, int(8 * scale)))
                    text_x = cell_x + scaled_cell_width / 2
                    text_y = cell_y + scaled_cell_height / 2
                    c.drawCentredString(text_x, text_y, cell_text)
                    
        except Exception as e:
            print(f"Erreur lors du dessin du tableau: {e}")
    
    # === MÉTHODES D'ÉDITION ===
    
    def copy_text(self):
        """Copier le texte sélectionné"""
        try:
            if self.text_widget.tag_ranges(tk.SEL):
                self.text_widget.clipboard_clear()
                self.text_widget.clipboard_append(self.text_widget.selection_get())
                self.update_status("Texte copié")
        except tk.TclError:
            pass
            
    def paste_text(self):
        """Coller le texte du presse-papiers"""
        try:
            clipboard_text = self.text_widget.clipboard_get()
            if self.text_widget.tag_ranges(tk.SEL):
                self.text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.text_widget.insert(tk.INSERT, clipboard_text)
            self.update_status("Texte collé")
        except tk.TclError:
            pass
            
    def select_all(self):
        """Sélectionner tout le texte"""
        self.text_widget.tag_add(tk.SEL, "1.0", tk.END)
        self.text_widget.mark_set(tk.INSERT, "1.0")
        self.text_widget.see(tk.INSERT)
        
    def zoom_in(self):
        """Augmenter la taille de la police"""
        current_font = self.text_widget.cget('font')
        if isinstance(current_font, tuple):
            family, size = current_font[0], current_font[1]
        else:
            family, size = self.font_family, self.font_size
        new_size = min(size + 2, 72)
        self.text_widget.configure(font=(family, new_size))
        self.font_size = new_size
        self.size_var.set(str(new_size))
        self.update_status(f"Zoom: {new_size}pt")
        
    def zoom_out(self):
        """Diminuer la taille de la police"""
        current_font = self.text_widget.cget('font')
        if isinstance(current_font, tuple):
            family, size = current_font[0], current_font[1]
        else:
            family, size = self.font_family, self.font_size
        new_size = max(size - 2, 8)
        self.text_widget.configure(font=(family, new_size))
        self.font_size = new_size
        self.size_var.set(str(new_size))
        self.update_status(f"Zoom: {new_size}pt")
        
    def fit_to_window(self):
        """Réinitialiser le zoom"""
        self.text_widget.configure(font=(self.font_family, 12))
        self.font_size = 12
        self.size_var.set("12")
        self.update_status("Zoom réinitialisé")
    
    # === MÉTHODES DE GESTION DES CALQUES ===
        
    def update_layer_list(self):
        self.layer_listbox.delete(0, tk.END)
        
        # Ajouter les formes
        for i, shape in enumerate(self.shapes):
            layer_name = f"Forme {i+1} ({shape['type']})"
            if shape['type'] == 'text' and 'text' in shape:
                preview = shape['text'][:20] + "..." if len(shape['text']) > 20 else shape['text']
                layer_name = f"Texte {i+1}: {preview}"
            self.layer_listbox.insert(tk.END, layer_name)
            
        # Ajouter les images
        for i, img in enumerate(self.images):
            filename = os.path.basename(img['path'])
            layer_name = f"Image {i+1}: {filename}"
            self.layer_listbox.insert(tk.END, layer_name)
            
        # Ajouter les tableaux
        for i, table in enumerate(self.tables):
            layer_name = f"Tableau {i+1} ({table['rows']}x{table['cols']})"
            self.layer_listbox.insert(tk.END, layer_name)
            
    def add_layer(self):
        """Ajouter un nouveau calque"""
        self.update_status("Utilisez les outils pour ajouter des éléments")
        
    def remove_layer(self):
        selection = self.layer_listbox.curselection()
        if selection:
            index = selection[0]
            total_shapes = len(self.shapes)
            total_images = len(self.images)
            
            if index < total_shapes:
                # Supprimer une forme
                shape = self.shapes[index]
                if 'id' in shape:
                    self.canvas.delete(shape['id'])
                del self.shapes[index]
            elif index < total_shapes + total_images:
                # Supprimer une image
                img_index = index - total_shapes
                img = self.images[img_index]
                if 'id' in img:
                    self.canvas.delete(img['id'])
                del self.images[img_index]
            else:
                # Supprimer un tableau
                table_index = index - total_shapes - total_images
                if table_index < len(self.tables):
                    table = self.tables[table_index]
                    # Supprimer tous les éléments du tableau
                    for item_id in table.get('items', []):
                        self.canvas.delete(item_id)
                    del self.tables[table_index]
                    
            self.update_layer_list()
            self.save_state()
            self.update_status("Calque supprimé")
                
    def move_layer_up(self):
        """Déplacer un calque vers le haut"""
        selection = self.layer_listbox.curselection()
        if selection and selection[0] > 0:
            index = selection[0]
            total_shapes = len(self.shapes)
            total_images = len(self.images)
            
            if index < total_shapes and index > 0:
                # Déplacer une forme
                self.shapes[index-1], self.shapes[index] = self.shapes[index], self.shapes[index-1]
                self.update_layer_list()
                self.layer_listbox.selection_set(index-1)
                self.update_status("Calque déplacé vers le haut")
        
    def move_layer_down(self):
        """Déplacer un calque vers le bas"""
        selection = self.layer_listbox.curselection()
        if selection:
            index = selection[0]
            total_shapes = len(self.shapes)
            total_images = len(self.images)
            total_items = total_shapes + total_images + len(self.tables)
            
            if index < total_items - 1:
                if index < total_shapes - 1:
                    # Déplacer une forme
                    self.shapes[index], self.shapes[index+1] = self.shapes[index+1], self.shapes[index]
                    self.update_layer_list()
                    self.layer_listbox.selection_set(index+1)
                    self.update_status("Calque déplacé vers le bas")
    
    # === MÉTHODES UNDO/REDO ===
        
    def save_state(self):
        """Sauvegarder l'état actuel pour l'undo/redo"""
        try:
            state = {
                'shapes': [self._serialize_shape(s) for s in self.shapes],
                'images': [self._serialize_image(i) for i in self.images],
                'tables': [self._serialize_table(t) for t in self.tables],
                'text': self.text_widget.get("1.0", tk.END),
                'bg_color': self.bg_color,
                'text_color': self.text_color,
                'font_family': self.font_family,
                'font_size': self.font_size
            }
            self.undo_stack.append(state)
            self.redo_stack.clear()
            if len(self.undo_stack) > 50:
                self.undo_stack.pop(0)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de l'état: {e}")
            
    def _serialize_shape(self, shape):
        """Sérialiser une forme pour la sauvegarde"""
        serialized = {
            'type': shape['type'],
            'coords': shape['coords'],
            'color': shape['color']
        }
        if 'text' in shape:
            serialized['text'] = shape['text']
        if 'font' in shape:
            serialized['font'] = shape['font']
        if 'width' in shape:
            serialized['width'] = shape['width']
        return serialized
        
    def _serialize_image(self, img):
        """Sérialiser une image pour la sauvegarde"""
        return {
            'path': img['path'],
            'coords': img['coords']
        }
        
    def _serialize_table(self, table):
        """Sérialiser un tableau pour la sauvegarde"""
        return {
            'coords': table['coords'],
            'rows': table['rows'],
            'cols': table['cols'],
            'data': table['data'],
            'cell_width': table['cell_width'],
            'cell_height': table['cell_height']
        }
            
    def undo(self):
        if self.undo_stack:
            try:
                current_state = {
                    'shapes': [self._serialize_shape(s) for s in self.shapes],
                    'images': [self._serialize_image(i) for i in self.images],
                    'tables': [self._serialize_table(t) for t in self.tables],
                    'text': self.text_widget.get("1.0", tk.END),
                    'bg_color': self.bg_color,
                    'text_color': self.text_color,
                    'font_family': self.font_family,
                    'font_size': self.font_size
                }
                self.redo_stack.append(current_state)
                
                prev_state = self.undo_stack.pop()
                self.restore_state(prev_state)
                self.update_status("Annulation effectuée")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'annulation: {e}")
            
    def redo(self):
        if self.redo_stack:
            try:
                current_state = {
                    'shapes': [self._serialize_shape(s) for s in self.shapes],
                    'images': [self._serialize_image(i) for i in self.images],
                    'tables': [self._serialize_table(t) for t in self.tables],
                    'text': self.text_widget.get("1.0", tk.END),
                    'bg_color': self.bg_color,
                    'text_color': self.text_color,
                    'font_family': self.font_family,
                    'font_size': self.font_size
                }
                self.undo_stack.append(current_state)
                
                next_state = self.redo_stack.pop()
                self.restore_state(next_state)
                self.update_status("Rétablissement effectué")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors du rétablissement: {e}")
            
    def restore_state(self, state):
        """Restaurer un état sauvegardé"""
        try:
            # Effacer le canvas
            self.canvas.delete("all")
            
            # Restaurer les propriétés
            self.bg_color = state['bg_color']
            self.text_color = state['text_color']
            self.font_family = state['font_family']
            self.font_size = state['font_size']
            
            # Restaurer le texte
            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert("1.0", state['text'])
            
            # Restaurer les formes
            self.shapes = []
            for shape_data in state['shapes']:
                self.shapes.append(self._deserialize_shape(shape_data))
                
            # Restaurer les images
            self.images = []
            for img_data in state['images']:
                restored_img = self._deserialize_image(img_data)
                if restored_img:
                    self.images.append(restored_img)
                    
            # Restaurer les tableaux
            self.tables = []
            for table_data in state['tables']:
                self.tables.append(self._deserialize_table(table_data))
                
            # Redessiner tout
            for shape in self.shapes:
                self.redraw_shape(shape)
            for image in self.images:
                self.redraw_image(image)
            for table in self.tables:
                self.redraw_table(table)
                
            self.update_layer_list()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la restauration: {e}")
            
    def _deserialize_shape(self, shape_data):
        """Désérialiser une forme"""
        return {
            'type': shape_data['type'],
            'coords': shape_data['coords'],
            'color': shape_data['color'],
            'text': shape_data.get('text', ''),
            'font': shape_data.get('font', ('Arial', 12)),
            'width': shape_data.get('width', 2),
            'id': None  # Sera assigné lors du redessin
        }
        
    def _deserialize_image(self, img_data):
        """Désérialiser une image"""
        try:
            if os.path.exists(img_data['path']):
                pil_image = PILImage.open(img_data['path'])
                max_size = (300, 300)
                pil_image.thumbnail(max_size, PILImage.Resampling.LANCZOS)
                img = ImageTk.PhotoImage(pil_image)
                
                return {
                    'path': img_data['path'],
                    'coords': img_data['coords'],
                    'image': img,
                    'pil_image': pil_image,
                    'id': None  # Sera assigné lors du redessin
                }
        except Exception as e:
            print(f"Erreur lors de la restauration de l'image {img_data['path']}: {e}")
        return None
        
    def _deserialize_table(self, table_data):
        """Désérialiser un tableau"""
        return {
            'coords': table_data['coords'],
            'rows': table_data['rows'],
            'cols': table_data['cols'],
            'data': table_data['data'],
            'cell_width': table_data['cell_width'],
            'cell_height': table_data['cell_height'],
            'items': []  # Sera rempli lors du redessin
        }
        
    def redraw_shape(self, shape):
        """Redessiner une forme sur le canvas"""
        try:
            if shape['type'] == 'rectangle':
                shape['id'] = self.canvas.create_rectangle(
                    *shape['coords'], outline=shape['color'], width=shape.get('width', 2))
            elif shape['type'] == 'circle':
                shape['id'] = self.canvas.create_oval(
                    *shape['coords'], outline=shape['color'], width=shape.get('width', 2))
            elif shape['type'] in ['line', 'freehand']:
                shape['id'] = self.canvas.create_line(
                    *shape['coords'], fill=shape['color'], width=shape.get('width', 2))
            elif shape['type'] == 'text':
                shape['id'] = self.canvas.create_text(
                    *shape['coords'], text=shape.get('text', ''), 
                    font=shape.get('font', ('Arial', 12)), 
                    fill=shape['color'], anchor="nw")
        except Exception as e:
            print(f"Erreur lors du redessin de la forme: {e}")
    
    def redraw_image(self, image):
        """Redessiner une image sur le canvas"""
        try:
            x, y = image['coords']
            img = image['image']
            image['id'] = self.canvas.create_image(x, y, image=img, anchor="nw")
        except Exception as e:
            print(f"Erreur lors du redessin de l'image: {e}")
    
    def redraw_table(self, table):
        """Redessiner un tableau sur le canvas"""
        x, y = table['coords']
        rows, cols = table['rows'], table['cols']
        cell_width, cell_height = table['cell_width'], table['cell_height']
        
        table_items = []
        for i in range(rows):
            for j in range(cols):
                cell_x = x + j * cell_width
                cell_y = y + i * cell_height
                
                rect_id = self.canvas.create_rectangle(
                    cell_x, cell_y, cell_x + cell_width, cell_y + cell_height,
                    outline="black", fill="white")
                
                text_id = self.canvas.create_text(
                    cell_x + cell_width//2, cell_y + cell_height//2,
                    text=f"Cellule {i+1},{j+1}", font=("Arial", 9))
                
                table_items.extend([rect_id, text_id])
        
        table['items'] = table_items
    
    # === MÉTHODES UTILITAIRES ===
    
    def update_status(self, message):
        """Mettre à jour la barre de statut"""
        self.status_bar.configure(text=message)
        self.root.after(3000, lambda: self.status_bar.configure(text="Prêt"))
        
    def create_tooltip(self, widget, text):
        """Créer une infobulle pour un widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="lightyellow", 
                           relief="solid", borderwidth=1, font=("Arial", 9))
            label.pack()
            widget.tooltip = tooltip
            
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
                
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)


class TextDialog:
    """Dialogue pour saisir du texte"""
    def __init__(self, parent, font_family="Arial", font_size=12, color="#000000"):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Ajouter du texte")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrer la fenêtre
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        tk.Label(self.dialog, text="Entrez votre texte:", font=('Arial', 12, 'bold')).pack(pady=10)
        
        self.text_entry = tk.Text(self.dialog, height=8, width=50, font=(font_family, font_size))
        self.text_entry.pack(padx=20, pady=10, fill="both", expand=True)
        
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="OK", command=self.ok_clicked, 
                 bg="#3498db", fg="white", padx=20).pack(side="left", padx=10)
        tk.Button(button_frame, text="Annuler", command=self.cancel_clicked,
                 bg="#e74c3c", fg="white", padx=20).pack(side="left", padx=10)
        
        self.text_entry.focus_set()
        
        # Gérer la fermeture de la fenêtre
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel_clicked)
        
        self.dialog.wait_window()
        
    def ok_clicked(self):
        self.result = self.text_entry.get("1.0", tk.END).strip()
        self.dialog.destroy()
        
    def cancel_clicked(self):
        self.result = None
        self.dialog.destroy()


class TableDialog:
    """Dialogue pour créer un tableau"""
    def __init__(self, parent):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Créer un tableau")
        self.dialog.geometry("300x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrer la fenêtre
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        tk.Label(self.dialog, text="Configuration du tableau", 
                font=('Arial', 12, 'bold')).pack(pady=10)
        
        frame = tk.Frame(self.dialog)
        frame.pack(pady=20)
        
        tk.Label(frame, text="Lignes:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.rows_spinbox = tk.Spinbox(frame, from_=1, to=20, width=10, value=3)
        self.rows_spinbox.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(frame, text="Colonnes:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.cols_spinbox = tk.Spinbox(frame, from_=1, to=10, width=10, value=3)
        self.cols_spinbox.grid(row=1, column=1, padx=10, pady=5)
        
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Créer", command=self.ok_clicked,
                 bg="#27ae60", fg="white", padx=20).pack(side="left", padx=10)
        tk.Button(button_frame, text="Annuler", command=self.cancel_clicked,
                 bg="#e74c3c", fg="white", padx=20).pack(side="left", padx=10)
        
        # Gérer la fermeture de la fenêtre
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel_clicked)
        
        self.dialog.wait_window()
        
    def ok_clicked(self):
        try:
            rows = int(self.rows_spinbox.get())
            cols = int(self.cols_spinbox.get())
            if rows < 1 or cols < 1:
                raise ValueError("Les valeurs doivent être positives")
            self.result = (rows, cols)
        except ValueError as e:
            messagebox.showerror("Erreur", f"Veuillez entrer des nombres valides: {e}")
            return
        self.dialog.destroy()
        
    def cancel_clicked(self):
        self.result = None
        self.dialog.destroy()


def main():
    """Fonction principale avec gestion d'erreur robuste"""
    try:
        # Vérifier les dépendances
        try:
            import tkinter as tk
            from tkinter import ttk
        except ImportError:
            print("Erreur: tkinter n'est pas installé")
            return
            
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
        except ImportError:
            print("Erreur: reportlab n'est pas installé. Installez-le avec: pip install reportlab")
            return
            
        try:
            from PIL import Image as PILImage, ImageTk
        except ImportError:
            print("Erreur: Pillow n'est pas installé. Installez-le avec: pip install Pillow")
            return
        
        root = tk.Tk()
        
        # Configuration de la fenêtre principale
        try:
            if os.name == 'nt':  # Windows
                root.state('zoomed')
            else:  # Linux/Mac
                root.attributes('-zoomed', True)
        except:
            # Fallback si les méthodes de maximisation ne fonctionnent pas
            root.geometry("1400x900")
        
        # Créer l'application
        app = AdvancedPDFEditor(root)
        
        # Démarrer la boucle principale
        root.mainloop()
        
    except Exception as e:
        print(f"Erreur fatale: {e}")
        try:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Erreur fatale", f"Une erreur fatale s'est produite: {e}")
        except:
            print("Impossible d'afficher la boîte de dialogue d'erreur")


if __name__ == "__main__":
    main()