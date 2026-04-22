from robots.ecosystem.factory import ecofactory
import matplotlib.pyplot as plt

plt.close('all')
plt.ion()

# create the ecosystem with 3 of each bot type and 2 chargers
es = ecofactory(robots=3, droids=3, drones=3, chargers=([20, 20], [60, 20]), pizzas=9)

es.display(show=1, pause=10)
es.debug = False
es.messages_on = False
es.duration = "1 week"

# KPI tracking - store starting values so we can compare at the end
kpi_start_distance = {}
kpi_start_delivered = {}
kpi_start_energy = {}

for bot in es.bots():
    kpi_start_distance[bot.name] = bot.distance
    kpi_start_delivered[bot.name] = bot.units_delivered
    kpi_start_energy[bot.name] = bot.energy

# home position where bots return when idle
home = [40, 20, 0]

# home position where bots return when idle
home = [40, 20, 0]

# different charge thresholds for each bot type
# robots are slower so they need to leave for charging earlier
# drones are faster so they can wait longer before charging
def get_charge_threshold(bot):
    if bot.kind == 'Robot':
        return 0.30   # slow bot, needs more buffer to reach charger
    elif bot.kind == 'Droid':
        return 0.25   # medium speed
    else:
        return 0.15   # drone is fast so can leave it later

while es.active:

    # store final KPI values after the run
    kpi_end_distance = {}
    kpi_end_delivered = {}
    kpi_end_energy = {}

    for bot in es.bots():
        kpi_end_distance[bot.name] = bot.distance
        kpi_end_delivered[bot.name] = bot.units_delivered
        kpi_end_energy[bot.name] = bot.energy

    for bot in es.bots():

        # go charge if battery is low
        # pick the nearest charger instead of always using the first one
        if bot.soc / bot.max_soc < get_charge_threshold(bot) and bot.station is None:
            nearest_charger = None
            nearest_dist = float('inf')
            for charger in es.chargers():
                d = ((bot.coordinates[0] - charger.coordinates[0])**2 +
                     (bot.coordinates[1] - charger.coordinates[1])**2) **0.5
                if d < nearest_dist:
                    nearest_dist = d
                    nearest_charger = charger
            bot.charge(nearest_charger)

        # if idle, find the nearest ready pizza instead of just the first one
        if bot.activity == 'idle':
            nearest_pizza = None
            nearest_dist = float('inf')
            for pizza in es.deliverables():
                if pizza.status == 'ready':
                    d = ((bot.coordinates[0] - pizza.coordinates[0])**2 +
                         (bot.coordinates[1] - pizza.coordinates[1])**2) **0.5
                    if d < nearest_dist:
                        nearest_dist = d
                        nearest_pizza = pizza
            if nearest_pizza:
                bot.deliver(nearest_pizza)

        # go home if nothing to do
        if not bot.destination and bot.coordinates != home:
            bot.target_destination = home

        if bot.target_destination:
            bot.move()

    es.update()

# print KPI results in a readable format
print("\n===== KPI RESULTS =====")
print(f"{'Bot':<10} {'Deliveries':>12} {'Distance':>12} {'Energy':>12}")
print("-" * 48)

for bot in es.bots():
    deliveries = kpi_end_delivered[bot.name] - kpi_start_delivered[bot.name]
    dist       = kpi_end_distance[bot.name] - kpi_start_distance[bot.name]
    energy     = kpi_end_energy[bot.name] - kpi_start_energy[bot.name]
    print(f"{bot.name:<10} {deliveries:>12} {round(dist,2):>12} {round(energy,2):>12}")

print("-" * 48)

# total across all bots
total_deliveries = sum(kpi_end_delivered[b.name] - kpi_start_delivered[b.name] for b in es.bots())
total_distance   = sum(kpi_end_distance[b.name] - kpi_start_distance[b.name] for b in es.bots())
total_energy     = sum(kpi_end_energy[b.name] - kpi_start_energy[b.name] for b in es.bots())

print(f"{'TOTAL':<10} {total_deliveries:>12} {round(total_distance,2):>12} {round(total_energy,2):>12}")
print("=======================\n")