from requests import get
from pandas import DataFrame, concat, read_excel
from os.path import exists
from sys import path
from time import strftime, localtime, sleep
from schedule import every, run_pending

path.append(r"R:\admin\cody")
from cody import post_message_to_slack, post_file_to_slack


from logging import basicConfig, getLogger, ERROR
basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=ERROR,
    datefmt='%d-%m-%Y %H:%M:%S')
logger = getLogger(__name__)

MINUTES_BETWEEN_SCRAPING = 30
API_URL = "https://api.integration.covid19.health.nz/locations/v1/current-locations-of-interest"
CITY_OF_INTEREST = "Christchurch"
LAST_LOCATIONS_FILEPATH = "last_covid_locations.xlsx"
CHANGED_LOCATIONS_FILEPATH = "changed_covid_locations.xlsx"


def update_locations_of_interest():

    all_locations_of_interest = get(API_URL).json()["items"]

    locations_of_interest_in_city = [ location for location in all_locations_of_interest if location["location"]["city"] == CITY_OF_INTEREST]

    # expand the location dict into each main dict
    _ = [ location.update(location["location"]) for location in  locations_of_interest_in_city ]

    current_locations = DataFrame(locations_of_interest_in_city).drop(columns=["location"])

    if exists(LAST_LOCATIONS_FILEPATH):

        with open(LAST_LOCATIONS_FILEPATH, "rb") as last_locations_file:
            previous_locations = read_excel(last_locations_file)
            last_locations_file.close()
            
            # test to see if the same as previous data
            if not previous_locations.equals(current_locations):
                
                # A change has occured
                changed_locations = concat([previous_locations, current_locations]).drop_duplicates(keep=False)

                # Determine if new or removed
                changed_locations["Status"] = ["New Location" if event_id in current_locations["eventId"] else "Removed Location" for event_id in changed_locations["eventId"]]

                changed_locations.sort_values("Status", inplace=True)
            
            else:
                # No updates found so stop the program
                return None
            
    else:
        # This is the first time running it and all current locations are new!
        changed_locations = current_locations
        changed_locations["Status"] = ["New Location"] * len(changed_locations)

    # Clean up the changed locations and save it as a csv
    changed_locations = changed_locations[["Status", "eventName", "address", "exposureType", "publicAdvice"]]
    changed_locations.reset_index(drop=False, inplace=True)
    changed_locations.to_excel(CHANGED_LOCATIONS_FILEPATH, index=False)

    # Save the current cases in the previous csv spot to replace it
    with open(LAST_LOCATIONS_FILEPATH, "wb") as last_locations_file:
        current_locations.to_excel(last_locations_file, index=False)

    message = f"There has been an update in the locations of interest for {CITY_OF_INTEREST}. For further details, please refer to the Ministry of Health's website: https://www.health.govt.nz/covid-19-novel-coronavirus/covid-19-health-advice-public/covid-19-information-close-contacts/covid-19-contact-tracing-locations-interest\n"

    # Notify
    post_message_to_slack("#covid_updates", message_type="Information", identifier="Covid Locations of Interest Update", message=message, greet=True)
    post_file_to_slack("#covid_updates", [CHANGED_LOCATIONS_FILEPATH], "", greet=False)



def dataframe_to_string(current_locations):

    string = current_locations.to_string()  



def main():

    # Schedule and perform the function every 30 mins
    try:
        every(1).minutes.do(update_locations_of_interest)
        while True:
            if localtime().tm_min % MINUTES_BETWEEN_SCRAPING == 0:
                # Then it's time to update!
                run_pending()
                sleep(61)

    # Log errors when they happen
    except Exception as error:
        time = strftime("%d %b %Y %H %M", localtime())
        logger.info("Scraping failed for at {} for {}".format(time, error))
        post_message_to_slack("#covid_updates", "Failure", "Covid Locations of Interest Update", message="Scraping failed at {} due to {}".format(time, error))
    

if __name__ == "__main__":
    main()