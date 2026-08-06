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
        """Detecta se a luta está ativa pelo botão FIGHT ou pelo HP do inimigo."""
        return (
            self.vision.template_exists("fight_button") or
            self.vision.template_exists("enemy_hp")
        )

    def handle_battle_loop(self) -> bool:
        """Ciclo completo de ataque e fechamento automático da tela de XP."""
        self.logger.info("=== COMBATE DETECTADO! BLOQUEANDO MOVIMENTO ===")
        start_battle_time = time.time()
        last_fight_coords = None

        # --- FASE 1: ATAQUES EM TURNO ---
        while self.is_in_battle():
            if time.time() - start_battle_time > self.config.battle_timeout:
                self.logger.error("Timeout de batalha atingido!")
                break

            fight_match = self.vision.find_template("fight_button")
            if fight_match:
                fx, fy = fight_match[0], fight_match[1]
                last_fight_coords = (fx, fy)

                self.logger.info(f"Clicando no FIGHT em ({fx}, {fy})")
                self.input_ctrl.click_position(fx, fy)
                time.sleep(0.5)

                # Clica na caixa do 1º Golpe
                self.logger.info("Executando o PRIMEIRO GOLPE...")
                self.input_ctrl.click_position(fx - 40, fy)
                time.sleep(0.1)
                self.input_ctrl.click_position(fx - 40, fy)
                self.input_ctrl.press_key("1")
                
                # Aguarda a animação do golpe ser processada pelo jogo
                time.sleep(2.5)
            else:
                # Se está em batalha mas o FIGHT sumiu (ex: animação de ataque rolando)
                time.sleep(0.5)

        # --- FASE 2: LIMPEZA DA TELA DE XP E VITÓRIA ---
        self.logger.info("Inimigo derrotado! Fechando tela de XP...")
        time.sleep(0.6)

        # Combina atalhos de teclado e clique centralizado no banner de XP
        for _ in range(7):
            self.input_ctrl.press_key("space")
            self.input_ctrl.press_key("enter")
            
            if last_fight_coords:
                # Clica no centro exato do banner inferior ("earned XP!")
                xp_box_x = last_fight_coords[0] - 350
                xp_box_y = last_fight_coords[1] + 15
                self.input_ctrl.click_position(xp_box_x, xp_box_y)
            
            time.sleep(0.35)

        self.logger.info("=== BATALHA FINALIZADA! RETOMANDO CAMINHADA ===")
        time.sleep(0.5)
        return True