from modules.google_genai_client import GoogleGenAIClient
from rich.console import Console

# Initialize the console for rich output
console = Console()
console.print("[bold cyan]Google GenAI Demo[/bold cyan]")

# Initialize the Google GenAI client
gervasio = GoogleGenAIClient()

# model
MODEL_ID = "gemini-2.0-flash"

# Generate a response
console.print("[yellow]Generating response...[/yellow]")
response = gervasio.client.models.generate_content(
    model=MODEL_ID,
    contents="Why am I alive?",
)

# Display the response content using the beautiful formatter
gervasio.display_response_text(response, "Philosophical Answer")

# Display both the dictionary and JSON representations using your new methods
console.print("\n[bold]Response Details:[/bold]")
gervasio.display_response_dict(response)
gervasio.display_response_json(response)
