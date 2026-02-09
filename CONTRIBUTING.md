# Contributing to Data Quality Framework

Thank you for your interest in contributing to the Data Quality Framework!

## Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd dq-ge-poc
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Initialize database**
   ```bash
   python scripts/init_database.py
   ```

## Running Tests

```bash
# Run example scripts to verify functionality
python examples/basic_usage.py
python examples/advanced_usage.py
```

## Code Style

- Follow PEP 8 style guidelines
- Use type hints where possible
- Add docstrings to all public functions and classes
- Keep functions focused and single-purpose

## Adding New Features

1. Create a feature branch
2. Make your changes
3. Add tests/examples if applicable
4. Update documentation
5. Submit a pull request

## Reporting Issues

When reporting issues, please include:
- Python version
- Great Expectations version
- PostgreSQL version
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs
