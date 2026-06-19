"""
Tool:Explain what a code field does in human language.
Reads a code file and returns its content with metadata,
formatted as a prompt for claude to explain in the requested language.
"""
from pathlib import Path

def explain_code(file_path: str, language: str = "English") -> str:
    """
    Reads a code file and returns its content with metadata,
    formatted as a prompt for claude to explain in the requested language.

    Args:
        file_path (str): The path to the code file to be explained.
        language (str): The language in which the explanation should be provided. Defaults to "English".

    Returns:
        str: A formatted string containing the file content and metadata, ready for explanation.
    """
    path = Path(file_path).expanduser().resolve()

    if not path.is_file():
        return f"The provided path '{file_path}' is not a valid file."

    if not path.exists():
        return f"The provided path '{file_path}' does not exist."
    #Limit file size to 1MB to avoid overwhelming the explanation
    max_file_size = 1 * 1024 * 1024  # 1MB
    file_size = path.stat().st_size
    if file_size > max_file_size:
        return f"The file '{file_path}' is too large ({file_size} bytes). Please provide a file smaller than 1MB for explanation."
    #Try to read the file content, handle potential encoding issues or permission errors gracefully
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, PermissionError):
        return f"Could not read the file '{file_path}' due to encoding issues or permission errors."
    #calculate basic metadata about the file to provide context for the explanation
    line_count=len(content.splitlines())
    char_count=len(content)
    code_language = path.suffix.lstrip(".").upper() if path.suffix else "Unknown"

    #normalize the requested language for explanation
    language = language.strip().title()

    #Build the multi language prompt
    return f""" File: {path.name}
    Path: {path}
    Size: {file_size:,} bytes |{line_count:,} lines | {char_count:,} characters
    Programming Language: {code_language}
    Explanation Language: {language}
    
    ---CODE---
    {content}
    ---END OF CODE---
    IMPORTANT: Please provide a detailed explanation of the above code in {language}. Focus on the purpose, functionality, and key components of the code. Avoid providing a line-by-line translation; instead, summarize the overall logic and structure. If applicable, include examples or scenarios where this code might be used.

    1.**Overall purpose**:What does this file do at a high level? What problem does it solve or what functionality does it provide?
    2.**Key components**: What are the main functions, classes, or sections of the code? Briefly describe what each major part does.
    3.**Important details**: Are there any specific lines or sections of the code that are particularly important or complex? Explain what they do and why they are significant.
    4.**Usage scenarios**: In what contexts or situations might this code be used? Are there any specific inputs, outputs, or dependencies that are important to understand?

    Rules for the response:
    - Provide a clear and concise explanation in {language}.
    -keep code identifierquotes in the explanation to help identify specific parts of the code.
    -keep technical terms and programming language syntax intact to preserve the meaning.
    -Make the explanation accessible to someone with a basic understanding of programming, but avoid oversimplifying technical details.
    """
#Test :run this file directly to test it
if __name__ == "__main__":
    import sys
    #Default values
    target_file = "src/tools/todo_finder.py"
    target_language = "English"

    #Accept CLI args :python code_explainer.py <file_path> <language>
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
    if len(sys.argv) > 2:
        target_language = sys.argv[2]

    print(f"Testing explain_code with file: {target_file} and language: {target_language}")
    result = explain_code(target_file, target_language)
    print(result)