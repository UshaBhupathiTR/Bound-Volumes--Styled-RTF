#!/usr/bin/env python3

import re

def find_form_ending(lines):
    """Find the end of a form block"""
    for i, line in enumerate(lines):
        if "►<section" in line:
            return i
        if "►<form" in line and i > 0:
            return i
        if "►<group" in line and i > 0:
            return i
        # Check for end patterns 
        if line.strip() in ["", "►"]:
            continue
        # Look for closing patterns that indicate end of form
        if i > 0 and any(pattern in line for pattern in ["►<header", "►<footer", "►<table", "►<section"]):
            return i
    return len(lines)

def replace_bracketed(text):
    """Replace [placeholders] with <inline.instr>...</inline.instr>"""
    def replace_match(match):
        content = match.group(1)
        return f"<inline.instr>{content}</inline.instr>"
    
    return re.sub(r'\[([^\]]+)\]', replace_match, text)

def update_form_tags(lines):
    index_j = find_form_ending(lines)
    print("check lines", lines)
    form_result = []
    
    # Extract form.fid
    fid_match = re.search(r'form\.fid="([^"]+)"', lines[0])
    fid = fid_match.group(1) if fid_match else ''

    # Extract agreement name and remaining content (text after last </field>)
    # Look for the last </field> and capture everything after it
    # Use a different approach - split by </field> and take the last part
    field_parts = lines[0].split('</field>')
    remaining_content = field_parts[-1].strip() if len(field_parts) > 1 else ''
    
    form_result.append(f"<form uuid=\"{fid}\">")

    # Add the remaining content from the first line if it exists
    if remaining_content and ("fcap.ref" not in lines[0]):
        if "p.ct.id" in lines[0]:
            form_result.append("<form.para>")
            form_result.append(f"<form.text>{remaining_content}</form.text>")
            form_result.append("</form.para>")
        else:
            form_result.append("<form.name.block>")
            form_result.append(f"<name>{remaining_content}</name>")
            form_result.append("</form.name.block>")

    # Track if caption block is opened
    caption_opened = False
    if "fcap.ref" in lines[0] or (len(lines) > 1 and "fcap.ref" in lines[1]):
        refname = re.search(r'fcap.ref="([^"]+)"', lines[0] + lines[1]).group(1)
        form_result.append(f"<caption.block ref=\"{refname}\" date.updated=\"0\">")
        caption_opened = True
        if "fcap.ref" in lines[1] and "</field>" in lines[1]:
            name_match_1 = re.search(r'</field>([^<]+)$', lines[1])
            name = name_match_1.group(1).strip() if name_match_1 else ''
        form_result.append(f"<form.line align = \"c\">{name}</form.line>")

    updated_lines = lines[1:index_j]
    if "fcap.ref" in lines[1]:
        updated_lines = lines[2:index_j]
    
    # Transform para tags to form tags
    for i, line in enumerate(updated_lines):
        if "<para " in line.strip():
            updated_lines[i] = re.sub(r'<para ', '<form.para ', line.strip())
        if "<para>" in line.strip():
            updated_lines[i] = re.sub(r'<para>', '<form.para>', line.strip())
        if "</para" in line.strip():
            updated_lines[i]  = re.sub(r'</para>', '</form.para>', line.strip())
        if "<para.text>" == line.strip():
            updated_lines[i]  = re.sub(r'<para.text>', '<form.text>', line.strip())
        if "</para.text>" in line.strip():
            updated_lines[i]  = re.sub(r'</para.text>', '</form.text>', line.strip())
        if "<heading>" in line.strip():
            print(f"Found heading line: {line.strip()}")
            updated_lines[i]  = re.sub(r'<heading>', '<form.name.block>', line.strip())
            updated_lines[i] = re.sub(r'</heading>', '</form.name.block>', updated_lines[i])
            
    
    i = 0
    # print(f"Processing {updated_lines}")
    while i < len(updated_lines):
        line = updated_lines[i].strip()
        
        # For now, just add all lines and check what happens
        line = replace_bracketed(line)
        form_result.append(line)
        i += 1
    
    # Close caption.block if it's still open at the end
    if caption_opened:
        form_result.append("</caption.block>")
    
    # print("Final form result:", form_result)
    return "\n".join(form_result), index_j

# Test the problematic input
test_input = [
    '►<field>form.du="0"</field><field>form.fid="Id5549ab01b6411e684899cfd92da4eb0"</field>►<field>p.ct.id="f2fd26a0b92511efa75bc0a5c2da1858|113|30:105"</field>No member of the [club/association] shall be discriminated against because of race, color, religion, ethnic or cultural background, <trace.deleted/>age, sex<trace.deleted/> or previous membership in a lawful [club/association], nor shall there be any discrimination based on race, color, religion, ethnic or cultural background, <trace.deleted/><trace.deleted/>age, sex,<trace.deleted/> or previous membership in a lawful [club/association] in the admission policies of the club or association.',
    '<heading>Notes to Form</heading>',
    '<heading>Tax Notes</heading>',
    '►<para ct.id="f2fd26a0b92511efa75bc0a5c2da1858|113|30:105">',
    '<para.text>',
    'A club organized for pleasure, recreation, and other nonprofitable purposes will not be exempt from taxation for any taxable year if, at any time during such taxable year, the charter, bylaws, or other governing instrument of the organization or any written policy statement of the organization contains a provision that provides for discrimination against any person on the basis of race, color, or religion. ►st.ref.id="I008A1I">26 U.S.C.A. &s;§501(i).',
    '</para.text>',
    '</para>',
    '<research.reference.block>',
    "<reference.entry><ref.text>►<tk>West's Key Number Digest, Internal Revenue &key;4045 to 4079</tk></ref.text></reference.entry>",
    '</research.reference.block>'
]

if __name__ == "__main__":
    print("Input lines:")
    for i, line in enumerate(test_input):
        print(f"{i}: {line}")

    print("\n" + "="*80 + "\n")

    # Test with update_form_tags
    result, end_index = update_form_tags(test_input)
    print(f"End index: {end_index}")
    print(f"Result:\n{result}")
    
    print("\n" + "="*80 + "\n")
    print("Expected content that should be preserved:")
    expected_content = [
        "No member of the [club/association] shall be discriminated...",
        "<heading>Notes to Form</heading>",
        "<heading>Tax Notes</heading>", 
        "►<para ct.id=...",
        "<para.text>",
        "A club organized for pleasure...",
        "</para.text>",
        "</para>",
        "<research.reference.block>",
        "<reference.entry>...",
        "</research.reference.block>"
    ]
    for item in expected_content:
        print(f"- {item}")