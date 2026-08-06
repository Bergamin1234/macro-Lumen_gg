import logging
import threading
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from main import MacroEngine


class TextHandler(logging.Handler):
    """Redireciona os logs do sistema diretamente para a janela da aplicação."""
    def __init__(self, text_widget: scrolledtext.ScrolledText) -> None:
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        def append() -> None:
            self.text_widget.configure(state="normal")
            self.text_widget.insert(tk.END, msg + "\n")
            self.text_widget.see(tk.END)
            self.text_widget.configure(state="disabled")
        self.text_widget.after(0, append)


class LumenaGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Lumena.gg - Macro Automation")
        self.root.geometry("500x580")
        self.root.resizable(False, False)

        self.engine = MacroEngine()

        self._build_interface()
        self._setup_logging()

    def _build_interface(self) -> None:
        # --- Painel de Controle Principal ---
        frame_control = ttk.LabelFrame(self.root, text=" Controles ", padding=10)
        frame_control.pack(fill="x", padx=10, pady=5)

        self.btn_toggle = tk.Button(
            frame_control,
            text="▶ INICIAR MACRO",
            bg="#4CAF50",
            fg="white",
            font=("Arial", 11, "bold"),
            height=2,
            command=self.toggle_macro,
        )
        self.btn_toggle.pack(fill="x", pady=2)

        # --- Painel de Configurações ---
        frame_config = ttk.LabelFrame(self.root, text=" Configurações Rápidas ", padding=10)
        frame_config.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_config, text="Padrão de Movimento:").grid(row=0, column=0, sticky="w", pady=5)
        self.combo_pattern = ttk.Combobox(
            frame_config,
            values=["zigzag", "square", "random", "custom"],
            state="readonly",
            width=15,
        )
        self.combo_pattern.set(self.engine.config.movement_pattern)
        self.combo_pattern.grid(row=0, column=1, sticky="e", padx=10, pady=5)
        self.combo_pattern.bind("<<ComboboxSelected>>", self.change_pattern)

        # --- Painel de Ferramentas ---
        frame_tools = ttk.LabelFrame(self.root, text=" Ferramentas de Visão ", padding=10)
        frame_tools.pack(fill="x", padx=10, pady=5)

        btn_test = ttk.Button(frame_tools, text="🔍 Testar Visão", command=self.test_recognition)
        btn_test.pack(side="left", expand=True, fill="x", padx=3)

        btn_capture = ttk.Button(frame_tools, text="📷 Capturar Template Visual", command=self.capture_template_dialog)
        btn_capture.pack(side="right", expand=True, fill="x", padx=3)

        # --- Painel de Logs em Tempo Real ---
        frame_log = ttk.LabelFrame(self.root, text=" Console de Saída ", padding=10)
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            frame_log, state="disabled", height=12, font=("Consolas", 9)
        )
        self.log_text.pack(fill="both", expand=True)

    def _setup_logging(self) -> None:
        handler = TextHandler(self.log_text)
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s]: %(message)s", "%H:%M:%S")
        handler.setFormatter(formatter)
        logging.getLogger("LumenaMacro").addHandler(handler)

    def toggle_macro(self) -> None:
        if not self.engine.running:
            self.engine.start_macro()
            self.btn_toggle.config(text="⏹ PARAR MACRO", bg="#F44336")
        else:
            self.engine.stop_macro()
            self.btn_toggle.config(text="▶ INICIAR MACRO", bg="#4CAF50")

    def change_pattern(self, event: tk.Event) -> None:
        new_pattern = self.combo_pattern.get()
        self.engine.config.movement_pattern = new_pattern
        self.engine.config.save_to_json()
        self.engine.logger.info(f"Padrão alterado para: '{new_pattern}'")

    def test_recognition(self) -> None:
        threading.Thread(target=self._run_test, daemon=True).start()

    def _run_test(self) -> None:
        self.engine.logger.info("Iniciando verificação de imagens na tela...")
        self.engine.vision.load_templates()
        for tname in self.engine.vision.templates.keys():
            res = self.engine.vision.find_template(tname)
            if res:
                self.engine.logger.info(f"[ENCONTRADO] '{tname}' nas coordenadas X={res[0]}, Y={res[1]}")
            else:
                self.engine.logger.warning(f"[NÃO ENCONTRADO] '{tname}'")

    def capture_template_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Novo Template")
        dialog.geometry("320x130")
        dialog.resizable(False, False)
        dialog.grab_set()

        ttk.Label(dialog, text="Nome do botão/imagem (ex: fight_button):").pack(pady=8)
        entry = ttk.Entry(dialog, width=30)
        entry.pack(pady=2)

        def start_capture() -> None:
            name = entry.get().strip()
            dialog.destroy()
            if name:
                threading.Thread(target=self._run_capture, args=(name,), daemon=True).start()

        ttk.Button(dialog, text="Iniciar Seleção", command=start_capture).pack(pady=10)

    def _run_capture(self, name: str) -> None:
        self.engine.logger.info("Mude para o jogo! A tela congelará em 3 segundos...")
        time.sleep(3.0)
        success = self.engine.vision.capture_template_interactive(name)
        if success:
            self.engine.logger.info(f"Template '{name}.png' criado com sucesso!")


if __name__ == "__main__":
    root = tk.Tk()
    app = LumenaGUI(root)
    root.mainloop()