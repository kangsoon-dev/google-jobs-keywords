from email.mime import application
from wsgiref.util import application_uri
import pandas as pd
import datetime
import logging
import time
import random
import os
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

GJOBS_URL = "https://www.google.com/search?q={}&ibp=htl;jobs"
GJOBS_URL_TODAY_SUBSTRING = "#htivrt=jobs&htichips=date_posted:today&htischips=date_posted;today"
OUTPUT_FILE_DIR = "job_scrape_master.csv"
THRESHOLD=10
CAP=50

class TimeKeeper:
    @property
    def now(self):
        '''
        return the current correct date and time using the format specified
        '''
        return f'{datetime.datetime.now():%d-%b-%Y T%I:%M}'

class GoogleJobsPageLocators:
    jobs_cards = 'li'
    job_desc_card_visible = '[id="tl_ditc"]'
    job_full_desc_button='[class="atHusc"]'
    job_desc_tag = '[class*=HBvzbc]'
    title_tag = '[class*=sH3zFd]'
    publisher_tag = '[class*=tJ9zfc]'
    result_title = '[class*="Fol1qc"]'
    publisher = '[class*=vNEEBe]'
    details = '[class*=I2Cbhb]'
    apply_link_cards = '[class*=DaDV9e]'

def scroll_element_into_view_and_click(driver, element):
    driver.execute_script("arguments[0].scrollIntoView();", element)
    element.click()

def show_full_job_description(job_desc_card):
    try:
        driver.implicitly_wait(0)
        full_desc_button = job_desc_card.find_element_by_css_selector(GoogleJobsPageLocators.job_full_desc_button)
        full_desc_button.click()
        driver.implicitly_wait(3)
    except Exception as e: # if no show full desc button found, continue
        driver.implicitly_wait(3)
        return

def create_driver_handler(driver_path="./chromedriver.exe"):
    '''
    creates a browser instance for selenium, 
    it adds some functionalities into the browser instance
    '''
    chrome_options = Options()
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("log-level=3")
    # the following two options are used to take out the chrome browser infobar
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_experimental_option("excludeSwitches",["enable-automation"])
    driver_instance = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
    driver_instance.implicitly_wait(10)
    return driver_instance

def nap(secs=random.randint(0,5)):
    '''
    sleeps the bot for specified number of seconds
    '''
    logging.info(f"Napping for {secs} seconds")
    print("nap for {} seconds".format(secs))
    time.sleep(secs)

def get_jobs(driver):
    timekeeper = TimeKeeper()
    job_cards = driver.find_elements_by_tag_name(GoogleJobsPageLocators.jobs_cards)
    
    if job_cards:
        count = 1
        while True: 
            try:
                card = job_cards[count-1]
                scroll_element_into_view_and_click(driver,card)
            except IndexError as err:
                break
            
            job_desc_card = driver.find_element_by_css_selector(GoogleJobsPageLocators.job_desc_card_visible)
            show_full_job_description(job_desc_card)
            scrape_job(timekeeper, job_desc_card)

            if (count % THRESHOLD) == 0: # this will trigger on the 10th item 
                nap(random.randint(1,6))
                job_cards = driver.find_elements_by_tag_name(GoogleJobsPageLocators.jobs_cards)

            if count == len(job_cards):
                logging.info("\aNew data isn't coming in.")
                break
            
            if count == CAP:
                break
            
            count += 1

def unpack_details(details):
    if len(details) == 0:
        return ["","",""]
    if len(details) == 1:
        return [details[0].text,"",""]
    elif len(details) == 2:
        return [details[0].text,"",details[1].text]
    elif len(details) == 3:
        if details[1].text[-4:] == "mins":
            return [details[0].text,"",details[2].text]
        else:
            return [details[0].text,details[1].text,details[2].text]
        
def scrape_job(timekeeper, desc_card):
    scrape_time = timekeeper.now
    job_title = desc_card.find_element_by_css_selector(GoogleJobsPageLocators.title_tag).text.split("\n")[0]
    pbctry = desc_card.find_element_by_css_selector(GoogleJobsPageLocators.publisher_tag).text
    publisher = pbctry.split("\n")[0]
    #country = pbctry.split("\n")[1]
    job_desc = desc_card.find_element_by_css_selector(GoogleJobsPageLocators.job_desc_tag).text
    details_elements = desc_card.find_elements_by_css_selector(GoogleJobsPageLocators.details)
    time_posted, salary, job_type = unpack_details(details_elements)
    application_link = [x.get_attribute("href") for x in desc_card.find_element_by_css_selector(GoogleJobsPageLocators.apply_link_cards).find_elements_by_xpath("//a[@href]") if x.text[:8] == "Apply on"]

    row = {
        "scrape_time": scrape_time,
        "job_title": job_title,
        "publisher": publisher,
        # "country": country,
        "time_posted":time_posted,
        "salary":salary,
        "job_type":job_type,
        "desc":job_desc,
        "application_link":application_link
    }

    df = pd.DataFrame.from_dict([row])
    try:
        df.to_csv(OUTPUT_FILE_DIR, mode='a', encoding='CP1252',header=not os.path.exists(OUTPUT_FILE_DIR),index=False)
    except Exception as e:
        logging.info("error with encoding on row:" + job_title + "@" + publisher)
        return

parser = argparse.ArgumentParser()
parser.add_argument('--search_term',type=str,help='job term to search for')
parser.add_argument('--limit',type=int,help='maximum number of jobs to scrape',default = 200)
parser.add_argument('--is_today',type=str,help='only scrape jobs posted today')
args = parser.parse_args()
CAP = args.limit
driver = create_driver_handler()
search_term = "data engineer"
search_page_url = GJOBS_URL.format(args.search_term)
if args.is_today == "True":
    search_page_url += GJOBS_URL_TODAY_SUBSTRING
driver.get(search_page_url)
get_jobs(driver)