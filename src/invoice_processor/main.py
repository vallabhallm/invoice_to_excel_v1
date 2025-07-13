import logging
import os
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress

from invoice_processor.workflows.invoice_workflow import run_invoice_processing

# Load environment variables
load_dotenv()

# Setup rich console and logging
console = Console()

# Configure logging with Rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)

# Create Typer app
app = typer.Typer(
    name="invoice-processor",
    help="AI-powered invoice processing system",
    add_completion=False
)


@app.command()
def process(
    input_dir: str = typer.Option(
        "data/input",
        "--input", "-i",
        help="Directory containing invoice files to process"
    ),
    output_dir: str = typer.Option(
        "data/output",
        "--output", "-o", 
        help="Directory to save processed results"
    ),
    processed_dir: str = typer.Option(
        "data/processed",
        "--processed", "-p",
        help="Directory to move processed files"
    )
):
    """Process invoices from input directory"""
    
    console.print(f"🧾 [bold blue]Starting Invoice Processing[/bold blue]")
    console.print(f"📁 Input directory: {input_dir}")
    console.print(f"📁 Output directory: {output_dir}")
    console.print(f"📁 Processed directory: {processed_dir}")
    
    # Check for AI API keys
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    
    if not (has_openai or has_anthropic):
        console.print("⚠️  [yellow]Warning: No AI API keys found. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in your .env file[/yellow]")
        console.print("The application will still attempt OCR extraction but AI-powered extraction will be unavailable.")
    else:
        ai_providers = []
        if has_openai:
            ai_providers.append("OpenAI")
        if has_anthropic:
            ai_providers.append("Anthropic")
        console.print(f"🤖 AI providers available: {', '.join(ai_providers)}")
    
    # Create directories if they don't exist
    Path(input_dir).mkdir(parents=True, exist_ok=True)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(processed_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        with Progress() as progress:
            task = progress.add_task("Processing invoices...", total=None)
            
            result = run_invoice_processing(input_dir, output_dir, processed_dir)
            
            progress.update(task, completed=100)
        
        console.print(f"✅ [bold green]{result}[/bold green]")
        
    except Exception as e:
        console.print(f"❌ [bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def setup():
    """Setup the invoice processing environment"""
    console.print("🔧 [bold blue]Setting up Invoice Processor[/bold blue]")
    
    # Create directory structure
    directories = [
        "data/input",
        "data/output", 
        "data/processed"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        console.print(f"📁 Created directory: {directory}")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# AI API Keys - Add your keys here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Logging level
LOG_LEVEL=INFO
"""
        env_file.write_text(env_content)
        console.print(f"📝 Created .env file: {env_file}")
        console.print("   Please edit .env file and add your AI API keys")
    
    console.print("✅ [bold green]Setup completed![/bold green]")
    console.print("\n📋 Next steps:")
    console.print("1. Edit .env file and add your AI API keys")
    console.print("2. Place invoice files (PDF/images) in data/input/")
    console.print("3. Run: invoice-processor process")


@app.command()
def status():
    """Check system status and configuration"""
    console.print("🔍 [bold blue]Invoice Processor Status[/bold blue]")
    
    # Check directories
    directories = {
        "Input": "data/input",
        "Output": "data/output",
        "Processed": "data/processed"
    }
    
    for name, path in directories.items():
        if Path(path).exists():
            file_count = len(list(Path(path).glob("*")))
            console.print(f"📁 {name}: {path} ✅ ({file_count} files)")
        else:
            console.print(f"📁 {name}: {path} ❌ (missing)")
    
    # Check AI API keys
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    
    console.print("\n🤖 AI Configuration:")
    if has_openai:
        console.print("   OpenAI API Key: ✅")
    else:
        console.print("   OpenAI API Key: ❌")
    
    if has_anthropic:
        console.print("   Anthropic API Key: ✅")
    else:
        console.print("   Anthropic API Key: ❌")
    
    if not (has_openai or has_anthropic):
        console.print("   ⚠️  No AI providers configured - only OCR will be available")


if __name__ == "__main__":
    app()
