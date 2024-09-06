---
applyTo: "**/*.py"
description: "Python library coding standards"
---

# Python Library Coding Standards

## Python Instructions

- Write clear and concise comments for each function.
- Ensure functions have descriptive names and include type hints.
- Provide docstrings following PEP 257 conventions.
- Use strict typing; avoid using `Any` unless absolutely necessary.
- don't use Dict, List, Set from typing module, use built-in generic types instead (e.g., dict, list, set).
- Break down complex functions into smaller, more manageable functions.
- This library is full asynchronous; use `async` and `await` keywords where appropriate.

## General Principles

- Always use `snake_case` for function and variable names.
- Use `PascalCase` for class names.
- Prefer modern Python syntax (e.g., Python 3.10+ features like `match-case` and `|` for union types).
- Use type hints for all public functions and methods.
- Provide docstrings following PEP 257 conventions

## Code Style & Structure

- Follow the **PEP 8** style guide for Python.
- Organize imports in groups: standard library, third-party, local imports.
- Use `f-strings` for string formatting.
- Avoid global state; prefer dependency injection.

## Documentation

- Use `"""docstring"""` for all public functions, classes, and modules.
- Include parameter descriptions, return value, and examples where applicable.
- Add a `Raises` section for exceptions that may be thrown.

## Testing

- Write unit tests using `pytest`.
- Place test files in a `tests/` directory with names like `test_*.py`.
- Ensure each test function is focused and isolated.
- Use fixtures for shared test setup.

## Error Handling

- Catch specific exceptions, not bare `except:`.
- Raise exceptions with descriptive messages.
- Use context managers (`with` statements) for resource management.

## Example Code

```python
def calculate_area(radius: float) -> float:
    """
    Calculate the area of a circle given its radius.

    Args:
        radius: The radius of the circle in units.

    Returns:
        The area of the circle in square units.

    Raises:
        ValueError: If radius is negative.

    Example:
        >>> calculate_area(5)
        78.53981633974483
    """
    if radius < 0:
        raise ValueError("Radius cannot be negative.")
    return 3.14159 * radius ** 2
```
