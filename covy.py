from requests import get
from pandas import DataFrame, concat, read_excel
from math import floor
from os import chdir
from os.path import exists
from sys import path
from time import localtime, sleep
from textwrap import wrap
from schedule import every, run_pending
from bs4 import BeautifulSoup
from datetime import datetime
from warnings import filterwarnings
filterwarnings("ignore")

chdir(r"\\file\Userss$\sar173\Home\My Documents\postgrad\covy")
path.append(r"R:\admin\cody")

from cody import post_message_to_slack, post_file_to_slack

from logging import basicConfig, INFO, getLogger
basicConfig(format='%(asctime)-35s %(message)s', level=INFO, datefmt='%a %d %b %Y, %I:%M:%S %p')
logger = getLogger(__name__)

MINUTES_BETWEEN_SCRAPING = 10
MOH_API_URL = "https://api.integration.covid19.health.nz/locations/v1/current-locations-of-interest"
UC_URL = "https://www.canterbury.ac.nz/covid-19/locations/"

CITY_OF_INTEREST = "Christchurch"
LAST_MOH_LOCATIONS_FILEPATH = "last_moh_locations.xlsx"
LAST_UC_LOCATIONS_FILEPATH = "last_uc_locations.xlsx"


def update_uc_locations():
    """Find changes in the University of Canterbury's database of locations of interest"""
    
    # Grab the html code from the webbsite and use BeautifulSoup to store all the information
    soup = BeautifulSoup(get(UC_URL).text, "lxml")
    
    # List the correct amount of columns, as sometimes data rows are put as a table 'tr'
    column_names = ['Location', 'Date', 'Time', 'Categorisation', 'Added']
    # Each table relates to a seperate day, so find all tables in the html code
    current_locations = DataFrame()
    for table in soup.findAll("table"):
        # Find all rows in this table, where the it is a 1D column
        raw_rows = table.find_all("td")
        # Set up empty lists to contain the reshaped and processed data
        processed_rows = [[] for _ in range(len(raw_rows) // len(column_names))]
        for index, raw_row in enumerate(raw_rows):
            row_number = index // len(column_names) # relates to which row it should be on
            value = raw_row.text.strip("\n").strip().replace("\n", " ") # strip new lines            
            processed_rows[row_number].append(value.lower() if raw_row.text[0].isnumeric() else value.title())
        current_locations = concat([current_locations, DataFrame(data=processed_rows, columns=column_names)])
    current_locations.reset_index(drop=True, inplace=True)

    if exists(LAST_UC_LOCATIONS_FILEPATH):
        changed_locations = check_for_changes(current_locations, LAST_UC_LOCATIONS_FILEPATH)
        if len(changed_locations) == 0:
            # Break the program as no changes detected
            return None
    else:
        # This is the first time running it and all current locations are new!
        changed_locations = current_locations
        changed_locations["Status"] = ["New Location"] * len(changed_locations)

    # Clean up the changed locations
    changed_locations = changed_locations[["Status", "Location", "Date", "Time", "Categorisation", "Added"]]
    changed_locations.reset_index(drop=True, inplace=True)

    # Save the current cases in the previous file spot to replace it
    with open(LAST_UC_LOCATIONS_FILEPATH, "wb") as last_locations_file:
        current_locations.drop(columns=["Status"]).to_excel(last_locations_file, index=False)

    # Create the markdown file of the changed locations
    changed_locations = wrap_dataframe_rows(changed_locations)
    with open("updated uc locations.md", "w", encoding="utf-8") as file:
        _ = file.write(changed_locations.to_markdown(index=False, tablefmt="fancy_grid"))

    # Notify
    message = f"There has been an update in the locations of interest at the University of Canterbury. For further details, please refer to the <{UC_URL}|University of Canterbury's COVID website>."
    post_message_to_slack("#covid_updates", message_type="Information", identifier="Covid Locations of Interest Update", message=message)
    post_file_to_slack("#covid_updates", ["updated uc locations.md"], "", greet=False)


def update_moh_locations():
    """Find changes in the Ministry of Health's database of locations of interest"""
    
    # Query the API for current data
    all_locations_of_interest = get(MOH_API_URL).json()["items"]

    # The 'location' attribute is a nested dictionary, so add it to the global dictionary instead
    locations_of_interest_in_city = [ location for location in all_locations_of_interest if location["location"]["city"] == CITY_OF_INTEREST]
    _ = [ location.update(location["location"]) for location in  locations_of_interest_in_city ]

    current_locations = DataFrame(locations_of_interest_in_city)
    current_locations = current_locations[["eventName", "address", "startDateTime", "endDateTime", "exposureType"]]
    
    print("1")

    if exists(LAST_MOH_LOCATIONS_FILEPATH): 
        changed_locations = check_for_changes(current_locations, LAST_MOH_LOCATIONS_FILEPATH)
        if len(changed_locations) == 0:
            # Break the program
            return None            
    else:
        # This is the first time running it and all current locations are new!
        changed_locations = current_locations.copy()
        changed_locations["Status"] = ["New Location"] * len(changed_locations)

    # Turn the nasty strings into datetime objects so that we can write a nice string of the date and times.
    changed_locations["startDateTime"] = [datetime.strptime(value.replace("T", " ").replace("Z", ""), "%Y-%m-%d %H:%M:%S.%f") for value in changed_locations["startDateTime"]]
    changed_locations["endDateTime"] = [datetime.strptime(value.replace("T", " ").replace("Z", ""), "%Y-%m-%d %H:%M:%S.%f") for value in changed_locations["endDateTime"]]
    changed_locations["Date"] = [datetime.strftime(start_value, "%A/%m/%Y") for start_value in changed_locations["startDateTime"]]
    changed_locations["Time"] = ["{} - {}".format(datetime.strftime(start_value, "%I:%M%p"), datetime.strftime(end_value, "%I:%M%p")).lower() for start_value, end_value in zip(changed_locations["startDateTime"], changed_locations["endDateTime"])]
    print("3")
    # Clean up the changed locations
    changed_locations = changed_locations[["Status", "eventName", "address", "Date", "Time", "exposureType"]]
    changed_locations.rename(columns={"eventName":"Place", "address":"Address", "exposureType":"Exposure"}, inplace=True)
    changed_locations.reset_index(drop=True, inplace=True)

    # Save the current cases in the previous file spot to replace it
    with open(LAST_MOH_LOCATIONS_FILEPATH, "wb") as last_locations_file:
        current_locations.to_excel(last_locations_file, index=False)
    print("4")
    # Create the markdown file of the changed locations
    changed_locations = wrap_dataframe_rows(changed_locations)
    with open("updated moh locations.md", "w", encoding="utf-8") as file:
        _ = file.write(changed_locations.to_markdown(index=False, tablefmt="fancy_grid"))

    # Notify
    message = f"There has been an update in the locations of interest for {CITY_OF_INTEREST}. For further details, please refer to the <https://www.health.govt.nz/covid-19-novel-coronavirus/covid-19-health-advice-public/covid-19-information-close-contacts/covid-19-contact-tracing-locations-interest| Ministry of Health's website>."
    post_message_to_slack("#covid_updates", message_type="Information", identifier="Covid Locations of Interest Update", message=message)
    post_file_to_slack("#covid_updates", ["updated moh locations.md"], "", greet=False)


def check_for_changes(current_locations, previous_locations_fp):
    """Assess the current_locations DataFrame against the previous_locations DataFrame, and return any changes in the current_locations DataFrame."""

    # Open the previous file
    with open(previous_locations_fp, "rb") as last_locations_file:
        previous_locations = read_excel(last_locations_file)
        last_locations_file.close()

    previous_locations = previous_locations[current_locations.columns]

    # Test to see if the same as previous data
    if not previous_locations.equals(current_locations):
        # Find the overlaps which is changed_locations
        changed_locations = concat([previous_locations, current_locations]).drop_duplicates(keep=False)
        # Convert the old dataframess to numpy arrays to check if in them
        previous_locations_array = previous_locations.to_numpy()
        current_locations_array = current_locations.to_numpy()
        # Assess if the change is new or removed by seeing which old dataframe it is in
        changed_locations["Status"] = ["New Location" if row in current_locations_array and row not in previous_locations_array else "Removed Location" for row in changed_locations.to_numpy()]
        changed_locations.sort_values("Status", inplace=True)
        return changed_locations
    
    else:
        # No updates found so send back empty DataFrame
        return DataFrame()


def wrap_dataframe_rows(changed_locations, width_limit=150):
    """Enforce a strict width limit on a DataFrame such that it can be printed out nicely. If the width of the DataFrame is over the limit, then the largest column is halved untill the limit is met. It assumes all dtypes are strings. New line characters are inserted into the strng to make the DataFrame reduce in width."""

    while len(changed_locations.to_markdown(index=False).split("\n")[0]) >= width_limit:
        column_line = changed_locations.to_markdown(index=False).split("\n")[0]
        row_lengths = [len(col) for col in column_line.split("|")[1:-1]]
        column_index = row_lengths.index(max(row_lengths))
        column_name = changed_locations.columns[column_index]
        # Split in half
        halved_values = []
        for value in changed_locations[column_name]:
            words = wrap(value, floor(row_lengths[column_index]/2), break_long_words=True, break_on_hyphens=True, drop_whitespace=True)
            final = ''
            for word in words:
                final += word + "\n"
            halved_values.append(final[:-1])
        changed_locations[column_name] = halved_values

    return changed_locations


def update():
    """Attempt to find changes to the locations of interest at both the University of Canterbury's campus and in Chhristchurch according to the Ministry of Health."""
    try:
        update_uc_locations()
        logger.info("Scraping successful for UC locations")
    except Exception as error:
        error_string = f"Scraping failed for UC locations due to: {error}"
        logger.info(error_string)
        post_message_to_slack("#covid_updates", "Failure", "Covid Locations of Interest Update", message=error_string)

    try:
        update_moh_locations()
        logger.info("Scraping successful for MOH locations")
    except Exception as error:
        error_string = f"Scraping failed for MOH locations due to: {error}"
        logger.info(error_string)
        post_message_to_slack("#covid_updates", "Failure", "Covid Locations of Interest Update", message=error_string)


def main():
    # Schedule and perform the function for every minute
    every(1).minutes.do(update)
    while True:
        print("Waiting...", end="\r")
        if localtime().tm_min % MINUTES_BETWEEN_SCRAPING == 0:
            print("Running!", end="\r")
            # Then it's time to update!
            run_pending()
            sleep(61)


if __name__ == "__main__":
    main()