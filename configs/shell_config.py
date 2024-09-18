"""
This configuration file defines several lists of commands and symbols for use 
in a shell execution context.
"""

# List of all commands that can be executed
COMMANDS = {
    'mkdir', 
    'docker', 
    'python', 
    'python3', 
    'pip', 
    'virtualenv', 
    'mv', 
    'pytest', 
    'touch', 
    'cat', 
    'ls', 
    'curl',
    'uvicorn',
    'dotnet'
}

# List of symbols that are used to join or pipe commands in a shell context
SHELL_COMMANDS_JOIN_SYMBOLS= [
    "&&",
    "||",
    "|",
    ";"
]

# List of commands that are specifically allowed for coders to execute
CODER_COMMANDS = [
    'mkdir', 
    'docker', 
    'python', 
    'python3', 
    'pip', 
    'virtualenv', 
    'mv', 
    'pytest', 
    'touch', 
    'cat', 
    'ls',
    'dotnet'
]
