#!/usr/bin/env python3
"""
Test script to verify our code extraction matches web1's pattern exactly.
"""

import requests
import json

# Test content that matches exactly how AI responses look
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

def test_extraction():
    """Test our code extraction endpoint."""
    
    # Start the server first (you may need to run this separately)
    url = "http://localhost:8001/api/code/extract"
    
    payload = {
        "messageId": "test-message-123",
        "content": test_content
    }
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Code extraction successful!")
            print(f"📊 Found {len(data['data'])} code blocks:")
            
            for i, block in enumerate(data['data'], 1):
                print(f"\n🔹 Block {i}:")
                print(f"   Language: {block['language']}")
                print(f"   Filename: {block['filename']}")
                print(f"   Lines: {block['lineCount']}")
                print(f"   Preview: {block['preview'][:50]}...")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure web_backend_v2 is running on port 8001")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_extraction()