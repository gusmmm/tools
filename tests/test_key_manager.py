import os
import pytest
from unittest.mock import patch
from modules.key_manager import KeyManager
from dotenv import load_dotenv
from rich import print

# Define a fixture to set up and tear down environment variables for testing
@pytest.fixture(scope="module")
def env_setup():
    """
    Fixture to set up and tear down environment variables for testing.
    """
    print("[bold blue]Setting up environment for testing...[/bold blue]")
    # Setup: Load .env file for testing
    load_dotenv(".env.test")  # Load the test .env file
    print("[green]Loaded .env.test[/green]")

    # Provide the KeyManager instance
    print("[yellow]Yielding KeyManager instance...[/yellow]")
    yield KeyManager(dotenv_path=".env.test")

    # Teardown: Clean up any environment variables set during testing
    # This is important to prevent tests from affecting each other
    print("[bold red]Tearing down environment...[/bold red]")
    # Safely clear environment variables
    for key in list(os.environ.keys()):  # Iterate over a copy of keys
        if (key.startswith("PYTEST_") and key != "PYTEST_CURRENT_TEST") or key in ["TEST_KEY"]:
            print(f"[cyan]Deleting environment variable: {key}[/cyan]")
            del os.environ[key]
    # Don't delete PYTEST_CURRENT_TEST as pytest will handle it
    print("[bold green]Environment teardown complete.[/bold green]")

def test_key_manager_initialization(env_setup):
    """
    Test that the KeyManager initializes correctly.
    """
    key_manager = env_setup
    assert key_manager.dotenv_path == ".env.test"
    print("[green]KeyManager initialized correctly[/green]")

def test_get_key_success(env_setup):
    """
    Test that get_key retrieves an existing key successfully.
    """
    key_manager = env_setup
    key_value = key_manager.get_key("TEST_KEY")
    assert key_value == "test_value"
    print("[green]Successfully retrieved key[/green]")

def test_get_key_failure(env_setup):
    """
    Test that get_key raises ValueError when the key does not exist.
    """
    key_manager = env_setup
    with pytest.raises(ValueError) as excinfo:
        key_manager.get_key("NON_EXISTENT_KEY")
    assert "Key 'NON_EXISTENT_KEY' not found in environment variables." in str(excinfo.value)
    print("[green]Successfully raised ValueError for non-existent key[/green]")

def test_validate_key_success(env_setup):
    """
    Test that validate_key does not raise an exception when the key exists.
    """
    key_manager = env_setup
    try:
        key_manager.validate_key("TEST_KEY")
    except ValueError:
        pytest.fail("validate_key raised ValueError unexpectedly!")
    print("[green]validate_key passed successfully[/green]")

def test_validate_key_failure(env_setup):
    """
    Test that validate_key raises ValueError when the key does not exist.
    """
    key_manager = env_setup
    with pytest.raises(ValueError) as excinfo:
        key_manager.validate_key("NON_EXISTENT_KEY")
    assert "Key 'NON_EXISTENT_KEY' not found in environment variables." in str(excinfo.value)
    print("[green]validate_key failed successfully[/green]")

if __name__ == "__main__":
    pytest.main()