# Contributing to Automated News Fetcher

First off, thank you for considering contributing to the Automated News Fetcher! It's people like you that make this tool better for everyone.

## Code of Conduct

This project and everyone participating in it is governed by our commitment to creating a welcoming and respectful environment. By participating, you are expected to uphold this standard.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

**Bug Report Template:**
```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
 - OS: [e.g. Ubuntu 22.04]
 - Python Version: [e.g. 3.9.7]
 - MySQL Version: [e.g. 8.0.32]

**Additional context**
Add any other context about the problem here.
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description** of the enhancement
- **Use case**: Why would this be useful?
- **Proposed solution**: How should it work?
- **Alternatives considered**: What other solutions did you consider?

### Adding New News Sources

We welcome additions of new news sources! To add a source:

1. Test the source manually to ensure it's scrapable
2. Identify the correct CSS selectors
3. Add configuration to `custom_sources` dictionary
4. Test thoroughly using option 7 in the menu
5. Document the source in your pull request

**Source Configuration Template:**
```python
'New Source Name': {
    'url': "https://newswebsite.com/category",
    'selectors': {
        'article_container': ['div.article', 'article.story'],
        'title': ['h2.headline', 'h3.title'],
        'link': ['a.story-link'],
        'date': ['time.published', 'span.date']
    }
}
```

### Pull Request Process

1. **Fork the repository** and create your branch from `main`
   ```bash
   git checkout -b feature/AmazingFeature
   ```

2. **Make your changes** following our coding standards

3. **Test your changes** thoroughly
   - Run the fetch operation
   - Test with multiple sources
   - Verify database operations
   - Check email functionality

4. **Update documentation**
   - Update README.md if needed
   - Add comments to complex code
   - Update CHANGELOG.md

5. **Commit your changes** with clear messages
   ```bash
   git commit -m "Add: New feature description"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/AmazingFeature
   ```

7. **Open a Pull Request** with:
   - Clear title describing the change
   - Detailed description of what changed and why
   - Screenshots/logs if applicable
   - Reference any related issues

## Development Setup

### Prerequisites
- Python 3.7+
- MySQL 5.7+
- Git

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/your-username/news-fetcher.git
cd news-fetcher

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
mysql -u root -p < database_schema.sql

# Copy and configure environment file
cp .env.example .env
# Edit .env with your credentials

# Run tests
python news_fetcher.py
```

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

```python
# Good: Clear function names with docstrings
def fetch_articles_from_source(source_name, max_articles=10):
    """
    Fetch articles from a specific news source.
    
    Args:
        source_name (str): Name of the news source
        max_articles (int): Maximum articles to fetch
        
    Returns:
        list: List of article dictionaries
    """
    pass

# Good: Descriptive variable names
article_count = len(articles)
published_date = parse_date(date_string)

# Bad: Unclear names
a = len(articles)
d = parse_date(date_string)
```

### Documentation Standards

- **All functions** must have docstrings
- **Complex logic** should have inline comments
- **Configuration changes** should be documented in README

### Commit Message Format

```
Type: Brief description (50 chars or less)

More detailed explanation if needed. Wrap at 72 characters.
Explain what changed and why, not how.

- Bullet points are okay
- Use present tense: "Add feature" not "Added feature"
- Reference issues: "Fixes #123"
```

**Commit Types:**
- `Add:` New feature or functionality
- `Fix:` Bug fix
- `Update:` Update existing functionality
- `Remove:` Remove feature or code
- `Refactor:` Code refactoring
- `Docs:` Documentation changes
- `Test:` Adding or updating tests

### Testing Guidelines

Before submitting PR, test:

1. **Database operations**
   ```python
   # Test database connection
   # Test article insertion
   # Test duplicate prevention
   # Test query operations
   ```

2. **Web scraping**
   ```python
   # Test each source individually
   # Verify article extraction
   # Check date parsing
   # Validate URLs
   ```

3. **Email functionality**
   ```python
   # Test email sending
   # Verify HTML formatting
   # Check CC functionality
   # Validate error handling
   ```

4. **API operations**
   ```python
   # Test API key rotation
   # Verify rate limit handling
   # Check error recovery
   ```

## Project Structure

```
news-fetcher/
├── news_fetcher.py          # Main application file
├── requirements.txt         # Python dependencies
├── database_schema.sql      # Database setup
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
├── README.md               # Main documentation
├── CONTRIBUTING.md         # This file
├── LICENSE                 # MIT License
└── docs/                   # Additional documentation
    ├── INSTALLATION.md     # Detailed setup guide
    ├── API.md              # API documentation
    └── TROUBLESHOOTING.md  # Common issues
```

## Adding New Features

### Feature Request Process

1. **Open an issue** describing the feature
2. **Discuss** with maintainers and community
3. **Get approval** before starting work
4. **Implement** following guidelines above
5. **Submit PR** with tests and documentation

### Feature Development Checklist

- [ ] Feature approved via issue discussion
- [ ] Code implemented following style guide
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No breaking changes (or clearly documented)
- [ ] Backwards compatible when possible

## Code Review Process

### For Contributors

- Be responsive to feedback
- Make requested changes promptly
- Ask questions if unclear
- Be patient - reviews take time

### What We Look For

1. **Code Quality**
   - Follows style guide
   - Well-documented
   - No unnecessary complexity

2. **Functionality**
   - Works as intended
   - Handles edge cases
   - Proper error handling

3. **Testing**
   - Adequately tested
   - No breaking changes
   - Backwards compatible

4. **Documentation**
   - README updated if needed
   - Code comments added
   - Clear commit messages

## Recognition

Contributors will be:
- Listed in README.md
- Mentioned in release notes
- Credited in CHANGELOG.md

## Questions?

Feel free to:
- Open an issue for discussion
- Contact maintainers
- Join our community discussions

## License

This project is licensed under the MIT License - see the [License](https://github.com/Acash-bits/Regulations_and_News_Tracker?tab=MIT-1-ov-file) file for details.

---

Thank you for contributing to making this project better! 🎉