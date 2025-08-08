#!/usr/bin/env python3
"""
Test file with intentional errors for demonstrating AgentsTeam error correction
"""

# This will cause a NameError
def main():
    print("Hello, World!")
    result = undefined_variable + 5  # This will cause a NameError
    print(f"Result: {result}")

# This will cause a SyntaxError  
def broken_function()
    return "Missing colon will cause syntax error"

if __name__ == "__main__":
    main()
