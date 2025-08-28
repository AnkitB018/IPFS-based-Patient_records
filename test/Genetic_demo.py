import random


# Chromosome Representation
class Chromosome:
    def __init__(self, replication_count=None, snapshot_interval=None, gateway_order=None):
        # Gene 1: replication count (1–5 copies of data)
        self.replication_count = replication_count if replication_count is not None else random.randint(1, 5)
        # Gene 2: snapshot interval (time units 1–10)
        self.snapshot_interval = snapshot_interval if snapshot_interval is not None else random.randint(1, 10)
        # Gene 3: gateway order (which gateway to prioritize, random permutation of 3)
        self.gateway_order = gateway_order if gateway_order is not None else random.sample(["A", "B", "C"], 3)

        self.fitness = None  # to be computed

    # Fitness function 
    def evaluate(self):
        replication_score = 10 - abs(self.replication_count - 3)
        interval_score = 10 - abs(self.snapshot_interval - 5)
        gateway_score = 5 if self.gateway_order[0] == "A" else 2

        self.fitness = replication_score + interval_score + gateway_score
        return self.fitness

    # Crossover
    def crossover(self, other):
        child1 = Chromosome(
            replication_count=self.replication_count,
            snapshot_interval=other.snapshot_interval,
            gateway_order=self.gateway_order[:2] + other.gateway_order[2:]
        )
        child2 = Chromosome(
            replication_count=other.replication_count,
            snapshot_interval=self.snapshot_interval,
            gateway_order=other.gateway_order[:2] + self.gateway_order[2:]
        )
        return child1, child2

    # Mutation
    def mutate(self):
        if random.random() < 0.3:  # 30% chance
            self.replication_count = random.randint(1, 5)
        if random.random() < 0.3:
            self.snapshot_interval = random.randint(1, 10)
        if random.random() < 0.3:
            random.shuffle(self.gateway_order)

    def __repr__(self):
        return (f"Chromosome(replication={self.replication_count}, "
                f"interval={self.snapshot_interval}, "
                f"gateways={self.gateway_order}, "
                f"fitness={self.fitness:.2f})")


# GA Driver
def init_population(size):
    return [Chromosome() for _ in range(size)]


def run_ga(generations=5, pop_size=6):
    population = init_population(pop_size)

    for gen in range(generations):
        print(f"\n--- Generation {gen+1} ---")

        # Evaluate current population
        for chromo in population:
            chromo.evaluate()
            print(chromo)

        # Select top 2 parents
        population.sort(key=lambda x: x.fitness, reverse=True)
        parents = population[:2]

        # Create next generation
        new_population = []
        while len(new_population) < pop_size:
            parent1, parent2 = random.sample(parents, 2)
            child1, child2 = parent1.crossover(parent2)

            child1.mutate()
            child2.mutate()

            new_population.extend([child1, child2])

        population = new_population[:pop_size]

    # ✅ Evaluate final population before picking best
    for chromo in population:
        chromo.evaluate()

    best = max(population, key=lambda x: x.fitness)
    print("\nBest solution found:", best)



# Run the GA
if __name__ == "__main__":
    run_ga()
