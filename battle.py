import time
import logging
from config import Config
from vision import VisionSystem
from input_controller import InputController


class BattleManager:
    def __init__(self, config: Config, vision: VisionSystem, input_ctrl: InputController) -> None:
        self.config = config
        self.vision = vision
        self.input_ctrl = input_ctrl
        self.logger = logging.getLogger("LumenaMacro.Battle")

    def is_in_battle() -> bool:
        return (
            self.vision.template_exists("fight_button") or
            self.vision.template_exists("battle_hud") or
            self.vision.template_exists("enemy_hp_bar")
        )

    def handle_battle_loop() -> bool:
        self.logger.info("Batalha detectada! Iniciando automação de combate.")
        start_battle_time = time.time()

        while True:
            if time.time() - start_battle_time > self.config.battle_timeout:
                self.logger.error("Timeout de batalha atingido. Tentando recuperar...")
                return False

            if self.vision.template_exists("fight_button"):
                self.logger.info("Menu de combate aberto. Selecionando primeiro golpe.")
                self.vision.click_template("fight_button")
                time.sleep(self.config.attack_delay)

                if self.vision.template_exists("move_1"):
                    self.vision.click_template("move_1")
                    self.logger.info("Primeiro golpe selecionado.")
                else:
                    self.input_ctrl.press_key("1")
                    self.logger.info("Atalho '1' pressionado para o primeiro golpe.")

                time.sleep(2.0)

            if self.vision.template_exists("xp_screen") or self.vision.template_exists("victory_label"):
                self.logger.info("Vitória detectada! Limpando telas de recompensa.")
                self.clear_post_battle_screens()
                return True

            if self.vision.template_exists("dialog_continue"):
                self.vision.click_template("dialog_continue")
                time.sleep(0.5)

            if not self.is_in_battle() and not self.vision.template_exists("xp_screen"):
                time.sleep(1.0)
                if not self.is_in_battle():
                    self.logger.info("Batalha finalizada com sucesso.")
                    return True

            time.sleep(0.3)

    def clear_post_battle_screens() -> None:
        start_time = time.time()
        while time.time() - start_time < 10.0:
            clicked = False
            for template in ["xp_screen", "continue_button", "close_button", "dialog_continue"]:
                if self.vision.click_template(template):
                    clicked = True
                    time.sleep(0.5)

            if not clicked and not self.is_in_battle():
                break
            time.sleep(0.3)