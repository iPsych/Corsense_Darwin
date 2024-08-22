import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from csDriver import Corsense
import numpy as np
import asyncio
import threading

# Initialize communication with CorSense
cs = Corsense()

# Initialise figure
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

# Initialise variables
xs = []
ys = []
idxs = []
temp = []

def animate(i):
    global xs, ys, idxs, temp
    rr = cs.rr()[0]

    if rr > 0:
        temp.append(rr)

        if len(temp) > 10:
            medRR = np.median(temp[-9:])
            mrr = np.abs(np.diff(temp) - medRR)
            idxs = np.where(mrr > 250)[0]

            # remove if consecutive
            idxs = np.delete(idxs, np.where(np.diff(idxs) == 1)[0] + 1)

            idxs = list(idxs)

            xs.append(dt.datetime.now().strftime('%S.%f'))
            ys.append(rr)

            ax.clear()
            ax.plot(xs, ys, markevery=idxs, marker='o', color='steelblue', markerfacecolor="firebrick",
                    markeredgecolor="firebrick")

        plt.xticks([])
        plt.title('RR Intervals over Time')
        plt.ylabel('RR (ms)')

async def run_ble():
    await cs.initialize()
    while True:
        await asyncio.sleep(0.1)  # Keeps the BLE connection alive

def run_asyncio_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Create a new event loop for the asyncio thread
asyncio_loop = asyncio.new_event_loop()

# Start the asyncio loop in a separate thread
threading.Thread(target=run_asyncio_loop, args=(asyncio_loop,), daemon=True).start()

# Schedule the BLE task in the asyncio loop
asyncio_loop.call_soon_threadsafe(lambda: asyncio.create_task(run_ble()))

# Start the matplotlib animation
anim = animation.FuncAnimation(fig, animate, interval=1000)
plt.show()