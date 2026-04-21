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

# home position where bots return when idle
home = [40, 20, 0]

# basic charge threshold - will improve this later
charge_threshold = 0.20

while es.active:

    for bot in es.bots():

        # go charge if battery is low
        if bot.soc / bot.max_soc < charge_threshold and bot.station is None:
            charger = es.chargers()[0]
            bot.charge(charger)

        # if idle, find a pizza to deliver
        if bot.activity == 'idle':
            for pizza in es.deliverables():
                if pizza.status == 'ready':
                    bot.deliver(pizza)
                    break

        # go home if nothing to do
        if not bot.destination and bot.coordinates != home:
            bot.target_destination = home

        if bot.target_destination:
            bot.move()

    es.update()