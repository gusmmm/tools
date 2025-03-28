from google import genai
from google.genai import types
from modules.key_manager import KeyManager
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import List, Dict, Any, Optional
import logging

# get the GEMINI API key from the .env file
key_manager = KeyManager()
key_manager.validate_key("GEMINI_API_KEY")
GEMINI_API_KEY = key_manager.get_key("GEMINI_API_KEY")

# Initialize the Google GenAI client
MODEL_ID = "gemini-2.0-flash"
client = genai.Client(
    api_key=GEMINI_API_KEY,
)

class GoogleGenAIClient:
    """
    A client for interacting with Google's Generative AI services using the Google GenAI SDK.
    
    This class provides methods to authenticate with Google GenAI API,
    list available models, and generate content using Google's Gemini models.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the GoogleGenAIClient.
        
        Args:
            api_key: Optional API key. If not provided, will use the one from KeyManager
        """
        self.console = Console()
        self.api_key = api_key or GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key)
        self.logger = logging.getLogger(__name__)
    
    def list_available_models(self, display_output: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieves and displays all available Google GenAI models.
        
        This function queries the Google GenAI API to get the list of models that are 
        available for the authenticated user. It can either return the data silently 
        or display it in a formatted rich table.
        
        Args:
            display_output: If True, prints the available models in a formatted table.
                          If False, returns the data without printing. Default is True.
        
        Returns:
            A list of dictionaries containing information about each available model.
            Each dictionary contains details such as name, version, display name, 
            description, input token limit, output token limit, etc.
        
        Raises:
            Exception: If there is an error retrieving the models from the Google API.
        """
        try:
            # Fetch all available models using client.models.list() method from the Google GenAI SDK
            models = self.client.models.list()
            
            # Process model information into a more consistent format
            processed_models = []
            
            for model in models:
                # Extract relevant model information
                model_info = {
                    "name": model.name,
                    "display_name": model.display_name,
                    "description": model.description,
                    "supported_generation_methods": [
                        action for action in model.supported_actions if hasattr(model, "supported_actions")
                    ],
                    "input_token_limit": model.input_token_limit if hasattr(model, "input_token_limit") else None,
                    "output_token_limit": model.output_token_limit if hasattr(model, "output_token_limit") else None,
                    "temperature_range": {
                        "min": model.temperature_range.min if hasattr(model, "temperature_range") else None,
                        "max": model.temperature_range.max if hasattr(model, "temperature_range") else None
                    }
                }
                processed_models.append(model_info)
            
            # If display_output is True, show the results in a rich table
            if display_output:
                self._display_models_table(processed_models)
                
            return processed_models
            
        except Exception as e:
            error_msg = f"Error retrieving available models: {str(e)}"
            self.logger.error(error_msg)
            self.console.print(Panel(f"[bold red]{error_msg}[/bold red]", 
                                     title="Error", border_style="red"))
            return []
    
    def _display_models_table(self, models: List[Dict[str, Any]]) -> None:
        """
        Displays the available models in a formatted rich table.
        
        Args:
            models: A list of dictionaries containing model information.
        """
        # Create a new rich table
        table = Table(title="Available Google GenAI Models")
        
        # Add columns to the table
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Display Name", style="green")
        table.add_column("Input Token Limit", justify="right", style="yellow")
        table.add_column("Output Token Limit", justify="right", style="yellow")
        table.add_column("Generation Methods", style="magenta")
        
        # Add rows to the table
        for model in models:
            table.add_row(
                model["name"],
                model["display_name"] or "N/A",
                str(model["input_token_limit"]) if model["input_token_limit"] else "N/A",
                str(model["output_token_limit"]) if model["output_token_limit"] else "N/A",
                ", ".join(model["supported_generation_methods"]) or "N/A"
            )
        
        # Print the table
        self.console.print(table)
    
    def test_generate_content(self, prompt: str, model_name: str = "gemini-2.0-flash") -> bool:
        """
        Tests the Google GenAI client by generating content with a specified model.
        
        This function sends a simple prompt to the specified model and displays the 
        response in a formatted panel. It's useful for verifying that the API key 
        is valid and that the model is accessible.
        
        Args:
            prompt: The text prompt to send to the model.
            model_name: The name of the model to use for generation. Default is "gemini-2.0-flash".
        
        Returns:
            True if the content was successfully generated, False otherwise.
            
        Raises:
            Exception: If there is an error generating the content.
        """
        try:
            with self.console.status(f"[bold blue]Generating content with {model_name}...[/bold blue]"):
                # Generate content using the specified model
                response = self.client.models.generate_content(
                    model=model_name, 
                    contents=prompt
                )
                
            # Display the generated content in a panel with a title
            self.console.print("\n[bold green]✓ Content generated successfully![/bold green]")
            self.console.print(Panel(
                response.text,
                title=f"[bold cyan]Response from {model_name}[/bold cyan]",
                border_style="green",
                expand=False,
                width=100
            ))
            
            return True
            
        except Exception as e:
            error_msg = f"Error generating content: {str(e)}"
            self.logger.error(error_msg)
            self.console.print(Panel(
                f"[bold red]{error_msg}[/bold red]",
                title="Error",
                border_style="red"
            ))
            return False

    def display_response_dict(self, response, title="Response as Dictionary"):
        """
        Display the response dictionary in a beautiful way.
        
        Args:
            response: The response from the model
            title: The title for the panel
        """
        from rich.pretty import Pretty
        
        # Get the dictionary representation
        response_dict = response.to_json_dict()
        
        # Display in a beautiful panel with nice formatting
        self.console.print(Panel(
            Pretty(response_dict),
            title=f"[bold cyan]{title}[/bold cyan]",
            border_style="green",
            expand=False
        ))
        
    def display_response_json(self, response, title="Response as JSON"):
        """
        Display the response JSON in a beautiful way.
        
        Args:
            response: The response from the model
            title: The title for the panel
        """
        import json
        from rich.syntax import Syntax
        
        # Get the JSON representation and pretty-print it
        response_json = response.model_dump_json()
        formatted_json = json.dumps(json.loads(response_json), indent=2)
        
        # Display with syntax highlighting
        self.console.print(Panel(
            Syntax(formatted_json, "json", theme="monokai", line_numbers=True),
            title=f"[bold cyan]{title}[/bold cyan]",
            border_style="blue",
            expand=False
        ))
    
    def display_response_text(self, response, title="Model Response"):
        """
        Display the model's text response in a beautiful, readable format.
        
        This method formats and displays the text content from a model response
        with proper styling, formatting, and structure to enhance readability.
        It handles different types of content including paragraphs, bullet points,
        and code blocks while maintaining the original structure.
        
        Args:
            response: The response object from the model containing the text to display
            title (str, optional): The title to display above the response. Defaults to "Model Response".
        
        Returns:
            None: The formatted response is directly printed to the console
        
        Example:
            >>> client = GoogleGenAIClient()
            >>> response = client.client.models.generate_content(...)
            >>> client.display_response_text(response, "Answer to Life Question")
        """
        from rich.markdown import Markdown
        from rich.padding import Padding
        
        # Extract the text from the response
        text = response.text
        
        # Check if the response text exists
        if not text or text.strip() == "":
            self.console.print(Panel(
                "[italic yellow]Empty response received from the model.[/italic yellow]",
                title=f"[bold cyan]{title}[/bold cyan]",
                border_style="yellow",
                expand=False
            ))
            return
        
        # Display the title header
        self.console.print(f"\n[bold cyan]━━━ {title} ━━━[/bold cyan]")
        
        # Try to parse as markdown for better formatting
        try:
            # Add padding for better visual appearance
            markdown_content = Markdown(text)
            padded_content = Padding(markdown_content, (1, 2))
            
            # Display in a panel with a clean design
            self.console.print(Panel(
                padded_content,
                border_style="bright_blue",
                expand=False,
                padding=(0, 1)
            ))
        except Exception:
            # Fallback to simple panel if markdown parsing fails
            self.console.print(Panel(
                text,
                border_style="bright_blue",
                expand=False,
                padding=(1, 2)
            ))


# Simple test if the module is run directly
if __name__ == "__main__":
    console = Console()
    console.print("\n[bold cyan]Testing Google GenAI Client Module[/bold cyan]\n")
    
    try:
        # Create a client instance
        genai_client = GoogleGenAIClient()
        
        # Test menu
        console.print("[bold]Choose a test option:[/bold]")
        console.print("1. List available models")
        console.print("2. Generate sample content")
        console.print("3. Run both tests")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == "1" or choice == "3":
            # Test listing available models
            console.print("\n[bold]Retrieving available models...[/bold]")
            models = genai_client.list_available_models()
            
            if models:
                console.print(f"\n[bold green]Successfully retrieved {len(models)} models![/bold green]")
            else:
                console.print("\n[bold yellow]No models were retrieved. Check your API key or network connection.[/bold yellow]")
        
        if choice == "2" or choice == "3":
            # Test content generation
            console.print("\n[bold]Testing content generation...[/bold]")
            test_prompt = "Write a short story about a magic ghost that died, a ghost of a ghost."
            genai_client.test_generate_content(test_prompt)
            
    except Exception as e:
        console.print(f"\n[bold red]Error in test: {str(e)}[/bold red]")
