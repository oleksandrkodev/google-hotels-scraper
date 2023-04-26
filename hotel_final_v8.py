# Dependencies
import csv
import datetime
# import sys
import time
from time import sleep

import pandas as pd  # To store data in dataframe
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from unidecode import unidecode

# Constants
URL = "https://www.google.com/travel/hotels"
todaysdate = datetime.date.today()

NB_HOTELS_CHUNK_SIZE = 50
# You may want to test with this value being half the number of rows in the CSV,
# to execute 2 "scrapes" in a concurrent way,
# i.e. one for the first half of hotels in the CSV
# the second for the other half.

NB_CONCURRENT_WORKERS = 1


# Functions
def setup_driver():
    # Doing the driver setting
    service = Service(
        executable_path=r"C:\Users\KHUYNH\Desktop\Work\Hoken\Scraper\chromedriver.exe"
    )
    # Not sure this executable path setting is actually used. Could try without.
    options = Options()
    options.add_argument("--start-maximized")
    # other options to try
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_experimental_option("detach", True)
    options.page_load_strategy = "normal"
    driver = webdriver.Chrome(service=service, options=options)
    actions = ActionChains(driver)
    wait = WebDriverWait(driver, 20)  # we may try with 3 values: 15, 20, 30
    return driver, actions, wait


def search_hotel(driver, actions, wait, input_text):
    sleep(2)
    search_form = wait.until(
        EC.visibility_of_element_located((By.CLASS_NAME, "SS0SXe"))
    )
    x_button = search_form.find_element(By.TAG_NAME, "button")
    actions.move_to_element(x_button).click().perform()
    search_bar = driver.find_elements(By.TAG_NAME, "input")[1]
    search_bar.send_keys(input_text)
    search_bar.send_keys(Keys.ENTER)


def save_data(data, todaysdate):
    df = pd.DataFrame(data)
    df.scrape_base_price = df.scrape_base_price.apply(
        lambda x: x.replace("$", "").replace(",", "")
    )
    # df.scrape_average_price_fees = df.scrape_average_price_fees.apply(
    #     lambda x: x.replace("$", "").replace(",", "")
    # )
    # df.scrape_total_price = df.scrape_total_price.apply(
    #     lambda x: x.replace("$", "").replace(",", "")
    # )
    df.to_csv(f"final_data_{todaysdate}.csv", index=False)
    df.to_csv(f"final_data_{todaysdate}_BACKUP.csv", index=False)
    print("Data created successfully")


def handle_broken_case(
    id_hotel,
    hotel_title,
    city,
    check_ins,
    check_outs,
    base_price_out,
    # average_price_out,
    # fees_price_out,
    # total_price_out,
    nights_out,
    re_attempt,
):
    data = {
        "hotel_id": id_hotel,
        "hotel": unidecode(hotel_title),
        "check_in": check_ins,
        "check_out": check_outs,
        "City": city,
        "hoken_base_price": base_price_out,
        # "hoken_average_price_fees": average_price_out,
        # "hoken_total_price": total_price_out,
        # "fees": fees_price_out,
        "nights": nights_out,
    }
    re_attempt.append(data)
    return re_attempt


def extract_checkin_checkout_inputs(driver):
    # check_out_input and check_in_input checks!
    # Note: Augment the wait time (from 2), if needed
    check_out_input = (
        WebDriverWait(driver, 2)
        .until(
            EC.visibility_of_element_located(
                (By.XPATH, '//*[@id="dwrFZd0"]/div/div[2]/div[1]')
            )
        )
        .text
    )
    check_in_input = (
        WebDriverWait(driver, 2)
        .until(
            EC.visibility_of_element_located(
                (By.XPATH, '//*[@id="dwrFZd0"]/div/div[1]/div[1]')
            )
        )
        .text
    )
    print("check " + check_in_input)
    print("check " + check_out_input)
    return check_in_input, check_out_input


# Additional functions


# # Function created, but the usage is currently disabled!! May reuse later!
# def parse_ota_data(online_travel_agents):
#     # Returns: average_price_fees_list, total_price_list
#
#     average_price_fees_list = []
#     total_price_list = []
#
#     for online in online_travel_agents:
#         try:
#             average_price_fees = (
#                 online.find("div", class_="Einivf qOlGCc")
#                 .find("span", class_="MW1oTb")
#                 .get_text()
#             )
#             print(average_price_fees)
#             if not average_price_fees:
#                 print("UNABLE TO EXTRACT span / class MW1oTb for 'average_price_fees'")
#             average_price_fees_list.append(average_price_fees)
#         except Exception:
#             # average_price_fees = None
#             pass
#
#     for online in online_travel_agents:
#         try:
#             total_price = (
#                 online.find("div", class_="Einivf qOlGCc")
#                 .find("span", class_="UeIHqb")
#                 .get_text()
#             )
#             print(total_price)
#             if not total_price:
#                 print("UNABLE TO EXTRACT span / class UeIHqb for 'total_price'")
#             total_price_list.append(total_price)
#         except Exception:
#             # total_price = None
#             pass
#
#     print(f"Average Price Fees list {len(average_price_fees_list)}")
#     print(average_price_fees_list)
#     print(f"Total Price list {len(total_price_list)}")
#     print(total_price_list)
#
#     return average_price_fees_list, total_price_list


def extract_ota_and_price_list(
    driver,
    actions,
    wait,
    OTA_list,
    price_list,
    more_option_button_one=False,
    more_option_button_two=False,
):
    # Retrieves and returns: OTA_list, price_list

    if more_option_button_one:
        try:
            sleep(2)
            more_option = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "bbRZy"))
            )
            actions.move_to_element(more_option).click().perform()
            print('Click "more-option" bar.')
            sleep(2)
        except Exception:
            print('No "more-option" button. Continue Scraping.')

    # 2 'more-option' buttons tried using XPATH
    if more_option_button_two:
        try:
            sleep(2)
            more_option = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        '//*[@id="overview"]/c-wiz[1]/c-wiz[3]/div/section/div[2]/c-wiz/div[2]/div/button/span',
                    )
                )
            )
            actions.move_to_element(more_option).click().perform()
            print('Click "more-option" bar.')
            sleep(2)
        except Exception:
            print('No "more-option" button. Continue Scraping.')

        # more-option #2
        try:
            sleep(2)
            more_option2 = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        '//*[@id="prices"]/c-wiz[1]/c-wiz/div/div/div/div/div/div/div/section/div[2]/c-wiz/div/div/div[2]/div[2]/span/div[47]',
                    )
                )
            )
            actions.move_to_element(more_option2).click().perform()
            print('Click "more-option" bar #2.')
            sleep(2)
        except Exception:
            print('No "more-option" button #2. Continue Scraping.')

    driver.execute_script("window.scrollTo(0, 0);")
    price_container = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                '//*[@id="prices"]/c-wiz/c-wiz/div/div/div/div/div/div/div/section/div[2]/c-wiz/div/div/div[2]',
            )
        )
    )
    names = price_container.find_elements(By.CLASS_NAME, "NiGhzc")
    prices_row = price_container.find_elements(By.CLASS_NAME, "pNExyb")

    for name in names:
        name_text = name.text.replace("\n", " ")
        OTA_list.append(name_text)
        # while "" in OTA_list:
        #     OTA_list.remove("")
    OTA_list = list(set(OTA_list)).remove("")  # try this instead

    for price in prices_row:
        price_text = price.text
        price_list.append(price_text)
        # while "" in price_list:
        #     price_list.remove("")
    price_list = list(set(price_list)).remove("")  # try this instead

    print(f"Price list {len(price_list)}")
    print(price_list)
    print(f"OTA list {len(OTA_list)}")
    print(OTA_list)

    return OTA_list, price_list


# Main processing code
def run_process(rows, todaysdate):
    """rows is the list of rows coming from the CSV file"""
    ids = []
    hotels = []
    cities = []
    check_in_dates = []
    check_out_dates = []
    re_attempt = []
    base_prices = []
    average_prices = []
    fees_prices = []
    total_prices = []
    nights = []

    # Other variables initialization
    number_of_success = 0
    check_in_input, check_out_input = "", ""

    # Loop through each row in the CSV file
    for row in rows:
        # print("row", row)
        # Access some columns of each row
        id_hotel = row[0]
        hotel = row[1]
        city = row[4]
        check_in_date = row[10]
        check_out_date = row[12]
        base_price = row[15]
        fees = row[16]
        average_price = row[17]
        total_price = row[18]
        night = row[14]

        # populate the lists we need for the next steps
        ids.append(id_hotel)
        cities.append(city)
        hotels.append(hotel)
        check_in_dates.append(check_in_date)
        check_out_dates.append(check_out_date)
        base_prices.append(base_price)
        average_prices.append(average_price)
        fees_prices.append(fees)
        total_prices.append(total_price)
        nights.append(night)

    # First Output
    final_data = []
    for i in range(
        len(ids)
    ):  # Delete -125 if you want to scrape in one run all the row in csv
        driver, actions, wait = setup_driver()
        driver.get(URL)

        OTA_list = []  # Online Travel Agent
        price_list = []
        total_price_list = []
        average_price_fees_list = []
        hotel_name = hotels[i]
        print(unidecode(hotel_name))
        city = cities[i]
        try:
            # enter hotel name and do the search
            search_hotel(
                driver, actions, wait, input_text=unidecode(hotel_name) + " " + city
            )
            result = f"Entering The Hotel Name: {hotel_name}."
            print(result)
            sleep(2)

            # Check-in date
            # driver.execute_script("window.scrollTo(0, 0);")
            sleep(4)
            try:
                check_in = driver.find_element(
                    By.XPATH,
                    '//*[@id="overview"]/c-wiz[1]/c-wiz[3]/div/section/div[1]/div[1]/div/div/div[2]/div[1]/div/input',
                )
            except:
                # click first listing
                print("There is still a container so click the container.")
                container = driver.find_element(By.CLASS_NAME, "PVOOXe")
                container.click()
                sleep(2)

                check_in = driver.find_element(
                    By.XPATH,
                    '//*[@id="overview"]/c-wiz[1]/c-wiz[3]/div/section/div[1]/div[1]/div/div/div[2]/div[1]/div/input',
                )
            actions.move_to_element(check_in).click().perform()
            # try:
            #     # iframe = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'scSharedMaterialbuttonroot scSharedMaterialbuttonnavigational scSharedMaterialbuttonicon-only')))
            #     # driver.switch_to.frame(iframe)
            #     close_button = wait.until(EC.presence_of_element_located((By.CLASS_NAME,
            #                                                             'scSharedMaterialbuttonroot scSharedMaterialbuttonnavigational scSharedMaterialbuttonicon-only')))
            #     actions.move_to_element(close_button).click().perform()
            #     print("Close pop-up survey.")
            # except Exception:
            #     print("No pop-up survey.")

            date_check_in = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, f"div[aria-label='{check_in_dates[i]}']")
                )
            )
            print(f"Input check-in date: {check_in_dates[i]}.")
            sleep(4)
            actions.move_to_element(date_check_in)
            actions.click()
            actions.perform()

            date_check_out = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, f"div[aria-label='{check_out_dates[i]}']")
                )
            )
            print(f"Input check-out date: {check_out_dates[i]}.")
            sleep(3)
            actions.move_to_element(date_check_out).click().perform()
            # click off the dates
            actions.move_by_offset(100, 100)
            actions.click()
            actions.perform()
            # twice to be sure
            actions.move_by_offset(100, 100)
            actions.click()
            actions.perform()
            check_in_input = check_in_dates[i]
            check_out_input = check_out_dates[i]
            # check_out_input = (driver.find_element
            #             (By.XPATH, '//*[@id="dwrFZd0"]/div/div[1]/div[1]')
            #         )
            #     ).text
            # )
            # print("check " + check_out_input)

            # check_in_input = (
            #     wait.until(
            #         EC.visibility_of_element_located(
            #             (By.XPATH, '//*[@id="dwrFZd0"]/div/div[2]/div[1]')
            #         )
            #     ).text
            # )
            # print("check " + check_in_input)

            # check_in_input, check_out_input = extract_checkin_checkout_inputs(driver)
            # sleep(2)

            # scraping process
            print("Scraping process.")
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            sleep(2)
            try:
                not_available = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            '//*[@id="prices"]/c-wiz/c-wiz/div/div/div/div/div/div/div/section/div[2]/c-wiz/c-wiz/div[1]/div/div',
                        )
                    )
                )
                not_available_window2 = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            '//*[@id="prices"]/c-wiz[1]/c-wiz/div/div/div/div/div/div/div/section/div[2]/c-wiz/c-wiz/div[1]',
                        )
                    )
                )
                if not_available:
                    not_available = not_available
                    print("Not available is true from try if.")
                elif not_available_window2:
                    not_available = not_available_window2
                    print("Not available is true from try if 2.")
            except Exception:
                not_available = False
                print("Not available is false.")
            try:
                contact_this_property = wait.until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "MEVoGd AdWm1c"))
                )
                contact_this_property_window2 = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            '//*[@id="prices"]/c-wiz[1]/c-wiz/div/div/div/div/div/div/div/section/div[2]/c-wiz/div[1]/div[1]/div[1]',
                        )
                    )
                )
                if contact_this_property:
                    contact_this_property = contact_this_property
                    print("Contact this property from try if.")
                elif contact_this_property:
                    contact_this_property = contact_this_property_window2
                    print("Contact this property from try if 2.")
            except Exception:
                contact_this_property = False
                print("Contact this property is false.")
            driver.execute_script("window.scrollTo(0, 0);")
            sleep(1)

            if not_available:
                # create dictionary
                id_hotel = ids[i]
                hotel_title = hotels[i]
                check_outs = check_out_dates[i]
                check_ins = check_in_dates[i]
                base_price_out = base_prices[i]
                # average_price_out = average_prices[i]
                # fees_price_out = fees_prices[i]
                # total_price_out = total_prices[i]
                nights_out = nights[i]
                data = {
                    "hotel_id": id_hotel,
                    "hotel": unidecode(hotel_title),
                    "agents": "Not Available",
                    "scrape_position": "Not Available",
                    "scrape_date": todaysdate,
                    "check_in": check_ins,
                    "check_out": check_outs,
                    "check_in_search": "Not Available",
                    "check_out_search": "Not Available",
                    "hoken_base_price": base_price_out,
                    "scrape_base_price": "Not Available",
                    # "hoken_average_price_fees": average_price_out,
                    # "scrape_average_price_fees": "Not Available",
                    # "hoken_total_price": total_price_out,
                    # "scrape_total_price": "Not Available",
                    # "fees": fees_price_out,
                    "nights": nights_out,
                }
                final_data.append(data)
                print(f"Row {i + 1}: {hotel_name} is not available.")
            elif contact_this_property:
                # create dictionary
                id_hotel = ids[i]
                hotel_title = hotels[i]
                check_outs = check_out_dates[i]
                check_ins = check_in_dates[i]
                base_price_out = base_prices[i]
                # average_price_out = average_prices[i]
                # fees_price_out = fees_prices[i]
                # total_price_out = total_prices[i]
                nights_out = nights[i]
                data = {
                    "hotel_id": id_hotel,
                    "hotel": unidecode(hotel_title),
                    "agents": OTA_list[j],
                    "scrape_position": j + 1,
                    "scrape_date": todaysdate,
                    "check_in": check_ins,
                    "check_out": check_outs,
                    "check_in_search": "Contact this property",
                    "check_out_search": "Contact this property",
                    "hoken_base_price": base_price_out,
                    # "scrape_base_price": "Contact this property",
                    # "hoken_average_price_fees": average_price_out,
                    # "scrape_average_price_fees": "Contact this property",
                    # "hoken_total_price": total_price_out,
                    # "scrape_total_price": "Contact this property",
                    "fees": fees_price_out,
                    "nights": nights_out,
                }
                final_data.append(data)
                print(f"Row {i + 1}: {hotel_name} Contact this property.")
                sleep(2)
            else:
                # Retrieve the Online agent travels and the prices
                OTA_list, price_list = extract_ota_and_price_list(
                    driver,
                    actions,
                    wait,
                    OTA_list,
                    price_list,
                    more_option_button_two=True,
                )

                # headers = soup.find_all("div", class_="vxYgIc")[4]
                # online_travel_agents = headers.find_all("div", class_="NiGhzc")
                # for online in online_travel_agents:
                #     try:
                #         average_price_fees = (
                #             online.find("div", class_="Einivf qOlGCc")
                #             .find("span", class_="MW1oTb")
                #             .get_text()
                #         )
                #         print(average_price_fees)
                #         if not average_price_fees:
                #             print("UNABLE TO EXTRACT span / class MW1oTb for 'average_price_fees'")
                #         average_price_fees_list.append(average_price_fees)
                #     except Exception:
                #         average_price_fees = None

                # for online in online_travel_agents:
                #     try:
                #         total_price = (
                #             online.find("div", class_="Einivf qOlGCc")
                #             .find("span", class_="UeIHqb")
                #             .get_text()
                #         )
                #         print(total_price)
                #         if not total_price:
                #             print("UNABLE TO EXTRACT span / class UeIHqb for 'total_price'")
                #         total_price_list.append(total_price)
                #     except Exception:
                #         total_price = None

                # print(f"Average Price Fees list {len(total_price_list)}")
                # print(average_price_fees_list)
                # print(f"Total Price list {len(total_price_list)}")
                # print(total_price_list)

                # create dictionary
                id_hotel = ids[i]
                hotel_title = hotels[i]
                check_outs = check_out_dates[i]
                check_ins = check_in_dates[i]
                base_price_out = base_prices[i]
                # average_price_out = average_prices[i]
                # fees_price_out = fees_prices[i]
                # total_price_out = total_prices[i]
                nights_out = nights[i]
                for j in range(len(OTA_list)):
                    data = {
                        "hotel_id": id_hotel,
                        "hotel": unidecode(hotel_title),
                        "agents": OTA_list[j],
                        "scrape_position": j + 1,
                        "scrape_date": todaysdate,
                        "check_in": check_ins,
                        "check_out": check_outs,
                        "check_in_search": check_in_input,
                        "check_out_search": check_out_input,
                        "hoken_base_price": base_price_out,
                        "scrape_base_price": price_list[j],
                        # "hoken_average_price_fees": average_price_out,
                        # "scrape_average_price_fees": average_price_fees_list[j],
                        # "hoken_total_price": total_price_out,
                        # "scrape_total_price": total_price_list[j],
                        # "fees": fees_price_out,
                        "nights": nights_out,
                    }
                    final_data.append(data)
                print(f"Row {i + 1}: {hotel_name} successfully scraped.")
                number_of_success += 1
                print("number_of_success", number_of_success)
                driver.close()

        except TimeoutException:
            print("Exception")
            # Try to scrape from container
            try:
                container = wait.until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "PVOOXe"))
                )
            except Exception:
                container = False

            if container:
                print("There is still a container so click the container.")
                container.click()
                sleep(2)
                # go to current tab
                # get current window handle
                p = driver.current_window_handle

                # get first child window
                chwd = driver.window_handles

                for w in chwd:
                    # switch focus to child window
                    if w != p:
                        driver.switch_to.window(w)
                try:
                    price_tab = wait.until(
                        EC.element_to_be_clickable((By.XPATH, '//*[@id="prices"]'))
                    )
                    actions.move_to_element(price_tab).click().perform()
                    driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);"
                    )
                except Exception:
                    price_tab = wait.until(
                        EC.element_to_be_clickable((By.ID, "prices"))
                    )
                    actions.move_to_element(price_tab).click().perform()
                    driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);"
                    )
                # Change the currency
                # sleep(1)
                # try:
                #     currency = wait.until(
                #         EC.element_to_be_clickable((By.XPATH, '//*[@id="prices"]/div/c-wiz[2]/footer/div[1]/c-wiz/button')))
                #     currency.click()
                # except Exception:
                #     currency = wait.until(EC.element_to_be_clickable(
                #         (By.XPATH, '//*[@id="prices"]/c-wiz[2]/div/c-wiz[2]/footer/div[1]/c-wiz/button')))
                #     currency.click()
                # sleep(4)
                # usd = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="USD"]')))
                # actions.move_to_element(usd).click().perform()
                # done_button = driver.find_element(By.XPATH, '//*[@id="yDmH0d"]/div[6]/div/div[2]/div[3]/div[2]/button')
                # sleep(1)
                # done_button.click()

                # Check-in date
                driver.execute_script("window.scrollTo(0, 0);")
                sleep(3)
                # driver.execute_script("window.scrollTo(0, 0);")
                try:
                    check_in = driver.find_element(
                        By.XPATH,
                        '//*[@id="overview"]/c-wiz[1]/c-wiz[3]/div/section/div[1]/div[1]/div/div/div[2]/div[1]/div/input',
                    )
                except:
                    # click first listing
                    print("There is still a container so click the container.")
                    container = driver.find_element(By.CLASS_NAME, "PVOOXe")
                    container.click()
                    sleep(2)

                    check_in = driver.find_element(
                        By.XPATH,
                        '//*[@id="overview"]/c-wiz[1]/c-wiz[3]/div/section/div[1]/div[1]/div/div/div[2]/div[1]/div/input',
                    )

                sleep(2)
                actions.move_to_element(check_in).click().perform()
                # try:
                #     survey_popup = wait.until(
                #         EC.element_to_be_clickable(
                #             (
                #                 By.CLASS_NAME,
                #                 "scSharedMaterialbuttonroot scSharedMaterialbuttonnavigational scSharedMaterialbuttonicon-only",
                #             )
                #         )
                #     )
                #     actions.move_to_element(survey_popup).click().perform()
                #     iframe = wait.until(
                #         EC.presence_of_element_located((By.ID, "google-hats-survey"))
                #     )
                #     driver.switch_to.frame(iframe)
                #     close_button = driver.find_element(
                #         By.CLASS_NAME,
                #         "scSharedMaterialbuttonroot scSharedMaterialbuttonnavigational scSharedMaterialbuttonicon-only",
                #     )
                #     actions.move_to_element(close_button).click().perform()
                #     print("Close pop-up survey.")
                # except Exception:
                #     print("No pop-up survey.")

                date_check_in = wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, f"div[aria-label='{check_in_dates[i]}']")
                    )
                )
                print(f"Input check-in date: {check_in_dates[i]}.")
                sleep(1)
                actions.move_to_element_with_offset(date_check_in, -10, 10)
                actions.click()
                actions.perform()
                date_check_out = wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, f"div[aria-label='{check_out_dates[i]}']")
                    )
                )
                print(f"Input check-out date: {check_out_dates[i]}.")
                sleep(3)
                actions.move_to_element(date_check_out).click().perform()
                # sleep(2)
                # try:
                #     google_icon = wait.until(
                #         EC.element_to_be_clickable(
                #             (
                #                 By.XPATH,
                #                 '//*[@id="yDmH0d"]/c-wiz[2]/div/div[2]/div[1]/div[1]/div[2]/div[1]/a',
                #             )
                #         )
                #     )
                # except Exception:
                #     google_icon = False
                # try:
                #     sign_in = wait.until(
                #         EC.element_to_be_clickable(
                #             (By.CLASS_NAME, "gb_ja gb_ka gb_ge gb_gd")
                #         )
                #     )
                # except Exception:
                #     sign_in = False
                # if google_icon:
                #     # create an ActionChains instance and move the mouse to the desired location
                #     actions.move_to_element(google_icon).move_by_offset(0, 100)
                #     # perform the click action
                #     actions.click().perform()
                # else:
                #     sleep(2)
                #     sign_in = wait.until(
                #         EC.element_to_be_clickable((By.CLASS_NAME, "gb_1c"))
                #     )
                #     actions.move_to_element(sign_in).move_by_offset(-100, 0)
                #     actions.click().perform()
                #     print("Click a point close to sign in button.")
                # click off the dates
                actions.move_by_offset(100, 100)
                actions.click()
                actions.perform()
                # twice to be sure
                actions.move_by_offset(100, 100)
                actions.click()
                actions.perform()
                check_in_input = check_in_dates[i]
                check_out_input = check_out_dates[i]
                # check_out_input = (driver.find_element
                #             (By.XPATH, '//*[@id="dwrFZd0"]/div/div[1]/div[1]')
                #         )
                #     ).text
                # )
                # print("check " + check_out_input)

                # check_in_input = (
                #     wait.until(
                #         EC.visibility_of_element_located(
                #             (By.XPATH, '//*[@id="dwrFZd0"]/div/div[2]/div[1]')
                #         )
                #     ).text
                # )
                # print("check " + check_in_input)

                # check_in_input, check_out_input = extract_checkin_checkout_inputs(driver)
                # sleep(2)

                # scraping process
                print("Scraping process.")
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, "html.parser")
                sleep(3)
                try:
                    not_available = wait.until(
                        EC.element_to_be_clickable(
                            (
                                By.XPATH,
                                '//*[@id="prices"]/c-wiz/c-wiz/div/div/div/div/div/div/div/section/div[2]/c-wiz/c-wiz/div[1]/div/div',
                            )
                        )
                    )
                    not_available_window2 = wait.until(
                        EC.element_to_be_clickable(
                            (
                                By.XPATH,
                                '//*[@id="prices"]/c-wiz[1]/c-wiz/div/div/div/div/div/div/div/section/div[2]/c-wiz/c-wiz/div[1]',
                            )
                        )
                    )
                    if not_available:
                        not_available = not_available
                        print("Not available is true from try if.")
                    elif not_available_window2:
                        not_available = not_available_window2
                        print("Not available is true from try if 2.")
                except Exception:
                    not_available = False
                    print("Not available is false.")
                try:
                    contact_this_property = wait.until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "MEVoGd AdWm1c"))
                    )
                    contact_this_property_window2 = wait.until(
                        EC.element_to_be_clickable(
                            (
                                By.XPATH,
                                '//*[@id="prices"]/c-wiz[1]/c-wiz/div/div/div/div/div/div/div/section/div[2]/c-wiz/div[1]/div[1]/div[1]',
                            )
                        )
                    )

                    if contact_this_property:
                        contact_this_property = contact_this_property
                        print("Contact this property from try if.")
                    elif contact_this_property:
                        contact_this_property = contact_this_property_window2
                        print("Contact this property from try if 2.")
                except Exception:
                    contact_this_property = False
                    print("Contact this property is false.")
                # driver.execute_script("window.scrollTo(0, 0);")
                # headers = soup.find_all("div", class_="vxYgIc")[3]
                # online_travel_agents = headers.find_all("div", class_="ADs2Tc")
                # for online in online_travel_agents:
                #     try:
                #         average_price_fees = (
                #             online.find("div", class_="Einivf qOlGCc")
                #             .find("span", class_="MW1oTb")
                #             .get_text()
                #         )
                #         print(average_price_fees)
                #         if not average_price_fees:
                #             print("UNABLE TO EXTRACT span / class MW1oTb for 'average_price_fees'")
                #         average_price_fees_list.append(average_price_fees)
                #     except Exception:
                #         average_price_fees = None

                # for online in online_travel_agents:
                #     try:
                #         total_price = (
                #             online.find("div", class_="Einivf qOlGCc")
                #             .find("span", class_="UeIHqb")
                #             .get_text()
                #         )
                #         print(total_price)
                #         if not total_price:
                #             print("UNABLE TO EXTRACT span / class UeIHqb for 'total_price'")
                #         total_price_list.append(total_price)
                #     except Exception:
                #         total_price = None
                sleep(1)

                if not_available:
                    # create dictionary
                    id_hotel = ids[i]
                    hotel_title = hotels[i]
                    check_outs = check_out_dates[i]
                    check_ins = check_in_dates[i]
                    base_price_out = base_prices[i]
                    # average_price_out = average_prices[i]
                    # fees_price_out = fees_prices[i]
                    # total_price_out = total_prices[i]
                    nights_out = nights[i]
                    data = {
                        "hotel_id": id_hotel,
                        "hotel": hotel_name,
                        "agents": "Not Available",
                        "scrape_position": "Not Available",
                        "scrape_date": todaysdate,
                        "check_in": check_ins,
                        "check_out": check_outs,
                        "check_in_search": "Not Available",
                        "check_out_search": "Not Available",
                        "hoken_base_price": base_price_out,
                        "scrape_base_price": "Not Available",
                        # "hoken_average_price_fees": average_price_out,
                        # "scrape_average_price_fees": "Not Available",
                        # "hoken_total_price": total_price_out,
                        # "scrape_total_price": "Not Available",
                        # "fees": fees_price_out,
                        "nights": nights_out,
                    }
                    final_data.append(data)
                    print(f"Row {i + 1}: {hotel_name} is not available.")
                    sleep(2)
                    driver.close()
                elif contact_this_property:
                    # create dictionary
                    id_hotel = ids[i]
                    hotel_title = hotels[i]
                    check_outs = check_out_dates[i]
                    check_ins = check_in_dates[i]
                    base_price_out = base_prices[i]
                    # average_price_out = average_prices[i]
                    # fees_price_out = fees_prices[i]
                    # total_price_out = total_prices[i]
                    nights_out = nights[i]
                    data = {
                        "hotel_id": id_hotel,
                        "hotel": unidecode(hotel_title),
                        "agents": OTA_list[j],
                        "scrape_position": j + 1,
                        "scrape_date": todaysdate,
                        "check_in": check_ins,
                        "check_out": check_outs,
                        "check_in_search": "Contact this property",
                        "check_out_search": "Contact this property",
                        "hoken_base_price": base_price_out,
                        "scrape_base_price": "Contact this property",
                        # "hoken_average_price_fees": average_price_out,
                        # "scrape_average_price_fees": "Contact this property",
                        # "hoken_total_price": total_price_out,
                        # "scrape_total_price": "Contact this property",
                        # "fees": fees_price_out,
                        "nights": nights_out,
                    }
                    final_data.append(data)
                    print(f"Row {i + 1}: {hotel_name} Contact this property.")
                    sleep(2)
                    driver.close()
                else:
                    # Retrieve the Online agent travels and the prices (NOW USING THE FUNCTION)
                    OTA_list, price_list = extract_ota_and_price_list(
                        driver,
                        actions,
                        wait,
                        OTA_list,
                        price_list,
                        more_option_button_one=True,
                    )

                    # create dictionary
                    id_hotel = ids[i]
                    hotel_title = hotels[i]
                    check_outs = check_out_dates[i]
                    check_ins = check_in_dates[i]
                    base_price_out = base_prices[i]
                    # average_price_out = average_prices[i]
                    # fees_price_out = fees_prices[i]
                    # total_price_out = total_prices[i]
                    nights_out = nights[i]
                    for j in range(len(OTA_list)):
                        data = {
                            "hotel_id": id_hotel,
                            "hotel": unidecode(hotel_title),
                            "agents": OTA_list[j],
                            "scrape_position": j + 1,
                            "scrape_date": todaysdate,
                            "check_in": check_ins,
                            "check_out": check_outs,
                            "check_in_search": check_in_input,
                            "check_out_search": check_out_input,
                            "hoken_base_price": base_price_out,
                            "scrape_base_price": price_list[j],
                            # "hoken_average_price_fees": average_price_out,
                            # "scrape_average_price_fees": average_price_fees_list[j],
                            # "hoken_total_price": total_price_out,
                            # "scrape_total_price": total_price_list[j],
                            # "fees": fees_price_out,
                            "nights": nights_out,
                        }
                        final_data.append(data)
                    print(f"Row {i + 1}: {hotel_name} successfully scraped.")
                    number_of_success += 1
                    driver.close()
            else:
                print("broken (even w/ scraping from container)")
                # Add broken case data for later re-attempt
                re_attempt = handle_broken_case(
                    ids[i],
                    hotels[i],
                    cities[i],
                    check_in_dates[i],
                    check_out_dates[i],
                    base_prices[i],
                    # average_prices[i],
                    # fees_prices[i],
                    # total_prices[i],
                    nights[i],
                    re_attempt,
                )
                print(
                    f"I can't scrape row {i + 1}: {hotel_name}. I will re-attempt in the next scraping"
                )
                sleep(3)
                driver.close()
        except Exception:
            print("broken")
            # Add broken case data for later re-attempt
            re_attempt = handle_broken_case(
                ids[i],
                hotels[i],
                cities[i],
                check_in_dates[i],
                check_out_dates[i],
                base_prices[i],
                # average_prices[i],
                # fees_prices[i],
                # total_prices[i],
                nights[i],
                re_attempt,
            )
            print(
                f"I can't scrape row {i + 1}: {hotel_name}. I will re-attempt in the next scraping"
            )
            sleep(3)
            driver.close()

    return final_data, re_attempt


def chunks(list_to_chunk, size):
    """Split a list into chunks with length = size"""
    return (
        list_to_chunk[pos : pos + size] for pos in range(0, len(list_to_chunk), size)
    )


if __name__ == "__main__":
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # start time
    start = time.time()
    todaysdate = datetime.date.today()
    print(todaysdate)

    # Open the CSV file with the open function
    with open("Hotels to Scrape.csv", newline="") as csvfile:
        # Read the CSV file using the csv.reader module
        reader = csv.reader(csvfile)
        rows = list(reader)[1:]  # skip the heading row
        # rows = list(reader)[1:15]  # QUICK TESTING!

    # Transform the list into multiple chunks, for doing
    # concurrent processing
    rows_chuncks = chunks(rows, size=NB_HOTELS_CHUNK_SIZE)

    # Do the scraping
    results = {}
    with ThreadPoolExecutor(max_workers=NB_CONCURRENT_WORKERS) as executor:
        # Start and mark each future with its chunk (of rows to process)
        future_to_chunk_nb = {
            executor.submit(run_process, chunk, todaysdate): chunk_nb
            for chunk_nb, chunk in enumerate(rows_chuncks, 1)
        }
        for future in as_completed(future_to_chunk_nb):
            chunk_nb = future_to_chunk_nb[future]
            result_data, re_attempt = future.result()

            # Collect the results for merge into the data structures to save
            results[chunk_nb] = result_data, re_attempt

    # prepare for the last parts
    merged_final_data = []
    merged_re_attempt = []
    for key in results:
        merged_final_data = merged_final_data + results[key][0]
        merged_re_attempt = merged_re_attempt + results[key][1]

    # save result data
    if merged_final_data:
        save_data(merged_final_data, todaysdate)

    # time spent
    end = time.time()
    print(f"Completed in {(end - start)/60:.2f} minutes")
    print("************")

    # Save the data about failed cases
    print("re_attempt data:", merged_re_attempt)
    #  create csv file for failed scraping process
    df1 = pd.DataFrame(merged_re_attempt)
    df1.to_csv(f"final_data_reattempt_1_{todaysdate}.csv", index=False)
