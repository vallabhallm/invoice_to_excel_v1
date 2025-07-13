# Invoice Processing Application

A modern, AI-powered invoice processing system built with Python, Prefect workflows, and GenAI models. This application automatically extracts structured data from PDF and image invoices, outputting normalized CSV data with comprehensive reporting.

## 🚀 Features

### Core Functionality
- **Multi-format Support**: Process PDF files and images (PNG, JPEG, TIFF, BMP)
- **AI-Powered Extraction**: Uses OpenAI GPT and Anthropic Claude for intelligent data extraction
- **OCR Fallback**: Tesseract OCR for text extraction when AI fails
- **Recursive Directory Processing**: Automatically processes invoices in nested subdirectories
- **Prefect Workflows**: Robust, scalable workflow orchestration with retry logic
- **Rich CLI**: Beautiful command-line interface with progress indicators

### Advanced Features
- **Structured Output**: Flattened CSV format with header data repeated for each line item
- **Comprehensive Reporting**: Automatic generation of processing summaries and analytics
- **Directory Structure Preservation**: Maintains original folder organization in processed files
- **Error Handling**: Graceful handling of corrupted files, API failures, and processing errors
- **Intelligent Fallbacks**: AI → OCR → Basic structure creation for maximum processing success
- **Multi-provider AI Support**: Primary/fallback configuration with OpenAI and Anthropic

## 📋 Prerequisites

- Python 3.9+
- Poetry for dependency management
- Tesseract OCR installed on your system
- OpenAI API key and/or Anthropic API key (optional but recommended)

### Installing Tesseract

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

## 🛠️ Installation

1. **Install Poetry (if not already installed):**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. **Install dependencies:**
```bash
poetry install
```

3. **Activate the virtual environment:**
```bash
poetry shell
```

4. **Setup the application:**
```bash
invoice-processor setup
```

5. **Configure API keys:**
Edit the `.env` file and add your AI API keys:
```env
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## 🎯 Usage

### Basic Usage

1. **Place invoice files** in the `data/input/` directory (supports nested folders)
2. **Run the processor:**
```bash
invoice-processor process
```

### Advanced Usage

```bash
# Process with custom directories
invoice-processor process --input /path/to/invoices --output /path/to/results

# Check system status
invoice-processor status

# Get help
invoice-processor --help
```

### Programmatic Usage

```python
from invoice_processor import run_invoice_processing

# Process invoices programmatically
result = run_invoice_processing(
    input_dir="data/input",
    output_dir="data/output", 
    processed_dir="data/processed"
)
print(result)
```

## 📊 Output Format

The application generates multiple output files:

### 1. Main CSV Output (`processed_invoices_YYYYMMDD_HHMMSS.csv`)

| Field | Description |
|-------|-------------|
| invoice_number | Invoice number |
| invoice_date | Invoice date (YYYY-MM-DD) |
| due_date | Payment due date |
| vendor_name | Vendor/supplier name |
| vendor_address | Vendor address |
| total_amount | Total invoice amount |
| item_description | Line item description |
| quantity | Item quantity |
| unit_price | Price per unit |
| line_total | Line item total |
| file_path | Source file path |
| processing_timestamp | When processed |

**Note:** Header information is repeated for each line item, creating a flat, denormalized structure perfect for analysis.

### 2. Processing Summary (`invoice_processing_summary_YYYYMMDD_HHMMSS.txt`)

Comprehensive text report including:
- Processing overview and success rates
- Financial summary with totals and averages
- Detailed invoice table
- Processing status breakdown

### 3. Summary Table (`invoice_summary_table_YYYYMMDD_HHMMSS.csv`)

One row per invoice with:
- File path and invoice details
- Processing status and quality
- Vendor/customer information
- Financial summaries

## 🏗️ Architecture

### System Components

```mermaid
graph TD
    subgraph "User"
        U[User]
    end

    subgraph "Invoice Processor Application"
        CLI(CLI)
        W[Workflow Engine - Prefect]
        
        subgraph "Extractors"
            PDF[PDF Extractor]
            IMG[Image Extractor]
            AI[AI Extractor]
        end

        subgraph "Utilities"
            FU[File Utilities]
            OU[Output Utilities]
        end
        
        DM[Data Models - Pydantic]
    end

    subgraph "External Services"
        OAI[OpenAI API]
        ANT[Anthropic API]
        TESS[Tesseract OCR]
    end

    U -- "Runs commands" --> CLI
    CLI -- "Starts processing" --> W
    W -- "Finds files" --> FU
    W -- "Extracts text/images" --> PDF
    W -- "Extracts text" --> IMG
    W -- "Extracts structured data" --> AI
    W -- "Saves results" --> OU
    
    AI -- "Calls API" --> OAI
    AI -- "Calls API" --> ANT
    IMG -- "Performs OCR" --> TESS
    PDF -- "Performs OCR (fallback)" --> TESS

    W -. "Uses" .-> DM
    AI -. "Creates" .-> DM
    OU -. "Reads" .-> DM
```

### Processing Workflow Sequence

```mermaid
sequenceDiagram
    participant CLI
    participant Workflow
    participant FileUtils
    participant Extractors
    participant AI
    participant OCR
    participant Output
    
    CLI->>Workflow: process_invoices()
    Workflow->>FileUtils: get_invoice_files(recursive=True)
    FileUtils-->>Workflow: List of invoice files
    
    loop For each file
        Workflow->>Extractors: extract_text_from_file()
        Extractors->>Extractors: Try PDF text extraction
        alt PDF text sufficient
            Extractors-->>Workflow: Text content
        else PDF text insufficient
            Extractors->>OCR: Convert PDF to images + OCR
            OCR-->>Extractors: OCR text
            Extractors-->>Workflow: OCR text
        end
        
        Workflow->>AI: extract_invoice_structure()
        AI->>AI: Try OpenAI
        alt OpenAI succeeds
            AI-->>Workflow: Structured invoice
        else OpenAI fails
            AI->>AI: Try Anthropic
            alt Anthropic succeeds
                AI-->>Workflow: Structured invoice
            else Both AI fail
                AI->>AI: Create basic structure
                AI-->>Workflow: Basic invoice
            end
        end
        
        Workflow->>Workflow: flatten_invoice_data()
        Workflow->>FileUtils: move_processed_file()
    end
    
    Workflow->>Output: save_results_to_csv()
    Workflow->>Output: generate_summary_reports()
    Output-->>CLI: Processing complete
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT models | Optional |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude models | Optional |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | Optional |

### AI Provider Priority

1. **OpenAI (Primary)**: Always tried first if API key available
2. **Anthropic (Fallback)**: Used only if OpenAI fails or unavailable
3. **OCR-only (Final Fallback)**: Creates basic structure with raw OCR text

### Directory Structure

```
data/
├── input/           # Place invoice files here (supports nested folders)
│   ├── vendor_a/
│   ├── vendor_b/
│   └── main_invoices.pdf
├── output/          # Generated CSV and summary files
└── processed/       # Moved files (preserves original structure)
    ├── vendor_a/
    └── vendor_b/
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests with coverage
poetry run pytest

# Run with detailed coverage report
poetry run pytest --cov=src/invoice_processor --cov-report=html

# Run specific test categories
poetry run pytest tests/test_models.py  # Unit tests
poetry run pytest tests/features/       # BDD tests
```

### Test Structure

- **Unit Tests**: Comprehensive coverage of individual components
- **Integration Tests**: End-to-end workflow testing
- **BDD Tests**: Business scenario testing with Gherkin syntax
- **Fixtures**: Reusable test data and mock objects

### Coverage Requirements

The project maintains >95% test coverage across all modules:
- Models and data structures: 100%
- File utilities: 100%
- Text extraction: 100%
- Workflow orchestration: 93%
- Summary generation: 98%

## 🚨 Troubleshooting

### Common Issues

1. **No AI API keys**: The app will work with OCR only but accuracy may be lower
2. **Tesseract not found**: Install Tesseract OCR on your system
3. **Poor extraction quality**: Try higher resolution images or cleaner PDFs
4. **Memory issues**: Process files in smaller batches
5. **Permission errors**: Ensure read/write access to input/output directories

### API Quota Management

- **OpenAI Quota Exceeded**: System automatically falls back to Anthropic
- **Both APIs Exhausted**: System continues with OCR-only processing
- **Rate Limiting**: Built-in retry logic with exponential backoff

### File Processing Issues

- **Corrupted PDFs**: Logged and skipped, processing continues
- **Unsupported Formats**: Only PDF and image formats are processed
- **Large Files**: Automatic memory management and chunked processing

## 📈 Performance Optimization

### Best Practices

1. **Batch Processing**: Process multiple files in single run
2. **Directory Organization**: Group similar invoices in subdirectories
3. **Image Quality**: Use high-resolution scans for better OCR accuracy
4. **API Management**: Monitor API usage and implement rate limiting

### Scaling Considerations

- **Prefect Integration**: Leverage Prefect for distributed processing
- **Database Storage**: Consider database backend for large volumes
- **Cloud Deployment**: Deploy on cloud platforms for scalability
- **Monitoring**: Implement logging and metrics collection

## 🔒 Security

### Data Protection

- **Local Processing**: All data processed locally by default
- **API Security**: Secure API key management via environment variables
- **File Permissions**: Proper file system permissions enforcement
- **No Data Persistence**: Temporary data cleaned up after processing

### Best Practices

- Store API keys in `.env` file (not in code)
- Use environment-specific configurations
- Implement access controls for sensitive directories
- Regular security updates for dependencies

## 📄 License

[Your License Here]

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Install development dependencies: `poetry install`
3. Install pre-commit hooks: `pre-commit install`
4. Create a feature branch
5. Make your changes with tests
6. Ensure tests pass: `poetry run pytest`
7. Submit a pull request

### Code Standards

- **Type Hints**: Required for all public APIs
- **Documentation**: Docstrings for all classes and functions
- **Testing**: >95% coverage required
- **Code Style**: Black formatting, flake8 linting
- **BDD Tests**: Gherkin scenarios for new features

### Architecture Guidelines

- **Separation of Concerns**: Clear module boundaries
- **Dependency Injection**: Use of fixtures and dependency injection
- **Error Handling**: Comprehensive error handling and logging
- **Configuration**: Environment-based configuration management

## 📞 Support

For issues and feature requests:
- GitHub Issues: [Repository Issues](your-repo-url/issues)
- Documentation: [Full Documentation](your-docs-url)
- Examples: See `examples/` directory

---

**Built with ❤️ using Python, Prefect, OpenAI, and Anthropic**