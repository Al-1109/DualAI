import datetime
import socket

print(f"Test deploy successful at: {datetime.datetime.now()}")
print(f"Running from: {__file__}")
print(f"Hostname: {socket.gethostname()}") 