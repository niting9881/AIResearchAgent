# Contributing to LLM Research Intelligence Hub

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Getting Started

1. **Fork the Repository**
   ```bash
   git clone https://github.com/yourusername/llm-research-intelligence-hub.git
   cd llm-research-intelligence-hub
   ```

2. **Set Up Development Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Code Standards

- **Python Version**: 3.11+
- **Style Guide**: PEP 8
- **Formatter**: Black (line length: 120)
- **Linter**: Flake8, Pylint
- **Type Hints**: Use type hints where applicable

### Before Committing

1. **Format Your Code**
   ```bash
   make format
   ```

2. **Run Linters**
   ```bash
   make lint
   ```

3. **Run Tests**
   ```bash
   make test
   ```

### Commit Messages

Follow the conventional commits specification:

- `feat: Add new feature`
- `fix: Bug fix`
- `docs: Documentation changes`
- `style: Code style changes (formatting)`
- `refactor: Code refactoring`
- `test: Add or update tests`
- `chore: Maintenance tasks`

Example:
```
feat: Add blog scraper agent for OpenAI and Anthropic

- Implemented BeautifulSoup scraper
- Added LangGraph agent for orchestration
- Updated tests and documentation
```

### Pull Request Process

1. **Update Documentation**: Ensure README and docs are updated
2. **Add Tests**: Include unit tests for new features
3. **Update CHANGELOG**: Add entry for your changes
4. **Create PR**: Submit pull request with clear description
5. **Code Review**: Address review comments
6. **Merge**: Once approved, maintainers will merge

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
```

## Project Structure

```
src/
├── ingestion/      # Data scrapers
├── processing/     # Document processing
├── vector_db/      # Qdrant operations
├── rag/            # RAG components
├── agents/         # LangGraph agents
├── llm/            # LLM clients
├── evaluation/     # Evaluation framework
├── monitoring/     # Monitoring and logging
├── app/            # Streamlit application
└── utils/          # Utility functions
```

## Testing Guidelines

### Unit Tests
- Place in `tests/unit/`
- Test individual functions and classes
- Use pytest fixtures
- Mock external dependencies

### Integration Tests
- Place in `tests/integration/`
- Test component interactions
- Use test databases
- Clean up after tests

### Example Test
```python
import pytest
from src.ingestion.arxiv_scraper import ArxivScraper

def test_arxiv_scraper_search():
    scraper = ArxivScraper()
    papers = scraper.search_papers(max_results=5)
    
    assert len(papers) > 0
    assert 'title' in papers[0]
    assert 'authors' in papers[0]
```

## Documentation

- **Docstrings**: Use Google-style docstrings
- **README**: Keep README up-to-date
- **Architecture**: Update architecture.md for major changes
- **API Docs**: Document all public APIs

### Docstring Example
```python
def search_papers(query: str, max_results: int = 50) -> List[Dict]:
    """
    Search for papers on arXiv.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        List of paper dictionaries with metadata
        
    Raises:
        ValueError: If query is empty
        APIError: If arXiv API request fails
        
    Example:
        >>> scraper = ArxivScraper()
        >>> papers = scraper.search_papers("attention mechanisms", max_results=10)
        >>> print(len(papers))
        10
    """
```

## Issue Reporting

### Bug Reports
Include:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Screenshots (if applicable)

### Feature Requests
Include:
- Clear description of feature
- Use case and motivation
- Proposed implementation (optional)
- Alternative solutions considered

## Code Review Guidelines

### As a Reviewer
- Be respectful and constructive
- Explain reasoning for suggestions
- Approve if minor changes needed
- Request changes for major issues

### As an Author
- Respond to all comments
- Don't take feedback personally
- Ask for clarification if needed
- Update PR based on feedback

## Community

- **Discussions**: Use GitHub Discussions for questions
- **Issues**: Use GitHub Issues for bugs and features
- **Email**: Contact maintainers at [email]

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉
