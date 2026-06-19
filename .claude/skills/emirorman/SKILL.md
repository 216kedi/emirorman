```markdown
# emirorman Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches you the core development patterns and conventions used in the `emirorman` Python repository. You'll learn about file naming, import/export styles, commit conventions, and testing patterns, as well as how to execute common workflows with suggested commands.

## Coding Conventions

### File Naming
- Use **camelCase** for file names.
  - Example: `myModule.py`, `dataProcessor.py`

### Import Style
- Use **relative imports** within the codebase.
  - Example:
    ```python
    from .utils import helperFunction
    ```

### Export Style
- Use **named exports** (explicitly define what is exported).
  - Example:
    ```python
    def processData(data):
        # logic here
        return result

    __all__ = ['processData']
    ```

### Commit Patterns
- Commit messages are **freeform** (no strict prefixes).
- Average commit message length: **63 characters**.
  - Example:  
    ```
    Fix bug in dataProcessor when handling empty input arrays
    ```

## Workflows

### Adding a New Module
**Trigger:** When you need to add new functionality as a module  
**Command:** `/add-module`

1. Create a new Python file using camelCase (e.g., `newFeature.py`).
2. Implement your functions or classes.
3. Use relative imports to access shared utilities.
4. Define `__all__` for explicit exports.
5. Write corresponding tests in a `*.test.*` file.
6. Commit your changes with a descriptive message.

### Writing and Running Tests
**Trigger:** When you need to verify code correctness  
**Command:** `/run-tests`

1. Create a test file matching the pattern `*.test.*` (e.g., `myModule.test.py`).
2. Write test functions for your code.
3. Use your preferred test runner (framework is unspecified).
4. Run the tests and ensure all pass before committing.

### Refactoring Code
**Trigger:** When improving or restructuring existing code  
**Command:** `/refactor`

1. Identify the code to refactor.
2. Update file and function names to follow camelCase and named exports.
3. Adjust relative imports as needed.
4. Update or add tests to cover changes.
5. Commit with a clear message describing the refactor.

## Testing Patterns

- Test files follow the pattern: `*.test.*` (e.g., `dataProcessor.test.py`).
- The testing framework is **unknown**; use your preferred Python testing tool (e.g., `unittest`, `pytest`).
- Place test files alongside or near the modules they test.

**Example:**
```python
# dataProcessor.test.py

from .dataProcessor import processData

def test_processData_handles_empty():
    assert processData([]) == []
```

## Commands

| Command        | Purpose                                        |
|----------------|------------------------------------------------|
| /add-module    | Scaffold and add a new module                  |
| /run-tests     | Run all test files in the repository           |
| /refactor      | Refactor existing code following conventions   |
```
