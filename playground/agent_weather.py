from modules.google_genai_client import GoogleGenAIClient
from modules.weather_data import WeatherDataService
from modules.geocoding import GeocodingService
from google.genai import types
from rich.console import Console
from typing import Optional, Dict, Any

# Initialize the console for rich output
console = Console()
console.print("[bold cyan]Google GenAI weather Demo[/bold cyan]")

# Initialize the Google GenAI client
gervasio = GoogleGenAIClient()

# function that gets latitude and longitude of a city from geocoding
# and passes it to the weather_data
# returns a json with the weather data
def get_weather_data(city: str, country: Optional[str] = None) -> Dict[str, Any]:
    """
    Get weather data for a given city and country.
    Args:
        city (str): The name of the city.
        country (Optional[str]): The name of the country to disambiguate the city location. Defaults to None.
    Returns:
        Dict[str, Any]: Weather data in JSON format.
    """
    console.print(f"[yellow]Getting weather data for {city}{', ' + country if country else ''}...[/yellow]")
    geocoding = GeocodingService()
    coordinates = geocoding.geocode(city, country)
    if not coordinates:
        console.print("[red]City not found![/red]")
        return {"error": "City not found"}
    latitude, longitude = coordinates
    weather_data = WeatherDataService()
    weather_info = weather_data.get_complete_weather_json(latitude, longitude)
    return weather_info


# model
MODEL_ID = "gemini-2.0-flash"

# Generate a response
console.print("[yellow]Generating response...[/yellow]")
response = gervasio.client.models.generate_content(
    model=MODEL_ID,
    contents="What is the current weather in Porto, Portugal?",
    config=types.GenerateContentConfig(
        tools=[get_weather_data],
    )   
)

gervasio.display_response_text(response, "Weather Report")

# test the get_weather_data function
# city = "Porto"
# country = "Portugal"
# weather_info = get_weather_data(city, country)
# if weather_info and "error" not in weather_info:
#     console.print(f"[green]Weather data for {city}{', ' + country if country else ''}:[/green]")
#     console.print(weather_info)
# else:
#     console.print("[red]Failed to retrieve weather data.[/red]")
