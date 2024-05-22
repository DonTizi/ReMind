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

# Configuration de logging
logging.basicConfig(filename=os.path.join(os.path.dirname(__file__), 'logs', 'app.log'),
                    level=logging.INFO,
                    format='%(asctime)s: %(levelname)s: %(message)s')

# Chemins vers les dossiers principaux
main_folder = os.path.join(os.path.dirname(__file__), '..', 'screenshots')

def create_folder_for_today():
    """Create a directory for today's screenshots if it doesn't exist already."""
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    daily_folder = os.path.join(main_folder, date_str)
    if not os.path.exists(daily_folder):
        os.makedirs(daily_folder)
    return daily_folder

def combined_similarity_check(img1, img2):
    """Check both SSIM and histogram similarity to determine if significant changes have occurred."""
    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    ssim_score, _ = ssim(img1_gray, img2_gray, full=True)
    return ssim_score > 0.95  # Adjust these thresholds as needed

def take_screenshot_with_feature_check(daily_folder, last_image=None):
    """Take a screenshot and check feature similarity before saving."""
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    screenshot = Image.fromarray(screenshot_np)

    if last_image is not None:
        if combined_similarity_check(screenshot_np, last_image):
            return last_image  # Images are similar, do not save

    # Save the image if no similarity is found
    now = datetime.datetime.now()
    time_str = now.strftime("%H-%M-%S-%f")
    filename = f'Screen_{time_str}.jpeg'
    filepath = os.path.join(daily_folder, filename)
    screenshot = screenshot.convert('RGB')  # Convert to RGB to avoid RGBA to JPEG issue
    screenshot.save(filepath, 'JPEG')
    return screenshot_np

def run_screenshot_interval(interval, duration):
    """Execute taking screenshots at regular intervals for a specified duration, only if changes are detected."""
    start_time = datetime.datetime.now()
    daily_folder = create_folder_for_today()
    last_image = None

    while (datetime.datetime.now() - start_time).seconds < duration:
        last_image = take_screenshot_with_feature_check(daily_folder, last_image)
        time.sleep(interval)

if __name__ == "__main__":
    interval_seconds = 2  # Interval between screenshots
    duration_seconds = 3600  # Total duration of capture in seconds
    run_screenshot_interval(interval_seconds, duration_seconds)
