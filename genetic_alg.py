from route_simulation import *

import random


# Параметры генетического алгоритма
POPULATION_SIZE = 20  # Размер популяции
GENERATIONS = 30  # Количество поколений
MUTATION_RATE = 0.1  # Вероятность мутации


# Генерация начальной популяции
def generate_population(size, n1_range, n2_range):
    return [
        (random.choice(range(n1_range[0], n1_range[1] + 1, 2)),  # Четные значения для N1
         random.choice(range(n2_range[0], n2_range[1] + 1, 3)))  # Кратные 3 для N2
        for _ in range(size)
    ]


# Оценка фитнеса (метрики)
def fitness(individual):
    n1, n2 = individual
    simulation = Simulation(stops_positions, parking_positions, number_of_buses, n1, n2, validate=True)
    return simulation.run(), simulation.one_day_schedule  # Возвращаем значение метрики


# Селекция лучших индивидов
def select(population, fitness_scores, num_select):
    sorted_population = sorted(zip(population, fitness_scores), key=lambda x: x[1], reverse=True)
    return [ind for ind, _ in sorted_population[:num_select]]


# Скрещивание (комбинация родителей)
def crossover(parent1, parent2):
    n1 = random.choice([parent1[0], parent2[0]])  # Выбираем четное значение из родителей
    n2 = random.choice([parent1[1], parent2[1]])  # Выбираем кратное 3 значение из родителей
    return (n1, n2)


# Мутация (случайное изменение)
def mutate(individual, n1_range, n2_range):
    n1, n2 = individual
    if random.random() < MUTATION_RATE:
        n1 = random.choice(range(n1_range[0], n1_range[1] + 1, 2))  # Новое четное значение для N1
    if random.random() < MUTATION_RATE:
        n2 = random.choice(range(n2_range[0], n2_range[1] + 1, 3))  # Новое кратное 3 значение для N2
    return (n1, n2)


# Генетический алгоритм
def genetic_algorithm(n1_range, n2_range):
    population = generate_population(POPULATION_SIZE, n1_range, n2_range)
    best_individual = None
    best_fitness = float('-inf')

    for generation in range(GENERATIONS):
        # Оцениваем фитнес
        metrics = [fitness(ind) for ind in population]

        fitness_scores = [i[0] for i in metrics]

        # Сохраняем лучшего индивида
        max_gen_fitness = max(fitness_scores)
        if max_gen_fitness > best_fitness:
            best_fitness = max_gen_fitness
            best_schedule = metrics[fitness_scores.index(max_gen_fitness)][1]
            best_individual = population[fitness_scores.index(max_gen_fitness)]

        print(f"Поколение {generation + 1}: Лучший результат по метрике = {best_fitness}")

        # Селекция
        selected = select(population, fitness_scores, POPULATION_SIZE // 2)

        # Скрещивание и создание новой популяции
        offspring = []
        while len(offspring) < POPULATION_SIZE:
            parent1, parent2 = random.sample(selected, 2)
            child = crossover(parent1, parent2)
            child = mutate(child, n1_range, n2_range)
            offspring.append(child)

        population = offspring

    return best_individual, best_fitness, best_schedule


# Диапазоны водителей
n1_range = (2, 90)  # Четные значения для водителей типа 1
n2_range = (3, 99)  # Кратные 3 значения для водителей типа 2

# Запуск генетического алгоритма
best_solution, best_metric, best_schedule = genetic_algorithm(n1_range, n2_range)
print(f"Лучшее решение: Водители типа 1 = {best_solution[0]}, Водители типа 2 = {best_solution[1]}")
print(f"Максимальная метрика: {best_metric}")
for key, value in best_schedule.items():
    print(f'Водитель {key} выехал в {value[0][0]} приехал в {value[1][0]}, выехал в {value[0][1]}, приехал в {value[1][1]}')
