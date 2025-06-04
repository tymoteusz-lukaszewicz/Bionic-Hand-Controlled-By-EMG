import pygame
import serial
from collections import deque
import numpy as np
from scipy.signal import firwin

# ----- Serial Setup -----
ser = serial.Serial('COM4', 9600)  # Set your correct port
sampling_rate = 190  # Hz

# ----- FIR High-pass Filter Setup -----
cutoff_hz = 10  # Cutoff frequency in Hz
numtaps = 101  # Filter length (odd number recommended)
fir_coeff = firwin(numtaps, cutoff_hz, fs=sampling_rate, pass_zero=False)
fir_buffer = deque([0.0] * numtaps, maxlen=numtaps)

# ----- Pygame Setup -----
WIDTH, HEIGHT = 800, 400
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("EMG Real-Time Plot (Filtered & Raw)")
clock = pygame.time.Clock()

# ----- Signal Buffers -----
filtered_signal = deque([HEIGHT // 4] * WIDTH, maxlen=WIDTH)     # Upper half of screen
raw_signal = deque([3 * HEIGHT // 4] * WIDTH, maxlen=WIDTH)      # Lower half of screen

# ----- Rolling average buffer for raw signal centering -----
baseline_window = deque([0.0] * 30, maxlen=30)  # ~128 ms at 235 Hz

# ----- Colors -----
GREEN = (0, 255, 0)  # Filtered signal
RED = (255, 0, 0)    # Raw signal
BLACK = (0, 0, 0)    # Background

# ----- Scaling -----
scale_factor = 2  # Amplifies spikes

# ----- Main Loop -----
running = True
while running:
    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    try:
        line = ser.readline().decode(errors='ignore').strip()
        if line:
            value = float(line)

            # ----- Raw Signal Processing (with dynamic baseline) -----
            baseline_window.append(value)
            dynamic_center = sum(baseline_window) / len(baseline_window)
            raw_delta = (value - dynamic_center) * scale_factor
            y_raw = 3 * HEIGHT // 4 - int(raw_delta)
            y_raw = max(0, min(HEIGHT - 1, y_raw))
            raw_signal.append(y_raw)

            # ----- Filtered Signal Processing -----
            fir_buffer.append(value)
            if len(fir_buffer) == numtaps:
                filtered_value = np.dot(fir_coeff, list(fir_buffer))
                filtered_delta = filtered_value * scale_factor
                y_filtered = HEIGHT // 4 - int(filtered_delta)
                y_filtered = max(0, min(HEIGHT - 1, y_filtered))
                filtered_signal.append(y_filtered)

            # ----- Draw Raw Signal (Red) -----
            raw_points = [(i, y) for i, y in enumerate(raw_signal)]
            if len(raw_points) > 1:
                pygame.draw.lines(screen, RED, False, raw_points)

            # ----- Draw Filtered Signal (Green) -----
            filtered_points = [(i, y) for i, y in enumerate(filtered_signal)]
            if len(filtered_points) > 1:
                pygame.draw.lines(screen, GREEN, False, filtered_points)

    except (ValueError, serial.SerialException):
        pass

    pygame.display.flip()
    clock.tick(250)

pygame.quit()
