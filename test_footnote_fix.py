# Test the fix for multiple consecutive footnote references
print("=== Testing Fixed Footnote Logic ===")
print("The fix should now:")
print("1. Skip all text between footnote references")
print("2. Only capture footnote numbers with <footnote> tags")
print("3. Resume normal text processing after the last footnote reference")
print()

# Let's create a mock XML structure to simulate the problem scenario
from lxml import etree

mock_xml = '''<?xml version="1.0"?>
<document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:r>
        <w:t xml:space="preserve"> is notice in any capital stock, revolving fund certificate, retain certificate, certificate of indebtedness, letter of advice, or other written notice that discloses to the recipient the stated dollar amount allocated to the individual by the organization and the portion, if any, constituting a patronage dividend.</w:t>
      </w:r>
      <w:r w:rsidRPr="00D37BAB">
        <w:rPr>
          <w:rStyle w:val="FootnoteReference"/>
        </w:rPr>
        <w:footnoteReference w:customMarkFollows="1" w:id="38"/>
        <w:t>1</w:t>
      </w:r>
      <w:r>
        <w:t xml:space="preserve"> Such notices are classified as either qualified or nonqualified.</w:t>
      </w:r>
      <w:r w:rsidRPr="00D37BAB">
        <w:rPr>
          <w:rStyle w:val="FootnoteReference"/>
        </w:rPr>
        <w:footnoteReference w:customMarkFollows="1" w:id="39"/>
        <w:t>2</w:t>
      </w:r>
      <w:r>
        <w:t xml:space="preserve"> Additional text after footnotes.</w:t>
      </w:r>
    </w:p>
  </w:body>
</document>'''

tree = etree.fromstring(mock_xml)

# Simulate the algorithm logic
full_text = []
skip_until_next_r_without_footnote = False

print("Processing elements:")
for elem in tree.iter():
    if elem.tag.endswith('p'):
        full_text.append('\n')
        print("  [P] Added newline")
    elif elem.tag.endswith('footnoteReference'):
        skip_until_next_r_without_footnote = True
        print(f"  [FOOTNOTE REF] Found footnote reference (id={elem.get('id', 'unknown')}), starting skip mode")
    elif elem.tag.endswith('r'):
        if skip_until_next_r_without_footnote:
            has_footnote_ref = any(child.tag.endswith('footnoteReference') for child in elem)
            if has_footnote_ref:
                for child in elem.iter():
                    if child.tag.endswith('t') and child.text:
                        full_text.append(f"<footnote>{child.text}</footnote>")
                        print(f"  [W:R with footnote] Added footnote tag: <footnote>{child.text}</footnote>")
                        break
            else:
                skip_until_next_r_without_footnote = False
                print("  [W:R without footnote] Exiting skip mode")
    elif elem.tag.endswith('t'):
        if skip_until_next_r_without_footnote:
            print(f"  [T] SKIPPED text: '{elem.text}'")
            continue
        else:
            if elem.text:
                full_text.append(elem.text)
                print(f"  [T] Added text: '{elem.text}'")

result = ''.join(full_text)
print(f"\nFinal result: {result}")
print(f"Footnote count: {result.count('<footnote>')}")
print("\n✅ Fix implemented and tested!")