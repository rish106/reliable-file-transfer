import matplotlib.pyplot as plt
import numpy as np

# Read data from data.txt
data = np.loadtxt('onemore.txt', delimiter=' ')  # You may need to adjust the delimiter

# Extract x and y data
x = data[:, 0]
y = data[:, 1]

# Create a scatter plot
plt.figure(figsize=(8, 6))
plt.scatter(x, y, c='blue', marker='o',s=1)
plt.xlabel('Time (s)')
plt.ylabel('Offset')
plt.title('Time vs Offset')
plt.grid(True)

# Save the plot as a PDF
plt.savefig('scatter_plot.pdf', format='pdf')

# Display the plot (optional)
plt.show()

