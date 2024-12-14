from route_simulation import *

# Перебираем комбинации водителей
best_n1, best_n2 = 0, 0
max_metric = 0
best_schedule = []

for n1 in range(2, 90, 2):  # Водители типа 1
    for n2 in range(3, 99, 3):  # Водители типа 2
        # Симуляция перевезенных пассажиров
        simulation = Simulation(stops_positions, parking_positions, number_of_buses, n1, n2, validate=True)
        metric = simulation.run()
        if metric > max_metric:
            max_metric = metric
            best_n1, best_n2 = n1, n2
            best_schedule = simulation.one_day_schedule

print(f"Количество водителей: Тип 1 - {best_n1}, Тип 2 - {best_n2}, метрика - {max_metric}")
for key, value in best_schedule.items():
    print(f'Водитель {key} выехал в {value[0][0]} приехал в {value[1][0]}, выехал в {value[0][1]}, приехал в {value[1][1]}')
