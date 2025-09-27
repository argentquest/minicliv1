#!/usr/bin/env python3
"""
Debug the empty blocks issue.
"""

import re

content_with_empty = '''Valid code:
```python
print("Hello")
```

Empty block:
```javascript

```

Another empty:
```

```

More valid code:
```sql
SELECT 1;
```'''

def test_web1_pattern():
    """Test web1's exact pattern."""
    print("Testing web1's pattern: /```(\\w+)?\\n([\\s\\S]*?)\\n```/g")
    
    # Web1's exact pattern
    pattern = r'```(\w+)?\n([\s\S]*?)\n```'
    matches = re.findall(pattern, content_with_empty)
    
    print(f"Found {len(matches)} matches:")
    
    for i, (language, code) in enumerate(matches, 1):
        print(f"\nMatch {i}:")
        print(f"   Language: '{language}'")
        print(f"   Code length: {len(code)} chars")
        print(f"   Code stripped length: {len(code.strip())} chars")
        print(f"   Code repr: {repr(code)}")
        print(f"   Is empty after strip: {not bool(code.strip())}")

if __name__ == "__main__":
    test_web1_pattern()