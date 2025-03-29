from agents.weather_agent import WeatherAgent
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown

# Create a console for rich output
console = Console()
console.print(Panel("[bold cyan]Weather Query Assistant[/bold cyan]", border_style="cyan"))

# Initialize the agent - set print_to_terminal to True to let agent handle output
weather_agent = WeatherAgent(
    model_id="gemini-2.0-flash",
    return_type="text",
    print_to_terminal=True  # Let the agent handle printing to terminal
)

# Get the user's query
location = Prompt.ask("[cyan]Enter the location for weather information[/cyan]", default="Porto")
activity_question = Prompt.ask("[cyan]Ask a question about the weather (or press Enter to skip)[/cyan]", 
                              default="Is it good weather to go to the beach?")

# Construct the query
if activity_question:
    query = f"Get me the current weather in {location}. {activity_question}"
else:
    query = f"Get me the current weather in {location}."

# Process the query
console.print(Panel(f"Querying weather for [bold]{location}[/bold]", border_style="blue"))
console.print("[yellow]Processing query...[/yellow]")

# Let the agent handle the query, including any necessary clarification
try:
    weather_agent.process_query(query)
except Exception as e:
    console.print(Panel(f"[bold red]Error: {str(e)}[/bold red]", 
                      title="Error", border_style="red"))

console.print("\n[bold green]Query processing complete![/bold green]")