import os
import sys

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.parser import parse_single_file_data

# Create a temporary javascript file with emoji/unicode characters before a function definition
test_file = "test_unicode_temp.js"
code_content = """// 🚀 Emojis to shift byte offsets compared to char offsets!
// Clean unicode: ➔ ★ ❤ ☀ ☁ ☂ ☃ ☄ ☎ ☣ ☢ ☠ ⚔
function helloWorld() {
    return "hello";
}
"""

with open(test_file, "w", encoding="utf-8") as f:
    f.write(code_content)

try:
    res = parse_single_file_data(test_file, "javascript", 1500, 200)
    print("Parsed symbols:")
    for sym in res["symbols"]:
        print(f"  Name: '{sym['name']}' | Type: {sym['symbol_type']}")
        
    # Verify helloWorld is correctly extracted
    func_symbols = [s for s in res["symbols"] if s["symbol_type"] == "function"]
    if func_symbols and func_symbols[0]["name"] == "helloWorld":
        print("SUCCESS: Symbol name extracted correctly!")
    else:
        print("FAILED: Symbol name is wrong!")
finally:
    if os.path.exists(test_file):
        os.remove(test_file)
