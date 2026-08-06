import logging
import threading
import time
import tkinter as tk
from tkinter import scrolledtext, ttk

from main import MacroEngine


class TextHandler(logging.Handler):
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
        self.root.geometry("520x620")
        self.root.resizable(False, False)

        self.engine = MacroEngine()

        self._build_interface()
        self._setup_logging()

    def _build_interface(self) -> None:
        # --- Assistente Guiado ---
        frame_wizard = ttk.LabelFrame(self.root, text=" Configuração de Combate ", padding=10)
        frame_wizard.pack(fill="x", padx=10, pady=5)

        btn_wizard = tk.Button(
            frame_wizard,
            text="🧙 INICIAR REGISTRO DE COMBATE (2 PASSOS)",
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
            height=2,
            command=self.open_wizard,
        )
        btn_wizard.pack(fill="x")

        # --- Controles ---
        frame_control = ttk.LabelFrame(self.root, text=" Controles do Bot ", padding=10)
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

        # --- Movimento ---
        frame_config = ttk.LabelFrame(self.root, text=" Opções de Movimento ", padding=10)
        frame_config.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_config, text="Padrão de Caminhada:").grid(row=0, column=0, sticky="w", pady=5)
        self.combo_pattern = ttk.Combobox(
            frame_config,
            values=["zigzag", "square_large", "square_small", "random", "custom"],
            state="readonly",
            width=18,
        )
        self.combo_pattern.set(self.engine.config.movement_pattern)
        self.combo_pattern.grid(row=0, column=1, sticky="e", padx=10, pady=5)
        self.combo_pattern.bind("<<ComboboxSelected>>", self.change_pattern)

        # --- Logs ---
        frame_log = ttk.LabelFrame(self.root, text=" Log de Execução ", padding=10)
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

    def open_wizard(self) -> None:
        wiz = tk.Toplevel(self.root)
        wiz.title("Passo 1: Botão FIGHT")
        wiz.geometry("450x280")
        wiz.resizable(False, False)
        wiz.grab_set()

        lbl = ttk.Label(wiz, text="PASSO 1: CAPTURAR BOTÃO FIGHT", font=("Arial", 10, "bold"))
        lbl.pack(pady=10)

        txt = tk.Text(wiz, height=5, width=50, wrap="word", font=("Arial", 9))
        txt.pack(pady=5, padx=10)
        txt.insert("1.0", "1. Mude para o jogo durante uma batalha.\n2. Quando o botão vermelho FIGHT aparecer, clique abaixo.\n3. Selecione o botão FIGHT com o mouse e aperte ENTER.")
        txt.config(state="disabled")

        def cap1():
            wiz.destroy()
            threading.Thread(target=self._exec_step_1, daemon=True).start()

        tk.Button(wiz, text="📷 CAPTURAR FIGHT", bg="#FF9800", fg="white", font=("Arial", 10, "bold"), command=cap1).pack(pady=10)

    def _exec_step_1(self) -> None:
        self.engine.logger.info("Mude para o jogo! Congelando em 3s...")
        time.sleep(3.0)
        if self.engine.vision.capture_template_interactive("fight_button"):
            self.engine.logger.info("FIGHT capturado!")
            self.root.after(500, self._open_wizard_step_2)

    def _open_wizard_step_2(self) -> None:
        wiz = tk.Toplevel(self.root)
        wiz.title("Passo 2: Barra de HP Inimiga")
        wiz.geometry("450x280")
        wiz.resizable(False, False)
        wiz.grab_set()

        lbl = ttk.Label(wiz, text="PASSO 2: BARRA DE HP DO INIMIGO", font=("Arial", 10, "bold"))
        lbl.pack(pady=10)

        txt = tk.Text(wiz, height=5, width=50, wrap="word", font=("Arial", 9))
        txt.pack(pady=5, padx=10)
        txt.insert("1.0", "1. Durante a batalha, selecione a BARRA VERDE DE HP do Pokémon inimigo (no canto superior direito da tela).\n2. Isso garante que o bot saiba que está em combate mesmo quando o menu mudar.")
        txt.config(state="disabled")

        def cap2():
            wiz.destroy()
            threading.Thread(target=self._exec_step_2, daemon=True).start()

        tk.Button(wiz, text="📷 CAPTURAR BARRA DE HP", bg="#FF9800", fg="white", font=("Arial", 10, "bold"), command=cap2).pack(pady=10)

    def _exec_step_2(self) -> None:
        self.engine.logger.info("Mude para o jogo! Congelando em 3s...")
        time.sleep(3.0)
        if self.engine.vision.capture_template_interactive("enemy_hp"):
            self.engine.logger.info("HP Inimigo registrado! Bot pronto!")


if __name__ == "__main__":
    root = tk.Tk()
    app = LumenaGUI(root)
    root.mainloop()