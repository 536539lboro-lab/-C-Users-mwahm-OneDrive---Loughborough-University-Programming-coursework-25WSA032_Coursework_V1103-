from robots.ecosystem.factory import ecofactory
import matplotlib.pyplot as plt

plt.close('all')
plt.ion()

# ----------------------------------------------------------------
# helper function - returns charge threshold based on bot type
# robots are slower so need to start charging earlier
# drones are fast so can wait longer before charging
# ----------------------------------------------------------------
def get_charge_threshold(bot):
    if bot.kind == 'Robot':
        return 0.30
    elif bot.kind == 'Droid':
        return 0.25
    else:
        return 0.15


# ----------------------------------------------------------------
# helper function - finds nearest charger to a bot
# ----------------------------------------------------------------
def get_nearest_charger(bot, chargers):
    nearest = None
    nearest_dist = float('inf')
    for charger in chargers:
        d = ((bot.coordinates[0] - charger.coordinates[0])**2 +
             (bot.coordinates[1] - charger.coordinates[1])**2) **0.5
        if d < nearest_dist:
            nearest_dist = d
            nearest = charger
    return nearest


# ----------------------------------------------------------------
# helper function - finds nearest ready pizza to a bot
# ----------------------------------------------------------------
def get_nearest_pizza(bot, deliverables):
    nearest = None
    nearest_dist = float('inf')
    for pizza in deliverables:
        if pizza.status == 'ready':
            d = ((bot.coordinates[0] - pizza.coordinates[0])**2 +
                 (bot.coordinates[1] - pizza.coordinates[1])**2) **0.5
            if d < nearest_dist:
                nearest_dist = d
                nearest = pizza
    return nearest

# Optimisation notes:
# 1. Nearest charger - reduces travel time to charge, gets bots
#    back to deliveries faster. More important for slower bots.
# 2. Per-bot charge threshold - robots need a higher threshold
#    because they're slow and might not make it on 20%.
# 3. Nearest pizza - reduces empty travel distance, means bots
#    spend more time delivering and less time collecting.

# ================================================================
# RUN 1 - BASELINE (no optimisation, same as original demo)
# ================================================================
print("Running baseline (unoptimised)...")

es_baseline = ecofactory(robots=3, droids=3, drones=3, chargers=([20, 20], [60, 20]), pizzas=9)
es_baseline.display(show=0, pause=10)
es_baseline.debug = False
es_baseline.messages_on = False
es_baseline.duration = "1 week"

home = [40, 20, 0]
charger = es_baseline.chargers()[0]   # always use first charger - no optimisation
charge_threshold = 0.20               # fixed threshold for all bots - no optimisation

while es_baseline.active:
    for bot in es_baseline.bots():

        # basic charging - always go to first charger
        if bot.soc / bot.max_soc < charge_threshold and bot.station is None:
            bot.charge(charger)

        if bot.activity == 'idle':
            # basic pizza allocation - just take first available
            for pizza in es_baseline.deliverables():
                if pizza.status == 'ready':
                    bot.deliver(pizza)
                    break
            # go home if nothing to do
            if not bot.destination and bot.coordinates != home:
                bot.target_destination = home

        if bot.target_destination:
            bot.move()

    es_baseline.update()

print("Baseline run complete.")


# ================================================================
# RUN 2 - OPTIMISED (nearest charger + nearest pizza)
# ================================================================
print("Running optimised version...")

es_opt = ecofactory(robots=3, droids=3, drones=3, chargers=([20, 20], [60, 20]), pizzas=9)
es_opt.display(show=0, pause=10)
es_opt.debug = False
es_opt.messages_on = False
es_opt.duration = "1 week"

while es_opt.active:
    for bot in es_opt.bots():

        # optimised charging - nearest charger, per-bot threshold
        if bot.soc / bot.max_soc < get_charge_threshold(bot) and bot.station is None:
            nearest_charger = get_nearest_charger(bot, es_opt.chargers())
            bot.charge(nearest_charger)

        if bot.activity == 'idle':
            # optimised pizza allocation - nearest pizza
            nearest_pizza = get_nearest_pizza(bot, es_opt.deliverables())
            if nearest_pizza:
                bot.deliver(nearest_pizza)
            # go home if nothing to do
            if not bot.destination and bot.coordinates != home:
                bot.target_destination = home

        if bot.target_destination:
            bot.move()

    es_opt.update()

print("Optimised run complete.")


# ================================================================
# KPI COMPARISON
# ================================================================

# get totals from baseline
baseline_regs = list(es_baseline.registry(kind_class='Bot').values())
baseline_units    = sum(r['units_delivered'] for r in baseline_regs)
baseline_weight   = sum(r['weight_delivered'] for r in baseline_regs)
baseline_distance = sum(r['distance'] for r in baseline_regs)
baseline_broken   = sum(1 for r in baseline_regs if r['status'] == 'broken')

# get totals from optimised
opt_regs = list(es_opt.registry(kind_class='Bot').values())
opt_units    = sum(r['units_delivered'] for r in opt_regs)
opt_weight   = sum(r['weight_delivered'] for r in opt_regs)
opt_distance = sum(r['distance'] for r in opt_regs)
opt_broken   = sum(1 for r in opt_regs if r['status'] == 'broken')

# print comparison table
print("\n===== KPI COMPARISON: BASELINE vs OPTIMISED =====")
print(f"{'Metric':<25} {'Baseline':>12} {'Optimised':>12} {'Difference':>12}")
print("-" * 63)
print(f"{'Pizzas delivered':<25} {baseline_units:>12} {opt_units:>12} {opt_units - baseline_units:>+12}")
print(f"{'Weight delivered (kg)':<25} {baseline_weight:>12} {opt_weight:>12} {opt_weight - baseline_weight:>+12}")
print(f"{'Total distance':<25} {round(baseline_distance,1):>12} {round(opt_distance,1):>12} {round(opt_distance - baseline_distance,1):>+12}")
print(f"{'Broken bots':<25} {baseline_broken:>12} {opt_broken:>12} {opt_broken - baseline_broken:>+12}")
print("-" * 63)

# print individual bot tables
print("\n===== BASELINE - INDIVIDUAL BOTS =====")
es_baseline.tabulate('name', 'kind', 'status', 'units_delivered',
                     'weight_delivered', 'distance', 'energy', 'damage',
                     kind_class='Bot')

print("\n===== OPTIMISED - INDIVIDUAL BOTS =====")
es_opt.tabulate('name', 'kind', 'status', 'units_delivered',
                'weight_delivered', 'distance', 'energy', 'damage',
                kind_class='Bot')

# flag broken bots
print("\n===== BROKEN BOTS =====")
broken = list(es_opt.registry(kind_class='Bot', status='broken').values())
if broken:
    for r in broken:
        print(f"{r['name']} ({r['kind']}) broke after {r['age']} hours - damage points: {r['damage']}")
else:
    print("No broken bots in optimised run")

# bar chart comparing deliveries per bot for both runs
baseline_names  = [r['name'] for r in baseline_regs]
baseline_deliv  = [r['units_delivered'] for r in baseline_regs]
opt_names       = [r['name'] for r in opt_regs]
opt_deliv       = [r['units_delivered'] for r in opt_regs]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

ax1.bar(baseline_names, baseline_deliv, color='tomato')
ax1.set_xlabel('Bot')
ax1.set_ylabel('Pizzas delivered')
ax1.set_title('Baseline - Pizzas delivered per bot')

ax2.bar(opt_names, opt_deliv, color='steelblue')
ax2.set_xlabel('Bot')
ax2.set_ylabel('Pizzas delivered')
ax2.set_title('Optimised - Pizzas delivered per bot')

plt.tight_layout()
plt.savefig('python/kpi_comparison.png')
plt.show(block=True)