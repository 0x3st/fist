#!/usr/bin/env python3
"""
Test script to verify markdown conversion works in both local and deployment environments.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_mistune_import():
    """Test if mistune can be imported."""
    try:
        import mistune
        print("✅ mistune imported successfully")
        print(f"   Version: {mistune.__version__}")
        return True
    except ImportError as e:
        print("❌ mistune import failed:")
        print(f"   Error: {e}")
        return False

def test_markdown_conversion():
    """Test markdown to HTML conversion."""
    from app import markdown_to_html
    
    test_markdown = """# Test Header
This is **bold** and *italic* text.

## Code Example
```python
def hello():
    print('Hello World')
```

- List item 1
- List item 2

[Link](https://example.com)

| Column 1 | Column 2 |
|----------|----------|
| Cell 1   | Cell 2   |
"""
    
    try:
        html = markdown_to_html(test_markdown)
        print("✅ Markdown conversion successful")
        print(f"   HTML length: {len(html)} characters")
        
        # Check if it contains expected HTML elements
        expected_elements = ['<h1>', '<h2>', '<strong>', '<em>', '<pre>', '<code>', '<ul>', '<li>', '<a href=', '<table>']
        found_elements = [elem for elem in expected_elements if elem in html]
        
        print(f"   Found HTML elements: {len(found_elements)}/{len(expected_elements)}")
        if len(found_elements) >= len(expected_elements) * 0.8:  # At least 80% of elements found
            print("   ✅ HTML structure looks good")
        else:
            print("   ⚠️  Some HTML elements missing")
            print(f"   Missing: {set(expected_elements) - set(found_elements)}")
        
        return True
    except Exception as e:
        print("❌ Markdown conversion failed:")
        print(f"   Error: {e}")
        return False

def test_readme_reading():
    """Test README.md file reading."""
    from app import read_readme
    
    try:
        html = read_readme()
        print("✅ README reading successful")
        print(f"   HTML length: {len(html)} characters")
        
        # Check if it contains expected content
        if "FIST Content Moderation API" in html:
            print("   ✅ README content found")
        else:
            print("   ⚠️  Expected README content not found")
        
        return True
    except Exception as e:
        print("❌ README reading failed:")
        print(f"   Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing markdown functionality...")
    print("=" * 50)
    
    # Test 1: mistune import
    print("\n1. Testing mistune import:")
    mistune_ok = test_mistune_import()
    
    # Test 2: markdown conversion
    print("\n2. Testing markdown conversion:")
    conversion_ok = test_markdown_conversion()
    
    # Test 3: README reading
    print("\n3. Testing README reading:")
    readme_ok = test_readme_reading()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Mistune import: {'✅' if mistune_ok else '❌'}")
    print(f"   Markdown conversion: {'✅' if conversion_ok else '❌'}")
    print(f"   README reading: {'✅' if readme_ok else '❌'}")
    
    if all([mistune_ok, conversion_ok, readme_ok]):
        print("\n🎉 All tests passed! Deployment should work correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the issues above.")
        sys.exit(1)
