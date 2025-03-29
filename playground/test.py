from agents.weather_agent import WeatherAgent
from rich.console import Console

# Create a console for rich output
console = Console()
console.print("[bold cyan]Weather Query Test[/bold cyan]")

# Initialize the agent
weather_agent = WeatherAgent(
    model_id="gemini-2.0-flash",
    return_type="text", 
    print_to_terminal=True
)

# Define the query
query = "Get me the current weather in Porto. Is it good weather to go to the beach?"

# Process the query and get a response
console.print("[yellow]Processing query...[/yellow]")
response = weather_agent.process_query(query)

# If you want to do something with the response (it's already printed to terminal)
# console.print("\n[bold green]Query processed successfully![/bold green]")