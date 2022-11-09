class Dot:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if other:  # избегаем ошибки при сравнении с пустой строкой
            return self.x == other.x and self.y == other.y

    def __repr__(self):
        return f"({self.x}, {self.y})"


class BoardException(Exception):  # создаем собственные классы исключений
    pass


class BoardOutException(BoardException):
    def __str__(self):
        return "Вы пытаетесь выстрелить за доску!"


class BoardUsedException(BoardException):
    def __str__(self):
        return "Вы уже стреляли в эту клетку"


class BoardWrongShipException(BoardException):  # не показываем в консоль
    pass


class Ship:
    def __init__(self, size, bow, l, o):
        self.bow = bow  # начальные координаты
        self.size = size  # размер поля
        self.l = l  # длина корабля
        self.o = o  # ориентация - горизонтальная\вертикальная
        self.lives = l  # жизни корабля

    @property
    def dots(self):  # получаем точки каждого корабля
        ship_dots = []
        for i in range(self.l):
            cur_x = self.bow.x
            cur_y = self.bow.y

            if self.o == 0:  # хвост снизу от носа
                cur_x += i

            elif self.o == 2:  # хвост сверху от носа
                cur_x -= i

            elif self.o == -1:  # хвост слева от носа
                cur_y -= i

            elif self.o == 1:  # хвост справа от носа
                cur_y += i

            ship_dots.append(Dot(cur_x, cur_y))  # формируем список из точек корабля
        return ship_dots  # и возвращаем его


class ShipManual(Ship):  # ручная расстановка кораблей
    def dots_bow(self):
        bow = input('Введите координаты носа: ').split()  # получаем координаты носа
        if not self.check(bow):  # проверяем корректность координат
            return self.dots_bow()  # если неверно просим ввести повторно
        else:
            x, y = self.check(bow)

        if self.l > 1:  # запускаем ввод координат кормы
            return self.dots_stern(x, y)
        else:
            self.bow = Dot(x, y)
            return self.dots  # передаем координаты в универсальный метод dots

    def dots_stern(self, x, y):
        a, b, c, d = self.promt(x, y)  # подсказки куда можно поставить 2 координату
        stern = input(f'Введите координаты кормы {a}{b}{c}{d}: ').split()
        if not self.check(stern):
            return self.dots_stern(x, y)  # если координаты неверные, просим ввести их заново
        else:
            stern_x, stern_y = self.check(stern)  # получаем координаты кормы
            n = Dot(stern_x + 1, stern_y + 1)  # вспомогательная переменная
            if n == a or n == b or n == c or n == d:  # проверяем, что пользователь ввел координаты из подсказки
                self.orient(x, y, stern_x, stern_y)  # определяем ориентацию корабля исходя из координат носа и кормы
            else:
                print('Недопустимые координаты, введите заново')
                return self.dots_stern(x, y)
        self.bow = Dot(x, y)
        return self.dots

    def promt(self, x, y):  # формируем подсказки куда поставить корму
        a = Dot(x + self.l, y + 1) if x + self.l - 1 < self.size else ''
        b = Dot(x - self.l + 2, y + 1) if x + 1 - self.l >= 0 else ''
        c = Dot(x + 1, y + self.l) if y + self.l - 1 < self.size else ''
        d = Dot(x + 1, y - self.l + 2) if y + 1 - self.l >= 0 else ''
        return a, b, c, d

    def check(self, _input):  # проверяем полученные координаты
        if len(_input) != 2:
            print('Введите 2 координаты!')
            return False

        x, y = _input

        if not x.isdigit() or not y.isdigit():
            print('Введите числа!')
            return False

        if int(x) > self.size or int(y) > self.size:
            print('Координаты за пределами поля!')
            return False

        return int(x) - 1, int(y) - 1  # выводимое поле начинается с 1, поэтому отнимаем единицу

    def orient(self, x, y, stern_x, stern_y):  # определяем ориентацию корабля
        if stern_x == x:
            if stern_y > y:
                self.o = 1
            else:
                self.o = -1
        if stern_y == y:
            if stern_x > x:
                self.o = 0
            else:
                self.o = 2


class Board:
    def __init__(self, hid=False, size=6):
        self.size = size  # размеры доски
        self.hid = hid  # скрыть корабли или нет
        self.count = 0  # количество утопленных кораблей
        self.field = [["O"] * size for _ in range(size)]  # сама доска

        self.ships = []  # здесь сами корабли (объекты класса)
        self.free_dots = []  # куда можем походить\поставить корабль

    def free(self):  # формируем список свободных точек
        for i in range(self.size):
            for j in range(self.size):
                self.free_dots.append(Dot(i, j))

    def add_ship(self, ship, manual=False):  # добавляем корабли на доску
        if manual:  # ручной вводи координат
            ship.dots_bow()
        for d in ship.dots:  # проверяем, что корабль не выходит за поле
            if self.out(d) or d not in self.free_dots:  # не пересекается и не близко с другими кораблями
                raise BoardWrongShipException()
        for d in ship.dots:
            self.field[d.x][d.y] = "■"  # расставляем корабли на поле

        self.ships.append(ship)  # добавляем корабль в список
        if manual:  # показываем обводку при ручной расстановке
            self.contour(ship, True)
        else:
            self.contour(ship)  # не даем ставить корабли близко

    def contour(self, ship, verb=False):  # обводка корабля
        near = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 0), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]
        for d in ship.dots:
            for dx, dy in near:
                cur = Dot(d.x + dx, d.y + dy)  # в цикле получаем все точки вокруг точки корабля
                if not (self.out(cur)):  # если точки внутри доски
                    if verb and cur not in ship.dots:  # если показываем обводку и точка не занята кораблем
                        self.field[cur.x][cur.y] = "."
                    if cur in self.free_dots:  # удаляем свободные точки вокруг корабля
                        self.free_dots.remove(cur)

    def __str__(self):  # вывод поля в консоль
        res = ""
        res += '  | ' + ' | '.join([str(_) for _ in range(1, self.size + 1)]) + ' |'
        for i, row in enumerate(self.field):
            res += f"\n{i + 1} | " + " | ".join(row) + " |"
        if self.hid:  # скрываем корабли соперника
            res = res.replace("■", "O")
        return res

    def out(self, d):  # проверяем, что координаты внутри доски
        return not ((0 <= d.x < self.size) and (0 <= d.y < self.size))

    def shot(self, d):  # выстрел по доске
        if self.out(d):  # если выстрел за пределы доски
            raise BoardOutException()

        for ship in self.ships:  # для каждого корабля в списке
            if d in ship.dots:  # если выстрел попал в корабль
                ship.lives -= 1
                self.field[d.x][d.y] = "X"
                if ship.lives == 0:
                    self.count += 1  # увеличиваем счетчик потопленных кораблей
                    self.contour(ship, verb=True)  # обводим утопленный корабль
                    print("Корабль уничтожен!")
                    return True
                else:
                    print("Корабль ранен!")
                    return True

        self.field[d.x][d.y] = "."
        print("Мимо!")
        return False

    def begin(self):  # после расстановки кораблей обновляем начальные переменные
        self.free_dots = []
        self.free()
        for i in range(self.size):  # стираем обводку при ручной расстановке кораблей
            for j in range(self.size):
                if self.field[i][j] == '.':
                    self.field[i][j] = '0'
