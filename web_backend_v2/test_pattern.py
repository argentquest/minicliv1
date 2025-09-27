#!/usr/bin/env python3
"""
Test our regex pattern against web1's approach.
"""

import re

# Test content - typical AI response with code blocks
test_content = '''Here's a Python function:

```python
def process_data(items):
    """Process a list of items."""
    result = []
    for item in items:
        if item.strip():
            result.append(item.upper())
    return result
```

And here's some JavaScript:

```javascript
function calculateTotal(prices) {
    return prices.reduce((sum, price) => sum + price, 0);
}
```

You can also use this SQL query:

```sql
SELECT name, email, created_at 
FROM users 
WHERE active = 1 
ORDER BY created_at DESC
LIMIT 10;
```

This approach works well for data processing.'''

def test_web1_pattern():
    """Test web1's exact pattern."""
    print("Testing web1's pattern: /```(\\w+)?\\n([\\s\\S]*?)\\n```/g")
    
    # Web1's exact pattern
    pattern = r'```(\w+)?\n([\s\S]*?)\n```'
    matches = re.findall(pattern, test_content)
    
    print(f"Found {len(matches)} matches:")
    
    for i, (language, code) in enumerate(matches, 1):
        print(f"\nMatch {i}:")
        print(f"   Language: '{language}'")
        print(f"   Code length: {len(code)} chars")
        print(f"   First line: {repr(code.split(chr(10))[0] if code else '')}")
        print(f"   Code preview: {repr(code[:50])}")

def test_web1_detection():
    """Test web1's detection pattern."""
    print("\nTesting web1's detection: /```[\\s\\S]*?```/.test(text)")
    
    detection_pattern = r'```[\s\S]*?```'
    has_code = bool(re.search(detection_pattern, test_content))
    
    print(f"Has code fragments: {has_code}")

if __name__ == "__main__":
    test_web1_pattern()
    test_web1_detection()