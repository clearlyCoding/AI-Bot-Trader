import time

# Path to the file
filename = 'trace.txt'

# Loop to write to the file every 3 seconds
while True:
    with open(filename, 'a') as file:
        file.write('abc123\n')  # Writes abc123 and a newline to the file
    time.sleep(3)  # Waits for 3 seconds before the next write