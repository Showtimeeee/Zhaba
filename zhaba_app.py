
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


class SwampGame:
    """Движок игры 'Zhaba'."""
    def __init__(self):
        self.zhaba = None
        self.running = True

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def draw_zhaba(self):
        art = r"""
             _   _
            (.)_(.)
         _ (   _   ) _
        / \/`-----'\/ \
      __\ ( (     ) ) /__
      )   \ \     / /   (
       )___/ \___/ \___(
        """
        print(art)

    def startup(self):
        self.clear_screen()
        print("="*40)
        print("       ПРОЕКТ: ZHABA (ЖАБА) v1.0")
        print("="*40)
        name = input("Как назовем вашего подопечного? ")
        self.zhaba = Zhaba(name if name else "Геннадий")
        print(f"\n{self.zhaba.name} вылупился из икринки...")
        time.sleep(1.5)

    def random_event(self):
        """Случайные события в болоте."""
        event = random.random()
        if event < 0.15:
            print("\n🦅 Тень сверху! Аист пролетел мимо. Вы потеряли 10 энергии от страха.")
            self.zhaba.energy = max(0, self.zhaba.energy - 10)
        elif event < 0.30:
            print("\n⛈ Пошел дождь. Уровень слизи повысился!")
            self.zhaba.slime_level += 5
        elif event < 0.45:
            print("\n💎 Вы нашли блестящую пуговицу в грязи. Бесполезно, но красиво.")
            self.zhaba.inventory.append("Пуговица")
        else:
            print("\n🌿 В болоте сегодня спокойно...")

    def game_loop(self):
        while self.zhaba.is_alive and self.running:
            self.clear_screen()
            self.draw_zhaba()
            self.zhaba.show_stats()
            
            print("Что будем делать?")
            print("1. Охотиться на насекомых (Трата энергии, утоление голода)")
            print("2. Медитировать на кувшинке (Восстановление энергии)")
            print("3. Громко квакнуть (Призыв удачи/Опыт)")
            print("4. Исследовать дальний камыш (Опасно!)")
            print("5. Выход из игры")
            
            choice = input("Выберите действие (1-5): ")

            if choice == "1":
                self.action_hunt()
            elif choice == "2":
                self.action_rest()
            elif choice == "3":
                self.action_croak()
            elif choice == "4":
                self.action_explore()
            elif choice == "5":
                print("Сохранение жабьих сил... До встречи!")
                self.running = False
            else:
                print("Жаба не понимает такой команды...")
                time.sleep(1)

            # Механика времени и выживания
            self.zhaba.hunger += 5
            self.zhaba.days_survived += 1
            
            if self.zhaba.hunger >= 100:
                print("\n💀 Жаба умерла от голода...")
                self.zhaba.is_alive = False
            
            if self.zhaba.hp <= 0:
                print("\n💀 Жаба пала в бою...")
                self.zhaba.is_alive = False

            if self.zhaba.is_alive and self.running:
                input("\nНажмите Enter, чтобы прожить следующий день...")
                self.random_event()
                time.sleep(1)

    def action_hunt(self):
        if self.zhaba.energy < 20:
            print("Слишком мало энергии для прыжка!")
            return
        
        self.zhaba.energy -= 20
        catch = random.choice(["Муха", "Муха", "Стрекоза", "Ничего", "Пчела"])
        
        if catch == "Ничего":
            print("Вы промахнулись языком! Муха улетела.")
        elif catch == "Пчела":
            print("🐝 Ой! Вы съели пчелу, она ужалила вас изнутри!")
            self.zhaba.hp -= 15
        else:
            self.zhaba.eat(catch)

    def action_rest(self):
        print("🧘 Вы сидите на кувшинке и ловите дзен...")
        self.zhaba.energy = min(100, self.zhaba.energy + 40)
        self.zhaba.hp = min(self.zhaba.max_hp, self.zhaba.hp + 5)
        time.sleep(1)

    def action_croak(self):
        sounds = ["КВААА!", "бре-ке-кекс!", "Ква?", "КРОАК!"]
        print(f"\n📢 {self.zhaba.name} кричит: {random.choice(sounds)}")
        self.zhaba.exp += 2
        if random.random() < 0.2:
            print("На ваш зов прилетела жирная Муха!")
            self.zhaba.eat("Муха")
        time.sleep(1)

    def action_explore(self):
        print("🔍 Вы прыгаете в неизведанные дебри...")
        time.sleep(1)
        danger = random.randint(1, 3)
        if danger == 1:
            print("🐍 Змея! Вы едва спаслись, но получили ранение.")
            self.zhaba.hp -= 30
        elif danger == 2:
            print("✨ Вы нашли Тайную Запруду. Здесь много еды!")
            self.zhaba.eat("Золотой комар")
        else:
            print("💎 Вы нашли старую блесну. Теперь вы — Жаба-Воин.")
            self.zhaba.inventory.append("Блесна (+5 к крутости)")
            self.zhaba.exp += 20

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
