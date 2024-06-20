from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Dict
from bs4 import BeautifulSoup
import time

'''
Given a link to a filter on pipeline, uses selenium to find the filter
and scrape 1) the number of results associated with it & 2) the filter name.
'''
class FilterParser:
  def __init__(self, chromedriver_path, email, password):
    self.chromedriver_path = chromedriver_path
    self.email = email
    self.password = password
    # configure the Chrome driver for selenium
    self.configure_chromeDriver()

  '''
  Configuration for the chrome driver
  See README.md for more on how to set the chrome driver up for development / testing / deployment
  '''
  def configure_chromeDriver(self):
    self.chrome_options = webdriver.ChromeOptions()
    # Comment the next two lines out for easier testing
    self.chrome_options.add_argument('--headless') 
    self.chrome_options.add_argument('--ignore-certificate-errors')
    self.chrome_options.add_argument("--window-size=1920,1080")
    self.chrome_options.add_argument('--disable-gpu')
    self.service = ChromeService(executable_path=self.chromedriver_path)
    self.driver = webdriver.Chrome(service=self.service, options=self.chrome_options)

  '''
  Methods to start and stop the chromedriver to "avoid issues with lingering processes"
  '''
  def start_driver(self):
    if self.driver is None:
      self.driver = webdriver.Chrome(service=self.service, options=self.chrome_options)

  def stop_driver(self):
    if self.driver is not None:
      self.driver.quit()
      self.driver = None

  '''
  Logs the user into pipeline CRM so we can scrape filters off of the site
  '''
  def pipeline_login(self, link, wait_time = 45):
    self.start_driver()
    try:
      # maximize the window to prevent the popup from getting in the way of the login
      self.driver.maximize_window()
      self.driver.get(link)
      # Try filling the username, password fields, then clicking the submit button with the webdriver
      WebDriverWait(self.driver, wait_time).until(EC.presence_of_element_located((By.CLASS_NAME, 'email_or_username')))
      email_in = self.driver.find_element(By.CLASS_NAME, "email_or_username")
      email_in.send_keys(self.email)
      print("Found email field...")
      # time.sleeps aren't great practice, but they're here to make sure that all the fields are filled w/o glitches
      time.sleep(1.5)
      WebDriverWait(self.driver, wait_time).until(EC.presence_of_element_located((By.ID, 'user_password')))
      password_in = self.driver.find_element(By.ID, "user_password")
      password_in.send_keys(self.password)
      print("Found password field...")
      time.sleep(1.5)
      # scroll all the way down in the window to make sure that the submit button isn't covered by a popup
      self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
      WebDriverWait(self.driver, wait_time).until(EC.presence_of_element_located((By.NAME, 'commit')))
      submit = self.driver.find_element(By.NAME, "commit")
      submit.click()
      print("Found submit button...")
    except Exception as e:
      print("Login failed...", e)

  '''
  Scrapes information about a filter on pipeline given a group name and a link to that filter
  '''
  def scrape_filter_count(self, link_to_group: Dict[str, str], wait_time = 60):
    link = list(link_to_group.keys())[0]
    # login to pipeline and set up the document that'll be inserted into the database
    self.pipeline_login(link)
    document = {"group": link_to_group[link], "name": "", "count": "NaN", "link": link, "status": ""}
    # Scrape the filter name and count from the pipeline page
    try:
      # find the results count for a particular filter
      WebDriverWait(self.driver, wait_time).until(EC.presence_of_element_located((By.CLASS_NAME, "sc-kiEqrO.haJDsm")))
      search_results = self.driver.find_elements(By.CLASS_NAME, "sc-kiEqrO.haJDsm")
      if search_results:
        inner_html = search_results[0].get_attribute('innerHTML')
        document["count"] = inner_html.split(" matches out of")[0]
        # find the filter name
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        name_results = [span.text for span in soup.find_all("span", {"class": "sc-dGHRig cmEAoJ"})]
        document["name"] = name_results[0]
        # set the filter status
        document["status"] = 200
      else:
        raise TimeoutError
    except Exception as e:
      print("Error with scraping", e)
      document["status"] = 409
    finally:
      self.stop_driver()
    return document

# Testing
if __name__ == '__main__':
  e = FilterParser("./chromedriver", "athreya.daniel@tuckadvisors.com", "Athreya123!")
  test_result = e.scrape_filter_count({"https://app.pipelinecrm.com/list/19633216": "test group 1"})
  print(test_result)
