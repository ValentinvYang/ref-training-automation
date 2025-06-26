import random
import re
from pymongo import MongoClient

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Set up database
client = MongoClient('localhost', 27017)
db = client['ref-training']
collection = db['question']

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

            paragraphs = driver.find_elements(By.XPATH, "//p[contains(text(), '?')]")

            # Find all checkbox inputs
            checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
            if not checkboxes:
                print("No checkboxes found on the page. Check the URL or DOM structure.")
                driver.quit()
                exit()

            if paragraphs:
                question_element = paragraphs[-1]
                question_text = question_element.text
                print(question_element.text)

            answers = []
            label_map = {}

            # Extract text of checkboxes for database
            for checkbox in checkboxes:
                checkbox_id = checkbox.get_attribute("id")
                
                # 2. Find the associated label by matching the 'for' attribute
                try:
                    label = driver.find_element(By.XPATH, f"//label[@for='{checkbox_id}']")
                    label_text = label.text.strip()
                    answer_body = re.sub(r'^[A-C]\)\s*', '', label_text)
                    answers.append({"full": label_text, "body": answer_body, "checkbox": checkbox})
                except:
                    label_text = "(label not found)"
                
                print(f"Label text: {label_text}")

            # Check if question already in DB
            existing = collection.find_one({"question": question_text})

            if existing:
                print("!!!!!!!!!============ Question already exists in database. Using correct answers. ===========!!!!!!!!! ")

                correct_texts = []
                for answer in existing['answers']:
                    if answer.get('is_correct'):
                        correct_texts.append(answer['text'])

                for correct_text in correct_texts:
                    for ans in answers:
                        if correct_text in ans['body']:
                            checkbox = ans['checkbox']
                            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", checkbox)
                            time.sleep(0.3)
                            driver.execute_script("arguments[0].click();", checkbox)

            else:
                # Randomly select one
                selected_checkbox = random.choice(checkboxes)
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", selected_checkbox)
                time.sleep(0.5) # Let any hover/animation settle
                driver.execute_script("arguments[0].click();", selected_checkbox)

            # Wait for the "Senden" button to be clickable
            send_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Senden')]"))
            )
            send_button = driver.find_element(By.XPATH, "//button[contains(@title, 'Senden')]")

            # Scroll down and click button
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", send_button)
            driver.execute_script("arguments[0].click();", send_button)

            print("Answer submitted.")

            try:
                if i != 4:
                    time.sleep(2)                     
                    next_button = WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(@title, 'Nächste Frage')]"))
                    )
                    next_button = driver.find_element(By.XPATH, "//button[contains(@title, 'Nächste Frage')]")

                    # If WebDriverWait above has not thrown, this means our answer was wrong
                    print("Incorrect answer. Trying to extract correct answers")

                    # Scroll down
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_button)

                    correct_answers = driver.find_elements(By.XPATH, "//p[contains(text(), 'Die richtige Antwort ist')]")
                    correct_text_bodies = []
                    if correct_answers:
                        correct_answer = correct_answers[-1]
                        # Extract the letters out of the string:
                        answer_part = re.search(r'Die richtige Antwort ist (.*?)\.', correct_answer.text)
                        if answer_part:
                            # Get all A/B/C letters from string
                            correct_letters = re.findall(r'[ABC]', answer_part.group(1))
                            print("Extracted letters:", correct_letters)  

                            # Map each correct letter to the full label and extract the body
                            for letter in correct_letters:
                                for ans in answers:
                                    if ans['full'].startswith(f"{letter})"):
                                        # Extract body text without the label
                                        body = re.sub(rf"^{letter}\)\s*", "", ans['full']).strip();
                                        correct_text_bodies.append(body);   
                        print("Correct answer text bodies:", correct_text_bodies)

                    # Prepare data for writing into db
                    final_answers = []
                    for ans in answers:
                        is_correct = ans['body'] in correct_text_bodies
                        final_answers.append({"text": ans['body'], "is_correct": is_correct})

                    # Save question and answers to db 
                    doc = {
                        "question": question_text,
                        "answers": final_answers
                    }
                    collection.insert_one(doc)
                    print("Question saved to database")

                    # Continue
                    next_button.click()
                    print("Next question...")
                else:
                    print("----Fifth card through----")
            except:
                print("Correct answer. Waiting for next question...")

                # Check if not already in DB
                existing = collection.find_one({"question": question_text})
                if not existing:
                    print("Saving new correctly answered question to database.")

                    final_answers = []
                    for ans in answers:
                        is_correct = (ans['checkbox'] == selected_checkbox)
                        final_answers.append({
                            "text": ans['body'],
                            "is_correct": is_correct
                        })

                    doc = {
                        "question": question_text,
                        "answers": final_answers
                    }
                    collection.insert_one(doc)
                    print("✅ Question saved (correctly answered).")
                else:
                    print("Already in database, not saving.")

                continue

        except Exception as e:
            print(f"Unexpected error: {e}")
            break

    try:
        yes_button = WebDriverWait(driver, 8).until(
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
