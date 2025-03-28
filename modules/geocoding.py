import requests
from typing import Dict, Optional, Tuple, Any, Union, List
from rich.console import Console
from rich.panel import Panel
from rich import box
from rich.table import Table
import logging

class GeocodingService:
    """
    A service for converting location names to geographic coordinates.
    
    This class provides methods to convert a text-based location (like a city name)
    into latitude and longitude coordinates using the Nominatim geocoding API.
    """
    
    def __init__(self):
        """
        Initialize the GeocodingService.
        
        Sets up the base API URL and configures logging and display components.
        """
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.console = Console()
        self.logger = logging.getLogger(__name__)
    
    def geocode(self, location: str) -> Optional[Tuple[float, float]]:
        """
        Converts a location name to latitude and longitude coordinates.
        
        This method takes a text-based location description (such as a city name,
        address, or place name) and queries the Nominatim geocoding service to 
        obtain the corresponding latitude and longitude coordinates.
        
        Args:
            location (str): The name of the location to geocode (e.g., "Porto, Portugal")
            
        Returns:
            Optional[Tuple[float, float]]: A tuple containing (latitude, longitude) if 
                                          successful, or None if the location couldn't be found.
                                          
        Raises:
            ValueError: If the location string is empty or invalid
            RequestException: If there's a network or API error
        """
        if not location or not isinstance(location, str) or location.strip() == "":
            raise ValueError("Location must be a non-empty string")
        
        coordinates = self._get_coordinates_with_disambiguation(location)
        return coordinates
    
    def _get_coordinates_with_disambiguation(self, location: str) -> Optional[Tuple[float, float]]:
        """
        Gets coordinates for a location with country disambiguation if needed.
        
        This internal method handles the case when a location name is ambiguous
        (exists in multiple countries) by prompting the user to select the correct one.
        
        Args:
            location (str): The name of the location to geocode
            
        Returns:
            Optional[Tuple[float, float]]: A tuple containing (latitude, longitude) if 
                                          successful, or None if the location couldn't be found.
        """
        # Build query parameters - request multiple results for possible disambiguation
        params = {
            "q": location,
            "format": "json",
            "limit": 10,  # Get several results to check for ambiguity
            "addressdetails": 1
        }
        
        # Add user agent as required by Nominatim usage policy
        headers = {
            "User-Agent": "WeatherToolAgent/1.0"
        }
        
        try:
            response = requests.get(
                self.base_url, 
                params=params, 
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            results = response.json()
            
            if not results:
                self.console.print(f"[bold red]Location not found: {location}[/bold red]")
                return None
            
            # Check if we have multiple distinct countries in results
            # which would indicate an ambiguous place name
            countries = {}
            for result in results:
                if "address" in result and "country" in result["address"]:
                    country = result["address"]["country"]
                    if country not in countries:
                        countries[country] = []
                    countries[country].append(result)
            
            # If we have multiple countries, ask the user to disambiguate
            if len(countries) > 1:
                selected_result = self._prompt_country_selection(location, countries)
                if not selected_result:
                    return None
            else:
                # Just use the first result if no ambiguity
                selected_result = results[0]
            
            # Extract coordinates
            latitude = float(selected_result["lat"])
            longitude = float(selected_result["lon"])
            
            display_name = selected_result.get("display_name", location)
            self.console.print(f"[green]✓ Successfully geocoded: [bold]{display_name}[/bold] → ({latitude}, {longitude})[/green]")
            return (latitude, longitude)
            
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error during geocoding: {http_err}")
            self.console.print(f"[bold red]HTTP Error during geocoding: {http_err}[/bold red]")
        except requests.exceptions.ConnectionError:
            self.logger.error("Connection error: Unable to connect to geocoding API")
            self.console.print("[bold red]Connection Error: Unable to connect to geocoding API[/bold red]")
        except requests.exceptions.Timeout:
            self.logger.error("Timeout error: Geocoding request timed out")
            self.console.print("[bold red]Timeout Error: Geocoding request timed out[/bold red]")
        except requests.exceptions.RequestException as err:
            self.logger.error(f"An error occurred during geocoding: {err}")
            self.console.print(f"[bold red]Request Error during geocoding: {err}[/bold red]")
        except (ValueError, KeyError) as err:
            self.logger.error(f"Error parsing geocoding response: {err}")
            self.console.print(f"[bold red]Data Error: Could not parse geocoding response[/bold red]")
        
        return None
    
    def _prompt_country_selection(self, location: str, countries: Dict[str, List[Dict]]) -> Optional[Dict]:
        """
        Prompts the user to select a country when the location name is ambiguous.
        
        Args:
            location (str): The original location query
            countries (Dict[str, List[Dict]]): A dictionary mapping country names to lists of results
            
        Returns:
            Optional[Dict]: The selected location result or None if canceled
        """
        self.console.print(f"\n[yellow]Multiple locations found for '[bold]{location}[/bold]'. Please select a country:[/yellow]")
        
        # Create a table to display options
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim")
        table.add_column("Country")
        table.add_column("Display Name")
        
        country_list = list(countries.keys())
        
        # Add rows for each country option
        for i, country in enumerate(country_list, 1):
            # Use the first result for each country as an example
            example = countries[country][0].get("display_name", f"{location}, {country}")
            table.add_row(str(i), country, example)
        
        # Add option to try a different search
        table.add_row("0", "None of these", "Try a different search")
        
        # Display the options table
        self.console.print(table)
        
        # Get user selection
        while True:
            try:
                choice = input("\nEnter choice number: ")
                choice_num = int(choice)
                
                if choice_num == 0:
                    return None
                elif 1 <= choice_num <= len(country_list):
                    selected_country = country_list[choice_num - 1]
                    
                    # If there are multiple options even within the selected country
                    country_results = countries[selected_country]
                    if len(country_results) > 1:
                        return self._select_specific_location(country_results)
                    else:
                        return country_results[0]
                else:
                    self.console.print("[red]Invalid choice. Please try again.[/red]")
            except ValueError:
                self.console.print("[red]Please enter a valid number.[/red]")
    
    def _select_specific_location(self, locations: List[Dict]) -> Dict:
        """
        Allows the user to select a specific location from multiple options in the same country.
        
        Args:
            locations (List[Dict]): A list of location results from the API
            
        Returns:
            Dict: The selected location result
        """
        self.console.print("\n[yellow]Multiple specific locations found. Please select one:[/yellow]")
        
        # Create a table for the options
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim")
        table.add_column("Location")
        table.add_column("Type")
        
        # Add rows for each option
        for i, location in enumerate(locations, 1):
            display_name = location.get("display_name", "Unknown location")
            location_type = location.get("type", "Unknown")
            table.add_row(str(i), display_name, location_type)
        
        # Display the options
        self.console.print(table)
        
        # Get user selection
        while True:
            try:
                choice = input("\nEnter choice number: ")
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(locations):
                    return locations[choice_num - 1]
                else:
                    self.console.print("[red]Invalid choice. Please try again.[/red]")
            except ValueError:
                self.console.print("[red]Please enter a valid number.[/red]")
    
    def get_location_details(self, location: str) -> Dict[str, Any]:
        """
        Retrieves detailed information about a location including its coordinates.
        
        This method provides more comprehensive location data than the basic geocode method,
        including address components, bounding box, and other metadata returned by the
        geocoding service.
        
        Args:
            location (str): The name of the location to look up
            
        Returns:
            Dict[str, Any]: A dictionary containing detailed location information, including:
                - coordinates: (latitude, longitude) tuple
                - address: Components of the address (country, city, etc.)
                - display_name: Formatted full location name
                - bounding_box: Geographic bounding box of the location
                - status: Information about the request success/failure
                
        Raises:
            ValueError: If the location string is empty or invalid
        """
        if not location or not isinstance(location, str) or location.strip() == "":
            raise ValueError("Location must be a non-empty string")
        
        # First attempt to geocode with disambiguation
        coordinates = self._get_coordinates_with_disambiguation(location)
        
        if not coordinates:
            return {
                "status": {
                    "success": False,
                    "message": f"Location not found: {location}"
                }
            }
        
        # Once we have coordinates from the disambiguation process,
        # we can query the API again to get complete details
        lat, lon = coordinates
        
        # Build query parameters for reverse geocoding to get full details
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "addressdetails": 1
        }
        
        # Add user agent as required by Nominatim usage policy
        headers = {
            "User-Agent": "WeatherToolAgent/1.0"
        }
        
        try:
            response = requests.get(
                "https://nominatim.openstreetmap.org/reverse", 
                params=params, 
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Format the location details
            location_details = {
                "coordinates": {
                    "latitude": lat,
                    "longitude": lon
                },
                "display_name": result.get("display_name", location),
                "address": result.get("address", {}),
                "status": {
                    "success": True,
                    "message": f"Location found: {location}"
                }
            }
            
            # Add bounding box if available
            if "boundingbox" in result:
                location_details["bounding_box"] = {
                    "min_latitude": float(result["boundingbox"][0]),
                    "max_latitude": float(result["boundingbox"][1]),
                    "min_longitude": float(result["boundingbox"][2]),
                    "max_longitude": float(result["boundingbox"][3])
                }
            
            return location_details
            
        except Exception as e:
            self.logger.error(f"Error getting location details: {e}")
            return {
                "status": {
                    "success": False,
                    "message": f"Error: {str(e)}"
                }
            }

    def test_geocoding_service(self) -> None:
        """
        Tests the geocoding service with sample locations.
        
        This method provides a user interface to test the geocoding functionality
        by allowing the user to select from predefined locations or enter a custom one.
        """
        self.console.print("[bold cyan]Geocoding Service Test[/bold cyan]")
        
        # Sample locations for testing
        sample_locations = [
            "Porto, Portugal",
            "New York City, USA",
            "Tokyo, Japan",
            "Sydney, Australia", 
            "Cape Town, South Africa",
            # Ambiguous locations for testing
            "Springfield",
            "Paris",
            "Richmond"
        ]
        
        while True:
            self.console.print("\n[yellow]Select a location to geocode:[/yellow]")
            
            # Display sample locations
            for i, location in enumerate(sample_locations, 1):
                self.console.print(f"{i}. {location}")
            
            # Custom location option
            self.console.print(f"{len(sample_locations) + 1}. Enter custom location")
            self.console.print("0. Back")
            
            try:
                choice = int(input("\nEnter choice: "))
                
                if choice == 0:
                    break
                elif 1 <= choice <= len(sample_locations):
                    location = sample_locations[choice - 1]
                elif choice == len(sample_locations) + 1:
                    location = input("Enter location name: ")
                else:
                    self.console.print("[red]Invalid choice. Please try again.[/red]")
                    continue
                
                # Allow the user to try a different location if geocoding fails
                while True:
                    # Display geocoding results
                    self.console.print(f"\n[cyan]Geocoding: {location}[/cyan]")
                    
                    # Get basic coordinates with country disambiguation
                    coords = self.geocode(location)
                    if coords:
                        lat, lon = coords
                        self.console.print(f"Latitude: [bold]{lat}[/bold]")
                        self.console.print(f"Longitude: [bold]{lon}[/bold]")
                        
                        # Ask if user wants detailed information
                        show_details = input("\nShow detailed location information? (y/n): ").lower()
                        if show_details == 'y':
                            details = self.get_location_details(location)
                            
                            if details["status"]["success"]:
                                from rich.pretty import Pretty
                                self.console.print(Panel(
                                    Pretty(details),
                                    title=f"[bold cyan]Location Details: {location}[/bold cyan]",
                                    border_style="green",
                                    expand=False
                                ))
                            else:
                                self.console.print(f"[red]{details['status']['message']}[/red]")
                        break
                    else:
                        # Ask if the user wants to try another location
                        retry = input("Try a different location? (y/n): ").lower()
                        if retry == 'y':
                            location = input("Enter new location name: ")
                        else:
                            break
                
            except ValueError:
                self.console.print("[red]Please enter a number.[/red]")


# Test code to run if the module is executed directly
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create the service
    geocoding_service = GeocodingService()
    
    # Run the test interface
    try:
        geocoding_service.test_geocoding_service()
    except KeyboardInterrupt:
        print("\nExiting geocoding service.")