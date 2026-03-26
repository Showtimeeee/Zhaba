
import random
import time
import os
import sys
import json

class Zhaba:
    """Класс главного героя — Жабы."""
    def __init__(self, name="Геннадий"):
        self.name = name
        self.level = 1
        self.exp = 0
        self.hp = 100
        self.max_hp = 100
        self.hunger = 50  # 0 - сыт, 100 - умирает с голоду
        self.energy = 100
        self.slime_level = 10 # Уровень слизи (защита)
        self.inventory = []
        self.is_alive = True
        self.days_survived = 0

    def show_stats(self):
        print(f"\n--- ПРОФИЛЬ ЖАБЫ: {self.name} ---")
        print(f"Уровень: {self.level} | Опыт: {self.exp}/{self.level * 50}")
        print(f"Здоровье: {self.hp}/{self.max_hp} | Слизь: {self.slime_level}")
        print(f"Голод: {self.hunger}/100 | Энергия: {self.energy}/100")
        print(f"Инвентарь: {', '.join(self.inventory) if self.inventory else 'Пусто'}")
        print(f"Дней в болоте: {self.days_survived}")
        print("-" * 30)

    def eat(self, food_name):
        if food_name == "Муха":
            self.hunger = max(0, self.hunger - 15)
            self.exp += 5
            print("🐸 Ам! Вкусная муха.")
        elif food_name == "Стрекоза":
            self.hunger = max(0, self.hunger - 30)
            self.exp += 15
            print("🐸 Ого, целая стрекоза! Царский обед.")
        elif food_name == "Золотой комар":
            self.hunger = 0
            self.hp = min(self.max_hp, self.hp + 20)
            self.exp += 50
            print("✨ Золотой комар! Вы чувствуете прилив магических сил!")
        
        self.check_level_up()

    def check_level_up(self):
        if self.exp >= self.level * 50:
            self.exp -= self.level * 50
            self.level += 1
            self.max_hp += 20
            self.hp = self.max_hp
            print(f"🌟 УРОВЕНЬ ПОВЫШЕН! Теперь вы жаба {self.level} уровня.")



if __name__ == "__main__":
    game = SwampGame()
    try:
        game.startup()
        game.game_loop()
    except KeyboardInterrupt:
        print("\n\nЖаба ушла в спячку. Пока!")
    
    if not game.zhaba.is_alive:
        print("\n--- КОНЕЦ ИГРЫ ---")
        print(f"Ваша жаба {game.zhaba.name} прожила {game.zhaba.days_survived} дней.")
        print(f"Итоговый уровень: {game.zhaba.level}")
