import matplotlib.pyplot as plt
from fontTools.varLib.plot import stops
from matplotlib.widgets import Button
import random
import tkinter as tk
from tkinter import simpledialog



class BusStop:
    def __init__(self, position, idx=None):
        self.idx = idx
        if idx is not None:
            self.people = 0
        self.position = position
        self.taken = False

class Bus:
    def __init__(self, bus_number, current_stop, route, ax, validate, driver=None):
        self.bus_number = bus_number
        self.driver = driver
        self.current_stop = current_stop
        self.current_stop.taken = True
        self.route = route
        self.in_drive = 0
        self.capacity = 15
        self.passengers = 0
        self.transported = 0
        self.delay = None
        self.need_to_park = False
        if not validate:
            self.bus_point, = ax.plot(current_stop.position[0], current_stop.position[1], 'go',
                         color='orange',
                         markersize=12)
            self.text_marker = ax.text(self.current_stop.position[0], self.current_stop.position[1] + 0.6, f'№{self.bus_number}',
                                       color='black', fontsize=8, ha='left', zorder=10)
            self.driver_marker = ax.text(0, 0, '',
                                       color='black', fontsize=8, ha='left', zorder=10)
            self.bus_point.set_visible(False)
            self.text_marker.set_visible(False)

    def drive(self):
        if not self.current_stop.idx is None:
            next_stop_idx = (self.current_stop.idx + 1) % (len(self.route))
        else:
            next_stop_idx = 0
        self.current_stop.taken = False
        self.current_stop = self.route[next_stop_idx]

        # Пассажиры вышли
        people_leaved = random.randint(0, self.passengers)
        self.passengers = max(0, self.passengers - people_leaved)
        self.transported += people_leaved

        # Пассажиры вошли
        free_seats = self.capacity - self.passengers
        people_entered = min(free_seats, self.current_stop.people)
        self.passengers += people_entered
        self.current_stop.people = max(0, self.current_stop.people - people_entered)

        self.current_stop.taken = True

    def park_on_station(self, parking_lot, validate):
        self.transported += self.passengers
        self.passengers = 0
        for parking in parking_lot:
            if not parking.taken:
                self.current_stop = parking
                self.current_stop.taken = True
                self.driver.laps = -1
                if not validate:
                    self.bus_point.set_visible(False)
                    self.text_marker.set_visible(False)
                break

class DayDriver:
    def __init__(self, driver_id):
        self.driver_id = driver_id
        self.driver_type = 0
        self.max_laps_before_lunch = 4
        self.max_laps_after_lunch = 1
        self.max_laps = self.max_laps_before_lunch
        self.laps = -1

    def take_the_bus(self, buses, validate):
        for bus in buses:
            if bus.driver is None:
                bus.driver = self
                if not validate:
                    bus.driver_marker.set_color('black')
                    bus.bus_point.set_visible(True)
                    bus.text_marker.set_visible(True)
                return bus.bus_number

class NightDriver:
    def __init__(self, driver_id):
        self.driver_id = driver_id
        self.driver_type = 1
        self.max_laps = 2
        self.shifts = 0
        self.laps = -1

    def take_the_bus(self, buses, validate):
        for bus in buses:
            if bus.driver is None:
                bus.driver = self
                if not validate:
                    bus.driver_marker.set_color('red')
                    bus.bus_point.set_visible(True)
                    bus.text_marker.set_visible(True)
                return bus.bus_number


class Simulation:
    def __init__(self, stops_positions, parking_positions, number_of_buses, number_of_day_drivers, number_of_night_drivers, validate=False):
        self.validate = validate

        if not validate:
            self.fig, self.ax = plt.subplots()
        else:
            self.ax = None
        self.x_cords, self.y_cords = zip(*stops_positions)

        # Количество дневных и ночных водителей
        self.number_of_day_drivers = number_of_day_drivers
        self.number_of_night_drivers = number_of_night_drivers

        # Количество водителей на смене
        self.drivers_in_day_shift = number_of_day_drivers / 2
        self.drivers_in_night_shift = number_of_night_drivers / 3

        # Интервалы между ночными и дневными водителями
        self.day_interval = 90 // self.drivers_in_day_shift
        self.night_interval = 90 // self.drivers_in_night_shift

        # Список объектов BusStop
        self.stops = [BusStop(stops_positions[i], i) for i in range(len(stops_positions)-1)]
        self.parking_lot = [BusStop(position) for position in parking_positions]

        # Инициализируем автобусы
        self.buses = [Bus(i+1, self.parking_lot[i], self.stops, self.ax, validate) for i in range(number_of_buses)]
        self.day_buses_on_track = 0
        self.night_buses_on_track = 0

        # Инициализируем водителей
        self.day_drivers = [DayDriver(i) for i in range(number_of_day_drivers)]
        self.night_drivers = [NightDriver(i+number_of_day_drivers) for i in range(number_of_night_drivers)]
        self.free_day_drivers = None
        self.free_night_drivers = None

        self.is_paused = False  # Пауза?
        self.speed = 0.01 # Скорость анимации

        self.one_day_schedule = {}

        if not validate:
            # Кнопка для паузы
            self.ax_pause_button = plt.axes((0.48, 0.05, 0.2, 0.075))  # Позиция кнопки (левая, нижняя, ширина, высота)
            self.pause_button = Button(self.ax_pause_button, '||')
            self.pause_button.on_clicked(self.pause_button_func)

            # Кнопка для изменения скорости
            self.ax_speed_button = plt.axes((0.7, 0.05, 0.2, 0.075))  # Позиция кнопки (левая, нижняя, ширина, высота)
            self.speed_button = Button(self.ax_speed_button, 'Скорость')
            self.speed_button.on_clicked(self.speed_button_func)

        # Переменные времени
        self.time_text = None
        self.day_of_week_text = None
        self.day_text = None

        # Время
        self.days_of_week = ['Понедельник', 'Вторник', 'Среда',
                        'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        self.weekends = ['Суббота', 'Воскресенье']
        self.clock_time = '06:00'
        self.day_of_week = 'Понедельник'
        self.day_number = 1
        self.minutes = 0
        self.hours = 6

        # Тики
        self.day_bus_tick = 0
        self.night_bus_tick = 0
        self.last_day_departure = -self.day_interval
        self.last_night_departure = -self.night_interval

        self.need_nighters = False
        self.need_to_go = None

        self.start_number = None
        self.switch_count = 0
        self.switch = False

    # Запуск симуляции
    def run(self):
        if not self.validate:
            # Отображаем основную информацию
            self.plot_canvas()

        while self.day_number < 8:
            if not self.is_paused:
                # Определяем дневных водителей на сегодня
                if self.clock_time == '06:00' and self.day_of_week not in self.weekends:
                    self.initiate_day_drivers()

                # Определяем ночных водителей на сегодня
                if self.day_of_week not in self.weekends:
                    if self.clock_time == '17:00':
                        self.need_nighters = True
                        self.initiate_night_drivers()
                    elif self.clock_time == '22:30' or self.need_to_go == self.clock_time:
                        self.need_nighters = True
                else:
                    if self.clock_time == '10:00':
                        self.need_nighters = True
                        self.initiate_night_drivers()

                # Добавляем людей на остановки
                self.influx_of_people()

                # Передвижение автобусов
                self.bus_moving()

                if not self.validate:
                    # Отображаем автобусы
                    self.show_buses()

                # Обновление времени
                self.time_update()

                if not self.validate:
                    # Обновление холста
                    self.canvas_update()

                self.day_bus_tick += 1
                self.night_bus_tick += 1

            if not self.validate:
                plt.pause(0.1)

        if not self.validate:
            # Убираем оси
            self.ax.axis('off')
            self.ax.legend(loc='best')
            plt.show()

        return self.metric()

    # Функция для кнопки паузы
    def pause_button_func(self, event):
        self.is_paused = not self.is_paused
        new_label = '▶' if self.is_paused else '||'  # Устанавливаем новый текст
        self.pause_button.label.set_text(new_label)  # Меняем текст кнопки
        self.fig.canvas.draw_idle()  # Обновляем интерфейс

    # Функция для кнопки скорости
    def speed_button_func(self, event):
        root = tk.Tk()
        root.withdraw()

        # Всплывающее окно для ввода числа
        value = simpledialog.askfloat("Введите число", "Введите число от 0.01 до 5:",
                                      minvalue=0.01, maxvalue=5.0)
        if value is not None:  # Проверяем, что пользователь ввёл число
            self.speed = value
        root.destroy()


    # Функция для отображения автобусов
    def show_buses(self):
        # Отображаем автобусы
        for bus in self.buses:
            bus.bus_point.set_data([bus.current_stop.position[0]], [bus.current_stop.position[1]])
            bus.text_marker.set_position((bus.current_stop.position[0], bus.current_stop.position[1]+0.6))
            if bus.driver:
                bus.driver_marker.set_text(f'Водитель {bus.driver.driver_id}')
                bus.driver_marker.set_position((bus.current_stop.position[0], bus.current_stop.position[1] + 1.2))

    # Метод для отображения основной части холста
    def plot_canvas(self):
        # Увеличиваем нижний отступ, чтобы разместить кнопку
        plt.subplots_adjust(bottom=0.2)

        # Построение маршрута
        self.ax.plot(self.x_cords, self.y_cords, color='b', linestyle='-', linewidth=2)

        # Точки остановок
        self.ax.scatter(self.x_cords, self.y_cords, color='b', label='Bus stop', s=50, zorder=5)
        self.ax.scatter(self.x_cords[0], self.y_cords[0], color='green', s=50, label='Bus station', zorder=5)

        # Отображаем время
        self.initialization_of_time()

    # Метод инициализации времени
    def initialization_of_time(self):
        self.time_text = self.ax.text(14, 2, f"Время: {self.clock_time}", color='black', fontsize=12, ha='left')
        self.day_of_week_text = self.ax.text(14, 0, f"{self.day_of_week}", color='black', fontsize=12, ha='left')
        self.day_text = self.ax.text(14, 1, f"День: {self.day_number}", color='black', fontsize=12, ha='left')

    # Функция для обновления времени
    def time_update(self):
        # Обновляем время
        self.minutes += 1
        if self.minutes == 60:
            self.minutes = 0
            self.hours += 1
        if self.hours == 24:
            self.hours = 0
            self.day_number += 1
        self.day_of_week = self.days_of_week[(self.day_number - 1) % 7]
        self.clock_time = f'{self.hours:02d}:{self.minutes:02d}'

        if not self.validate:
            self.time_text.set_text(f"Время: {self.clock_time}")
            self.day_of_week_text.set_text(f"{self.day_of_week}")
            self.day_text.set_text(f"День: {self.day_number}")

    # Функция для обновления холста
    def canvas_update(self):
        # Обновляем график
        self.ax.axis('off')  # Убираем оси
        self.ax.legend(loc='best')
        self.fig.canvas.draw()
        plt.pause(self.speed)  # Пауза для анимации

    # Функция для передвижения автобусов
    def bus_moving(self):
        # На маршрут нужен дневной водитель
        if (self.day_bus_tick - self.last_day_departure >= self.day_interval) and (self.day_buses_on_track < self.drivers_in_day_shift or self.switch) and self.free_day_drivers: # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            self.last_day_departure = self.day_bus_tick
            driver_id = self.need_a_day_driver()

            if driver_id in self.one_day_schedule:
                if len(self.one_day_schedule[driver_id][0]) < 2:
                    self.one_day_schedule[driver_id][0].append(self.clock_time)
            else:
                self.one_day_schedule[driver_id] = [[self.clock_time], []]

            if not self.validate:
                print(f'Водитель-{driver_id} выехал в {self.clock_time}')
            if self.switch:
                self.switch_count += 1
            if self.switch_count == self.drivers_in_day_shift:
                self.switch = False
                self.switch_count = 0

        # На маршрут нужен ночной водитель
        if (self.night_bus_tick - self.last_night_departure >= self.night_interval and self.night_buses_on_track < self.drivers_in_night_shift and self.free_night_drivers and self.need_nighters) or (self.clock_time == self.need_to_go): # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            self.last_night_departure = self.night_bus_tick
            driver_id = self.need_a_night_driver()

            if not self.validate:
                print(f'Водитель-{driver_id} выехал в {self.clock_time}')
            #print(self.one_day_schedule[driver_id])
        for bus in self.buses:
            if bus.driver:
                if bus.driver.driver_type == 0:
                    # ДЛЯ ДНЕВНОГО АВТОБУСА
                    self.move_day_bus(bus)
                else:
                    # ДЛЯ НОЧНОГО АВТОБУСА
                    self.move_night_bus(bus)
                bus.in_drive += 1

    def need_a_day_driver(self):
        new_driver_on_track = self.free_day_drivers.pop(0)
        bus_number = new_driver_on_track.take_the_bus(self.buses, self.validate)
        if bus_number is None:
            self.parking_lot.append(BusStop((10, 5)))
            self.buses.append(Bus(self.buses[0].bus_number+1, self.parking_lot[-1], self.stops, self.ax, self.validate))
        self.day_buses_on_track += 1
        return new_driver_on_track.driver_id

    def need_a_night_driver(self):
        new_driver_on_track = self.free_night_drivers.pop(0)
        bus_number = new_driver_on_track.take_the_bus(self.buses, self.validate)
        if bus_number is None:
            self.parking_lot.append(BusStop((10, 5)))
            self.buses.append(Bus(self.buses[0].bus_number+1, self.parking_lot[-1], self.stops, self.ax, self.validate))
        self.night_buses_on_track += 1
        return new_driver_on_track.driver_id

    # Определение водителей на день
    def initiate_day_drivers(self):
        self.free_day_drivers = []
        for i in range(len(self.day_drivers)):
            day_driver = self.day_drivers.pop(0)
            self.day_drivers.append(day_driver)
            if len(self.free_day_drivers) < self.drivers_in_day_shift:
                day_driver.max_laps_before_lunch = 4
                day_driver.max_laps_after_lunch = 1
                day_driver.max_laps = day_driver.max_laps_before_lunch
                self.free_day_drivers.append(day_driver)
            elif len(self.free_day_drivers) >= self.drivers_in_day_shift:
                day_driver.max_laps_before_lunch = 1
                day_driver.max_laps_after_lunch = 4
                day_driver.max_laps = day_driver.max_laps_before_lunch
                self.free_day_drivers.append(day_driver)
            if len(self.free_day_drivers) == self.number_of_day_drivers:
                if not self.validate:
                    print("День укомплектован, работают водители:\n", end ='')
                    for free_day_driver in self.free_day_drivers:
                        print(f'Водитель {free_day_driver.driver_id}, до обеда {free_day_driver.max_laps_before_lunch}, после {free_day_driver.max_laps_after_lunch}' )
                    break

    def initiate_night_drivers(self):
        self.free_night_drivers = []
        for i in range(len(self.night_drivers)):
            night_driver = self.night_drivers.pop(0)
            self.night_drivers.append(night_driver)
            night_driver.max_laps = 2
            night_driver.shifts = 0
            self.free_night_drivers.append(night_driver)
            self.need_to_go = None
            if not self.validate:
                if len(self.free_night_drivers) == self.drivers_in_night_shift:
                    print('Ночные водители:\n', end='')
                    for free_night_driver in self.free_night_drivers:
                        print(f'Водитель {free_night_driver.driver_id}, до обеда {free_night_driver.max_laps}, после {free_night_driver.max_laps}')
                    break

    def move_day_bus(self, bus):
        # Водитель едет на стоянку
        if bus.need_to_park:
            bus.park_on_station(self.parking_lot, self.validate)

            if bus.driver.driver_id in self.one_day_schedule:
                if len(self.one_day_schedule[bus.driver.driver_id][1]) < 2:
                    self.one_day_schedule[bus.driver.driver_id][1].append(self.clock_time)
            else:
                self.one_day_schedule[bus.driver.driver_id] = [[], [self.clock_time]]

            if not self.validate:
                print(f'Водитель-{bus.driver.driver_id} приехал в {self.clock_time}')
            bus.need_to_park = False
            if bus.driver.max_laps == bus.driver.max_laps_before_lunch:
                self.free_day_drivers.append(bus.driver)
                bus.driver.max_laps = bus.driver.max_laps_after_lunch
            bus.driver.laps = -1
            bus.driver = None
            if not self.validate:
                bus.driver_marker.set_text('')
                bus.driver_marker.set_position((0, 0))
            self.day_buses_on_track -= 1
            self.switch = True
        # Водителю не надо на стоянку
        else:
            if bus.in_drive == bus.delay or bus.current_stop.idx is None:
                bus.drive()
                if bus.current_stop.idx == 0:
                    bus.driver.laps += 1
                    if bus.driver.laps == bus.driver.max_laps:
                        bus.need_to_park = True
                bus.in_drive = 0
                bus.delay = random.choices([4, 5, 6, 7], [0.2, 0.5, 0.2, 0.1])[0]

    def move_night_bus(self, bus):
        if bus.need_to_park:
            bus.park_on_station(self.parking_lot, self.validate)

            if not self.validate:
                print(f'Водитель-{bus.driver.driver_id} приехал в {self.clock_time}')
            bus.need_to_park = False
            bus.driver.laps = -1
            bus.driver = None
            if not self.validate:
                bus.driver_marker.set_text('')
                bus.driver_marker.set_position((0, 0))
            self.night_buses_on_track -= 1
        else:
            if bus.in_drive == bus.delay or bus.current_stop.idx is None:
                bus.drive()
                if bus.current_stop.idx == 0:
                    bus.driver.laps += 1
                    if bus.driver.laps == bus.driver.max_laps:
                        bus.need_to_park = True
                        bus.driver.shifts += 1
                        if self.night_buses_on_track == self.drivers_in_night_shift:
                            self.need_nighters = False
                        if bus.driver.shifts < 4:
                            self.free_night_drivers.append(bus.driver)
                        if (1 < bus.driver.shifts < 4) or (self.day_of_week in self.weekends and bus.driver.shifts < 4):
                            new_minutes = self.minutes+11
                            new_hours = self.hours
                            if new_minutes >= 60:
                                new_minutes = new_minutes % 60
                                new_hours += 1
                            if new_hours == 24:
                                self.hours = 0
                            self.need_to_go = f'{new_hours:02d}:{new_minutes:02d}'
                        if bus.driver.shifts == 3:
                            bus.driver.max_laps = 1
                bus.in_drive = 0
                bus.delay = random.choices([4, 5, 6, 7], [0.2, 0.5, 0.2, 0.1])[0]

    def influx_of_people(self):
        for bus_stop in self.stops:
            if self.clock_time == '00:00':
                bus_stop.people = 0
            if self.day_of_week not in self.weekends:
                if (6 <= self.hours < 9) or (17 <= self.hours < 20):
                    bus_stop.people += random.randint(2, 4)
                elif (9 <= self.hours < 17) or (20 <= self.hours < 22):
                    bus_stop.people += random.randint(0, 1)
                elif (22 <= self.hours < 24) or (0 <= self.hours < 6):
                    if self.minutes % 30 == 0:
                        bus_stop.people += random.randint(0, 1)
            else:
                if 17 <= self.hours < 20:
                    bus_stop.people += random.randint(1, 2)
                elif (10 <= self.hours < 17) or (20 <= self.hours < 22):
                    bus_stop.people += random.randint(0, 1)

    def metric(self):
        total_transported = 0
        for bus in self.buses:
            total_transported += bus.transported
        number_of_day_drivers = len(self.day_drivers)
        number_of_night_drivers = len(self.night_drivers)
        driver_cost = 1 * number_of_day_drivers + 1.2 * number_of_night_drivers
        return (1 * total_transported) / (1 * driver_cost)



# Ваши позиции остановок
stops_positions = [
    (6, 11), (8, 11), (8, 7), (11, 7), (15, 7), (15, 10), (18, 10),
    (18, 4), (15, 4), (11, 4), (11, 2), (11, 0), (9, 0),(7, 0), (7, 3),
    (4, 3), (4, 6), (4, 11), (6, 11)
]

# Переменные
number_of_buses = 10
number_of_day_drivers = 18
number_of_night_drivers = 3

# Места для автобусов на станции
parking_positions = [(10, 5) for _ in range(number_of_buses)]

#sim = Simulation(stops_positions, parking_positions, number_of_buses, number_of_day_drivers, number_of_night_drivers, validate=True)
#metric = sim.run()


