import os
import sys
import time
import logging
import threading
from typing import Optional

from config import Config
from input_controller import InputController
from vision import VisionSystem
from movement import MovementManager
from battle import BattleManager


def setup_logger(config: Config) -> logging.Logger:
    if not os.path.exists(config.logs_path):
        os.makedirs(config.logs_path)

    logger = logging.getLogger("LumenaMacro")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    file_handler = logging.FileHandler(
        os.path.join(config.logs_path, "macro.log"), encoding="utf-8"
    )
    console_handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


class MacroEngine:
    def __init__(self) -> None:
        self.config = Config.load_from_json()
        self.logger = setup_logger(self.config)
        self.input_ctrl = InputController()
        self.vision = VisionSystem(self.config, self.input_ctrl)
        self.movement = MovementManager(self.config, self.input_ctrl)
        self.battle = BattleManager(self.config, self.vision, self.input_ctrl)
        self.running = False
        self.macro_thread: Optional[threading.Thread] = None

    def start_macro() -> None:
        if self.running:
            print("A macro já está em execução.")
            return

        self.running = True
        self.macro_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.macro_thread.start()
        print("\n[+] Macro iniciada! Pressione CTRL+C no terminal para parar e voltar ao menu.\n")

    def stop_macro() -> None:
        self.running = False
        if self.macro_thread and self.macro_thread.is_alive():
            self.macro_thread.join(timeout=2.0)
        print("\n[-] Macro parada com sucesso.\n")

    def _run_loop() -> None:
        self.logger.info("Loop principal iniciado.")
        stuck_timer = time.time()

        while self.running:
            try:
                if self.battle.is_in_battle():
                    stuck_timer = time.time()
                    success = self.battle.handle_battle_loop()
                    if not success:
                        self.logger.warning("Falha na batalha. Executando rotina de recuperação.")
                        self.input_ctrl.press_key("escape")
                        time.sleep(1.0)
                else:
                    interrupted = self.movement.execute_step(
                        check_interrupt=lambda: self.battle.is_in_battle() or not self.running
                    )
                    if interrupted:
                        self.logger.info("Movimento interrompido por batalha ou pelo usuário.")

                if time.time() - stuck_timer > self.config.max_stuck_seconds:
                    self.logger.error("Detectado travamento global. Forçando reset de inputs.")
                    pyautogui_reset()
                    stuck_timer = time.time()

            except Exception as e:
                self.logger.exception(f"Erro não tratado no loop da macro: {e}")
                time.sleep(1.0)


def pyautogui_reset() -> None:
    import pyautogui
    for k in ["w", "a", "s", "d"]:
        pyautogui.keyUp(k)


class CLI:
    def __init__(self, engine: MacroEngine) -> None:
        self.engine = engine

    def show_menu() -> None:
        while True:
            print("=======================================")
            print("       LUMENA.GG - MACRO AUTOMATION    ")
            print("=======================================")
            print("1 - Iniciar Macro")
            print("2 - Configurações")
            print("3 - Testar Reconhecimento de Templates")
            print("4 - Capturar Novo Template (Região)")
            print("5 - Sair")
            print("=======================================")

            choice = input("Escolha uma opção: ").strip()

            if choice == "1":
                self.engine.start_macro()
                try:
                    while self.engine.running:
                        time.sleep(0.5)
                except KeyboardInterrupt:
                    self.engine.stop_macro()

            elif choice == "2":
                self.configure_menu()

            elif choice == "3":
                self.test_recognition()

            elif choice == "4":
                self.capture_template_cli()

            elif choice == "5":
                if self.engine.running:
                    self.engine.stop_macro()
                print("Encerrando programa...")
                break
            else:
                print("Opção inválida!")

    def configure_menu() -> None:
        cfg = self.engine.config
        print("\n--- Configurações Atuais ---")
        print(f"1. Padrão de Movimento: {cfg.movement_pattern}")
        print(f"2. Nível de Confiança (Match): {cfg.confidence}")
        print(f"3. Duração do Passo (s): {cfg.step_duration}")
        print(f"4. Índice do Monitor: {cfg.monitor_index}")
        print("5. Voltar")

        sub_choice = input("Selecione para alterar: ").strip()
        if sub_choice == "1":
            print("Padrões disponíveis: zigzag, square, random, custom")
            pat = input("Novo padrão: ").strip()
            if pat in ["zigzag", "square", "random", "custom"]:
                cfg.movement_pattern = pat
                cfg.save_to_json()
                print("Padrão atualizado!")
        elif sub_choice == "2":
            conf = input("Nova confiança (0.5 a 0.99): ").strip()
            try:
                cfg.confidence = float(conf)
                cfg.save_to_json()
                print("Confiança atualizada!")
            except ValueError:
                print("Valor inválido.")
        elif sub_choice == "3":
            dur = input("Duração do passo em segundos: ").strip()
            try:
                cfg.step_duration = float(dur)
                cfg.save_to_json()
                print("Duração atualizada!")
            except ValueError:
                print("Valor inválido.")
        elif sub_choice == "4":
            idx = input("Índice do Monitor (1, 2...): ").strip()
            try:
                cfg.monitor_index = int(idx)
                cfg.save_to_json()
                print("Monitor atualizado!")
            except ValueError:
                print("Valor inválido.")

    def test_recognition() -> None:
        print("\nTestando detecção de templates carregados...")
        self.engine.vision.load_templates()
        for tname in self.engine.vision.templates.keys():
            res = self.engine.vision.find_template(tname)
            if res:
                print(f"[ENCONTRADO] '{tname}' em Coordenadas: X={res[0]}, Y={res[1]}")
            else:
                print(f"[NÃO ENCONTRADO] '{tname}'")
        input("\nPressione ENTER para voltar...")

    def capture_template_cli() -> None:
        print("\n--- Ferramenta de Captura de Template ---")
        name = input("Nome do template (ex: fight_button): ").strip()
        if not name:
            return

        print("Aponte as coordenadas da região:")
        try:
            x = int(input("X inicial (topo esquerdo): "))
            y = int(input("Y inicial (topo esquerdo): "))
            w = int(input("Largura (width): "))
            h = int(input("Altura (height): "))

            success = self.engine.vision.save_region_as_template(x, y, w, h, name)
            if success:
                print(f"Template '{name}' capturado e salvo!")
            else:
                print("Falha ao capturar o template.")
        except ValueError:
            print("Entrada inválida! Insira números inteiros.")


if __name__ == "__main__":
    engine = MacroEngine()
    cli = CLI(engine)
    cli.show_menu()