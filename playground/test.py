from agents.weather_agent import WeatherAgent
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
import re

# Create a console for rich output
console = Console()
console.print(Panel("[bold cyan]Weather Query Assistant[/bold cyan]", border_style="cyan"))

# Initialize the agent
weather_agent = WeatherAgent(
    model_id="gemini-2.0-flash",
    return_type="text", 
    print_to_terminal=True
)

# Function to display responses in a nice format
def display_response(title, content):
    console.print(Panel(
        Markdown(content),
        title=title,
        title_align="left",
        border_style="yellow"
    ))

# Function to extract location from query
def extract_location(query_text):
    # Simple pattern to find "in X" or "for X" in queries like "weather in London"
    patterns = [
        r"(?:weather|forecast|temperature|conditions)\s+(?:in|at|for|of)\s+([A-Za-z\s]+)",
        r"(?:in|at|for)\s+([A-Za-z\s]+)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query_text.lower())
        if match:
            return match.group(1).strip()
    
    return None

# Get the user's query
location = Prompt.ask("[cyan]Enter the location for weather information[/cyan]", default="Porto")
activity_question = Prompt.ask("[cyan]Ask a question about the weather (or press Enter to skip)[/cyan]", 
                              default="Is it good weather to go to the beach?")

# Construct the query
if activity_question:
    query = f"Get me the current weather in {location}. {activity_question}"
else:
    query = f"Get me the current weather in {location}."

# Process the initial query and get a response
console.print(Panel(f"Querying weather for [bold]{location}[/bold]", border_style="blue"))
console.print("[yellow]Processing initial query...[/yellow]")
response = weather_agent.process_query(query)

# Display the initial response for debugging
display_response("Initial Response", response)

# Check if the response indicates clarification is needed
if ("would you like me to get" in response.lower() or 
    "i need more information" in response.lower() or
    "which country" in response.lower() or
    "multiple locations" in response.lower()):
    
    console.print("[bold yellow]Clarification needed![/bold yellow]")
    extracted_location = extract_location(query) or location
    
    # Ask for country or region clarification
    country = Prompt.ask(f"[cyan]Please specify which country/region {extracted_location} is in[/cyan]")
    
    # Create a new query with the clarified location
    clarified_query = f"Get me the current weather in {extracted_location}, {country}"
    if activity_question:
        clarified_query += f". {activity_question}"
    
    console.print(f"\n[yellow]Processing clarified query:[/yellow]")
    console.print(Panel(clarified_query, border_style="blue"))
    
    # Process the clarified query
    response = weather_agent.process_query(clarified_query)
    
    # Display the clarified response
    display_response("Clarified Response", response)

console.print("\n[bold green]Query processing complete![/bold green]")