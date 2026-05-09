"""Fix app.py UTF-8 encoding issues by either:
1. Adding UTF-8 encoding declaration at the top
2. Replacing common non-ASCII characters with ASCII equivalents
"""

from pathlib import Path

app_path = Path("app.py")

# Read as UTF-8 (will work because file IS valid UTF-8)
content = app_path.read_text(encoding="utf-8")

# Show what's at byte position 6217
raw_bytes = app_path.read_bytes()
problem_area = raw_bytes[6180:6260]
print("Bytes around position 6217:")
print(repr(problem_area))
print()

# Replace common non-ASCII chars with ASCII
replacements = {
    "\u201C": '"',   # left double quote "
    "\u201D": '"',   # right double quote "
    "\u2018": "'",   # left single quote '
    "\u2019": "'",   # right single quote '
    "\u2013": "-",   # en dash –
    "\u2014": "-",   # em dash —
    "\u2026": "...", # ellipsis …
    "\u00A0": " ",   # non-breaking space
    "\u200B": "",    # zero-width space
    "\ufeff": "",    # BOM
}

# Common emojis that might be in the file
emojis_to_remove = [
    "\U0001F3AF",  # 🎯
    "\U0001F680",  # 🚀
    "\u2705",      # ✅
    "\u274C",      # ❌
    "\U0001F517",  # 🔗
    "\U0001F4CA",  # 📊
    "\U0001F465",  # 👥
    "\U0001F4DD",  # 📝
    "\U0001F4E7",  # 📧
    "\U0001F4F1",  # 📱
    "\U0001F30D",  # 🌍
    "\U0001F4A1",  # 💡
    "\u26A0\ufe0f", # ⚠️
    "\u2B50",      # ⭐
    "\U0001F525",  # 🔥
    "\U0001F4C8",  # 📈
]

# Apply replacements
original_content = content
for old, new in replacements.items():
    if old in content:
        count = content.count(old)
        print(f"Replacing {count}x {repr(old)} with {repr(new)}")
        content = content.replace(old, new)

# Remove emojis
for emoji in emojis_to_remove:
    if emoji in content:
        count = content.count(emoji)
        print(f"Removing {count}x emoji {repr(emoji)}")
        content = content.replace(emoji, "")

# Find any remaining non-ASCII chars
remaining_non_ascii = []
for i, char in enumerate(content):
    if ord(char) > 127:
        remaining_non_ascii.append((i, char, hex(ord(char))))

if remaining_non_ascii:
    print(f"\n{len(remaining_non_ascii)} non-ASCII chars still in file:")
    for pos, char, hex_code in remaining_non_ascii[:20]:
        # Get a bit of context
        start = max(0, pos - 30)
        end = min(len(content), pos + 30)
        context = content[start:end].replace('\n', '\\n')
        print(f"  pos {pos}: {repr(char)} ({hex_code}) — context: ...{context}...")

# Write back as UTF-8 with explicit BOM-free format
app_path.write_text(content, encoding="utf-8")

# Verify it imports cleanly now
print("\n=== Testing import ===")
try:
    import importlib
    import sys
    if "app" in sys.modules:
        del sys.modules["app"]
    importlib.import_module("app")
    print("SUCCESS: app.py imports cleanly!")
except UnicodeDecodeError as e:
    print(f"STILL FAILING: {e}")
    print("\nNext step: manually open app.py and search for the problem character")
except Exception as e:
    print(f"Different error (probably import-related, not encoding): {type(e).__name__}: {e}")