import json
from google import genai
from google.genai import types

# PORT = "7800"
# os.environ['http_proxy'] = f"http://127.0.0.1:{PROXY_PORT}"
# os.environ['https_proxy'] = f"http://127.0.0.1:{PROXY_PORT}"


class GeminiService:
    response_schema = {
        "type": "object",
        "minProperties": 1,
        "additionalProperties": {
            "type": "object",
            "properties": {
                "severity": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 3,
                    "description": (
                        "Potential clinical impact and health damage to an "
                        "individual upon infection, ranging from mild symptoms"
                        "(1) to life-threatening conditions (3), (0) for unkown."
                    ),
                },
                "severity_reason": {
                    "type": "string",
                    "description": (
                        "A very brief reason for the " "severity score, under 20 words."
                    ),
                },
                "risk_of_exposure": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 3,
                    "description": (
                        "General likelihood of a traveler contracting the disease"
                        " based on its transmission mode and inherent contagiousness"
                        " (1=Low, 2=Medium, 3=High), (0) for unkown."
                    ),
                },
                "exposure_reason": {
                    "type": "string",
                    "description": (
                        "A very brief reason for the risk_of_exposure "
                        "score, under 20 words."
                    ),
                },
                "confidence": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 3,
                    "description": (
                        "The degree of certainty in the overall assessment,"
                        " reflecting the alignment with authoritative medical "
                        "guidelines (1=Low, 2=Medium, 3=High), (0) for unkown."
                    ),
                },
            },
            "required": [
                "severity",
                "severity_reason",
                "risk_of_exposure",
                "exposure_reason",
                "confidence",
            ],
            "additionalProperties": False,
        },
    }

    def __init__(self, api_key: str, model_id: str):
        if not api_key:
            raise ValueError("API key is missing.")
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id

    def disease_assessment(self, disease: set):

        prompt = """
            You are assessing infectious disease risk for an airport-oriented
            travel safety service for short- and medium-term visitors,
            You assessments must base on general authoritative
            medical/public health knowledge and be completely objective.
            Assume customers are likely to move through
            airports, public transport, hotels, tourist
            sites and other shared public infrastructure
            that can be moderately crowded or crowded.
            Do not Assume visitors stay at home most of the time.
            Do not assume they remain only in major urban areas.
            Do not assume unusual occupational, agricultural,
            or long term community exposure.
            For each disease mentioned, return their severity,
            severity_reason, risk_of_exposure, exposure_reason, confidence.
            Assess each disease from the perspective of a
            typical short- to medium-term traveler.
            Assume the disease is present at the destination.

            Assessment rubrics:
            Severity measures the likely clinical impact on
            an individual if infected.
            Consider factors such as typical symptom burden,
            risk of complications, likelihood of needing
            medical care or hospitalization,
            potential long-term harm, and mortality risk.
            0 = Unknown
            1 = Low: usually mild and self-limiting, limited clinical impact
            2 = Medium: can cause substantial illness
            and may require medical attention or treatment
            3 = High: can cause severe disease, serious complications,
            hospitalization, or death

            Risk of exposure measures how likely a typical
            short to medium term traveler is to be exposed during
            ordinary travel, considering common movement through airports,
            transport routes, urban areas, regional towns,
            and sometimes semi-urban or rural settings depending on itinerary.
            0 = Unknown
            1 = Low: relatively unlikely exposure for a typical traveler
            2 = Medium: plausible exposure under normal travel behavior
            3 = High: relatively likely exposure due to common transmission
            routes, crowd contact, environmental exposure,
            or active circulation

            Confidence measures how certain the severity and risk-of-exposure
            assessments are based on the available information
            and general authoritative medical/public health knowledge.
            You must
            Use 3 only when the disease characteristics
            and traveler exposure profile are well-established
            and the assessment is straightforward.
            Use 2 when the assessment is generally reasonable
            but some uncertainty remains.
            Use 1 when the disease name is ambiguous,
            uncommon, context-dependent,
            or the assessment depends heavily on missing details.
            Use 0 when the information is
            insufficient for a meaningful judgment.
            Do not default to 3, you are allowed to be not confident

            Use each disease name as a top-level JSON key.
            Each disease must map to anobject containing exactly: severity,
            severity_reason, risk_of_exposure, exposure_reason, confidence.
            Return only valid JSON matching the required schema.

            Schema:
                """

        diseases_list = ", ".join(sorted(disease))

        schema_str = json.dumps(self.response_schema, indent=2)

        full_prompt = prompt + schema_str + f"\n\nDiseases to assess: {diseases_list}"
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_json_schema=self.response_schema,
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            print(response.parsed)
            return response.parsed

        except Exception as e:
            raise RuntimeError(f"{self.model_id} request crashed: {e}")


# if __name__ == "__main__":
#     AI = GeminiService(API_KEY, model_id="gemini-3-flash-preview")
#     # AI = GeminiService(API_KEY, model_id="gemini-3.1-pro-preview")
#     while True:
#         user_input = input("\ninput diseases:")
#         diseases = set(user_input.split())
#         print(diseases)
#         AI.disease_assessment(diseases)
