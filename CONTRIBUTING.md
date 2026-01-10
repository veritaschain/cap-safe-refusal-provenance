# Contributing to CAP-SRP

Thank you for your interest in contributing to the Safe Refusal Provenance project!

## Ways to Contribute

### 1. Report Issues

- **Bugs**: Open an issue with reproduction steps
- **Security**: Email security@veritaschain.org (do NOT open public issues)
- **Features**: Describe the use case and expected behavior

### 2. Submit Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes
4. Run tests: `python tests/test_srp.py`
5. Commit: `git commit -m "Add: feature description"`
6. Push and open a PR

### 3. Improve Documentation

- Fix typos or unclear sections
- Add examples
- Translate (Japanese, Chinese, etc.)

### 4. Review PRs

- Test proposed changes
- Provide constructive feedback

## Code Standards

### Python Style

```python
def example_function(param: str) -> bool:
    """
    Brief description.
    
    Args:
        param: Description
        
    Returns:
        Description of return value
    """
    pass
```

- Follow PEP 8
- Use type hints
- Document with docstrings

### Commit Messages

- `Add:` New features
- `Fix:` Bug fixes
- `Docs:` Documentation
- `Test:` Test changes
- `Refactor:` Code refactoring

### Testing

- All new features must include tests
- Run `python tests/test_srp.py` before committing
- Maintain or improve coverage

## Specification Changes

For changes to the CAP-SRP specification:

1. Open a discussion issue first
2. Provide rationale and use cases
3. Consider backwards compatibility
4. Include reference implementation updates

## License

By contributing, you agree that your contributions will be licensed
under CC BY 4.0.

## Contact

- General: standards@veritaschain.org
- Security: security@veritaschain.org
- Website: https://veritaschain.org

---

Thank you for helping make AI systems more transparent and accountable!
