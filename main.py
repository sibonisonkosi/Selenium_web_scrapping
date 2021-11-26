from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import pickle
import json
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
# package for sharepoint
from shareplum import Office365
from shareplum import Site
from shareplum.site import Version

from requests.auth import HTTPBasicAuth
import requests
import json
import numpy as np


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)


class Methods:
    to_pass_credentials = HTTPBasicAuth('API auth-code')
    url_campaigns = "api_link"
    campaign_ids = []
    authcookie = Office365('https://_sharepoint_', username='_company_email_',
                           password='password').GetCookies()
    site = Site('https://_sharepoint_/sites/_group_/', version=Version.v365,
                authcookie=authcookie)
    folder = site.Folder('Shared Documents')
    dont_need_campaigns = open('dont_need_v1.txt')

    def __init__(self):
        self.response = requests.get(self.url_campaigns, auth=self.to_pass_credentials)
        self.all_campaigns = self.response.json()
        self.dont_need_campaigns_array = self.dont_need_campaigns.read().split(sep='\n')

    def create_campaign_list_from_api(self):
        for all_camp in self.all_campaigns:
            if str(all_camp['id']) not in self.dont_need_campaigns_array:
                self.campaign_ids.append(all_camp['id'])
        return self.campaign_ids

    def get_total_pros_per_page(self, pros_rows):
        list_allpages_lastpage = []
        no_ = self.extract_prospect_list(pros_rows)
        first_split = int(str(no_ / 10).split('.')[0])
        second_split = int(str(no_ / 10).split('.')[1])

        list_allpages_lastpage.append(first_split)
        list_allpages_lastpage.append(second_split)
        return list_allpages_lastpage

    def extract_prospect_list(self, pros_rows):
        pros_no = pros_rows.split()[0].replace("(", '') if '(' in pros_rows.split()[0] else pros_rows.split()[0]
        print(pros_rows, pros_no)
        return int(pros_no)


# Creating class Methode object

obj_ = Methods()

# Change this when you about to host to Luna
# PATH = 'C:\Program Files (x86)\chromedriver.exe'
# driver = webdriver.Chrome(PATH)
driver = webdriver.Chrome(ChromeDriverManager().install())

# start login code
url_login = '_link_'  # used as a login URL
driver.get(url_login)

# Retrieve cookies if you have entered the credentials once, if not there will be no session to re-call
cookies_found = False
try:
    cookies = pickle.load(open("cookies.pkl", "rb"))
    cookies_found = True
except FileNotFoundError as e:
    cookies_found = False

if cookies_found:
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get(url_login)
else:
    username = driver.find_element_by_name("login")
    username.send_keys("_username_")
    password = driver.find_element_by_name("password")
    password.send_keys("_password_")
    password.send_keys(Keys.RETURN)
    pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))  # save cookies

# End login code

# to be used stats url with a string holder "%s"
url_campaign_edit = 'https://_link_/%s'
campaign_ids = obj_.create_campaign_list_from_api()  # this returns a list of filtered campaigns
field_campaigns = []
campaigns_with_steps = []
count = 0

# Start of main for loop
for campaigns in campaign_ids:
    dict_list_of_all_pros = {}
    running = False  # True if the campaign is running
    first_edit_page = True  # Woodpecker has two different edits
    existing_data = json.load(open('scraped_prospect.json', encoding="utf8"))
    if str(campaigns) not in existing_data.keys():

        try:
            #  The loop is to be broken if the execution is successful else it's going to keep repeating.
            while True:
                try:
                    try:
                        driver.get(url_campaign_edit % campaigns)
                        print(url_campaign_edit % campaigns)
                        count = count + 1
                        print(count)
                        from_stats = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR,
                                                            "#divContent > div > div > div.boxSummaryHead > div > div.headerName > "
                                                            "div > div.data > a"))
                        )
                        try:

                            from_stats.click()
                        except ElementClickInterceptedException:
                            print('from hyperlink failed to click')
                            continue

                        # Checking if the pause pop-up exist
                        try:
                            pause_for_editing = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                "#body > div.MyCustomPopupPanel.mcp-show > div > div > "
                                                                "div > div > div.content-cont > div.popup-actions > "
                                                                "div.btn-green"))
                            )
                            try:
                                driver.execute_script("arguments[0].click();", pause_for_editing)
                                # pause_for_editing.click()
                            except ElementClickInterceptedException:
                                print('Unable to click pause')
                                continue

                            running = True
                        except:
                            running = False
                    except NoSuchElementException:
                        print('Element not found, re-trying')
                        # Continue under all exception is for starting the while loop again.
                        continue
                    # This try catch is search if edit is the first search for a specific property
                    try:
                        second_edit_content = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR,
                                 "#divContent > div > div > div:nth-child(2) > div > div > div.gwt-Label.hand.step"))
                        )
                        first_edit_page = False
                    except:
                        first_edit_page = True

                    # Main commands
                    if first_edit_page:
                        # Show hidden div tags for prospects
                        select_all_div = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR,
                                 "#divContent > div > div:nth-child(4) > div.ifcampaign-step--title.step--hidden"))
                        )
                        # To interact with javascript
                        driver.execute_script("arguments[0].click();", select_all_div)
                        # catching the number of prospects
                        no_of_prospects = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR,
                                 "#divContent > div > div:nth-child(4) > div.ifcampaign-step--subtitle"))
                        )

                        total_pros = no_of_prospects.get_attribute('innerHTML')
                        if total_pros == "":
                            total_pros = "0 in campaigns"
                        # clean the total_pros to list with total table pages and how many in the last page
                        row_no_list = obj_.get_total_pros_per_page(total_pros)

                        # Dictionary to hold prospects and save it to a file
                        dict_list_of_all_pros[campaigns] = []
                        for x in range(len(row_no_list)):
                            # what is used e.g: [4,5] four is the number of pages and is the number of prospect
                            # in the last page
                            all_ = row_no_list[x]
                            if x == 0:
                                while all_ != 0:
                                    for y in range(10):
                                        prospect = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                                  "div.ifcampaign-cont.no-width-limit > "
                                                                  "div.new_prospects > div:nth-child(2) > "
                                                                  "div:nth-child(2) > div.new_prospects--table-panel > "
                                                                  "div.newTable > div > div > div > div > div > "
                                                                  "div.tableConst > div > div.panelTable > "
                                                                  "div.panelCels > div.myColumn > div.data > "
                                                                  "div:nth-child(%s) > div > "
                                                                  "div.gwt-Label.cellLabel.handText" % str(
                                                    y + 1)))
                                        )

                                        status = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                                  "div.ifcampaign-cont.no-width-limit > div.new_prospects "
                                                                  "> div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > "
                                                                  "div > div > div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar"
                                                                  "-visible > div.csp-content-wrapper > div > "
                                                                  "div.panelMove > div.panelTable > div.panelCels > "
                                                                  "div:nth-child(1) > div.data > div:nth-child(%s) > div > "
                                                                  "span.ddm-text" % str(y + 1)))
                                        )

                                        last_contacted = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                                  "div.ifcampaign-cont.no-width-limit > div.new_prospects "
                                                                  "> div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > "
                                                                  "div > div > div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar"
                                                                  "-visible > div.csp-content-wrapper > div > "
                                                                  "div.panelMove > div.panelTable > div.panelCels > "
                                                                  "div:nth-child(9) > div.data > div:nth-child(%s) > div" % str(
                                                    y + 1)))
                                        )

                                        last_responded = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                                  "div.ifcampaign-cont.no-width-limit > div.new_prospects "
                                                                  "> div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > "
                                                                  "div > div > div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar"
                                                                  "-visible > div.csp-content-wrapper > div > "
                                                                  "div.panelMove > div.panelTable > div.panelCels > "
                                                                  "div:nth-child(12) > div.data > div:nth-child(%s) > div"
                                                 % str(y + 1)))
                                        )

                                        city = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                                  "div.ifcampaign-cont.no-width-limit > div.new_prospects "
                                                                  "> div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > "
                                                                  "div > div > div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar"
                                                                  "-visible > div.csp-content-wrapper > div > "
                                                                  "div.panelMove > div.panelTable > div.panelCels > "
                                                                  "div:nth-child(16) > div.data > div:nth-child(%s) > div"
                                                 % str(y + 1)))
                                        )

                                        industry = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                                  "div.ifcampaign-cont.no-width-limit > div.new_prospects "
                                                                  "> div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > "
                                                                  "div > div > div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar"
                                                                  "-visible > div.csp-content-wrapper > div > "
                                                                  "div.panelMove > div.panelTable > div.panelCels > "
                                                                  "div:nth-child(20) > div.data > div:nth-child(%s) > div"
                                                 % str(y + 1)))
                                        )

                                        first_name = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                                  "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                                  "div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(2) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        last_name = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                                  "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                                  "div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(3) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        imported = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                                  "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                                  "div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(4) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        company = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                                  "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                                  "div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(5) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        website = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                                  "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                                  "div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(6) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        linkedin = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                                  "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                                  "div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(7) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        tags = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                                  "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                                  "div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(8) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        in_campaign = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                                  "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                                  "div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(10) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        email_sent = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                                  "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                                  "div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(11) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        tittle = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                                  "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                                  "div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(13) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        phone = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                                  "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                                  "div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(14) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        temp = {
                                            'Email': prospect.get_attribute('innerHTML'),
                                            'Status': status.get_attribute('innerHTML'),
                                            'Last Contacted': last_contacted.get_attribute('innerHTML'),
                                            'Last Responded': last_responded.get_attribute('innerHTML'),
                                            'City': city.get_attribute('innerHTML'),
                                            'Industry': industry.get_attribute('innerHTML'),
                                            'First Name': first_name.get_attribute('innerHTML'),
                                            'Last Name': last_name.get_attribute('innerHTML'),
                                            'Imported': imported.get_attribute('innerHTML'),
                                            'Company': company.get_attribute('innerHTML'),
                                            'Website': website.get_attribute('innerHTML'),
                                            'LinkedIn': linkedin.get_attribute('innerHTML'),
                                            'Tags': tags.get_attribute('innerHTML'),
                                            'In Campaigns': in_campaign.get_attribute('innerHTML'),
                                            'Emails Sent': email_sent.get_attribute('innerHTML'),
                                            'Tittle': tittle.get_attribute('innerHTML'),
                                            'Phone': phone.get_attribute('innerHTML'),
                                        }
                                        # 1
                                        dict_list_of_all_pros[campaigns].append(temp)

                                    #     next should be her
                                    # Check if the last page has prospects if not don't press next but finish
                                    if all_ != 1:
                                        next_page = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                            "#divContent > div > div:nth-child(4) > "
                                                                            "div.ifcampaign-cont.no-width-limit > "
                                                                            "div.new_prospects > div:nth-child(2) > "
                                                                            "div:nth-child(2) > div.myPagination > div:nth-child("
                                                                            "1) > div:nth-child(8) > div.gwt-Label.next"))
                                        )
                                        driver.execute_script("arguments[0].click();", next_page)
                                    else:
                                        if row_no_list[1] == 0:
                                            pass
                                        else:
                                            next_page = WebDriverWait(driver, 10).until(
                                                EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                                "#divContent > div > div:nth-child(4) > "
                                                                                "div.ifcampaign-cont.no-width-limit > "
                                                                                "div.new_prospects > div:nth-child(2) > "
                                                                                "div:nth-child(2) > div.myPagination > div:nth-child("
                                                                                "1) > div:nth-child(8) > div.gwt-Label.next"))
                                            )
                                            driver.execute_script("arguments[0].click();", next_page)
                                    all_ = all_ - 1
                            elif x == 1:
                                for y in range(all_):
                                    prospect = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                              "div.ifcampaign-cont.no-width-limit > "
                                                              "div.new_prospects > div:nth-child(2) > "
                                                              "div:nth-child(2) > div.new_prospects--table-panel > "
                                                              "div.newTable > div > div > div > div > div > "
                                                              "div.tableConst > div > div.panelTable > "
                                                              "div.panelCels > div.myColumn > div.data > "
                                                              "div:nth-child(%s) > div > "
                                                              "div.gwt-Label.cellLabel.handText" % str(
                                                y + 1)))
                                    )

                                    status = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                              "div.ifcampaign-cont.no-width-limit > div.new_prospects "
                                                              "> div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > "
                                                              "div > div > div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar"
                                                              "-visible > div.csp-content-wrapper > div > "
                                                              "div.panelMove > div.panelTable > div.panelCels > "
                                                              "div:nth-child(1) > div.data > div:nth-child(%s) > div > "
                                                              "span.ddm-text" % str(y + 1)))
                                    )

                                    last_contacted = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                              "div.ifcampaign-cont.no-width-limit > div.new_prospects "
                                                              "> div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > "
                                                              "div > div > div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar"
                                                              "-visible > div.csp-content-wrapper > div > "
                                                              "div.panelMove > div.panelTable > div.panelCels > "
                                                              "div:nth-child(9) > div.data > div:nth-child(%s) > div" % str(
                                                y + 1)))
                                    )

                                    last_responded = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                              "div.ifcampaign-cont.no-width-limit > div.new_prospects "
                                                              "> div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > "
                                                              "div > div > div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar"
                                                              "-visible > div.csp-content-wrapper > div > "
                                                              "div.panelMove > div.panelTable > div.panelCels > "
                                                              "div:nth-child(12) > div.data > div:nth-child(%s) > div"
                                             % str(y + 1)))
                                    )

                                    city = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                              "div.ifcampaign-cont.no-width-limit > div.new_prospects "
                                                              "> div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > "
                                                              "div > div > div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar"
                                                              "-visible > div.csp-content-wrapper > div > "
                                                              "div.panelMove > div.panelTable > div.panelCels > "
                                                              "div:nth-child(16) > div.data > div:nth-child(%s) > div"
                                             % str(y + 1)))
                                    )

                                    industry = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                              "div.ifcampaign-cont.no-width-limit > div.new_prospects "
                                                              "> div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > "
                                                              "div > div > div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar"
                                                              "-visible > div.csp-content-wrapper > div > "
                                                              "div.panelMove > div.panelTable > div.panelCels > "
                                                              "div:nth-child(20) > div.data > div:nth-child(%s) > div"
                                             % str(y + 1)))
                                    )

                                    first_name = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                              "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                              "div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                              "div.panelCels > div:nth-child(2) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    last_name = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                              "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                              "div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                              "div.panelCels > div:nth-child(3) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    imported = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                              "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                              "div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                              "div.panelCels > div:nth-child(4) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    company = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                              "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                              "div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                              "div.panelCels > div:nth-child(5) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    website = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                              "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                              "div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                              "div.panelCels > div:nth-child(6) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    linkedin = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                              "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                              "div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                              "div.panelCels > div:nth-child(7) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    tags = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                              "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                              "div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                              "div.panelCels > div:nth-child(8) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    in_campaign = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                              "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                              "div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                              "div.panelCels > div:nth-child(10) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    email_sent = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                              "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                              "div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                              "div.panelCels > div:nth-child(11) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    tittle = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                              "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                              "div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                              "div.panelCels > div:nth-child(13) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    phone = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div:nth-child(4) > "
                                                              "div.ifcampaign-cont.no-width-limit > div.new_prospects > "
                                                              "div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                              "div.panelCels > div:nth-child(14) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    temp = {
                                        'Email': prospect.get_attribute('innerHTML'),
                                        'Status': status.get_attribute('innerHTML'),
                                        'Last Contacted': last_contacted.get_attribute('innerHTML'),
                                        'Last Responded': last_responded.get_attribute('innerHTML'),
                                        'City': city.get_attribute('innerHTML'),
                                        'Industry': industry.get_attribute('innerHTML'),
                                        'First Name': first_name.get_attribute('innerHTML'),
                                        'Last Name': last_name.get_attribute('innerHTML'),
                                        'Imported': imported.get_attribute('innerHTML'),
                                        'Company': company.get_attribute('innerHTML'),
                                        'Website': website.get_attribute('innerHTML'),
                                        'LinkedIn': linkedin.get_attribute('innerHTML'),
                                        'Tags': tags.get_attribute('innerHTML'),
                                        'In Campaigns': in_campaign.get_attribute('innerHTML'),
                                        'Emails Sent': email_sent.get_attribute('innerHTML'),
                                        'Tittle': tittle.get_attribute('innerHTML'),
                                        'Phone': phone.get_attribute('innerHTML'),
                                    }
                                    dict_list_of_all_pros[campaigns].append(temp)

                    # if the second edit is true
                    else:
                        no_of_prospects = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR,
                                 "#divContent > div > div > div:nth-child(3) > div > div.prospectFromCampaign > "
                                 "div > div > span"))
                        )

                        total_pros = no_of_prospects.get_attribute('innerHTML')
                        if total_pros == "":
                            break
                        try:
                            row_no_list = obj_.get_total_pros_per_page(total_pros)
                        except IndexError as e:
                            print('O prospects exits')
                            break

                        # Dictionary to hold prospects

                        dict_list_of_all_pros[campaigns] = []
                        for x in range(len(row_no_list)):
                            all_ = row_no_list[x]
                            if x == 0:
                                while all_ != 0:
                                    for y in range(10):
                                        prospect = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                                  "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > "
                                                                  "div > div > div > div.tableConst > div > div.panelTable > "
                                                                  "div.panelCels > div.myColumn > div.data > div:nth-child(%s) > "
                                                                  "div > div.gwt-Label.cellLabel.handText" % str(
                                                    y + 1)))
                                        )

                                        status = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                                  "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > "
                                                                  "div > div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable "
                                                                  "> div.panelCels > div:nth-child(1) > div.data > div:nth-child("
                                                                  "%s) > div > span.ddm-text" % str(y + 1)))
                                        )

                                        last_contacted = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                                  "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > "
                                                                  "div > div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable "
                                                                  "> div.panelCels > div:nth-child(9) > div.data > div:nth-child("
                                                                  "%s) > div" % str(
                                                    y + 1)))
                                        )

                                        last_responded = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                                  "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > "
                                                                  "div > div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable "
                                                                  "> div.panelCels > div:nth-child(12) > div.data > "
                                                                  "div:nth-child(%s) > div "
                                                 % str(y + 1)))
                                        )

                                        city = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                                  "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > "
                                                                  "div > div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable "
                                                                  "> div.panelCels > div:nth-child(16) > div.data > "
                                                                  "div:nth-child(%s) > div "
                                                 % str(y + 1)))
                                        )

                                        industry = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                                  "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > "
                                                                  "div > div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable "
                                                                  "> div.panelCels > div:nth-child(20) > div.data > "
                                                                  "div:nth-child(%s) > div "
                                                 % str(y + 1)))
                                        )

                                        first_name = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                                  "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(2) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        last_name = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                                  "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(2) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        imported = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                                  "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(4) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        company = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                                  "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > "
                                                                  "div > div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable "
                                                                  "> div.panelCels > div:nth-child(5) > div.data > div:nth-child("
                                                                  "%s) > div" % str(y + 1)))
                                        )

                                        website = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                                  "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(6) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        linkedin = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                                  "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(7) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        tags = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                                  "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(8) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        in_campaign = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                                  "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(10) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        email_sent = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                                  "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(11) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        tittle = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                                  "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(13) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        phone = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located(
                                                (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                                  "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                                  "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                                  "div > div > "
                                                                  "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                                  "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                                  "div.panelCels > div:nth-child(14) > div.data > div:nth-child(%s) > "
                                                                  "div" % str(y + 1)))
                                        )

                                        temp = {
                                            'Email': prospect.get_attribute('innerHTML'),
                                            'Status': status.get_attribute('innerHTML'),
                                            'Last Contacted': last_contacted.get_attribute('innerHTML'),
                                            'Last Responded': last_responded.get_attribute('innerHTML'),
                                            'City': city.get_attribute('innerHTML'),
                                            'Industry': industry.get_attribute('innerHTML'),
                                            'First Name': first_name.get_attribute('innerHTML'),
                                            'Last Name': last_name.get_attribute('innerHTML'),
                                            'Imported': imported.get_attribute('innerHTML'),
                                            'Company': company.get_attribute('innerHTML'),
                                            'Website': website.get_attribute('innerHTML'),
                                            'LinkedIn': linkedin.get_attribute('innerHTML'),
                                            'Tags': tags.get_attribute('innerHTML'),
                                            'In Campaigns': in_campaign.get_attribute('innerHTML'),
                                            'Emails Sent': email_sent.get_attribute('innerHTML'),
                                            'Tittle': tittle.get_attribute('innerHTML'),
                                            'Phone': phone.get_attribute('innerHTML'),
                                        }
                                        dict_list_of_all_pros[campaigns].append(temp)
                                    #     next should be her
                                    if all_ != 1:
                                        next_page = WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                            "#divContent > div > div > div:nth-child(3) > div > "
                                                                            "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                                            "div.myPagination > div:nth-child(1) > div.hover > "
                                                                            "div.gwt-Label.next"))
                                        )
                                        driver.execute_script("arguments[0].click();", next_page)
                                    else:
                                        if row_no_list[1] == 0:
                                            pass
                                        else:
                                            next_page = WebDriverWait(driver, 10).until(
                                                EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                                "#divContent > div > div > div:nth-child(3) > div > "
                                                                                "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                                                "div.myPagination > div:nth-child(1) > div.hover > "
                                                                                "div.gwt-Label.next"))
                                            )
                                            driver.execute_script("arguments[0].click();", next_page)

                                    all_ = all_ - 1
                            elif x == 1:
                                for y in range(all_):
                                    prospect = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                              "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > "
                                                              "div > div > div > div.tableConst > div > div.panelTable > "
                                                              "div.panelCels > div.myColumn > div.data > div:nth-child(%s) > "
                                                              "div > div.gwt-Label.cellLabel.handText" % str(
                                                y + 1)))
                                    )

                                    status = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                              "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > "
                                                              "div > div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable "
                                                              "> div.panelCels > div:nth-child(1) > div.data > div:nth-child("
                                                              "%s) > div > span.ddm-text" % str(y + 1)))
                                    )

                                    last_contacted = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                              "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > "
                                                              "div > div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable "
                                                              "> div.panelCels > div:nth-child(9) > div.data > div:nth-child("
                                                              "%s) > div" % str(
                                                y + 1)))
                                    )

                                    last_responded = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                              "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > "
                                                              "div > div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable "
                                                              "> div.panelCels > div:nth-child(12) > div.data > "
                                                              "div:nth-child(%s) > div "
                                             % str(y + 1)))
                                    )

                                    city = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                              "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > "
                                                              "div > div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable "
                                                              "> div.panelCels > div:nth-child(16) > div.data > "
                                                              "div:nth-child(%s) > div "
                                             % str(y + 1)))
                                    )

                                    industry = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                              "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > "
                                                              "div > div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable "
                                                              "> div.panelCels > div:nth-child(20) > div.data > "
                                                              "div:nth-child(%s) > div "
                                             % str(y + 1)))
                                    )

                                    first_name = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                              "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > "
                                                              "div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable "
                                                              "> "
                                                              "div.panelCels > div:nth-child(2) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    last_name = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                              "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                              "div.panelCels > div:nth-child(2) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    imported = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                              "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                              "div.panelCels > div:nth-child(4) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    company = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                              "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > "
                                                              "div > div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable "
                                                              "> div.panelCels > div:nth-child(5) > div.data > div:nth-child("
                                                              "%s) > div" % str(y + 1)))
                                    )

                                    website = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                              "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                              "div.panelCels > div:nth-child(6) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    linkedin = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                              "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                              "div.panelCels > div:nth-child(7) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    tags = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                              "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                              "div.panelCels > div:nth-child(8) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    in_campaign = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                              "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                              "div.panelCels > div:nth-child(10) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    email_sent = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                              "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                              "div.panelCels > div:nth-child(11) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    tittle = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                              "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                              "div.panelCels > div:nth-child(13) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    phone = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#divContent > div > div > div:nth-child(3) > div > "
                                                              "div.new_prospects > div:nth-child(2) > div:nth-child(2) > "
                                                              "div.new_prospects--table-panel > div.newTable > div > div > div > "
                                                              "div > div > "
                                                              "div.CustomScrollbarPanel.tableMove.csp-scrollbar-visible > "
                                                              "div.csp-content-wrapper > div > div.panelMove > div.panelTable > "
                                                              "div.panelCels > div:nth-child(14) > div.data > div:nth-child(%s) > "
                                                              "div" % str(y + 1)))
                                    )

                                    temp = {
                                        'Email': prospect.get_attribute('innerHTML'),
                                        'Status': status.get_attribute('innerHTML'),
                                        'Last Contacted': last_contacted.get_attribute('innerHTML'),
                                        'Last Responded': last_responded.get_attribute('innerHTML'),
                                        'City': city.get_attribute('innerHTML'),
                                        'Industry': industry.get_attribute('innerHTML'),
                                        'First Name': first_name.get_attribute('innerHTML'),
                                        'Last Name': last_name.get_attribute('innerHTML'),
                                        'Imported': imported.get_attribute('innerHTML'),
                                        'Company': company.get_attribute('innerHTML'),
                                        'Website': website.get_attribute('innerHTML'),
                                        'LinkedIn': linkedin.get_attribute('innerHTML'),
                                        'Tags': tags.get_attribute('innerHTML'),
                                        'In Campaigns': in_campaign.get_attribute('innerHTML'),
                                        'Emails Sent': email_sent.get_attribute('innerHTML'),
                                        'Tittle': tittle.get_attribute('innerHTML'),
                                        'Phone': phone.get_attribute('innerHTML'),
                                    }
                                    dict_list_of_all_pros[campaigns].append(temp)
                    dict_list_of_all_pros = existing_data | dict_list_of_all_pros

                    with open('scraped_prospect.json', 'w', encoding='utf-8') as f:
                        json.dump(dict_list_of_all_pros, f, indent=4,
                                  ensure_ascii=False, cls=NpEncoder)
                    # Resume campaign if it was running
                    if running:
                        resume_campaign = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR,
                                 "#divContent > div > div.ifcampaign-header > "
                                 "div.ifcampaign_edit-header > div.ifcampaign_edit-header--buttons > "
                                 "div.btn.icon.running.big"))
                        )
                        try:

                            driver.execute_script("arguments[0].click();", resume_campaign)
                        except ElementClickInterceptedException:
                            print('Unable to click resume')
                            continue

                        success_pop_up = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR,
                                 "#body > div.MyCustomPopupPanel.mcp-show > div > div > div > div > "
                                 "div.content-cont > div.popup-actions > div"))
                        )
                        try:

                            driver.execute_script("arguments[0].click();", resume_campaign)
                        except ElementClickInterceptedException:
                            print('Unable to click resume')
                    break
                except TimeoutException:
                    print("Timed out")
                    field_campaigns.append(campaigns)

        except IndexError as e:
            field_campaigns.append(campaigns)
            print("Campaigns Failed %s" % e, field_campaigns)

# end of main for loop


authcookie = Office365('https://_sharepoint_', username='_company_email_',
                       password='password').GetCookies()
site = Site('https://_sharepoint_/sites/_groupname_/', version=Version.v365, authcookie=authcookie);
folder = site.Folder('Shared Documents')

with open('scraped_prospect.json', mode='rb') as file:
    fileContent = file.read()
folder.upload_file(fileContent, "scraped_prospect.json")

driver.quit()
print(campaigns_with_steps)
print("passed: ", len(campaigns_with_steps))

print(campaigns_with_steps)
print("Failed: ", len(field_campaigns))
print("===================file saved===============================================")
