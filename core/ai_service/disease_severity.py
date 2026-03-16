import json
import os

from .disease_severity_update import GeminiService
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

disease_info_json = BASE_DIR / "disease_info.json"

ALLOWED_LEVELS = {
    "unknown": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
}

ALLOWED_LEVELS_REVERSE = {
    0 : "unknown",
    1 : "low",
    2 : "medium",
    3 : "high"
}

data_keys = {"severity", "severity_reason", "risk_of_exposure", "exposure_reason", "confidence"}

def extract_disease_names_from_response(response_raw):
    data = json.loads(response_raw)
    diseases = data.get("by_disease", [])

    disease_names = set()
    for item in diseases:
        if isinstance(item, dict) and isinstance(item.get("disease"), str) and item.get("disease").strip():
            disease_names.add(item.get("disease").strip())

    return disease_names



def extract_disease_name_from_JSON():
    with open(disease_info_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    disease_names = set()
    for disease in data.items():
        if isinstance(disease[0], str) and disease[0].strip():
            disease_names.add(disease[0])

    return disease_names



def need_updates(response_set: set, json_set: set):
    return response_set.difference(json_set)


def initialize_json():
    with open(disease_info_json, "w", encoding="utf-8") as f:
        initial_data = {}
        json.dump(initial_data, f, indent=2)




def validate_response(data, new_disease: set):
    if not isinstance(data, dict):
        return ["Entire response isn't in JSON format"], {}
    err_response = []

    correct_data = {}
    
    for disease_name, disease_data in data.items():
        
        if not isinstance(disease_name, str) :
            err_response.append(f"{disease_name} is not a valid str")
            continue
        disease_name = disease_name.strip()
        if not disease_name:
            err_response.append("Disease name is empty")
            continue
        if disease_name not in new_disease:
            err_response.append(f"{disease_name} is not valid new disease")
            continue


        data_keys = {"severity", "severity_reason", "risk_of_exposure", "exposure_reason", "confidence"}

        if not isinstance(disease_data, dict):
            err_response.append( f"{disease_name} has no valid data")
            continue
        
        clean_keys = True
        for key in disease_data.keys():
            if not isinstance(key, str):
                err_response.append( f"{disease_name} has key {key} not in str")
                clean_keys = False
                break

        if not clean_keys:
            continue

        if set(key.strip().lower() for key in disease_data.keys()) != data_keys:
            err_response.append( f"{disease_name} has no enough valid keys in data ")
            continue

        clean_values = True
        normalized_data = {}
        for key, value in disease_data.items():
            normalized_key = key.strip().lower()

            if normalized_key in {"severity_reason", "exposure_reason"}:
                if not isinstance(value, str) or not value.strip():
                    err_response.append( f"{disease_name}.{key} has invalid value: {value!r}")
                    clean_values = False
                    break

                normalized_value = value.strip()

            else:
                if not isinstance(value, str) or value.strip().lower() not in ALLOWED_LEVELS.keys():
                    if not isinstance(value, int) or value < 0 or value >= 4:
                        err_response.append( f"{disease_name}.{key} has invalid value: {value!r}")
                        clean_values = False
                        break

                if isinstance(value, str):
                    normalized_value = value.strip().lower()
                else:
                    normalized_value = ALLOWED_LEVELS_REVERSE[value]

            normalized_data[normalized_key] = normalized_value



        if clean_values:
            correct_data[disease_name] = normalized_data
        
    print(err_response)
        

    return err_response, correct_data

        



def append_json(update_data, new_disease:set):
    with open(disease_info_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    update = json.loads(update_data)

    err_response, correct_data = validate_response(update, new_disease)

    for disease_name, disease_value in correct_data.items():
        data[disease_name] = disease_value

    with open(disease_info_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent = 2)


def generate_disease_severity_entry(response_raw, api_key:str, model_id:str="gemini-3-flash-preview"):
    if not os.path.exists(disease_info_json):
        initialize_json()

    if isinstance(response_raw, dict):
        response_raw = json.dumps(response_raw)

    response_set = extract_disease_names_from_response(response_raw)
    json_set = extract_disease_name_from_JSON()
    new_disease = need_updates(response_set, json_set)

    if not new_disease:
        return {
            "new_disease": [],
            "updated_disease": [],
            "errors": [],
        }

    AI = GeminiService(api_key, model_id=model_id)
    update_data = AI.disease_assessment(new_disease)

    err_response, correct_data = validate_response(update_data, new_disease)

    if correct_data:
        append_json(json.dumps(correct_data), new_disease)

    return {
        "new_disease": sorted(new_disease),
        "updated_disease": sorted(correct_data.keys()),
        "errors": err_response,
    }