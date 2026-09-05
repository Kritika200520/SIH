import requests
import ssl
import urllib.request
import json

def get_current_rainfall(lat, lng):
    """
    Fetches the 24-hour precipitation sum for a given latitude and longitude using Open-Meteo API.
    Returns the rainfall in mm. If it fails, returns a default mock value.
    """
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&daily=precipitation_sum&timezone=auto&forecast_days=1"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        rainfall = data.get("daily", {}).get("precipitation_sum", [0.0])[0]
        return float(rainfall) if rainfall is not None else 0.0
    except Exception as e:
        print(f"[Weather API] Failed to fetch via requests: {e}. Trying urllib...")
        # Fallback to urllib with unverified SSL context just in case
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
                data = json.loads(response.read())
                rainfall = data.get("daily", {}).get("precipitation_sum", [0.0])[0]
                return float(rainfall) if rainfall is not None else 0.0
        except Exception as e2:
            print(f"[Weather API] Failed to fetch via urllib: {e2}")
            return None

