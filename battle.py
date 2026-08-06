import time
import logging
from config import Config
from vision import VisionSystem
from input_controller import InputController


class BattleController:
    def __init__(self, config: Config, vision: VisionSystem, input_ctrl: InputController) -> None:
        self.config = config
        self.vision = vision
        self.input_ctrl = input_ctrl
        self.logger = logging.getLogger("LumenaMacro")

    def in_battle(self) -> bool:
        return (
            self.vision.template_exists("fight_button.png") or 
            self.vision.template_exists("battle_hud.png")
        )

    def handle_battle(self) -> bool:
        self.logger.info("Batalha detectada! Iniciando sequência de combate.")
        start_time = time.time()

        while time.time() - start_time < self.config.battle_timeout:
            fight_loc = self.vision.wait_template("fight_button.png", timeout=3.0)
            if fight_loc:
                cx, cy = self.vision.get_center_coords(fight_loc)
                self.input_ctrl.click(cx, cy)
                self.logger.info("Menu 'Fight' clicado.")
                time.sleep(0.5)

                move_loc = self.vision.wait_template("first_move.png", timeout=2.0)
                if move_loc:
                    mx, my = self.vision.get_center_coords(move_loc)
                    self.input_ctrl.click(mx, my)
                    self.logger.info("Primeiro golpe ativado.")
                else:
                    self.input_ctrl.click(cx, cy)

            xp_loc = self.vision.find_template("xp_screen.png")
            if xp_loc:
                cx, cy = self.vision.get_center_coords(xp_loc)
                self.input_ctrl.click(cx, cy)
                self.logger.info("Tela de Experiência/Recompensa fechada.")
                time.sleep(0.5)

            close_loc = self.vision.find_template("close_battle.png")
            if close_loc:
                cx, cy = self.vision.get_center_coords(close_loc)
                self.input_ctrl.click(cx, cy)
                self.logger.info("Batalha finalizada via botão de fechamento.")
                return True

            if not self.in_battle() and not self.vision.template_exists("xp_screen.png"):
                self.logger.info("Batalha concluída com sucesso. Retornando ao mapa.")
                return True

            time.sleep(self.config.attack_delay)

        self.logger.error("Timeout de batalha excedido. Retornando controle ao loop principal.")
        return False