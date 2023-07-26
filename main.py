import json
import os
import time
import sys
from selenium import webdriver
from bs4 import BeautifulSoup
from vertexai.preview.language_models import TextGenerationModel
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# Set up the ChromeDriver
options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--profile-directory=Default')
options.add_argument('--remote-debugging-port=9222')
options.add_argument('--crash-dumps-dir=/tmp')
options.add_argument('--user-data-dir=~/.config/google-chrome')

driver = webdriver.Chrome(options=options)

# Retrieve Job-defined env vars
TASK_INDEX = os.getenv("CLOUD_RUN_TASK_INDEX", 0)
TASK_ATTEMPT = os.getenv("CLOUD_RUN_TASK_ATTEMPT", 0)

# Replace "YOUR_WEBPAGE_URL_HERE" with the actual URL of the webpage you want to scrape
webpage_url = "http://34.149.45.141/"

# Define the CSS paths for the words you want to extract
css_paths = [
    "html.ng-scope body div.sentence.ng-scope div.line.line1.slide-in span.result.adjective.slide-in span.word.ng-binding",
    "html.ng-scope body div.sentence.ng-scope div.line.line1.slide-in span.result.noun.slide-in span.word.ng-binding",
    "html.ng-scope body div.sentence.ng-scope div.line.line2.slide-in span.result.verb.slide-in span.word.ng-binding",
]

def extract_words_from_webpage(url, css_paths, d):
    try:

        # Load the webpage
        d.get(url)

        # Wait for the dynamic content to load (you may need to adjust the waiting time)
        time.sleep(5)

        # Get the current page source after content is loaded
        page_source = d.page_source

        # Close the WebDriver
        d.quit()

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(page_source, "html.parser")

        # Extract words using the provided CSS paths
        words = []
        for css_path in css_paths:
            elements = soup.select(css_path)
            for element in elements:
                word = element.get_text(strip=True)
                if word:
                    words.append(word)

        return words

    except Exception as e:
        print("An error occurred:", e)
    return None

def main():

    print(f"Starting Task #{TASK_INDEX}, Attempt #{TASK_ATTEMPT}...")

    # Extract words from the webpage using Selenium
    extracted_words = extract_words_from_webpage(webpage_url, css_paths, driver)

    if extracted_words:
        print("Extracted words:", extracted_words)
        # Rest of the code to generate funny sentences using the extracted words...
        text_model = TextGenerationModel.from_pretrained("text-bison@001")

        words = ""
        for w in extracted_words:
            words = words + w + ' '

        prompt = "You are very funny. Make a one-sentence joke with these words: " + words + " and don't explain it."

        response = text_model.predict(prompt=prompt, temperature=0.5)

        print(response.text)

        print(f"Completed Task #{TASK_INDEX}.")

    else:
        print("Failed to extract words from the webpage.")

# Start script
if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        message = (
            f"Task #{TASK_INDEX}, " + f"Attempt #{TASK_ATTEMPT} failed: {str(err)}"
        )

        print(json.dumps({"message": message, "severity": "ERROR"}))
        sys.exit(1)  # Retry Job Task by exiting the process

