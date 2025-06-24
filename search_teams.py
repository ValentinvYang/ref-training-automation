import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Set up Chrome WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Navigate to the page
driver.get("https://teams.microsoft.com/v2/")
input("Navigate to the page and press ENTER here to continue...")

while True:
    print("Starting new learning session...")

    for i in range(5):
        try:
            # Wait for checkboxes to load
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='checkbox']"))
            )

            # Find all checkbox inputs
            checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
            if not checkboxes:
                print("No checkboxes found on the page. Check the URL or DOM structure.")
                driver.quit()
                exit()

            # Randomly select one
            selected_checkbox = random.choice(checkboxes)

            # Scroll to and click the selected checkbox
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", selected_checkbox)
            selected_checkbox.click()

            # Wait for the "Senden" button to be clickable
            send_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Senden')]"))
            )
            send_button = driver.find_element(By.XPATH, "//button[contains(@title, 'Senden')]")
            if not send_button:
                print("No send button found on the page. Check the URL or DOM structure.")
                driver.quit()
                exit()

            # Scroll down and click button
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", send_button)
            driver.execute_script("arguments[0].click();", send_button)

            print("Random answer selected and form submitted.")

            try: 
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Nächste Frage')]"))
                )
                next_button = driver.find_element(By.XPATH, "//button[contains(@title, 'Nächste Frage')]")
                if not next_button:
                    print("No next button found on the page. Check the URL or DOM structure.")
                    driver.quit()
                    exit()

                # Scroll down
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_button)
                next_button.click()
                print("Incorrect answer. Proceeding to next question.")
            except:
                print("Correct answer. Waiting for next question...")
                continue

        except Exception as e:
            print(f"Unexpected error: {e}")
            break

    try:
        yes_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Ja')]"))
        )        
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", yes_button)
        yes_button.click()
        print("🔁 New session started.")
    except Exception as e:
        print(f"❌ Could not find or click 'Ja' button: {e}")
        break

print("Finished or exited")
driver.quit()
