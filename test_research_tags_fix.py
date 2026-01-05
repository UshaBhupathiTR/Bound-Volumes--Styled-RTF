# Test script for the fixed add_research_tags function
import sys
sys.path.append('.')

# Import necessary functions from main.py 
from main import add_research_tags, find_r_block_ending, remove_text_between_tags

# Test the fixed add_research_tags function with the user's example
test_research_input = [
    'Research References',
    '►<field>tk.ref.id="I00I382"</field>West\'s Key Number Digest, Corporations and Business Organizations &key;3411',
    'Some additional content without field reference',
    '<trace>This content should be preserved</trace>',
    '<trace.deleted/>',
    'More content that should not be dropped'
]

print("Testing fixed add_research_tags function:")
print("Input:")
for i, line in enumerate(test_research_input):
    print(f"  {i}: {line}")

try:
    result, consumed = add_research_tags(test_research_input)
    print(f"\nOutput (consumed {consumed} lines):")
    print(result)
    print("\nSuccess: Function completed without errors")
    
    # Check if content is preserved
    if 'Some additional content' in result:
        print("✅ Additional content preserved")
    else:
        print("❌ Additional content dropped")
        
    if '<trace>' in result:
        print("✅ Trace elements preserved") 
    else:
        print("❌ Trace elements dropped")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()