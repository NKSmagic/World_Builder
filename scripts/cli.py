#!/usr/bin/env python3

def main():
    print("World Builder CLI is alive!")
    # Add a quick check for venv interpreter path:
    import sys
    print(f"Python: {sys.executable}")

if __name__ == "__main__":
    main()