import numpy as np
import matplotlib.pyplot as plt

tau = 1.0
t = np.linspace(0, 5*tau, 1000)
y = (1/tau) * np.exp(-t/tau)

plt.plot(t, y, label='Impulzová odozva')
plt.axhline(0, color='black',linewidth=0.5)
plt.axvline(0, color='black',linewidth=0.5)
plt.xlabel('Čas (s)')
plt.ylabel('Amplitúda')
plt.title('Odpoveď systému 1. rádu na impulzový skok')
plt.legend()
plt.grid(True)
plt.show()  