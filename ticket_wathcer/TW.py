import requests
from bs4 import BeautifulSoup
import time
import random
import logging
import winsound
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ticket_monitor.log"),
        logging.StreamHandler()
    ]
)

# Configuration
TARGET_URL = "https://facility.ticketlink.co.kr/reserve/price/schedule/232972690?menuIndex=reserve"
LOGIN_URL = "https://ticketlink.co.kr/login"
CHECK_INTERVAL_MIN = 20  # Minimum seconds between checks
CHECK_INTERVAL_MAX = 40  # Maximum seconds between checks
TARGET_WORD = "매진"  # The word to monitor for changes (sold out)

# User credentials - replace with your actual credentials
USERNAME = "your_username"
PASSWORD = "your_password"

# User agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
]

def play_alert():
    """Play an alert sound when ticket status changes"""
    # Play alert sound (frequency = 1000Hz, duration = 1000ms)
    for _ in range(5):  # Play 5 times
        winsound.Beep(1000, 1000)
        time.sleep(0.5)
    
    logging.info("ALERT: Ticket status has changed!")

def get_random_user_agent():
    """Return a random user agent from the list"""
    return random.choice(USER_AGENTS)

def setup_driver():
    """Set up and return a configured Chrome WebDriver"""
    options = Options()
    # options.add_argument("--headless")  # Uncomment to run in headless mode
    options.add_argument(f"user-agent={get_random_user_agent()}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def login(driver):
    """Log in to TicketLink using Selenium"""
    try:
        logging.info("Attempting to log in...")
        driver.get(LOGIN_URL)
        
        # Wait for login form to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "userEmail"))
        )
        
        # Enter credentials and submit
        driver.find_element(By.ID, "userEmail").send_keys(USERNAME)
        driver.find_element(By.ID, "userPassword").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(text(), '로그인')]").click()
        
        # Wait for login to complete
        time.sleep(5)
        
        if "login" not in driver.current_url:
            logging.info("Login successful")
            return True
        else:
            logging.error("Login failed")
            return False
            
    except Exception as e:
        logging.error(f"Error during login: {str(e)}")
        return False

def check_ticket_status(driver):
    """Check the ticket availability status"""
    try:
        logging.info(f"Accessing target page: {TARGET_URL}")
        driver.get(TARGET_URL)
        
        # Wait for page to load completely
        time.sleep(5)
        
        # Look for elements that might contain the "매진" text
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find all buttons or elements that might contain ticket status
        status_elements = soup.find_all(["button", "span", "div"], class_=lambda c: c and ("status" in c.lower() or "btn" in c.lower()))
        
        # Look for the target word in these elements
        found_target_word = False
        for element in status_elements:
            if TARGET_WORD in element.text:
                found_target_word = True
                logging.info(f"Found '{TARGET_WORD}' in element: {element.text.strip()}")
                
        if not found_target_word:
            logging.info(f"'{TARGET_WORD}' not found - ticket status may have changed!")
            return False
        
        return True
        
    except Exception as e:
        logging.error(f"Error checking ticket status: {str(e)}")
        return None

def main():
    """Main function to run the monitoring process"""
    driver = setup_driver()
    
    try:
        if not login(driver):
            logging.error("Failed to log in. Please check your credentials.")
            return
        
        previous_status_sold_out = None
        
        while True:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logging.info(f"Checking ticket status at {current_time}")
            
            status_sold_out = check_ticket_status(driver)
            
            if status_sold_out is None:
                logging.warning("Could not determine ticket status. Will retry.")
            elif previous_status_sold_out is not None and previous_status_sold_out != status_sold_out:
                if status_sold_out:
                    logging.info("Ticket status changed: Now sold out")
                else:
                    logging.info("Ticket status changed: No longer sold out!")
                    play_alert()
            
            previous_status_sold_out = status_sold_out
            
            # Random sleep to avoid detection
            sleep_time = random.uniform(CHECK_INTERVAL_MIN, CHECK_INTERVAL_MAX)
            logging.info(f"Sleeping for {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user.")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
    finally:
        driver.quit()
        logging.info("Browser closed. Monitoring ended.")

if __name__ == "__main__":
    main()