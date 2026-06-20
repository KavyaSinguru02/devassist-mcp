"""

DevAssist Direct Client -100% MY CODE,ZERO EXTERNAL AI!

A smart CLI that:
1.Connects to my DevAssist MCP server
2.Lets you sun any tool with simple commands
3.Uses NO AO -pure Python +UX
4.Works completely offline,completely private

"""

import asyncio
import json
import sys
from pathlib import Path
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_SCRIPT=str(Path(__file__).parent/"server.py")

class Color:
    """ANSI color codes for beautiful terminal output."""
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    DIM ="\033[2m"
    RESET = "\033[0m"

COMMANDS ={
    "explain": {
        "tool":"explain_code",
        "description":"Explain a code file (with optional language)",
        "usage":"explain <file_path> [language]",
        "example":"explain src/tools/todp_finder.py English",
        "min_args":1,
        "build_args":lambda parts:{
            "file_path": parts[0],
            "language":parts[1] if len(parts)>1 else "English",
        },
    },
    "test": {
        "tool":"generate_tests",
        "description":"Generate unit tests for a  file",
        "usage":"tests <file_path> [framework] [coverage]",
        "example":"tests src/tools/todp_finder.py pytest thorough",
        "min_args":1,
        "build_args":lambda parts:{
            "file_path": parts[0],
            "framework":parts[1] if len(parts)>1 else "pytest",
            "coverage_level": parts[2] if len(parts)>2 else "thorough",
        },
    },
    "review":{
        "tool":"analyze_git_diff",
        "description":"Review uncommitted git changes",
        "usage":"review [repo_path] [focus]",
        "example":"review.security",
        "min_args":0,
        "build_args":lambda parts:{
            "repo_path": parts[0] if len(parts)>0 else "."
            "review_focus":parts[1] if len(parts)>1 else "general",
        },
    },
    "todos":{
        "tool":"find_todos",
        "description":"Find TODOs/FIXMEs/HACKs in codebase",
        "usage":"todos [directory]",
        "example":"todos.",
        "min_args":0,
        "build_args":lambda parts:{
            "directory": parts[0] if len(parts)>0 else ".",
        },

    },
    "commit":{
        "tool":"suggest_commit_message",
        "description":"suggest commit messaage for staged changes",
        "usage":"commit [repo_path] [style]",
        "example":"commit.conventional",
        "min_args":0,
        "build_args":lambda parts:{
            "repo_path": parts[0] if len(parts)>0 else ".",
            "style":parts[1] if len(parts)>1 else "conventional"
        },

    },
}


class DevAssistClient:
    """Custom MCP client -no external API just smart python"""

    def __init__(self):
        self.session=None
        self.exit_stack=AsyncExitStack()
        self.tools=[]

    async def connect(self):
        """Spawn the MCP Server as subprocess and connect via stdio."""
        print(f"{Color.CYAN} Connecting to DevAssist MCP server...{Color.RESET}")

        server_params = StdioServerParameters(
            command=sys.executable
            args=[SERVER_SCRIPT],
        )

        stdio_transport=await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read, write =stdio_transport

        self.session =await self.exit_stack.enter_async_context(
            ClientSession(read, write)
        )

        await self.session.initialize()

        response = await self.session.list_tools()
        self.tools =response.tools

        print(f"{Color.GREEN} Connected ! Found {len(self.tools)} tools available.{Color.RESET}\n")

    async def call_tools, tool_name:str, arguments: dict) ->str:
        """Execute a tool on the MCP Server."""
    try:
        result =await self.session.call_tool(tool_name, arguments)
        if result.content and len(result.content) > 0:
            return result.content[0].text
        return "(empty response)"
    except Exception as e:
        return f" Tool error: {str(e)}"
    
    async def cleanup(self):
        await self.exit_stack.aclose()
def print_banner():
    print(f"""
{Color.CYAN}{Color.BOLD}__________________________________________________________
|            DEV ASSIST-Direct Tool CLI                                 |              
|           100 % MY CODE . ZERO External AI                            |            
|_______________________________________________________________________|){Color.RESET}
""")
    

def print_help():
    print(f"\n{Color.BOLD}{Color.YELLOW} Available Commands:{Color.RESET}\n")
    for cmd, info in COMMANDS.items():
        print(f"  {Color.GREEN}{Color.BOLD}{cmd:<10}{Color.RESET} {info['description']}")
        print(f"                 {Color.CYAN}Usage:{Color.RESET}  {info['usage']}")
        print(f"                  {Color.CYAN}Example:{Color.RESET}  {Color.DIM}{INFO['example']}"
{Color.RESET}\n")
    print(f"  {Color.GREEN}{Color.BOLD}{'help':<10}{Color.RESET} Show this menu")
    print(f"  {Color.GREEN}{Color.BOLD}{'tools':<10}{Color.RESET} List all available MCP tools")
    print(f"  {Color.GREEN}{Color.BOLD}{'clear':<10}{Color.RESET} Clear the screen")
    print(f"  {Color.GREEN}{Color.BOLD}{'quit':<10}{Color.RESET} Exit DevAssist\n")
def print_tools (tools): 
    print(f"\n{Color.BOLD}{Color.MAGENTA) Registered MCP Tools: {Color.RESET}\n") 
    for tool in tools: 
        print(f" (Color.GREEN}{Color.BOLD) tool.name} {Color.RESET}") 
        desc= tool.description.split(".")[0] if tool.description else "No description" 
        print(f"  {Color.DIM}{desc[:80]}...(Color.RESET}\n") 
async def interactive_loop(): 
    print_banner()
    
    client = DevAssistClient() 
    
    try: 
        await client.connect() 
        print(f"{Color. YELLOW} Type {Color.BOLD}'help'{Color.RESET}{Color.YELLOW} for commands, 
        {Color.BOLD}'quit'{Color.RESET}{Color.YELLOW} to exit{Color.RESET}\n")
        
        while True: 
            try: user_input = input(f"{Color.BOLD}{Color.BLUE}devassist>{Color.RESET} ").strip() 
            
            if not user_input: 
                continue 
            parts user_input.split() 
            command parts[0].lower() 
            args parts [1:] 
            
            if command in ("quit", "exit", "bye"): 
                print(f"\n{Color.GREEN} Goodbye! {Color.RESET}") 
                break 
            
            if command in ("help", "?"): 
                print_help() 
                continue 
            
            if command = "tools": 
                print_tools(client.tools) 
                continue 
            
            if command == "clear": 
                print("\033[2J\033[H", end="") 
                print_banner() 
                continue 
            
            if command in COMMANDS: 
                cmd_info = COMMANDS [command] 
                if len(args) < cmd_info["min_args"]: 
                    print(f"{Color.RED} Missing required arguments! {Color.RESET}")
                    print(f" {Color.CYAN}Usage:{Color.RESET}  {cmd_info['usage']}")
                    print(f" {Color.CYAN} Example:{Color.RESET} {cmd_info['example']}\n") 
                    continue 
                try: 
                    tool_args = cmd_info["build_args"](args) 
                except (IndexError, KeyError) as e: 
                    print(f"{Color.RED} Invalid arguments: {e}{Color.RESET}") 
                    continue (Color.RESET}") 
                
                print(f"\n{Color.CYAN} Calling tool: {Color.BOLD}{cmd_info['tool']} 
{Color.RESET}")                      
                      
                args_preview= json.dumps(tool_args, indent=2) 
                if len(args_preview) > 200: 
                    args_preview = args_preview[:200] + "..." 
                print(f"{Color.DIM} Args {args_preview}{Color.RESET}") 
                print(f"{Color. YELLOW} Running... {Color.RESET}\n") 
                
                result = await client.call_tool(cmd_info["tool"], tool_args) 
                
                print(f"{Color.GREEN}{'-'* 60}{Color.RESET}") 
                print(f"{Color.BOLD} Result: {Color.RESET}\n") 
                print(result)
                print(f"{Color.GREEN}{'-'* 60}{Color.RESET}"\n) 
            
            
            else: 
                print(f"{Color.RED} Unknown command: '{command}'{Color.RESET}") 
                print(f"{Color. YELLOW} Type {Color.BOLD} 'help' {Color.RESET} {Color.YELLOW} for 
available commands {Color.RESET}\n")

            except KeyboardInterrupt: 
                print(f"\n\n{Color.GREEN} Goodbye! {Color.RESET}") 
                break 
            except Exception as e: 
                print(f"{Color.RED} Error: {e}{Color.RESET}\n") 
                continue 
    finally: 
        await client.cleanup() 
    
if__name__ =="__main__": 
   asyncio.run(interactive_loop())


        