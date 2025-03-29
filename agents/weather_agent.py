from modules.google_genai_client import GoogleGenAIClient
from modules.weather_data import WeatherDataService
from modules.geocoding import GeocodingService
from google.genai import types
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich import box
import json
from typing import Optional, Dict, Any, Literal, Union

class WeatherAgent:
    """
    A class that manages weather data retrieval and AI-powered weather information processing.
    
    This agent combines geocoding services, weather data services, and Google's Generative AI
    to provide comprehensive weather information based on user queries.
    """
    
    def __init__(
        self, 
        model_id: str = "gemini-2.0-flash",
        return_type: Literal["text", "json", "both"] = "text",
        print_to_terminal: bool = True
    ):
        """
        Initialize the WeatherAgent with customizable parameters.
        
        Args:
            model_id (str): The Google Generative AI model ID to use. Defaults to "gemini-2.0-flash".
            return_type (Literal["text", "json", "both"]): The format of the returned data. Defaults to "text".
            print_to_terminal (bool): Whether to print the results to the terminal. Defaults to True.
        """
        self.model_id = model_id
        self.return_type = return_type
        self.print_to_terminal = print_to_terminal
        
        # Initialize services
        self.console = Console()
        self.genai_client = GoogleGenAIClient()
        
        if self.print_to_terminal:
            self.console.print(Panel("[bold cyan]Weather Agent Initialized[/bold cyan]", 
                                     subtitle=f"Using model: {self.model_id}",
                                     box=box.ROUNDED))
    
    def get_weather_data(self, city: str, country: Optional[str] = None) -> Dict[str, Any]:
        """
        Get weather data for a given city and country.
        
        Args:
            city (str): The name of the city.
            country (Optional[str]): The name of the country to disambiguate the city location. Defaults to None.
        
        Returns:
            Dict[str, Any]: Weather data in JSON format.
        """
        if self.print_to_terminal:
            self.console.print(f"[yellow]Getting weather data for {city}{', ' + country if country else ''}...[/yellow]")
        
        try:
            geocoding = GeocodingService()
            coordinates = geocoding.geocode(city, country)
            
            if not coordinates:
                if self.print_to_terminal:
                    self.console.print("[red]City not found![/red]")
                return {"error": "City not found"}
            
            latitude, longitude = coordinates
            weather_data = WeatherDataService()
            weather_info = weather_data.get_complete_weather_json(latitude, longitude)
            return weather_info
        except Exception as e:
            error_msg = f"Error retrieving weather data: {str(e)}"
            if self.print_to_terminal:
                self.console.print(f"[bold red]{error_msg}[/bold red]")
            return {"error": error_msg}
    
    def extract_response_text(self, response) -> str:
        """
        Extract text content from the Google GenAI response.
        
        Args:
            response: The response object from Google GenAI.
            
        Returns:
            str: The extracted text content.
        """
        try:
            # Extract the text from the response
            return response.text
        except Exception as e:
            error_msg = f"Error extracting text from response: {str(e)}"
            if self.print_to_terminal:
                self.console.print(f"[bold red]{error_msg}[/bold red]")
            return f"Error: {error_msg}"
    
    def extract_response_json(self, response) -> Dict[str, Any]:
        """
        Extract JSON content from the Google GenAI response.
        
        Args:
            response: The response object from Google GenAI.
            
        Returns:
            Dict[str, Any]: The extracted JSON content.
        """
        try:
            # First try to get structured JSON from the response
            if hasattr(response, "candidates") and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, "content") and candidate.content:
                        if hasattr(candidate.content, "parts"):
                            for part in candidate.content.parts:
                                if hasattr(part, "function_call"):
                                    return part.function_call.args
            
            # If no structured JSON found, try to parse the text as JSON
            text = self.extract_response_text(response)
            # Look for JSON-like content within the text
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            # If all else fails, return a dict with the text
            return {"text": text}
        except Exception as e:
            error_msg = f"Error extracting JSON from response: {str(e)}"
            if self.print_to_terminal:
                self.console.print(f"[bold red]{error_msg}[/bold red]")
            return {"error": error_msg}
    
    def display_weather_report(self, text_content: str, title: str = "Weather Report"):
        """
        Display a formatted weather report panel in the terminal.
        
        Args:
            text_content (str): The text content to display.
            title (str): The title of the panel. Defaults to "Weather Report".
        """
        if self.print_to_terminal:
            self.console.print(Panel(
                text_content,
                title=title,
                border_style="cyan",
                padding=(1, 2),
                box=box.ROUNDED
            ))
    
    def display_json_report(self, json_content: Dict[str, Any], title: str = "Weather Report JSON"):
        """
        Display a formatted JSON report panel in the terminal.
        
        Args:
            json_content (Dict[str, Any]): The JSON content to display.
            title (str): The title of the panel. Defaults to "Weather Report JSON".
        """
        if self.print_to_terminal:
            json_str = json.dumps(json_content, indent=2)
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
            self.console.print(Panel(
                syntax,
                title=title,
                border_style="green",
                padding=(1, 2),
                box=box.ROUNDED
            ))
    
    def process_query(self, query: str) -> Union[str, Dict[str, Any], tuple]:
        """
        Process a weather-related query using Google's Generative AI.
        
        Args:
            query (str): The weather-related question to process.
            
        Returns:
            Union[str, Dict[str, Any], tuple]: 
                - If return_type is "text": A string containing the AI response.
                - If return_type is "json": A dictionary containing the AI response.
                - If return_type is "both": A tuple containing (text, json).
        """
        if self.print_to_terminal:
            self.console.print(Panel(
                f"[yellow]{query}[/yellow]",
                title="Processing Weather Query",
                border_style="blue",
                box=box.ROUNDED
            ))
        
        try:
            response = self.genai_client.client.models.generate_content(
                model=self.model_id,
                contents=query,
                config=types.GenerateContentConfig(
                    tools=[self.get_weather_data],
                )   
            )
            
            # Handle different return types
            if self.return_type == "text":
                text_response = self.extract_response_text(response)
                self.display_weather_report(text_response)
                return text_response
                
            elif self.return_type == "json":
                json_response = self.extract_response_json(response)
                self.display_json_report(json_response)
                return json_response
                
            else:  # "both"
                text_response = self.extract_response_text(response)
                json_response = self.extract_response_json(response)
                
                self.display_weather_report(text_response)
                self.display_json_report(json_response)
                    
                return text_response, json_response
                
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            if self.print_to_terminal:
                self.console.print(f"[bold red]{error_msg}[/bold red]")
            
            if self.return_type == "text":
                return f"Error: {error_msg}"
            elif self.return_type == "json":
                return {"error": error_msg}
            else:  # "both"
                return f"Error: {error_msg}", {"error": error_msg}


# Example usage and testing
if __name__ == "__main__":
    console = Console()
    
    def show_menu():
        console.print("\n[bold cyan]Weather Agent Demo Menu[/bold cyan]")
        console.print("[1] Get weather for a specific location")
        console.print("[2] Ask a weather-related question")
        console.print("[3] Change display settings")
        console.print("[4] Exit")
        return console.input("[yellow]Select an option (1-4): [/yellow]")
    
    def settings_menu(agent):
        console.print("\n[bold cyan]Display Settings[/bold cyan]")
        console.print(f"[1] Change return type (current: {agent.return_type})")
        console.print(f"[2] Change model (current: {agent.model_id})")
        console.print("[3] Back to main menu")
        
        choice = console.input("[yellow]Select an option (1-3): [/yellow]")
        
        if choice == "1":
            console.print("\n[bold cyan]Return Type Options[/bold cyan]")
            console.print("[1] Text only")
            console.print("[2] JSON only")
            console.print("[3] Both text and JSON")
            
            type_choice = console.input("[yellow]Select return type (1-3): [/yellow]")
            
            if type_choice == "1":
                agent.return_type = "text"
            elif type_choice == "2":
                agent.return_type = "json"
            elif type_choice == "3":
                agent.return_type = "both"
                
            console.print(f"[green]Return type set to: {agent.return_type}[/green]")
            
        elif choice == "2":
            models = {
                "1": "gemini-2.0-flash",
                "2": "gemini-2.0-pro", 
                "3": "gemini-1.5-flash",
                "4": "gemini-1.5-pro"
            }
            
            console.print("\n[bold cyan]Available Models[/bold cyan]")
            for key, model in models.items():
                console.print(f"[{key}] {model}")
                
            model_choice = console.input("[yellow]Select model (1-4): [/yellow]")
            if model_choice in models:
                agent.model_id = models[model_choice]
                console.print(f"[green]Model set to: {agent.model_id}[/green]")
    
    # Create a weather agent with default settings
    agent = WeatherAgent(
        model_id="gemini-2.0-flash",
        return_type="text",
        print_to_terminal=True
    )
    
    # Main application loopprint_to_terminal=True
    while True:
        choice = show_menu()
        
        if choice == "1":
            city = console.input("[yellow]Enter city: [/yellow]")
            country = console.input("[yellow]Enter country (optional, press Enter to skip): [/yellow]")
            if not country:
                country = None
                
            weather_data = agent.get_weather_data(city, country)
            if "error" not in weather_data:
                agent.display_json_report(weather_data, f"Weather Data for {city}{', ' + country if country else ''}")
                
        elif choice == "2":
            query = console.input("[yellow]Enter your weather question: [/yellow]")
            agent.process_query(query)
            
        elif choice == "3":
            settings_menu(agent)
            
        elif choice == "4":
            console.print("[bold green]Thank you for using Weather Agent. Goodbye![/bold green]")
            break
        
        else:
            console.print("[bold red]Invalid option. Please try again.[/bold red]")