from random import randint
from internal import *


class Player:
    def __init__(self, board, enemy):
        self.board = board  # доска игрока
        self.enemy = enemy  # доска соперника

    def ask(self):  # для классов наследников
        raise NotImplementedError()

    def move(self):  # ход игрока
        while True:
            try:  # если пользователь походи корректно
                target = self.ask()  # запрашиваем координаты куда стрелять
                repeat = self.enemy.shot(target)  # попали или нет в корабль
                return repeat
            except BoardException as e:  # выстрел за пределы доски
                print(e)


class AI(Player):  # ход компьютера
    def ask(self):  # случайный выстрел по свободным клеткам
        d = self.enemy.free_dots.pop(randint(0, len(self.enemy.free_dots) - 1))
        print(f"Ход компьютера: {d.x + 1} {d.y + 1}")
        return d


class ImprovedAI(AI):  # усовершенствованный АИ
    kill_ship = []  # возможные точки нахождения корабля после попадания
    name = 'Компьютер'

    def ask(self):  # переопределяем метод запроса координат
        if self.kill_ship:  # сперва пытаемся добить
            d = self.kill_ship.pop(randint(0, len(self.kill_ship) - 1))
        else:  # случайный ход по свободным точкам
            d = self.enemy.free_dots.pop(randint(0, len(self.enemy.free_dots) - 1))
        print(f"Ход компьютера: {d.x + 1} {d.y + 1}")
        return d

    def move(self):  # переопределим метод
        while True:
            try:
                target = self.ask()
                repeat = self.enemy.shot(target)
                if repeat:  # если попали, создаем список точек для добивания
                    self.kill(target)
                return repeat
            except BoardException as e:
                print(e)

    def kill(self, target):
        busy = [
            (-1, -1), (1, -1),
            (-1, 1), (1, 1)
        ]  # корабль не может располагаться по диагонали
        for dx, dy in busy:
            x = dx + target.x
            y = dy + target.y
            if Dot(x, y) in self.enemy.free_dots:
                self.enemy.free_dots.remove(Dot(x, y))  # поэтому диагональные точки от места попадания нужно исключить
        near = [
            (0, 1),
            (-1, 0), (1, 0),
            (0, -1)
        ]  # берем точки слева справа сверху и снизу от места попадания
        for dx, dy in near:
            x = dx + target.x
            y = dy + target.y
            if Dot(x, y) in self.enemy.free_dots:
                self.kill_ship.append(Dot(x, y))  # добавляем их в список для добивания


class User(Player):
    name = 'Пользователь'

    def ask(self):  # для юзера ручной ввод координат
        while True:  # проверяем их на корректность
            cords = input("Ваш ход: ").split()

            if len(cords) != 2:
                print(" Введите 2 координаты! ")
                continue

            x, y = cords

            if not (x.isdigit()) or not (y.isdigit()):
                print(" Введите числа! ")
                continue

            x, y = int(x), int(y)
            d = Dot(x - 1, y - 1)
            if d not in self.enemy.free_dots:
                raise BoardUsedException()
            self.enemy.free_dots.remove(d)
            return d


class Game:  # основная логика
    def __init__(self, lens, size=6):
        self.size = size  # размер поля
        self.lens = lens  # список длин располагаемых кораблей
        self.ai = None  # объект компьютер
        self.us = None  # объект юзер

    def gen_board(self):  # генерируем доски для юзера и компьютера
        co = self.random_board()  # случайная доска для АИ
        # у юзера спрашиваем, хочет ли он сам расставить корабли
        if input('\nРасставите корабли вручную? (y/n): ') == 'y':
            pl = self.manual_board()  # если да, запускаем ручную расстановку кораблей
        else:
            pl = self.random_board()  # иначе генерируем случайную доску
        co.hid = True  # скрываем доску компьютера
        self.ai = ImprovedAI(co, pl)  # создаем объекты игроков
        self.us = User(pl, co)

    def random_board(self):  # случайная генерация доски
        board = None
        while board is None:  # пока не удалось сгенерировать доску пытаемся еще
            board = self.random_place()
        return board

    def random_place(self):
        board = Board(size=self.size)  # создаем экземпляр доски
        board.free()  # создаем список свободных точек
        attempts = 0
        for l in self.lens:
            while True:
                attempts += 1
                if attempts > 2000:
                    return None  # если не удалось сгенерировать доску
                # создаем случайный корабль, корабли размещаются либо вниз вертикально, либо вправо горизонтально
                ship = Ship(self.size, Dot(randint(0, self.size - l), randint(0, self.size - l)), l, randint(0, 1))
                try:
                    board.add_ship(ship)  # пытаемся добавить корабль на доску
                    break  # если успех, переходим к следующему
                except BoardWrongShipException:
                    pass
        board.begin()

        return board

    def manual_board(self):  # расставляем корабли вручную
        board = Board(size=self.size)
        board.free()
        for l in self.lens:
            while True:
                ship = ShipManual(self.size, None, l, None)  # начальные координаты и ориентацию определим вручную
                print(board)  # показываем поле после каждого корабля
                try:
                    board.add_ship(ship, manual=True)
                    break
                except BoardWrongShipException:
                    print('Не удалось поставить корабль! Попробуйте расположить в другом месте.')
        board.begin()
        return board

    @staticmethod
    def greet():  # приветствие
        print("-------------------")
        print("  Приветсвуем вас  ")
        print("      в игре       ")
        print("    морской бой    ")
        print("-------------------")
        print(" формат ввода: x y ")
        print(" x - номер строки  ")
        print(" y - номер столбца ")

    def loop(self):  # цикл ходов
        num = 0
        while True:
            self.print_board()  # выводим доски пользователя и компьютера
            if num % 2 == 0:  # четные ходы за юзером
                print("-" * 20)
                print("Ходит пользователь!")
                repeat = self.us.move()  # попали(повторить ход) или нет
                if self.check_win(self.us):  # проверяем наличие победителя
                    break
            else:  # нечетные ходы за АИ
                print("-" * 20)
                print("Ходит компьютер!")
                repeat = self.ai.move()
                if self.check_win(self.ai):
                    break

            num += 1  # увеличиваем счетчик ходов
            if repeat:
                num -= 1  # если попали, уменьшаем счетчик ходов

    def check_win(self, pl):  # проверка победителя
        if pl.enemy.count == len(self.lens):  # если количество потопленных кораблей равно количеству кораблей на доске
            print("-" * 20)
            print(f"{pl.name} выиграл!")
            print(pl.enemy)
            return True

    def print_board(self):  # демонстрация досок в начале игры
        print("-" * 20)
        print("Доска пользователя:")
        print(self.us.board)
        print("-" * 20)
        print("Доска компьютера:")
        print(self.ai.board)

    def start(self):
        self.greet()  # приветствие
        self.gen_board()  # создаем доски
        self.loop()  # запускаем цикл ходов


if __name__ == "__main__":

    len_ships = [3, 2, 2, 1, 1, 1, 1]  # задаем список кораблей
    size = 6  # задаем размер поля
    g = Game(len_ships, size)
    g.start()  # запуск игры
