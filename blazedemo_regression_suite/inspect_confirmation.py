"""Inspect reserve page DOM structure."""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import time

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
driver.set_page_load_timeout(30)
wait = WebDriverWait(driver, 15)

# Go to route search
driver.get("https://blazedemo.com/")
Select(driver.find_element(By.CSS_SELECTOR, "select[name='fromPort']")).select_by_visible_text("Paris")
Select(driver.find_element(By.CSS_SELECTOR, "select[name='toPort']")).select_by_visible_text("Buenos Aires")
driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

time.sleep(3)
print("URL:", driver.current_url)
print("TITLE:", driver.title)
print("=== BODY TEXT ===")
print(driver.find_element(By.TAG_NAME, "body").text[:2000])
print()
print("=== TABLE HTML ===")
tables = driver.find_elements(By.TAG_NAME, "table")
for i, t in enumerate(tables):
    print(f"--- Table {i} ---")
    html = t.get_attribute("outerHTML")
    print(html[:3000])

print()
print("=== ALL ROWS ===")
rows = driver.find_elements(By.XPATH, "//table/tbody/tr")
print(f"Found {len(rows)} rows via //table/tbody/tr")
for idx, row in enumerate(rows):
    cells = row.find_elements(By.TAG_NAME, "td")
    print(f"Row {idx}: {len(cells)} cells")
    for ci, cell in enumerate(cells):
        print(f"  Cell[{ci}]: '{cell.text.strip()}'")

driver.quit()
