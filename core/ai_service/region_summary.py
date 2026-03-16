import json
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from pathlib import Path
import os
# import region_summary_api
from . import region_summary_api

BASE_DIR = Path(__file__).resolve().parent
DISEASE_INFO_JSON = BASE_DIR / "disease_info.json"

BASE_DIR2 = Path(__file__).resolve().parents[2]



def filter_start_date(window:str, today:date|None = None) -> date:
    if today is None:
        today = date.today()

    start_date = today
    if window == "7day":
        start_date = today - timedelta(7)
    elif window == "1month":
        start_date = today - relativedelta(months=1)
    elif window == "3month":
        start_date = today - relativedelta(months=3)
    elif window == "6month":
        start_date = today - relativedelta(months=6)

    return start_date


def filter_date(start_date:date | None, end_date:date | None, database:list)->list:
    beginning = str(start_date)
    ending = str(end_date)
    result = []

    for alert in database:
        alert_date = alert['fields']["date"]

        if end_date and ending < alert_date:
            continue
        if start_date and alert_date < beginning:
            break
        result.append(alert)
    
    return result


def sort_database(database:list):
    return sorted(database, key=lambda a:a["fields"]["date"], reverse=True)


def find_by_every_location(database: list, location_str: str) -> list:
    chains = []

    for alert in database:
        location = alert["fields"]["locations"]

        for L in location:
            matched = False

            for part in L:
                if part.lower() == location_str.lower():
                    matched = True
                    break

            if matched:
                chains.append(L)

    unique = set()
    result = []

    for l in chains:
        chain = ">".join(l)
        if chain not in unique:
            unique.add(chain)
            result.append(l)

    return result

def find_by_exact_location(database:list, location_chain:list) -> list:
    results = []
    for alert in database:
        location = alert["fields"]["locations"]
        # print(location)
        for L in location:
            if L == location_chain:
                results.append(alert)
                break
    
    return results



def find_by_upper_location(database:list, location_chain:list) -> list:
    chains = []
    results = []

    for i in range(len(location_chain), 0, -1):
        chains.append(location_chain[:i])

    for alert in database:
        location = alert["fields"]["locations"]
        for L in location:
            if L in chains:
                results.append(alert)
                break
    
    return results
        

def find_related_location(database:list, location_chain:list, exact_match:list|None = None) -> list:
    keyword=location_chain[-1].lower()
    country = location_chain[0].lower()

    unique = set()
    if exact_match:
        for alert in exact_match:
            unique.add(alert["fields"]["external_id"])

    results = []

    for alert in database:
        external_id = alert["fields"]["external_id"]
        if external_id in unique:
            continue

        location = alert["fields"]["locations"]
        matched = False

        for L in location:
            if len(L) > len(location_chain) and L[:len(location_chain)] == location_chain:
                matched = True
                break

        if not matched:
            title = alert["fields"]["title"].lower()
            if keyword in title:
                for L in location:
                    if len(L) > 0 and L[0].lower() == country:
                        matched = True
                        break

        if matched:
            results.append(alert)
            unique.add(external_id)

    return results


# database is required, one of location_chain and location_str is required, location_str should be the most precise region only e.g. Sydney

def filter_entry(end_date: date | None = None, window: str | None = None, start_date: date | None = None, location_chain: list | None = None, location_str: str | None = None, database: list = None ) -> list:
    
    if not database:
        raise ValueError("database is required")

    if not location_chain and not location_str:
        raise ValueError("location_chain or location_str is required")

    if end_date is None:
        end_date = date.today()

    if start_date is None and window is None:
        start_date = end_date

    if window is not None:
        start_date = filter_start_date(window, end_date)

    database = filter_date(start_date, end_date, database)

    if location_chain is None:
        chains = find_by_every_location(database, location_str)
        if not chains:
            return [], None
        location_chain = chains[0]

    exact_match = find_by_exact_location(database, location_chain)
    related_match = find_related_location(database, location_chain, exact_match)

    return exact_match + related_match, location_chain





def extract_disease_name_from_result(result:list):
    disease_names = set()

    for alert in result:
        fields = alert.get("fields", {})
        diseases = fields.get("diseases", [])

        if not isinstance(diseases, list):
            continue

        for disease in diseases:
            if isinstance(disease, str) and disease.strip():
                disease_names.add(disease.strip())

    return disease_names



def search_disease_info_from_JSON(result:list):
    disease_info_json = "disease_info.json"
    with open(disease_info_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    disease_names = extract_disease_name_from_result(result)

    results = {}

    for disease in disease_names:
        if disease in data:
            results[disease]=data[disease]

    return results

def generate_summary_entry(database: list, end_date: date | None = None, window: str | None = None, start_date: date | None = None, location_chain: list | None = None, location_str: str | None = None):
    result, location_chain = filter_entry(end_date=end_date,window=window, start_date=start_date, location_chain=location_chain, location_str=location_str,  database=database)
    diseases = extract_disease_name_from_result(result)

    API_KEY = os.getenv("GEMINI_API_KEY")

    AI = region_summary_api.GeminiSummary(API_KEY, model_id="gemini-3-flash-preview")
    response = AI.region_summary(result, location_chain, diseases )
    return {
        "summary":response,
        "location_chain":location_chain
    }


if __name__ == "__main__":

#     # # print(str(filter_start_date("1month")))
    # file = r"seng3011-Zulu\scraper\scraper\alerts.json"

    file = BASE_DIR2 / "scraper" / "scraper" / "alerts.json"
    with open(file, "r",encoding="utf-8") as f:
        database = json.load(f)
#     #     # print(database)
#     #     start_date = filter_start_date("3month")
#     #     print(start_date)
#     #     database = filter_date(start_date, end_date=None, database=database)
#     #     location_chain = find_by_every_location(database, "Hong Kong")
#     #     print(location_chain)
#     #     exact_match = find_by_exact_location(database, location_chain[0])
#     #     print(exact_match)
#     #     print(len(exact_match))
#     #     title_match = find_related_location(database, location_chain[0], exact_match)
#     #     print(title_match)
#     #     print(len(title_match))

#     with open(file, "r") as f:
#         database = json.load(f)
#     # result = filter_entry(window="3month", location_str="Hong Kong", database=database)
#     # print(result)
#     # diseases = extract_disease_name_from_result(result)
#     # print(diseases)
#     # # print(search_disease_info_from_JSON(diseases))

#     # API_KEY = "AIzaSyCa6LB5tin7aK604YEsL9M3wQedlLptmE8"

#     # AI = region_summary_api.GeminiSummary(API_KEY, model_id="gemini-3-flash-preview")
#     # location_chain = find_by_every_location(database, "Hong Kong")
#     # response = AI.region_summary(result, location_chain, {} )
#     # # print(response)
    generate_summary_entry(window="3month",location_str="New South Wales", database=database)


