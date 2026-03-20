from google import genai
from google.genai import types
from datetime import date
import os

# PORT = "7800"
# os.environ['http_proxy'] = f"http://127.0.0.1:{PROXY_PORT}"
# os.environ['https_proxy'] = f"http://127.0.0.1:{PROXY_PORT}"

os.getenv("GEMINI_API_KEY")


class GeminiSummary:
    response_schema = {
        "type": "object",
        "description": (
            "Structured travel-risk summary based only on the provided"
            " outbreak alerts and disease metadata for the requested location context"
        ),
        "additionalProperties": False,
        "properties": {
            "overall_assessment": {
                "type": "object",
                "description": (
                    "High-level assessment for the requested location. "
                    "This should give the main travel-risk picture in a short"
                    " paragraph and explain the overall level briefly and objectively"
                ),
                "additionalProperties": False,
                "properties": {
                    "location": {
                        "type": "array",
                        "description": "Copy the exact location from the input context",
                        "items": {"type": "string"},
                        "minItems": 1,
                    },
                    "summary": {
                        "type": "string",
                        "description": (
                            "A concise but slightly detailed summary paragraph"
                            " for the requested location It should synthesize "
                            "recent/repeated alert signals, disease metadata, "
                            "and travel relevance for short- and medium-term visitors"
                        ),
                    },
                    "overall_risk_level": {
                        "type": "string",
                        "description": (
                            "Overall travel-risk level for the requested "
                            "location based only on the provided alerts "
                            "and disease metadata: choose High if there is any recent"
                            " alert with high severity or high exposure, or if there "
                            "are multiple recent alerts; choose Medium if these "
                            "conditions are met but the alerts are not recent; choose "
                            "Low if there are no alerts, or if the alerts are not"
                            " recent and do not involve high severity or high exposure."
                        ),
                        "enum": ["high", "medium", "low"],
                    },
                    "key_reasons": {
                        "type": "array",
                        "description": (
                            "Main reasons supporting the overall assessment, "
                            "you should mention concrete drivers such as recency,"
                            " repeated alerts, strong exposure relevance, or strong "
                            "severity relevance"
                        ),
                        "items": {"type": "string"},
                        "minItems": 1,
                        "maxItems": 4,
                    },
                },
                "required": [
                    "location",
                    "summary",
                    "overall_risk_level",
                    "key_reasons",
                ],
            },
            "major_threats": {
                "type": "object",
                "description": (
                    "Current main threats for the requested "
                    "location in the travel context."
                ),
                "additionalProperties": False,
                "properties": {
                    "high_exposure": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/threat_item"},
                    },
                    "high_severity": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/threat_item"},
                    },
                },
                "required": ["high_exposure", "high_severity"],
            },
            "potential_threats": {
                "type": "object",
                "description": (
                    "Relevant but less central threats " "for the requested location."
                ),
                "additionalProperties": False,
                "properties": {
                    "high_exposure": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/threat_item"},
                    },
                    "high_severity": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/threat_item"},
                    },
                    "other_relevant_threats": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/threat_item"},
                    },
                },
                "required": [
                    "high_exposure",
                    "high_severity",
                    "other_relevant_threats",
                ],
            },
            "ignored_alerts": {
                "type": "array",
                "description": (
                    "Alerts ignored only because they are "
                    "clearly outside the requested location context."
                ),
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "external_id": {"type": "string"},
                        "reason": {"type": "string"},
                    },
                    "required": ["external_id", "reason"],
                },
            },
        },
        "required": [
            "overall_assessment",
            "major_threats",
            "potential_threats",
            "ignored_alerts",
        ],
        "$defs": {
            "threat_item": {
                "type": "object",
                "description": "A disease entry inside a threat category.",
                "additionalProperties": False,
                "properties": {
                    "disease": {"type": "string"},
                    "why_included": {"type": "string"},
                    "supporting_alert_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                    },
                },
                "required": ["disease", "why_included", "supporting_alert_ids"],
            }
        },
    }

    def __init__(self, api_key: str, model_id: str):
        if not api_key:
            raise ValueError("API key is missing.")
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id

    def region_summary(
        self, alerts: list, location_chain: list, disease_info: dict = {}
    ):

        prompt = f"""
            You are assessing infectious disease risk for an
            airport-oriented travel
            safety service for short- and medium-term visitors,
            You assessments must base on alert and diseases
            information provided below as list.

            Summarize base on the provided outbreak alerts
            and the provided disease
            metadata, DO NOT RESEARCH.
            Do not use web search, external sources, tools,
            or unstated medical facts.
            You can mention if the provided
            data is insufficient for a conclusion.

            Assume customers are likely to move through airports, public
            transport, hotels, tourist sites and other shared public
            infrastructure that can be moderately crowded or crowded.
            Do not Assume visitors stay at home most of the time.
            Do not assume they remain only in major urban areas.
            Do not assume unusual occupational, agricultural,
            or long term community exposure.

            Pay attention to the publish date of alerts.
            Today is {date.today()}.
            The location is {location_chain}, carefully ignore alerts
            only when they obviously unrelated to this location.
            List all the ignored alerts follow the schema.
            Repeated alerts for the same disease or area may indicate
             a stronger signal, but do not overstate certainty
             beyond the provided evidence.

            Your task is to create a concise, objective summary for
            travel-risk interpretation by:
            1. outbreak evidence from the provided filtered alerts
            2. disease-level context from the provided disease metadata

            Return only valid JSON matching the required schema.

            Provided alerts:
            {alerts}

            Provided disease metadata:
            {disease_info}
                """

        # schema_str = json.dumps(self.response_schema, indent=2)

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
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


if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key is None:
        raise ValueError("GEMINI_API_KEY not set")

    AI = GeminiSummary(api_key, model_id="gemini-3-flash-preview")
    # # AI = GeminiService(API_KEY, model_id="gemini-3.1-pro-preview")
    # while True:
    #     user_input = input("\ninput diseases:")
    #     diseases = set(user_input.split())
    #     print(diseases)
    #     AI.disease_assessment(diseases)
