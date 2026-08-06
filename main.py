import os
import time
import logging
import threading
import cv2
from config import Config
from vision import VisionSystem
from input_controller import InputController
from movement import MovementController
from battle import BattleController


def setup_logging(logs_dir: str) -> None:
    os.makedirs(logs_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(logs_dir, "macro.log"), encoding="utf-8"),
            logging.StreamHandler()
        ]
    )


class LumenaMacroApp:
    def __init__(self) -> None:
        self.config = Config.load_from_json()
        setup_logging(self.config.logs_dir)
        self.logger = logging.getLogger("LumenaMacro")

        self.vision = VisionSystem(
            templates_dir=self.config.templates_dir,
            confidence=self.config.confidence,
            monitor_index=self.config.monitor
        )
        self.input_ctrl = InputController()
        self.movement = MovementController(self.config, self.input_ctrl)
        self.battle = BattleController(self.config, self.vision, self.input_ctrl)

        self.is_running = False
        self.macro_thread: threading.Thread | None = None

    def _macro_loop(self) -> None:
        self.logger.info("Loop da macro iniciado.")
        while self.is_running:
            try:
                if self.battle.in_battle():
                    self.battle.handle_battle()
                else:
                    self.movement.execute_step()
                time.sleep(0.02)
            except Exception as e:
                self.logger.error(f"Erro de execução capturado: {e}")
                time.sleep(1.0)

    def start_macro(self) -> None:
        if not self.is_running:
            self.is_running = True
            self.macro_thread = threading.Thread(target=self._macro_loop, daemon=True)
            self.macro_thread.start()
            print("\n[+] Macro INICIADA com sucesso.")

    def stop_macro(self) -> None:
        if self.is_running:
            self.is_running = False
            if self.macro_thread and self.macro_thread.is_alive():
                self.macro_thread.join(timeout=2.0)
            print("\n[-] Macro PARADA com sucesso.")

    def test_vision(self) -> None:
        print("\n--- TESTANDO VISÃO COMPUTACIONAL ---")
        screenshot = self.vision.get_screenshot()
        if not self.vision.templates:
            print("[!] NENHUM TEMPLATE ENCONTRADO na pasta de templates.")
            return

        for name in self.vision.templates.keys():
            match = self.vision.find_template(name, screenshot=screenshot)
            if match:
                print(f"[OK] Template '{name}' ENCONTRADO em: {match}")
            else:
                print(f"[X] Template '{name}' NÃO encontrado.")

    def capture_template(self) -> None:
        print("\n--- CAPTURA DE NOVO TEMPLATE ---")
        filename = input("Nome do arquivo (ex: fight_button.png): ").strip()
        if not filename.endswith((".png", ".jpg")):
            filename += ".png"

        print("Aguarde 3 segundos para alterar a janela para o jogo...")
        time.sleep(3)
        screenshot = self.vision.get_screenshot()
        save_path = os.path.join(self.config.templates_dir, filename)
        cv2.imwrite(save_path, screenshot)
        self.vision.load_templates()
        print(f"[+] Captura inteira salva em '{save_path}'. Recorte o elemento visual exato usando um editor de imagem.")

    def show_settings(self) -> None:
        print("\n--- CONFIGURAÇÕES ---")
        print(f"Modo de Padrão de Movimento: {self.config.movement_pattern}")
        print(f"Limiar de Confiança da Visão: {self.config.confidence}")
        print(f"Duração de Cada Passo: {self.config.step_duration}s")
        print(f"Timeout Máximo de Batalha: {self.config.battle_timeout}s")
        print(f"Monitor Selecionado: {self.config.monitor}")

    def menu(self) -> None:
        while True:
            status_str = "EXECUTANDO" if self.is_running else "PARADO"
            print("\n==================================")
            print(f"   LUMENA.GG MACRO BOT [{status_str}]")
            print("==================================")
            print("1 - Alternar Macro (Iniciar / Parar)")
            print("2 - Exibir Configurações")
            print("3 - Testar Reconhecimento Visual")
            print("4 - Capturar Template de Tela")
            print("5 - Sair")
            
            choice = input("Escolha uma opção: ").strip()

            if choice == "1":
                if self.is_running:
                    self.stop_macro()
                else:
                    self.start_macro()
            elif choice == "2":
                self.show_settings()
            elif choice == "3":
                self.test_vision()
            elif choice == "4":
                self.capture_template()
            elif choice == "5":
                self.stop_macro()
                print("Encerrando a aplicação...")
                break
            else:
                print("Opção inválida.")


if __name__ == "__main__":
    app = LumenaMacroApp()
    app.menu()