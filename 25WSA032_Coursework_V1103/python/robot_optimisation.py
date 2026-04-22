from robots.ecosystem.factory import ecofactory
import matplotlib.pyplot as plt

plt.close('all')
plt.ion()

# create the ecosystem with 3 of each bot type and 2 chargers
es = ecofactory(robots=3, droids=3, drones=3, chargers=([20, 20], [60, 20]), pizzas=9)

es.display(show=0, pause=10)
es.debug = False
es.messages_on = False
es.duration = "1 week"

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

# print final KPI table using the ecosystem's built in tabulate method
# learned about this from the week 8 performance analysis guide
print("\n===== FINAL BOT PERFORMANCE =====")
es.tabulate('name', 'kind', 'status', 'units_delivered',
            'weight_delivered', 'distance', 'energy', 'damage',
            kind_class='Bot')

# flag any broken bots
print("\n===== BROKEN BOTS =====")
broken = list(es.registry(kind_class='Bot', status='broken').values())
if broken:
    for r in broken:
        print(f"{r['name']} ({r['kind']}) broke after {r['age']} hours - damage points: {r['damage']}")
else:
    print("No broken bots - all survived the run")

# simple bar chart of pizzas delivered per bot
bot_registers   = list(es.registry(kind_class='Bot').values())
names           = [r['name'] for r in bot_registers]
units_delivered = [r['units_delivered'] for r in bot_registers]

plt.figure()
plt.bar(names, units_delivered, color='steelblue')
plt.xlabel('Bot')
plt.ylabel('Pizzas delivered')
plt.title('Pizzas delivered per bot')
plt.tight_layout()
plt.savefig('python/kpi_deliveries.png')
plt.show(block=True)