# Author: Elyes Rayane Melbouci
# Purpose: This script takes screenshots at regular intervals, checks for significant changes using SSIM and histogram similarity, and saves the screenshots if changes are detected.

import sqlite3
import os
import time
import logging
from PIL import Image
import datetime
import numpy as np
import pyautogui
import cv2
from skimage.metrics import structural_similarity as ssim
import sys
import threading
from pathlib import Path

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# Paths to main directories
base_dir = Path.home() / 'Library' / 'Application Support' / 'RemindEnchanted'
screenshots_folder = base_dir / 'screenshots'
screenshots_folder.mkdir(parents=True, exist_ok=True)

def create_folder_for_today():
    """Create a directory for today's screenshots if it doesn't exist already."""
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    daily_folder = screenshots_folder / date_str
    if not daily_folder.exists():
        daily_folder.mkdir(parents=True, exist_ok=True)
    return daily_folder

def combined_similarity_check(img1, img2, threshold=0.95):
    """Check both SSIM and histogram similarity to determine if significant changes have occurred."""
    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    ssim_score, _ = ssim(img1_gray, img2_gray, full=True)

    # Convert the histograms to CV_32F
    hist1 = cv2.calcHist([img1_gray], [0], None, [256], [0, 256]).flatten()
    hist2 = cv2.calcHist([img2_gray], [0], None, [256], [0, 256]).flatten()
    hist1 = np.float32(hist1)
    hist2 = np.float32(hist2)

    hist_score = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

    return (ssim_score > threshold) and (hist_score > threshold)  # Adjust these thresholds as needed

def take_screenshot_with_feature_check(daily_folder, last_image=None):
    """Take a screenshot and check feature similarity before saving."""
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot.resize((1200, 1000)))  # Resize the screenshot to reduce memory usage
    screenshot = Image.fromarray(screenshot_np)

    if last_image is not None:
        if combined_similarity_check(screenshot_np, last_image):
            return last_image  # Images are similar, do not save

    # Save the image if no similarity is found
    now = datetime.datetime.now()
    time_str = now.strftime("%H-%M-%S-%f")
    filename = f'Screen_{time_str}.jpeg'
    filepath = daily_folder / filename
    screenshot = screenshot.convert('RGB')  # Convert to RGB to avoid RGBA to JPEG issue
    screenshot.save(str(filepath), 'JPEG')  # Convert Path to string
    return screenshot_np

def run_screenshot_interval(interval, duration, threshold=0.95, buffer_size=10):
    """Execute taking screenshots at regular intervals for a specified duration, only if changes are detected."""
    start_time = datetime.datetime.now()
    daily_folder = create_folder_for_today()
    last_image = None
    buffer = []

    while (datetime.datetime.now() - start_time).seconds < duration:
        last_image = take_screenshot_with_feature_check(daily_folder, last_image)
        buffer.append(last_image)
        if len(buffer) > buffer_size:
            buffer.pop(0)
        if len(buffer) >= 2:
            avg_ssim_score = np.mean([combined_similarity_check(buffer[i], buffer[i-1], threshold=0.9) for i in range(1, len(buffer))])
            if avg_ssim_score < threshold:
                threshold = avg_ssim_score * 0.9
        time.sleep(interval)

if __name__ == "__main__":
    interval_seconds = 2  # Interval between screenshots
    duration_seconds = 86400  # Total duration of capture in seconds
    thread1 = threading.Thread(target=run_screenshot_interval, args=(interval_seconds, duration_seconds, 0.9, 10))
    thread1.start()