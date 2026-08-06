import logging
import time
from config import Config
from input_controller import InputController
from vision import VisionSystem


class BattleManager:
    def __init__(self, config: Config, vision: VisionSystem, input_ctrl: InputController) -> None:
        self.config = config
        self.vision = vision
        self.input_ctrl = input_ctrl
        self.logger = logging.getLogger("LumenaMacro.Battle")

    def is_in_battle(self) -> bool:
        """Verifica se está na tela de batalha detectando o botão FIGHT ou o 1º ATAQUE."""
        return (
            self.vision.template_exists("fight_button") or
            self.vision.template_exists("first_attack")
        )

    def handle_battle_loop(self) -> bool:
        """Gerencia o ciclo completo do combate."""
        self.logger.info("Combate detectado! Iniciando ações.")
        start_battle_time = time.time()
        last_action_time = time.time()

        while True:
            # Proteção contra travamento
            if time.time() - start_battle_time > self.config.battle_timeout:
                self.logger.error("Timeout de batalha atingido. Forçando saída.")
                return False

            # Passo 1: Clicar no botão FIGHT (Se visível)
            if self.vision.click_template("fight_button"):
                self.logger.info("Clicou no botão FIGHT.")
                last_action_time = time.time()
                time.sleep(self.config.attack_delay)
                continue

            # Passo 2: Clicar SEMPRE no Primeiro Golpe (Se visível)
            if self.vision.click_template("first_attack"):
                self.logger.info("Clicou no PRIMEIRO GOLPE.")
                last_action_time = time.time()
                time.sleep(1.5)
                continue

            # Passo 3: Se não há botões de combate, clica na tela para avançar falas/XP
            if not self.is_in_battle():
                time.sleep(0.5)
                # Segunda checagem para confirmar se a batalha realmente acabou
                if not self.is_in_battle():
                    self.logger.info("Batalha finalizada com sucesso!")
                    return True

            # Passo 4: Se o combate travou em animação ou tela de XP, clica no centro
            if time.time() - last_action_time > 1.2:
                # Clica na região central/inferior para fechar caixas de texto/XP
                self.input_ctrl.click_position(600, 500)
                time.sleep(0.3)

            time.sleep(0.2)