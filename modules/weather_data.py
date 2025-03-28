import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from typing import Dict, Optional, Tuple, Any, Union
import logging

class WeatherDataService:
    """
    A service for retrieving and displaying weather data from the Open-Meteo API.
    
    This class provides methods to fetch current weather information and forecasts
    based on geographical coordinates, with rich formatted output options.
    """
    
    def __init__(self):
        """
        Initialize the WeatherDataService.
        
        Sets up the base API URL and configures logging and display components.
        """
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.console = Console()
        self.logger = logging.getLogger(__name__)
    
    def get_weather(self, latitude: float, longitude: float, 
                   include_forecast: bool = False) -> Optional[Dict[str, Any]]:
        """
        Retrieves current weather data for the specified coordinates.
        
        This method makes an API request to the Open-Meteo service with the provided
        latitude and longitude. It validates the coordinates, handles potential errors,
        and returns structured weather information.
        
        Args:
            latitude: The geographical latitude (between -90 and 90 degrees)
            longitude: The geographical longitude (between -180 and 180 degrees)
            include_forecast: Whether to include forecast data (default: False)
            
        Returns:
            A dictionary containing current weather data if successful, None otherwise.
            The dictionary includes temperature, wind speed, wind direction, and weather code.
            
        Raises:
            ValueError: If latitude or longitude values are outside valid ranges
        """
        # Validate coordinates
        if not -90 <= latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90 degrees")
        if not -180 <= longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180 degrees")
        
        # Build query parameters
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": "true"
        }
        
        # Add forecast parameters if requested
        if include_forecast:
            params.update({
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                "forecast_days": 7
            })
        
        try:
            # Make API request
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()  # Raises an exception for 4XX/5XX responses
            
            data = response.json()
            return data
            
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error occurred: {http_err}")
            self.console.print(f"[bold red]HTTP Error: {http_err}[/bold red]")
        except requests.exceptions.ConnectionError:
            self.logger.error("Connection error: Unable to connect to weather API")
            self.console.print("[bold red]Connection Error: Unable to connect to weather API[/bold red]")
        except requests.exceptions.Timeout:
            self.logger.error("Timeout error: Request timed out")
            self.console.print("[bold red]Timeout Error: Request timed out[/bold red]")
        except requests.exceptions.RequestException as err:
            self.logger.error(f"An error occurred: {err}")
            self.console.print(f"[bold red]Request Error: {err}[/bold red]")
        except ValueError as err:
            self.logger.error(f"JSON parsing error: {err}")
            self.console.print(f"[bold red]Data Error: Could not parse API response[/bold red]")
            
        return None
    
    def display_weather(self, latitude: float, longitude: float, 
                       location_name: Optional[str] = None) -> None:
        """
        Retrieves and displays current weather information in a rich formatted panel.
        
        This method fetches weather data and presents it in a visually appealing format
        with appropriate styling for different weather conditions.
        
        Args:
            latitude: The geographical latitude
            longitude: The geographical longitude
            location_name: Optional name of the location to display (default: coordinates)
            
        Returns:
            None: Results are displayed directly to the console
        """
        try:
            # Get weather data
            data = self.get_weather(latitude, longitude)
            
            if not data or "current_weather" not in data:
                self.console.print("[bold red]No weather data available[/bold red]")
                return
            
            weather = data["current_weather"]
            location_display = location_name or f"{latitude}, {longitude}"
            
            # Create a weather emoji based on weather code
            weather_icon = self._get_weather_icon(weather["weathercode"])
            
            # Create a rich table for the data
            table = Table(show_header=False, box=None)
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")
            
            # Add rows with data
            table.add_row("Temperature", f"{weather['temperature']}°C")
            table.add_row("Wind Speed", f"{weather['windspeed']} km/h")
            table.add_row("Wind Direction", f"{weather['winddirection']}° {self._get_wind_direction_text(weather['winddirection'])}")
            table.add_row("Weather Condition", self._get_weather_description(weather["weathercode"]))
            
            # Create and display a panel with the table
            self.console.print(Panel(
                table,
                title=f"[bold blue]Current Weather for {location_display} {weather_icon}[/bold blue]",
                border_style="cyan"
            ))
            
        except Exception as e:
            self.logger.error(f"Error displaying weather: {e}")
            self.console.print(f"[bold red]Error displaying weather: {str(e)}[/bold red]")
    
    def display_forecast(self, latitude: float, longitude: float,
                        location_name: Optional[str] = None) -> None:
        """
        Retrieves and displays a 7-day weather forecast in a rich formatted table.
        
        This method fetches forecast data and presents it in a visually appealing table
        with daily temperature ranges and precipitation information.
        
        Args:
            latitude: The geographical latitude
            longitude: The geographical longitude
            location_name: Optional name of the location to display (default: coordinates)
            
        Returns:
            None: Results are displayed directly to the console
        """
        try:
            # Get weather data with forecast
            data = self.get_weather(latitude, longitude, include_forecast=True)
            
            if not data or "daily" not in data:
                self.console.print("[bold red]No forecast data available[/bold red]")
                return
            
            forecast = data["daily"]
            location_display = location_name or f"{latitude}, {longitude}"
            
            # Create a rich table for the forecast
            table = Table(title=f"7-Day Forecast for {location_display}")
            table.add_column("Date", style="cyan")
            table.add_column("Min Temp", style="blue")
            table.add_column("Max Temp", style="red")
            table.add_column("Precipitation", style="green")
            
            # Add rows with data
            for i in range(len(forecast["time"])):
                date = forecast["time"][i]
                min_temp = f"{forecast['temperature_2m_min'][i]}°C"
                max_temp = f"{forecast['temperature_2m_max'][i]}°C"
                precip = f"{forecast['precipitation_sum'][i]} mm"
                
                table.add_row(date, min_temp, max_temp, precip)
            
            # Display the table
            self.console.print(table)
            
        except Exception as e:
            self.logger.error(f"Error displaying forecast: {e}")
            self.console.print(f"[bold red]Error displaying forecast: {str(e)}[/bold red]")
    
    def weather_menu(self) -> None:
        """
        Displays an interactive menu for retrieving weather information.
        
        This method presents a user-friendly menu interface allowing users to
        choose between different weather data options and input location coordinates.
        
        Returns:
            None: Menu is displayed directly in the console
        """
        self.console.print("[bold cyan]Weather Data Service[/bold cyan]")
        
        while True:
            self.console.print("\n[yellow]Select an option:[/yellow]")
            self.console.print("1. Get current weather by coordinates")
            self.console.print("2. Get 7-day forecast by coordinates")
            self.console.print("3. View example locations")
            self.console.print("0. Exit")
            
            choice = input("\nEnter choice (0-3): ")
            
            if choice == "0":
                break
                
            elif choice == "1":
                try:
                    lat = float(input("Enter latitude: "))
                    lon = float(input("Enter longitude: "))
                    location = input("Enter location name (optional): ")
                    location = location if location.strip() else None
                    self.display_weather(lat, lon, location)
                except ValueError:
                    self.console.print("[bold red]Invalid coordinates. Please enter numeric values.[/bold red]")
                
            elif choice == "2":
                try:
                    lat = float(input("Enter latitude: "))
                    lon = float(input("Enter longitude: "))
                    location = input("Enter location name (optional): ")
                    location = location if location.strip() else None
                    self.display_forecast(lat, lon, location)
                except ValueError:
                    self.console.print("[bold red]Invalid coordinates. Please enter numeric values.[/bold red]")
                
            elif choice == "3":
                self._show_example_locations()
                
            else:
                self.console.print("[red]Invalid choice. Please try again.[/red]")
    
    def _get_weather_icon(self, code: int) -> str:
        """
        Returns a weather emoji based on the weather code.
        
        Args:
            code: The WMO weather code
            
        Returns:
            A string containing an appropriate emoji for the weather condition
        """
        weather_icons = {
            0: "☀️",  # Clear sky
            1: "🌤️",  # Mainly clear
            2: "⛅",  # Partly cloudy
            3: "☁️",  # Overcast
            45: "🌫️",  # Fog
            48: "🌫️",  # Depositing rime fog
            51: "🌦️",  # Light drizzle
            53: "🌧️",  # Moderate drizzle
            55: "🌧️",  # Dense drizzle
            61: "🌦️",  # Slight rain
            63: "🌧️",  # Moderate rain
            65: "🌧️",  # Heavy rain
            71: "❄️",  # Slight snow
            73: "❄️",  # Moderate snow
            75: "❄️",  # Heavy snow
            80: "🌦️",  # Slight rain showers
            81: "🌧️",  # Moderate rain showers
            82: "🌧️",  # Violent rain showers
            85: "🌨️",  # Slight snow showers
            86: "🌨️",  # Heavy snow showers
            95: "⛈️",  # Thunderstorm
            96: "⛈️",  # Thunderstorm with slight hail
            99: "⛈️",  # Thunderstorm with heavy hail
        }
        return weather_icons.get(code, "❓")
    
    def _get_weather_description(self, code: int) -> str:
        """
        Returns a human-readable weather description based on the weather code.
        
        Args:
            code: The WMO weather code
            
        Returns:
            A string description of the weather condition
        """
        weather_descriptions = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow fall",
            73: "Moderate snow fall",
            75: "Heavy snow fall",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        return weather_descriptions.get(code, f"Unknown (code: {code})")
    
    def _get_wind_direction_text(self, degrees: float) -> str:
        """
        Converts wind direction in degrees to cardinal direction text.
        
        Args:
            degrees: Wind direction in degrees
            
        Returns:
            A string representation of the cardinal direction
        """
        directions = [
            "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
        ]
        index = round(degrees / (360 / len(directions))) % len(directions)
        return directions[index]
    
    def _show_example_locations(self) -> None:
        """
        Displays a list of example locations with their coordinates.
        
        Returns:
            None: Information is displayed directly to the console
        """
        # Create a table of example locations
        table = Table(title="Example Locations")
        table.add_column("City", style="cyan")
        table.add_column("Country", style="green")
        table.add_column("Latitude", justify="right")
        table.add_column("Longitude", justify="right")
        
        # Add example cities
        table.add_row("New York", "USA", "40.7128", "-74.0060")
        table.add_row("London", "UK", "51.5074", "-0.1278")
        table.add_row("Tokyo", "Japan", "35.6762", "139.6503")
        table.add_row("Sydney", "Australia", "-33.8688", "151.2093")
        table.add_row("Rio de Janeiro", "Brazil", "-22.9068", "-43.1729")
        table.add_row("Cape Town", "South Africa", "-33.9249", "18.4241")
        table.add_row("Moscow", "Russia", "55.7558", "37.6173")
        table.add_row("Porto", "Portugal", "41.1496", "-8.6109")
        
        self.console.print(table)

    def test_json_endpoints(self) -> None:
        """
        Tests and demonstrates the JSON data retrieval functions.
        
        This method provides examples of retrieving weather data in JSON format
        and displays the results in a nicely formatted way.
        """
        self.console.print("[bold cyan]Testing Weather Data JSON Endpoints[/bold cyan]")
        
        # Menu for location selection
        self.console.print("\n[yellow]Select a location:[/yellow]")
        self.console.print("1. New York (40.7128, -74.0060)")
        self.console.print("2. London (51.5074, -0.1278)")
        self.console.print("3. Custom coordinates")
        
        choice = input("\nEnter choice (1-3): ")
        
        try:
            if choice == "1":
                lat, lon = 40.7128, -74.0060
                location = "New York"
            elif choice == "2":
                lat, lon = 51.5074, -0.1278
                location = "London"
            elif choice == "3":
                lat = float(input("Enter latitude: "))
                lon = float(input("Enter longitude: "))
                location = input("Enter location name (optional): ") or f"{lat}, {lon}"
            else:
                self.console.print("[bold red]Invalid choice. Using default location.[/bold red]")
                lat, lon = 40.7128, -74.0060
                location = "New York"
                
            # Show menu for JSON format options
            self.console.print("\n[yellow]Select JSON data to retrieve:[/yellow]")
            self.console.print("1. Current weather only")
            self.console.print("2. Forecast only")
            self.console.print("3. Complete weather report")
            
            option = input("\nEnter choice (1-3): ")
            
            from rich.syntax import Syntax
            import json
            
            if option == "1":
                # Get and display current weather JSON
                data = self.get_weather_json(lat, lon)
                title = f"Current Weather JSON for {location}"
            elif option == "2":
                # Get and display forecast JSON
                data = self.get_forecast_json(lat, lon)
                title = f"Forecast JSON for {location}"
            elif option == "3":
                # Get and display complete weather JSON
                data = self.get_complete_weather_json(lat, lon)
                title = f"Complete Weather JSON for {location}"
            else:
                self.console.print("[bold red]Invalid choice. Showing current weather.[/bold red]")
                data = self.get_weather_json(lat, lon)
                title = f"Current Weather JSON for {location}"
            
            # Display the JSON with syntax highlighting
            json_str = json.dumps(data, indent=2)
            self.console.print(Panel(
                Syntax(json_str, "json", theme="monokai", line_numbers=True),
                title=f"[bold green]{title}[/bold green]",
                border_style="green",
                expand=False
            ))
            
        except Exception as e:
            self.console.print(f"[bold red]Error: {str(e)}[/bold red]")

    def get_weather_json(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Retrieves current weather data in a standardized JSON format.
        
        This method fetches weather information from Open-Meteo API and transforms 
        it into a well-structured JSON format that's consistent and easy to parse.
        The returned JSON maintains only the essential weather information in a 
        flattened, intuitive structure.
        
        Args:
            latitude (float): The geographical latitude (between -90 and 90 degrees)
            longitude (float): The geographical longitude (between -180 and 180 degrees)
        
        Returns:
            Dict[str, Any]: A dictionary containing formatted weather data with the following structure:
            {
                "location": {
                    "latitude": float,
                    "longitude": float
                },
                "current": {
                    "temperature": float,
                    "weather_condition": str,
                    "weather_code": int,
                    "wind": {
                        "speed": float,
                        "direction": float,
                        "direction_compass": str
                    },
                    "time": str (ISO format)
                },
                "units": {
                    "temperature": "°C",
                    "wind_speed": "km/h"
                },
                "status": {
                    "success": bool,
                    "message": str
                }
            }
        
        Raises:
            ValueError: If latitude or longitude values are outside valid ranges
        """
        try:
            # Get raw data from API
            raw_data = self.get_weather(latitude, longitude)
            
            if not raw_data or "current_weather" not in raw_data:
                return {
                    "status": {
                        "success": False,
                        "message": "Failed to retrieve weather data"
                    }
                }
            
            # Extract current weather data
            current = raw_data["current_weather"]
            
            # Transform into standardized JSON format
            formatted_data = {
                "location": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "current": {
                    "temperature": current["temperature"],
                    "weather_condition": self._get_weather_description(current["weathercode"]),
                    "weather_code": current["weathercode"],
                    "wind": {
                        "speed": current["windspeed"],
                        "direction": current["winddirection"],
                        "direction_compass": self._get_wind_direction_text(current["winddirection"])
                    },
                    "time": current["time"]
                },
                "units": {
                    "temperature": "°C",
                    "wind_speed": "km/h"
                },
                "status": {
                    "success": True,
                    "message": "Weather data retrieved successfully"
                }
            }
            
            return formatted_data
        
        except Exception as e:
            self.logger.error(f"Error formatting weather data: {e}")
            return {
                "status": {
                    "success": False,
                    "message": f"Error: {str(e)}"
                }
            }

    def get_forecast_json(self, latitude: float, longitude: float, days: int = 7) -> Dict[str, Any]:
        """
        Retrieves weather forecast data in a standardized JSON format.
        
        This method fetches forecast information from Open-Meteo API and transforms 
        it into a structured JSON format that's consistent and easy to parse.
        The returned JSON includes daily forecasts with temperature ranges and 
        precipitation data.
        
        Args:
            latitude (float): The geographical latitude (between -90 and 90 degrees)
            longitude (float): The geographical longitude (between -180 and 180 degrees)
            days (int, optional): Number of forecast days to retrieve (max 7). Defaults to 7.
        
        Returns:
            Dict[str, Any]: A dictionary containing formatted forecast data with the following structure:
            {
                "location": {
                    "latitude": float,
                    "longitude": float
                },
                "forecast": [
                    {
                        "date": str (YYYY-MM-DD),
                        "temperature": {
                            "min": float,
                            "max": float
                        },
                        "precipitation": float
                    },
                    ...
                ],
                "units": {
                    "temperature": "°C",
                    "precipitation": "mm"
                },
                "status": {
                    "success": bool,
                    "message": str
                }
            }
        
        Raises:
            ValueError: If latitude or longitude values are outside valid ranges
        """
        try:
            # Validate days parameter
            if not 1 <= days <= 7:
                days = 7  # Default to 7 if invalid
            
            # Get raw forecast data
            raw_data = self.get_weather(latitude, longitude, include_forecast=True)
            
            if not raw_data or "daily" not in raw_data:
                return {
                    "status": {
                        "success": False,
                        "message": "Failed to retrieve forecast data"
                    }
                }
            
            # Extract daily forecast data
            daily = raw_data["daily"]
            
            # Transform into standardized JSON format
            forecast_days = []
            for i in range(min(days, len(daily["time"]))):
                forecast_days.append({
                    "date": daily["time"][i],
                    "temperature": {
                        "min": daily["temperature_2m_min"][i],
                        "max": daily["temperature_2m_max"][i]
                    },
                    "precipitation": daily["precipitation_sum"][i]
                })
            
            formatted_data = {
                "location": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "forecast": forecast_days,
                "units": {
                    "temperature": "°C",
                    "precipitation": "mm"
                },
                "status": {
                    "success": True,
                    "message": f"Forecast data retrieved successfully for {len(forecast_days)} days"
                }
            }
            
            return formatted_data
        
        except Exception as e:
            self.logger.error(f"Error formatting forecast data: {e}")
            return {
                "status": {
                    "success": False,
                    "message": f"Error: {str(e)}"
                }
            }

    def get_complete_weather_json(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Retrieves both current weather and forecast data in a combined JSON format.
        
        This method provides a comprehensive weather report including both current
        conditions and future forecast in a single, well-structured JSON response.
        It's useful for applications that need to display complete weather information
        at once.
        
        Args:
            latitude (float): The geographical latitude (between -90 and 90 degrees)
            longitude (float): The geographical longitude (between -180 and 180 degrees)
        
        Returns:
            Dict[str, Any]: A dictionary containing both current weather and forecast data
            with a unified structure combining both datasets.
        
        Raises:
            ValueError: If latitude or longitude values are outside valid ranges
        """
        try:
            # Get current weather and forecast separately
            current_data = self.get_weather_json(latitude, longitude)
            forecast_data = self.get_forecast_json(latitude, longitude)
            
            # Combine into a single response
            combined_data = {
                "location": current_data.get("location", {
                    "latitude": latitude,
                    "longitude": longitude
                }),
                "current": current_data.get("current", {}),
                "forecast": forecast_data.get("forecast", []),
                "units": {
                    **current_data.get("units", {}),
                    **forecast_data.get("units", {})
                },
                "status": {
                    "success": current_data.get("status", {}).get("success", False) and 
                               forecast_data.get("status", {}).get("success", False),
                    "message": "Complete weather data retrieved successfully" if 
                               (current_data.get("status", {}).get("success", False) and 
                                forecast_data.get("status", {}).get("success", False)) else
                               "Partial or no data retrieved"
                }
            }
            
            return combined_data
        
        except Exception as e:
            self.logger.error(f"Error creating combined weather data: {e}")
            return {
                "status": {
                    "success": False,
                    "message": f"Error: {str(e)}"
                }
            }


# Test code to run if the module is executed directly
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create the service
    weather_service = WeatherDataService()
    
    # Display the main menu
    try:
        # Enhanced menu with JSON options
        weather_service.console.print("[bold cyan]Weather Data Service[/bold cyan]")
        
        while True:
            weather_service.console.print("\n[yellow]Select an option:[/yellow]")
            weather_service.console.print("1. Get current weather by coordinates")
            weather_service.console.print("2. Get 7-day forecast by coordinates")
            weather_service.console.print("3. View example locations")
            weather_service.console.print("4. Test JSON endpoints")
            weather_service.console.print("0. Exit")
            
            choice = input("\nEnter choice (0-4): ")
            
            if choice == "0":
                break
            elif choice == "1":
                try:
                    lat = float(input("Enter latitude: "))
                    lon = float(input("Enter longitude: "))
                    location = input("Enter location name (optional): ")
                    location = location if location.strip() else None
                    weather_service.display_weather(lat, lon, location)
                except ValueError:
                    weather_service.console.print("[bold red]Invalid coordinates. Please enter numeric values.[/bold red]")
            elif choice == "2":
                try:
                    lat = float(input("Enter latitude: "))
                    lon = float(input("Enter longitude: "))
                    location = input("Enter location name (optional): ")
                    location = location if location.strip() else None
                    weather_service.display_forecast(lat, lon, location)
                except ValueError:
                    weather_service.console.print("[bold red]Invalid coordinates. Please enter numeric values.[/bold red]")
            elif choice == "3":
                weather_service._show_example_locations()
            elif choice == "4":
                weather_service.test_json_endpoints()
            else:
                weather_service.console.print("[red]Invalid choice. Please try again.[/red]")
    except KeyboardInterrupt:
        print("\nExiting weather service.")