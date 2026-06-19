"""
Tool: Generate unit tests for a code file using a specific framework.

Reads a code file and returns a prompt for claude to generate runnable unit tests covering happy paths and edge case in the requested framework.
"""
from pathlib import Path

#Supported testing framework with their typical conventions
SUPPORTED_FRAMEWORKS = {
    "pytest":{
        "language":"Python",
        "naming": "test_<module>.py with test_<function> functions",
        "style": "pytest fixtures,parameterize for multiple cases",
    },
    "unittest":{
        "language":"Python",
        "naming": "test_<module>.py with Test<Module> class and test_<function> methods",
        "style": "setUp/tearDown for fixtures, subTest for multiple cases",
    },
    "jest":{
        "language":"JavaScript/TypeScript",
        "naming": "<module>.test.js/ts with describe and it blocks",
        "style": "beforeEach/afterEach for setup, describe.each for multiple cases",
    },
    "mocha":{
        "language":"JavaScript/TypeScript",
        "naming": "<module>.test.js/ts with describe and it blocks",
        "style": "beforeEach/afterEach for setup, describe.each for multiple cases",
    },
    "junit":{
        "language":"Java",
        "naming": "<Module>Test.java with @Test annotated methods",
        "style": "@Before/@After for setup, parameterized tests for multiple cases",
    },
    "go test":{
        "language":"Go",
        "naming": "<module>_test.go with Test<Function> functions",
        "style": "table driven tests for multiple cases, setup in test function or TestMain",
    },
    "rspec":{
            "language":"Ruby",
            "naming": "<module>_spec.rb with describe and it blocks",
            "style": "before(:each)/after(:each) for setup, shared_examples for multiple cases",
        },
    "phpunit":{
        "language":"PHP",
        "naming": "<Module>Test.php with test<Function> methods",
        "style": "setUp/tearDown for fixtures, data providers for multiple cases",
    },
}

def generate_tests(
        file_path: str, 
        framework: str="pytest",
        coverage_level: str="thorough"
        ) -> str:
    """
    Read a code file and prepare a test-generation prompt for claude.

    Args:
        file_path (str): The path to the code file for which tests are to be generated.
        framework (str): The testing framework to use for generating tests. Defaults to "pytest".
        coverage_level (str): The level of test coverage desired. Options are "basic" or "thorough". Defaults to "thorough".

        Returns:
        Formatted prompt with code +test generation instructions for the specified framework and coverage level.
    """

    #convert to path object and resolve to absolute path
    path = Path(file_path).expanduser().resolve()

    #validate file existence
    if not path.is_file():
        return f"The provided path '{file_path}' is not a valid file."
    
    if not path.exists():
        return f"The provided path '{file_path}' does not exist."
    
    #limit file size to 1MB to avoid overwhelming the test generation
    max_file_size = 1 * 1024 * 1024  # 1MB
    file_size = path.stat().st_size

    if file_size > max_file_size:
        return f"The file '{file_path}' is too large ({file_size} bytes). Please provide a file smaller than 1MB for test generation."
    
    #validate framework
    framework=framework.strip().lower()
    if framework not in SUPPORTED_FRAMEWORKS:
        supported = ", ".join(SUPPORTED_FRAMEWORKS.keys())
        return f"Unsupported testing framework '{framework}'. Supported frameworks are: {supported}."
    
    #validate coverage level
    coverage_level=coverage_level.strip().lower()
    valid_coverage_levels = ["basic", "thorough","exhaustive"]
    if coverage_level not in valid_coverage_levels:
        return f"Invalid coverage level '{coverage_level}'. Valid options are: {', '.join(valid_coverage_levels)}."
    
    #read the file
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, PermissionError):
        return f"Could not read the file '{file_path}' due to encoding issues or permission errors."
    
    #calculate metadata
    line_count = len(content.splitlines())
    code_language = path.suffix.lstrip(".").upper() if path.suffix else "Unknown"
    framework_info = SUPPORTED_FRAMEWORKS[framework]

    #suggest test filename based on framework conventions
    stem=path.stem
    test_filename_map={
        "pytest": f"test_{stem}.py",
        "unittest": f"test_{stem}.py",
        "jest": f"{stem}.test.js",
        "mocha": f"{stem}.test.js",
        "junit": f"{stem}Test.java",
        "go test": f"{stem}_test.go",
        "rspec": f"{stem}_spec.rb",
        "phpunit": f"{stem}Test.php",

    }
    suggested_test_filename = test_filename_map.get(framework, f"test_{stem}.txt")

    #coverage level instructions
    coverage_instructions_map={
        "basic": "Generate basic unit tests covering the main functionality and happy paths.Aim for ~60% coverage with 1-2 test per functions ",
        "thorough": "Generate thorough unit tests covering main functionality, edge cases, and error handling.Aim for ~80% coverage with 2-3 tests per function.",
        "exhaustive": "Generate exhaustive unit tests covering all possible scenarios, edge cases, and error handling.Aim for 95+% coverage with 3-5 tests per function.",
    }
  
    #Build the prompt for test generation
    return f""" Generate unit tests for the following code file using the {framework} framework.
Source File: {path.name}
Path: {path}
Size: {file_size:,} bytes | {line_count:,} lines
Coverage Level: {coverage_level}
code Language: {code_language}
suggested Test Filename: {suggested_test_filename}
framework:{framework}({framework_info["language"]}) - {framework_info["naming"]} | {framework_info["style"]}


---SOURCE CODE---
{content}
---END OF SOURCE CODE---
Instructions:
{coverage_instructions_map[coverage_level]}

###Requirements

1.Use the {framework} framework conventions for naming, structure, and style.
2.Test file naming: {framework_info["naming"]}.
3.Use descriptive test names and docstrings to explain the purpose of each test.
4.Include docstrings for each test function/method to explain what is being tested and the expected outcome.
5.Cover Error handling and edge cases where applicable.
6.Mock external dependencies or services to isolate the unit under test.
7.Group related tests using fixtures, setup/teardown methods, or describe blocks as appropriate for the framework.


### Output Format
1.**Test File**: complete ,runnable code(use '''{code_language} ... ''' for code blocks) for the test file with all necessary imports, fixtures, and test cases.
2.**Test Coverage Summary**: A brief summary of the test coverage achieved, including the number of tests generated and any notable edge cases covered.
3.**Setup Instructions**: Any additional setup or configuration instructions needed to run the tests, if applicable.
4.**Notes**: Any additional notes or considerations for the generated tests, such as limitations or areas for further testing.
5.**Optional**: If applicable, provide a brief explanation of how to run the tests and interpret the results.

Make the test production quality,readable, maintainable, and follow best practices for the specified testing framework. Avoid generating placeholder or incomplete tests; ensure that each test is meaningful and contributes to the overall test coverage of the code file.
"""
#Test :run this file directly to test it
if __name__ == "__main__":
    import sys
    #Example usage
    target_file = generate_tests("src/tools/todo_finder.py", framework="pytest", coverage_level="thorough")
    target_framework = "pytest"
    target_coverage = "thorough"

    #Accept command line arguments for file path, framework, and coverage level
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
    if len(sys.argv) > 2:
        target_framework = sys.argv[2]
    if len(sys.argv) > 3:
        target_coverage = sys.argv[3]
    
    print(f"Testing generate_tests with file: {target_file}, framework: {target_framework}, coverage level: {target_coverage}")

    result = generate_tests(target_file, framework=target_framework, coverage_level=target_coverage)
    print(result)

