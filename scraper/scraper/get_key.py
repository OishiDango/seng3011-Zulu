from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, parse_qs

PROMED_EMAIL = "z5480247@ad.unsw.edu.au"
PROMED_PASSWORD = "79E8CRr!CRvw!PR"


def get_typesense_key(email: str, password: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        captured = {"key": None}

        def on_request(request):
            url = request.url
            if "multi_search" in url and "x-typesense-api-key=" in url:
                qs = parse_qs(urlparse(url).query)
                key = qs.get("x-typesense-api-key", [None])[0]
                if key:
                    captured["key"] = key

        page.on("request", on_request)

        page.goto("https://www.promedmail.org/", wait_until="domcontentloaded")
        page.get_by_role("link", name="Search", exact=True).click()

        page.wait_for_selector("#username", timeout=30000)
        page.fill("#username", email)
        page.fill("#password", password)

        page.locator("button[type='submit']").click()

        page.wait_for_url("**/search", timeout=60000)
        page.wait_for_timeout(5000)

        browser.close()

        if not captured["key"]:
            raise RuntimeError("Could not capture Typesense API key.")

        return captured["key"]


if __name__ == "__main__":
    key = get_typesense_key(PROMED_EMAIL, PROMED_PASSWORD)

    with open("promed_key.txt", "w", encoding="utf-8") as f:
        f.write(key)

    print("Saved key to promed_key.txt")
