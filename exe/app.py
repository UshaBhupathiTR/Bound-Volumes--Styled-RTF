#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import zipfile
from lxml import etree
import re
import string
import sys

import re
from collections import defaultdict
import win32com.client
import pythoncom

import requests
import time
import json
from openai import AzureOpenAI
from pathlib import Path
import ssl
import certifi
from websockets.sync.client import connect
import streamlit as st
import base64
import tempfile
import streamlit.web.cli as stcli

# In[ ]:

CHAPTER_NUMBER = 10
def extract_full_text_with_breaks(docx_path):
    # Open the .docx file as a zip archive
    with zipfile.ZipFile(docx_path, 'r') as docx_zip:
        # Read the document.xml file
        xml_content = docx_zip.read('word/document.xml')
        
    # Parse the XML content
    tree = etree.fromstring(xml_content)

    pretty_xml = etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True)
    with open("pretty_xml_intermediate.xml", 'wb') as f:
        f.write(pretty_xml)
    
    # Extract all text content, including field codes, and retain breaks
    full_text = []
    skip_next_text = False
    # for elem in tree.iter():
    #     # Add a newline for paragraph breaks
    #     if elem.tag.endswith('p'):
    #         full_text.append('\n')
    #     # Add text content
    #     elif elem.tag.endswith('t'):
    #             if elem.tag.endswith('instrText'):
    #                 if elem.text:
    #                     full_text.append("<field>" + elem.text + '</field>')
    #             else:
    #                 if elem.text:
    #                     full_text.append(elem.text)
    #     # Add a newline for line breaks (often represented by <w:br>)
    #     elif elem.tag.endswith('br'):
    #         full_text.append('\n')
    for elem in tree.iter():
        # Paragraph break
        if elem.tag.endswith('p'):
            full_text.append('\n')
        # Footnote reference
        elif elem.tag.endswith('footnoteReference'):
            # Save that the next <w:t> is the reference number
            skip_next_text = True

        # Text
        elif elem.tag.endswith('t'):
            if skip_next_text:
                # Wrap the footnote number in <footnote>
                full_text.append(f"<footnote>{elem.text}</footnote>")
                skip_next_text = False
            else:
                if elem.tag.endswith('instrText'):
                    if elem.text:
                        full_text.append("<field>" + elem.text + '</field>')
                else:
                    if elem.text:
                        full_text.append(elem.text)
        # Line break
        elif elem.tag.endswith('br'):
            full_text.append('\n')
    
    # Join all extracted text into a single string
    return ''.join(full_text)


# In[ ]:


# def extract_full_text_with_footnotes(doc_tree, footnote_tree):
#     ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
#     footnote_map = {}
#     for fn in footnote_tree.findall('.//w:footnote', namespaces=ns):
#         fn_id = fn.get('{%s}id' % ns['w'])
#         fn_text_parts = []
#         for elem in fn.iter():
#             tag = elem.tag
#             if tag.endswith('instrText') and elem.text:
#                 fn_text_parts.append(f'<field>{elem.text}</field>')
#             elif tag.endswith('t') and elem.text:
#                 fn_text_parts.append(elem.text)
#             elif tag.endswith('br'):
#                 fn_text_parts.append('<br>')
#             elif tag.endswith('p'):
#                 if fn_text_parts:
#                     fn_text_parts.append('\n')
#         footnote_map[fn_id] = ''.join(fn_text_parts).strip()
    
#     full_text = []
#     for elem in doc_tree.iter():
#         tag = elem.tag
#         # Paragraph break
#         if tag.endswith('p'):
#             full_text.append('\n')
#         # Field code in main document
#         elif tag.endswith('instrText'):
#             if elem.text:
#                 full_text.append(f'<field>{elem.text}</field>')
                
#         # Footnote reference
#         elif tag.endswith('footnoteReference'):
#             footnote_id = elem.get('{%s}id' % ns['w'])
#             full_text.append(f'<footnoteRef>{footnote_id}</footnoteRef>')
#             footnote_content = footnote_map.get(footnote_id, '')
#             if footnote_content:
#                 full_text.append(f'<footnoteText>{footnote_content}</footnoteText>')
#         # Text (but not instrText, which is handled above)
#         elif tag.endswith('t'):
#             if tag.endswith('instrText'):
#                 continue
#             if elem.text:
#                 full_text.append(elem.text)
#         # Line break
#         elif tag.endswith('br'):
#             full_text.append('<br>')
#     return ''.join(full_text)


# In[ ]:





# In[ ]:


# def extract_full_text_with_footnotes(doc_tree, footnote_tree):
#     ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
#     footnote_map = {}
#     for fn in footnote_tree.findall('.//w:footnote', namespaces=ns):
#         fn_id = fn.get('{%s}id' % ns['w'])
#         fn_text_parts = []
#         for elem in fn.iter():
#             tag = elem.tag
#             if tag.endswith('instrText') and elem.text:
#                 fn_text_parts.append(f'<field>{elem.text}</field>')
#             elif tag.endswith('t') and elem.text:
#                 fn_text_parts.append(elem.text)
#         footnote_map[fn_id] = ''.join(fn_text_parts).strip()
    
#     full_text = []
#     wrap_next_t_with_url = False

#     for elem in doc_tree.iter():
#         tag = elem.tag

#         if tag.endswith('p'):
#             full_text.append('\n')

#         elif tag.endswith('instrText'):
#             if elem.text:
#                 full_text.append(f'<field>{elem.text}</field>')
#                 if 'url.ref.id' in elem.text:
#                     print("Found URL ref in instrText", elem.text)
#                     wrap_next_t_with_url = True

#         elif tag.endswith('footnoteReference'):
#             footnote_id = elem.get('{%s}id' % ns['w'])
#             full_text.append(f'<footnote>')
#             footnote_content = footnote_map.get(footnote_id, '')
#             if footnote_content:
#                 full_text.append(f'<footnote.body>{footnote_content}</footnote.body></footnote>')

#         elif tag.endswith('t'):
#             # Skip if parent <w:r> has <w:footnoteReference>
#             skip_this = False
#             parent = elem.getparent()
#             if parent is not None and parent.tag.endswith('r'):
#                 for child in parent:
#                     if child.tag.endswith('footnoteReference'):
#                         skip_this = True
#                         break
#             if skip_this:
#                 continue
#             if elem.text:
#                 if wrap_next_t_with_url:
#                     full_text.append(f'<url>{elem.text}</url>')
#                     wrap_next_t_with_url = False
#                 else:
#                     full_text.append(elem.text)

#         elif tag.endswith('br'):
#             full_text.append('<br>')

#     return ''.join(full_text)


# In[ ]:


# def extract_full_text_with_footnotes_track(doc_tree, footnote_tree):
#     ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
#     footnote_map = {}

#     for fn in footnote_tree.findall('.//w:footnote', namespaces=ns):
#         fn_id = fn.get('{%s}id' % ns['w'])
#         fn_text_parts = []
#         for elem in fn.iter():
#             tag = elem.tag
#             if tag.endswith('instrText') and elem.text:
#                 fn_text_parts.extend(f'<field>{elem.text}</field>')
#             elif tag.endswith('t') and elem.text:
#                 fn_text_parts.append(elem.text)
#             elif tag.endswith('p'):
#                 fn_text_parts.extend('<f_break>')
#         footnote_map[fn_id] = ''.join(fn_text_parts).strip()

#     def process_element(elem, inside_ins=False, inside_del=False):
#         tag = elem.tag
#         result = []

#         # Handle w:ins (insertion)
#         if tag.endswith('ins'):
#             ins_parts = []
#             for child in elem:
#                 ins_parts.extend(process_element(child, inside_ins=True, inside_del=inside_del))
#             if ins_parts:
#                 result.append('<trace>')
#                 result.extend(ins_parts)
#                 result.append('</trace>')
#             return result

#         # Handle w:del (deletion)
#         if tag.endswith('del'):
#             del_parts = []
#             for child in elem:
#                 del_parts.extend(process_element(child, inside_ins=inside_ins, inside_del=True))
#             if del_parts:
#                 result.append('<trace.deleted>')
#                 result.extend(del_parts)
#                 result.append('</trace.deleted>')
#             return result

#         # Paragraph break
#         if tag.endswith('p'):
#             result.append('\n')

#         # Field code in main document
#         elif tag.endswith('instrText'):
#             if elem.text:
#                 result.append(f'<field>{elem.text}</field>')
                
#         # Footnote reference
#         # elif tag.endswith('footnoteReference'):
#         #     footnote_id = elem.get('{%s}id' % ns['w'])
#         #     result.extend(f'<footnote>')
#         #     footnote_content = footnote_map.get(footnote_id, '')
#         #     if footnote_content:
#         #         result.extend(f'<footnote.body>{footnote_content}</footnote.body></footnote>')
#         elif tag.endswith('footnoteReference'):
#             footnote_id = elem.get('{%s}id' % ns['w'])
#             footnote_content = footnote_map.get(footnote_id, '')
#             footnote_markup = ''
#             if footnote_content:
#                 footnote_markup = f'<footnote><footnote.body>{footnote_content}</footnote.body></footnote>'
#             else:
#                 footnote_markup = '<footnote></footnote>'

#             # MODIFIED: wrap footnote in trace tags if needed
#             if inside_ins:
#                 print("Inside ins, adding trace for footnote")
#                 result.append('<trace>')
#                 result.append(footnote_markup)
#                 result.append('</trace>')
#             elif inside_del:
#                 result.append('<trace.deleted>')
#                 result.append(footnote_markup)
#                 result.append('</trace.deleted>')
#             else:
#                 result.append(footnote_markup)

#         # Text (but not instrText, which is handled above)
#         elif tag.endswith('t'):
#             # SKIP if parent <w:r> contains a <w:footnoteReference>
#             skip_this = False
#             parent = elem.getparent()
#             if parent is not None and parent.tag.endswith('r'):
#                 # If any child of <w:r> is a <w:footnoteReference>, skip this <w:t>
#                 for child in parent:
#                     if child.tag.endswith('footnoteReference'):
#                         skip_this = True
#                         break
#             if skip_this:
#                 return []
#             if elem.text:
#                 result.append(elem.text)

#         # Line break
#         elif tag.endswith('br'):
#             result.append('<br>')

#         # Recursively process children (for non-leaf nodes)
#         for child in elem:
#             result.extend(process_element(child, inside_ins=inside_ins, inside_del=inside_del))

#         return result

#     # Start processing from the document root
#     full_text = process_element(doc_tree)
#     return ''.join(full_text)


# In[ ]:


def process_footnote_body(elem, inside_ins=False, inside_del=False):
    """
    Recursively process footnote XML and wrap ins/del runs as needed.
    Returns a string for the footnote body.
    """
    tag = elem.tag
    result = []

    # Handle insertions and deletions
    if tag.endswith('ins'):
        for child in elem:
            result.append(process_footnote_body(child, inside_ins=True, inside_del=inside_del))
        return ''.join(result)
    if tag.endswith('del'):
        for child in elem:
            result.append(process_footnote_body(child, inside_ins=inside_ins, inside_del=True))
        return ''.join(result)

    # Paragraph break
    if tag.endswith('p'):
        result.append('<f_break>')

    # Field code
    elif tag.endswith('instrText') and elem.text:
        result.append(f'<field>{elem.text}</field>')

    # Inserted or deleted text
    elif tag.endswith('t') and elem.text:
        text = elem.text
        if inside_ins:
            result.append(f'<trace>{text}</trace>')
        elif inside_del:
            if "Drafter's Note" in text:
                result.append(text)
            else:
                result.append(f'<trace.deleted/>')
            # result.append(f'<trace.deleted/>')
        else:
            result.append(text)
    elif tag.endswith('delText') and elem.text:
        # Only in a <w:del> context, but for safety:
        text = elem.text
        if inside_del:
            if "Drafter's Note" in text:
                result.append(text)
            else:
                result.append(f'<trace.deleted/>')
        else:
            result.append(text)

    # Recursively process children
    for child in elem:
        result.append(process_footnote_body(child, inside_ins=inside_ins, inside_del=inside_del))

    return ''.join(result)


# In[ ]:





# In[ ]:


# def extract_full_text_with_footnotes_track(doc_tree, footnote_tree):
#     ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
#     # Build footnote_map: footnote_id -> <w:footnote> element
#     footnote_map = {}
#     for fn in footnote_tree.findall('.//w:footnote', namespaces=ns):
#         fn_id = fn.get('{%s}id' % ns['w'])
#         footnote_map[fn_id] = fn  # Store the element itself, not the text

#     def process_element(elem, inside_ins=False, inside_del=False):
#         tag = elem.tag
#         result = []

#         if tag.endswith('ins'):
#             ins_parts = []
#             for child in elem:
#                 ins_parts.extend(process_element(child, inside_ins=True, inside_del=inside_del))
#             if ins_parts:
#                 result.append('<trace>')
#                 result.extend(ins_parts)
#                 result.append('</trace>')
#             return result

#         if tag.endswith('del'):
#             del_parts = []
#             for child in elem:
#                 del_parts.extend(process_element(child, inside_ins=inside_ins, inside_del=True))
#             if del_parts:
#                 result.append('<trace.deleted>')
#                 result.extend(del_parts)
#                 result.append('</trace.deleted>')
#             return result

#         if tag.endswith('p'):
#             result.append('\n')
#         elif tag.endswith('instrText'):
#             if elem.text:
#                 result.append(f'<field>{elem.text}</field>')
            
#         elif tag.endswith('footnoteReference'):
#             footnote_id = elem.get('{%s}id' % ns['w'])
#             footnote_elem = footnote_map.get(footnote_id)
#             if footnote_elem is not None:
#                 # Use process_footnote_body here!
#                 traced_body = process_footnote_body(footnote_elem, inside_ins, inside_del)
#             else:
#                 traced_body = ''
#             footnote_markup = f'<footnote><footnote.body>{traced_body}</footnote.body></footnote>'
#             result.append(footnote_markup)
#         elif tag.endswith('t'):
#             # Don't print text if parent <w:r> contains a <w:footnoteReference>
#             parent = elem.getparent()
#             skip_this = False
#             if parent is not None and parent.tag.endswith('r'):
#                 for child in parent:
#                     if child.tag.endswith('footnoteReference'):
#                         skip_this = True
#                         break
#             if not skip_this and elem.text:
#                 result.append(elem.text)
#         elif tag.endswith('br'):
#             result.append('<br>')

#         for child in elem:
#             result.extend(process_element(child, inside_ins=inside_ins, inside_del=inside_del))

#         return result

#     full_text = process_element(doc_tree)
#     return ''.join(full_text)


# In[ ]:


def extract_full_text_with_footnotes_track(doc_tree, footnote_tree):
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    footnote_map = {}
    if footnote_tree is not None:
        for fn in footnote_tree.findall('.//w:footnote', namespaces=ns):
            fn_id = fn.get('{%s}id' % ns['w'])
            footnote_map[fn_id] = fn

    def process_element(elem, inside_ins=False, inside_del=False, state=None):
        if state is None:
            state = {'wrap_next_t_with_url': False}
        tag = elem.tag
        result = []

        if tag.endswith('ins'):
            ins_parts = []
            for child in elem:
                ins_parts.extend(process_element(child, inside_ins=True, inside_del=inside_del, state=state))
            if ins_parts:
                result.append('<trace>')
                result.extend(ins_parts)
                result.append('</trace>')
            return result

        if tag.endswith('del'):
            del_parts = []
            for child in elem:
                del_parts.extend(process_element(child, inside_ins=inside_ins, inside_del=True, state=state))
            if del_parts:
                if "Drafter's Note" in del_parts:
                    result.extend(del_parts)
                else:
                    result.append(f'<trace.deleted/>')
            return result

        if tag.endswith('p'):
            result.append('\n')
        elif tag.endswith('instrText'):
            if elem.text:
                result.append(f'<field>{elem.text}</field>')
                if 'url.ref.id' in elem.text:
                    state['wrap_next_t_with_url'] = True
        elif tag.endswith('footnoteReference'):
            footnote_id = elem.get('{%s}id' % ns['w'])
            footnote_elem = footnote_map.get(footnote_id) if footnote_tree is not None else None
            if footnote_elem is not None:
                traced_body = process_footnote_body(footnote_elem, inside_ins, inside_del)
            else:
                traced_body = ''
            footnote_markup = f'<footnote><footnote.body>{traced_body}</footnote.body></footnote>'
            result.append(footnote_markup)
        elif tag.endswith('t'):
            parent = elem.getparent()
            skip_this = False
            if parent is not None and parent.tag.endswith('r'):
                for child in parent:
                    if child.tag.endswith('footnoteReference'):
                        skip_this = True
                        break
            if not skip_this and elem.text:
                if state.get('wrap_next_t_with_url', False):
                    result.append(f'<url>{elem.text}</url>')
                    state['wrap_next_t_with_url'] = False
                else:
                    result.append(elem.text)
        elif tag.endswith('br'):
            result.append('<br>')

        for child in elem:
            result.extend(process_element(child, inside_ins=inside_ins, inside_del=inside_del, state=state))

        return result

    full_text = process_element(doc_tree)
    return ''.join(full_text)


# In[ ]:


def flatten(l):
    for item in l:
        if isinstance(item, list):
            yield from flatten(item)
        else:
            yield item


# In[ ]:


# def extract_full_text_with_footnotes_track(doc_tree, footnote_tree):
#     ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
#     footnote_map = {}

#     # Define process_element FIRST so it's available below
#     def process_element(elem, inside_ins=False, inside_del=False):
#         tag = elem.tag
#         result = []

#         # Handle w:ins (insertion)
#         if tag.endswith('ins'):
#             ins_parts = []
#             for child in elem:
#                 ins_parts.extend(process_element(child, inside_ins=True, inside_del=inside_del))
#             if ins_parts:
#                 result.append('<trace>')
#                 result.extend(ins_parts)
#                 result.append('</trace>')
#             return result

#         # Handle w:del (deletion)
#         if tag.endswith('del'):
#             del_parts = []
#             for child in elem:
#                 del_parts.extend(process_element(child, inside_ins=inside_ins, inside_del=True))
#             if del_parts:
#                 result.extend('<trace.deleted>')
#                 result.extend(del_parts)
#                 result.append('</trace.deleted>')
#             return result

#         # Paragraph break
#         if tag.endswith('p'):
#             result.append('\n')

#         # Field code in main document
#         elif tag.endswith('instrText'):
#             if elem.text:
#                 field_markup = f'<field>{elem.text}</field>'
#                 if inside_ins:
#                     result.append('<trace>')
#                     result.append(field_markup)
#                     result.append('</trace>')
#                 elif inside_del:
#                     result.append('<trace.deleted>')
#                     result.append(field_markup)
#                     result.append('</trace.deleted>')
#                 else:
#                     result.append(field_markup)

#         # Footnote reference
#         elif tag.endswith('footnoteReference'):
#             footnote_id = elem.get('{%s}id' % ns['w'])
#             footnote_content = footnote_map.get(footnote_id, '')
#             footnote_markup = ''
#             if footnote_content:
#                 footnote_markup = f'<footnote><footnote.body>{footnote_content}</footnote.body></footnote>'
#             else:
#                 footnote_markup = '<footnote></footnote>'

#             if inside_ins:
#                 result.append('<trace>')
#                 result.extend(footnote_markup)
#                 result.append('</trace>')
#             elif inside_del:
#                 result.append('<trace.deleted>')
#                 result.extend(footnote_markup)
#                 result.append('</trace.deleted>')
#             else:
#                 result.append(footnote_markup)

#         # Text (but not instrText, which is handled above)
#         elif tag.endswith('t'):
#             skip_this = False
#             parent = elem.getparent()
#             if parent is not None and parent.tag.endswith('r'):
#                 for child in parent:
#                     if child.tag.endswith('footnoteReference'):
#                         skip_this = True
#                         break
#             if skip_this:
#                 return []
#             if elem.text:
#                 result.append(elem.text)

#         # Line break
#         elif tag.endswith('br'):
#             result.append('<br>')

#         # Recursively process children
#         for child in elem:
#             result.extend(process_element(child, inside_ins=inside_ins, inside_del=inside_del))

#         return result

#     # Now, build footnote_map using process_element
#     for fn in footnote_tree.findall('.//w:footnote', namespaces=ns):
#         fn_id = fn.get('{%s}id' % ns['w'])
#         fn_text_parts = []
#         for child in fn:
#             fn_text_parts.extend(process_element(child))
#         flat_fn_text_parts = list(flatten(fn_text_parts))
#         fn_text = ''.join(flat_fn_text_parts)
#         footnote_map[fn_id] = fn_text.strip()

#     # Start processing from the document root
#     full_text = process_element(doc_tree)
#     return ''.join(full_text)


# In[ ]:


def extract_text_between_tags(text):
    # Define the regular expression pattern
    pattern = r'<field>(.*?)</field>'
    
    # Use re.findall to find all matches
    matches = re.findall(pattern, text)
    
    return matches


# In[ ]:


def remove_text_between_tags(text, sub_text):
    # Define the regular expression pattern to match the tags and the text between them
    pattern = r'<field>.*?</field>'

    # Use re.sub to replace the matched text with an empty string
    # Replace the first match with sub_text, rest with blank
    def replacer(match, first):
        if first[0]:
            first[0] = False
            return sub_text
        else:
            return ''
    first = [True]
    result = re.sub(pattern, lambda m: replacer(m, first), text, flags=re.DOTALL)

    return result


# In[ ]:


def get_ending_treated(text):
    # text_lines = text.split('\n')
    return_text = []
    #save the lines until you find a line that starts with "Research reference"
    for i,line in enumerate(text):
        if line.lower().startswith("Research References".lower()):
            break
        return_text.append("<para><para.text>"+line.strip()+"</para.text></para>")
    return return_text, i


# In[ ]:


# only for research references
def find_r_block_ending(text):
    opening_tag_name = "<reference.entry><ref.text>"
    closing_tag_name = ""
    forbidden = {'wd.ref.id', 'tk.ref.id', 'rc.ref.id'}
    return_text = []
    i = 0
    for i, line in enumerate(text):
        # print("Processing line:", line)
        if "<field>" not in line and "<trace.deleted/>" not in line and (not line.strip().startswith("<trace>")):
            print("\n\nNo <field> tag found in line:", line)
            break
        # Extract text between <field> and </field>
        match = re.search(r"<field>(.*?)</field>", line)
        if match:
            field_text = match.group(1)
            # Check if any forbidden substring is present
            if not any(f in field_text for f in forbidden):
                break
        # If no forbidden words, add to return_text
        # updated_line = remove_text_between_tags(line)
        # print("Adding line:", line.strip())
        if line == "<trace.deleted/>":
            return_text.append("<trace.deleted/>")
            continue
        return_text.append(opening_tag_name + line.strip() + closing_tag_name)
    return return_text, i


# In[ ]:


def add_research_tags(lines):
    if isinstance(lines, str):
        lines = lines.split('\n')
    
    modified_text = []
    j = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        # print("Processing line:", i, ":", line)

        # if "Notes to Form" in line:
        #     modified_text.append("<note.block>")
        #     x = find_note_block_ending(lines[i+1:])
        if "Research References".lower() == line.replace("<trace>","").replace("</trace>","").replace("<trace.delted/>","").lower().strip():
        # if "Research References".lower() == line.lower().strip():
            # print("Found research reference block at line:", i)
            r_block_text, j = find_r_block_ending(lines[i+1:])
            modified_text.append("<research.reference.block>")
            # modified_text.append(r_block_text)
            for l in r_block_text:
                # Check for specific tags and replace them
                # l = l.replace("<field>", "", 1)
                # l = l.replace("</field>", "", 1)
                if "wd.ref.id" in l:
                    wd_text = remove_text_between_tags(l,"<wd>")
                    modified_text.append(wd_text+ "</wd></ref.text></reference.entry>")
                elif "tk.ref.id" in l:
                    tk_text = remove_text_between_tags(l, "<tk>")
                    modified_text.append(tk_text + "</tk></ref.text></reference.entry>")
                    # modified_text.append(l.replace("tk.ref.id", "<cite type=\"topic.key\">") + "</cite>")
                elif "rc.ref.id" in l:
                    rc_text = remove_text_between_tags(l, "<rc>")
                    modified_text.append( rc_text + "</rc></ref.text></reference.entry>")
                    # modified_text.append(l.replace("rc.ref.id", "<cite type=\"secondary\">") + "</cite>")
                # else:
                #     modified_text.append("<x>"+ l + "</x>")
            i = i + j + 2
            modified_text.append("</research.reference.block>")
        # elif "rc.ref.id" in line or "tk.ref.id" in line or "wd.ref.id" in line:
        #     # print("Found rc.ref.id or tk.ref.id or wd.ref.id at line:", i)
        #     # Check for specific tags and replace them
        #     if "wd.ref.id" in line:
        #         wd_text = remove_text_between_tags(line, "<cite type=\"secondary\">")
        #         modified_text.append(wd_text + "</cite>")
        #     elif "tk.ref.id" in line:
        #         tk_text = remove_text_between_tags(line, "<cite type=\"topic.key\">")
        #         modified_text.append(tk_text + "</cite>")
        #     elif "rc.ref.id" in line:
        #         rc_text = remove_text_between_tags(line, "<cite type=\"secondary\">")
        #         modified_text.append(rc_text + "</cite>")
        #     i += 1
        else:
            i += 1
            modified_text.append(line.strip())
    
    return "\n".join(modified_text), j+1


# In[ ]:


def split_text_by_continuous_roman_numerals(lines):
    roman_numerals = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX"]
    parts = []
    current_section = []
    expected_numeral_index = 0

    for line in lines:
        # Check if the line starts with a Roman numeral
        match = re.match(r'^([IVXL]+).\s', line)
        if match:
            numeral = match.group(1)
            # Verify if the numeral is the expected one in sequence
            if expected_numeral_index < len(roman_numerals) and numeral == roman_numerals[expected_numeral_index]:
                # If the current section is not empty, add it to sections
                if current_section:
                    parts.append("\n".join(current_section).strip())
                # Start a new section
                current_section = [line]
                expected_numeral_index += 1
            # else:
            #     # If the numeral is not continuous, print a warning and stop processing
            #     print(f"Warning: Expected {roman_numerals[expected_numeral_index]} but found {numeral}.")
            #     return []
        else:
            # Add the line to the current section
            current_section.append(line)

    # Add the last section if any
    if current_section:
        parts.append("\n".join(current_section).strip())

    return parts


# In[ ]:


def split_analytical_blocks(lines):
    # Generate designators A., B., ..., Z.
    designators = [f"{char}." for char in string.ascii_uppercase]
    
    # Initialize a dictionary to store sections by their designator
    sections = {designator: [] for designator in designators}

    current_designator = None

    # Iterate over each line
    for line in lines:
        # Split the line by spaces and check the first word
        if line.strip() == "":
            continue
        first_word = line.split(" ")[0]
        if first_word in designators:
            current_designator = first_word

        if current_designator:
            sections[current_designator].append(line)

    # Remove empty sections
    sections = {key: value for key, value in sections.items() if value}

    return sections


# In[ ]:


def split_numeric_sections(lines):
    # Initialize a dictionary to store sections by their numeric designator
    sections = {}
    current_designator = None

    # Iterate over each line
    for line in lines:
        # Check if the line starts with a number followed by a dot
        match = re.match(r'^(\d+)\.', line)
        if match:
            current_designator = match.group(1)
            if current_designator not in sections:
                sections[current_designator] = []

        if current_designator:
            sections[current_designator].append(line)

    # Convert sections dictionary to a list of sections
    section_list = [section for section in sections.values()]

    return section_list


# In[ ]:


def split_into_sections(lines):
    sections = []
    current_section = []

    for line in lines:
        first_word = line.split()[0] if line.split() else ""
        first_word = first_word.replace("<trace>","").replace("</trace>","").strip()
        if ":" in first_word and "<field>" not in first_word and "<trace.deleted" not in first_word and first_word.split(":")[0].isdigit() :
            if current_section:
                sections.append(current_section)
            current_section = [line.strip()]
        else:
            if current_section:
                current_section.append(line.strip())
    if current_section:
        sections.append(current_section)
    return sections


# In[ ]:


ESSO_TOKEN='eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IlJERTBPVEF3UVVVMk16Z3hPRUpGTkVSRk5qUkRNakkzUVVFek1qZEZOVEJCUkRVMlJrTTRSZyJ9.eyJodHRwczovL3RyLmNvbS9mZWRlcmF0ZWRfdXNlcl9pZCI6IjYxMjIwNjAiLCJodHRwczovL3RyLmNvbS9mZWRlcmF0ZWRfcHJvdmlkZXJfaWQiOiJUUlNTTyIsImh0dHBzOi8vdHIuY29tL2xpbmtlZF9kYXRhIjpbeyJzdWIiOiJvaWRjfHNzby1hdXRofFRSU1NPfDYxMjIwNjAifV0sImh0dHBzOi8vdHIuY29tL2V1aWQiOiIzNzQ2NTE3NC0xZWI1LTQyZTgtYjFkOC02MDAwZDRlNDQ4NmQiLCJodHRwczovL3RyLmNvbS9hc3NldElEIjoiYTIwODE5OSIsImdpdmVuX25hbWUiOiJVc2hhIENoYW5kYW5hIiwiZmFtaWx5X25hbWUiOiJVc2hhIENoYW5kYW5hIiwicGljdHVyZSI6Imh0dHBzOi8vcy5ncmF2YXRhci5jb20vYXZhdGFyL2U2MTkxN2I5ZjQ2NzljNTgzYzY4NzEwODU4ZTllNjkwP3M9NDgwJnI9cGcmZD1odHRwcyUzQSUyRiUyRmNkbi5hdXRoMC5jb20lMkZhdmF0YXJzJTJGdXMucG5nIiwidXBkYXRlZF9hdCI6MTcyNzk2OTMxNywiZW1haWwiOiJ1c2hhY2hhbmRhbmEuYmh1cGF0aGlAdGhvbXNvbnJldXRlcnMuY29tIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJpc3MiOiJodHRwczovL2F1dGgudGhvbXNvbnJldXRlcnMuY29tLyIsImF1ZCI6InRnVVZad1hBcVpXV0J5dXM5UVNQaTF5TnlvTjJsZmxJIiwiaWF0IjoxNzI3OTY5MzIwLCJleHAiOjE3MjgwMDUzMjAsInN1YiI6ImF1dGgwfDY0ZGRmZDkwZjZiODUwNGRmNDE5MTUyOSIsInNpZCI6IkMwWm9PSTQ2cElTWHdQQzZIbWhTalJfcjN3aHBtVGZFIiwibm9uY2UiOiJRM05GVjJ4V2ZtWjRja0pCWTNWWE1tZFlNVlZCVjFvNWJUZERhamxsWlZGMGFGUlNVRkpuV0drMWVnPT0ifQ.Zy9OGyzcK8vDFuTxNgWwvu0hHIb0zRiYATLpHHr-t-f93Y04Mvzlcnc4rS9PnIwfG7WlUOh82sX1uYZqgh2Ysw4lBYosFC7LvftopZ8hBK7HVNPOC9TEaCUUkShtdtKiifCHtY7ydEE-BDYUe6yv4NcUbtlhgKsAet1nyi4Bfl4UqVQullOlPpr693yb_76xM6EBOaHgl8_RyPK0AedD4XTWyviXn1hSAecxhyQaFqA5xxSk-6YxNujUrV9N1lZaSjxQdksapcIlc9_ugOKancs2Wvd4MTUJzoGtp_k6j3183sivzdbl47926F3Xb0OztjPXjxQ8T6gQkKbN2uzUCQ'


# In[ ]:


def find_closing_tag_llm(text, workflow_id):
    WEBSOCKET_URL = f"wss://wymocw0zke.execute-api.us-east-1.amazonaws.com/prod?Authorization={ESSO_TOKEN}"
    
    max_retries = 10
    base_delay = 15
    for attempt in range(max_retries):    
        try:
            # Step 4: Construct the message to convert the image
            summary_request_message = json.dumps({
                "action": "SendMessage",
                "workflow_id": workflow_id,
                "query": text,
                "is_persistence_allowed": False,
            })

            
            # Print the message for debugging
            # print(summary_request_message)

            # Create an SSL context using certifi's CA bundle
            ssl_context = ssl.create_default_context(cafile=certifi.where())

            # Connect to the WebSocket with the SSL context
            print("Connecting to WebSocket")
            ws = connect(WEBSOCKET_URL, ssl_context=ssl_context)
            ws.send(summary_request_message)

            # Receive the response from the WebSocket
            end_of_file = False
            model_answer = "" # Store the model answer here
            while not end_of_file:
                message = ws.recv()
                message = json.loads(message)
                for model, value in message.items():
                    if "answer" in value:
                        model_answer += value["answer"]
                    elif "cost_track" in value:
                        cost_tracker = value['cost_track']
                        end_of_file = True

            ws.close()    
            print(model_answer)
            # if "sorry" not in model_answer.replace("\n","")[:20]: 
            #     print("Model answer is not empty")
            return model_answer
            # else:
            #     print("Model answer is empty")
            #     if attempt == max_retries - 1:
            #         raise
            #     delay = base_delay * (2 ** attempt)
            #     time.sleep(delay)

        
        except Exception as e:
            print("Entered exception")
            print(f"An error occurred: {e} and retrying")

            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)


# In[ ]:


# def process_st_cc(text):

#     # replace_opening_tag_st = re.sub(r'st\.ref\.id=', '<st>', text.strip())
#     # replace_opening_tag_cc = re.sub(r'cc\.ref\.id=', '<cc>', replace_opening_tag_st.strip())

#     result = find_closing_tag_llm(text, workflow_id = "6c2542fd-bda9-47fa-8998-d86a0f6611e2" )
    
#     return result


# In[ ]:


def find_form_ending(lines):
    # exceptions = ["<heading>AMENDED FINAL JUDGMENT</heading>", 
    #               "<heading>FINAL JUDGMENT</heading>", 
    #               "<heading>SUPPLEMENTAL FINAL JUDGMENT</heading>", 
    #               "<heading>FINAL JUDGMENT OF DISMISSAL</heading>", 
    #               "<heading>FINAL JUDGMENT QUASHING ALTERNATIVE WRIT</heading>", 
    #               "<heading>ORDER FOR ACCOUNTING</heading>",
    #               "<heading>ORDER FOR CONTINUING GARNISHMENT</heading>",
    #               "<heading>ORDER OF INTERPLEADER</heading>",
    #               "<heading>FINAL JUDGMENT\r</heading>",
    #               "<heading>JUDGMENT APPOINTING COMMISSIONERS FOR PARTITION</heading>",
    #               "<heading>CONTINUING WRIT OF GARNISHMENT</heading>"]
    # for j, line in enumerate(lines):
    #     if ("<heading>" in line) and not any(x in line for x in exceptions):
    #         break
    for j, line in enumerate(lines):
        if (f"<heading>{CHAPTER_NUMBER}:" in line):
            break
    return j

    


# 

# In[ ]:


# def parse_fi_levels(text):
#     # Regex to match any fi.lvl, e.g., <field>fi.lvl="2"</field>
#     pattern = re.compile(r'<field>fi\.lvl="(\d+)"</field>')
#     # Find all level markers and their positions
#     matches = [(m.start(), int(m.group(1))) for m in pattern.finditer(text)]
    
#     # Add a sentinel for the end of the text
#     matches.append((len(text), None))
    
#     root = {'children': []}
#     stack = [(0, root)]  # (level, node)
    
#     for idx, (pos, lvl) in enumerate(matches[:-1]):
#         curr_lvl = matches[idx][1]
#         next_pos = matches[idx + 1][0]
#         content_start = pos + len(pattern.findall(text[pos:])[0])
#         content = text[content_start:next_pos].strip()
        
#         # Create a new node
#         node = {'level': curr_lvl, 'content': content, 'children': []}
        
#         # Find where to attach this node
#         while stack and stack[-1][0] >= curr_lvl:
#             stack.pop()
#         stack[-1][1]['children'].append(node)
#         stack.append((curr_lvl, node))
        
#     return root['children']


# In[ ]:


# parse_fi_levels_with_signatures(text)


# In[ ]:


import re

def parse_fi_levels_with_signatures(text):
    text = "\n".join(text) # Normalize line endings and strip whitespace
    # print(text)
    # Patterns
    lvl_pattern = re.compile(r'<field>fi\.lvl="(\d+)"</field>')
    sig_pattern = re.compile(r'(?P<sig>(?:<field>fsig\.pos="[^"]*"</field>\s*)*<field>fal\.lo="([yn])"</field>.*?(?=(?:<field>fi\.lvl="|\Z|<field>fal\.lo=)))', re.DOTALL)
    
    # Find all fi.lvl and fal.lo markers with their positions
    events = []
    for m in lvl_pattern.finditer(text):
        events.append( (m.start(), 'lvl', int(m.group(1)), m.end()) )
    for m in sig_pattern.finditer(text):
        events.append( (m.start(), 'sig', m.group('sig').strip(), m.end()) )
    # Sort by position in document
    events.sort()

    # Add sentinel for end of text
    events.append( (len(text), 'end', None, len(text)) )

    root = {'children': []}
    stack = [(0, root)]  # (level, node)
    prev_end = 0

    for idx, (pos, kind, value, end_pos) in enumerate(events[:-1]):
        next_pos = events[idx+1][0]
        # if pos > prev_end:
        #     # Unmarked content between events, attach to current level
        #     content = text[prev_end:pos].strip()
        #     if content:
        #         node = {'type': 'content', 'content': content}
        #         stack[-1][1]['children'].append(node)
        # Only attach as content node if NOT immediately before a section marker
        if pos > prev_end and (kind != 'lvl'):
            content = text[prev_end:pos].strip()
            if content:
                node = {'type': 'content', 'content': content}
                stack[-1][1]['children'].append(node)

        if kind == 'lvl':
            curr_lvl = value
            # Get header/content after the <field>fi.lvl...> marker up to next event
            content_start = end_pos
            content = text[content_start:next_pos].strip()
            node = {'type': 'section', 'level': curr_lvl, 'content': content, 'children': []}
            # Find where to attach this node
            while stack and stack[-1][0] >= curr_lvl:
                stack.pop()
            stack[-1][1]['children'].append(node)
            stack.append((curr_lvl, node))
        elif kind == 'sig':
            sig_content = value
            children = stack[-1][1]['children']
            # Merge with previous signature if exists
            if children and children[-1]['type'] == 'signature':
                children[-1]['content'] += '\n' + sig_content
            else:
                node = {'type': 'signature', 'content': sig_content}
                children.append(node)
        prev_end = end_pos

    return root['children']

# Example usage:
# with open('pasted-text-1752190088015.txt', encoding='utf-8') as f:
#     doc_text = f.read()
# hierarchy = parse_fi_levels_with_signatures(doc_text)
# print(hierarchy)


# In[ ]:


def parse_fi_levels_with_signatures_and_tables(text):
    text = "\n".join(text)  # Normalize line endings and strip whitespace

    # Patterns
    lvl_pattern = re.compile(r'<field>fi\.lvl="(\d+)"</field>')
    sig_pattern = re.compile(
        r'(?P<sig>(?:<field>fsig\.pos="[^"]*"</field>\s*)*<field>fal\.lo="([yn])"</field>.*?(?=(?:<field>fi\.lvl="|\Z|<field>fal\.lo=)))', 
        re.DOTALL
    )
    # -- Table pattern: matches table start to end (from <field>tbl.table.width=...> to the next non-table field or end)
    # We'll look for blocks starting with <field>tbl.table.width and include lines up to the next <field>fi.lvl, <field>fal.lo, or end of text.
    # This is a simple greedy match that should be improved for production use.
    table_pattern = re.compile(
        r'(?P<table><field>table\.resize="[^"]*"</field>.*?(?=(<field>fi\.lvl="|<field>fal\.lo=|<field>tbl\.table\.width="|\Z|<heading>)))',
        re.DOTALL
    )

    # Find all markers with their positions
    events = []
    for m in lvl_pattern.finditer(text):
        events.append((m.start(), 'lvl', int(m.group(1)), m.end()))
    for m in sig_pattern.finditer(text):
        events.append((m.start(), 'sig', m.group('sig').strip(), m.end()))
    for m in table_pattern.finditer(text):
        events.append((m.start(), 'table', m.group('table').strip(), m.end()))
    # Sort by position in document
    events.sort()

    # Add sentinel for end of text
    events.append((len(text), 'end', None, len(text)))

    root = {'children': []}
    stack = [(0, root)]  # (level, node)
    prev_end = 0

    for idx, (pos, kind, value, end_pos) in enumerate(events[:-1]):
        next_pos = events[idx+1][0]
        # Attach content node if appropriate
        if pos > prev_end and (kind != 'lvl'):
            content = text[prev_end:pos].strip()
            if content:
                node = {'type': 'content', 'content': content}
                stack[-1][1]['children'].append(node)

        if kind == 'lvl':
            curr_lvl = value
            content_start = end_pos
            content = text[content_start:next_pos].strip()
            node = {'type': 'section', 'level': curr_lvl, 'content': content, 'children': []}
            while stack and stack[-1][0] >= curr_lvl:
                stack.pop()
            stack[-1][1]['children'].append(node)
            stack.append((curr_lvl, node))
        elif kind == 'sig':
            sig_content = value
            children = stack[-1][1]['children']
            if children and children[-1]['type'] == 'signature':
                children[-1]['content'] += '\n' + sig_content
            else:
                node = {'type': 'signature', 'content': sig_content}
                children.append(node)
        elif kind == 'table':
            table_content = value
            node = {'type': 'table', 'content': table_content}
            stack[-1][1]['children'].append(node)
        prev_end = end_pos

    return root['children']

# Example usage:
# with open('pasted-text-1752190088015.txt', encoding='utf-8') as f:
#     doc_text = f.read()
# hierarchy = parse_fi_levels_with_signatures_and_tables(doc_text)
# print(hierarchy)


# In[ ]:


def extract_placeholders(text):
    # Replace [placeholders] with <inline.instr>__lsqb__placeholder__rsqb__</inline.instr>
    def replacer(match):
        content = match.group(1)
        return f'<inline.instr>&lsqb;{content}&rsqb;</inline.instr>'
    return re.sub(r'\[([^\]]+)\]', replacer, text)


# In[ ]:


def process_signature_group(lines):
    output = []
    vertical_space_needed = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Check for vertical space
        if 'fvs.amt="1"' in line:
            vertical_space_needed = True
            continue
        # Check for signature line
        if 'fal.lo="y"' in line:
            # Look for the label after <br>
            label_match = re.search(r'<br>\s*\[([^\]]+)\]', line)
            if label_match:
                label = label_match.group(1)
            else:
                # Sometimes <br> is present but no label
                label = ""
            output.append(('signature', label))
            continue
        # Check for address or acceptance line
        if 'fal.lo="n"' in line:
            # Is it an acceptance line?
            if 'Accepted:' in line:
                accept_match = re.search(r'Accepted:\s*\[([^\]]+)\]', line)
                if accept_match:
                    label = accept_match.group(1)
                    output.append(('accept', label))
            else:
                # Address line
                addr_match = re.search(r'\[([^\]]+)\]', line)
                if addr_match:
                    label = addr_match.group(1)
                    output.append(('address', label))
    return output, vertical_space_needed

def parse_input(input_text):
    if isinstance(input_text, str):
        input_text = input_text.strip()
    elif isinstance(input_text, list):
        input_text = '\n'.join(input_text).strip()
    # Split into first line and the rest
    lines = input_text.strip().splitlines()
    dated_line = ""
    if "fal.lo" in lines[0].lower():
        # If the first line contains a date, treat it as the dated line
        dated_line = lines[0].strip()
        rest = '\n'.join(lines[1:])
    else:
        # Otherwise, treat the first line as part of the content
        rest =  '\n'.join(lines)
    
    # Find signature group blocks
    # Split on fsig.pos (signature group indicator)
    sig_groups = re.split(r'<field>fsig\.pos="r"</field>►', rest)
    sig_groups = [sg for sg in sig_groups if sg.strip()]
    # Each group is separated by the indicator; process each group
    groups_content = []
    for group in sig_groups:
        # Each group is split by '►'
        group_lines = group.split('►')
        groups_content.append([line for line in group_lines if line.strip()])
    return dated_line, groups_content

def format_output(dated_line, groups_content):
    # Format dated line
    dated_line_processed = extract_placeholders(dated_line)
    # Remove <field> tags
    dated_line_processed = re.sub(r'<field>.*?</field>', '', dated_line_processed).strip()

    output = []
    output.append('<form.line align="l">')
    output.append('  ' + dated_line_processed)
    output.append('</form.line>')
    output.append('\n')
    output.append('<signature.block ref="manual">')
    output.append('  ')
    for group in groups_content:
        group_items, vertical_space_needed = process_signature_group(group)
        output.append('  <signature.group position="r">')
        output.append('    ')
        if vertical_space_needed:
            output.append('    <form.vertical.space amt="1"/>')
            output.append('    ')
        for item_type, label in group_items:
            if item_type == 'signature':
                output.append('    <form.line align="l" lineover="y">')
                output.append(f'      <inline.instr>&lsqb;{label}&rsqb;</inline.instr>')
                output.append('    </form.line>')
                output.append('    ')
            elif item_type == 'address':
                output.append('    <form.line align="l">')
                output.append(f'      <inline.instr>&lsqb;{label}&rsqb;</inline.instr>')
                output.append('    </form.line>')
                output.append('    ')
            elif item_type == 'accept':
                output.append('    <form.line align="l">')
                output.append(f'      Accepted: ')
                output.append(f'      <inline.instr>&lsqb;{label}&rsqb;</inline.instr>')
                output.append('    </form.line>')
                output.append('    ')
        output.append('  </signature.group>')
        output.append('  ')
    output.append('</signature.block>')
    return '\n'.join(output)



# In[ ]:


import re

def parse_fields(line):
    fields = {}
    for m in re.finditer(r'<field>(.*?)</field>', line):
        kv = m.group(1)
        if '=' in kv:
            k, v = kv.split('=', 1)
            fields[k.strip()] = v.strip().strip('"')
    return fields

def table_content_to_xml(table_content, tbl_ident=None):
    if isinstance(table_content, list):
        table_content = '►'.join(table_content)
    lines = [line.strip() for line in table_content.split('►') if line.strip()]

    colspecs, thead, tbody, current_row, para_blocks = [], [], [], [], []
    table_fields = {}
    tbl_attrs = {}

    in_thead = True

    for line in lines:
        # Handle <para> blocks
        if line.startswith('<form.para '):
            para_blocks.append(line)
            continue

        # Fields extraction
        fields = parse_fields(line)
        for k, v in fields.items():
            if k.startswith('tbl.'):
                attr_name = k.replace('tbl.', '')
                tbl_attrs[attr_name] = v
            if k.startswith('table.') or k.startswith('tgroup.'):
                table_fields[k] = v

        # Colspec
        if 'colspec.colname' in fields and 'colspec.colnum' in fields:
            colname = fields['colspec.colname']
            colnum = fields['colspec.colnum']
            colwidth = fields.get('colspec.colwidth', '1*')
            align = fields.get('colspec.align')
            align_attr = f' align="{align}"' if align else ''
            colspecs.append(f'<colspec colname="{colname}" colnum="{colnum}" colwidth="{colwidth}"{align_attr}/>')
            continue

        # Row delimiter
        if 'row.date.updated' in fields:
            if current_row:
                if in_thead:
                    thead.append(f"<row>{''.join(current_row)}</row>")
                else:
                    tbody.append(f"<row>{''.join(current_row)}</row>")
                current_row = []
            if len(thead) == 1:
                in_thead = False
            continue

        # Entry block
        if any(k.startswith('entry.') for k in fields):
            # Compose entry tag attributes
            entry_attrs = []
            for k, v in fields.items():
                if k.startswith('entry.'):
                    attr = k.replace('entry.', '')
                    entry_attrs.append(f'{attr}="{v}"')
            attrs_str = ' ' + ' '.join(entry_attrs) if entry_attrs else ''
            # Get value (what's after all <field> tags)
            value_match = re.search(r'(?:</field>)([^<]*)$', line)
            value = value_match.group(1).strip() if value_match else ''
            current_row.append(f'<entry{attrs_str}>{value}</entry>')
            continue

    # Add last row if any
    if current_row:
        if in_thead:
            thead.append(f"<row>{''.join(current_row)}</row>")
        else:
            tbody.append(f"<row>{''.join(current_row)}</row>")

    # Compose tbl attributes string
    tbl_attr_items = []
    if tbl_ident:
        tbl_attrs['ident'] = tbl_ident
    for k, v in tbl_attrs.items():
        tbl_attr_items.append(f'{k}="{v}"')
    tbl_attr_str = ' ' + ' '.join(tbl_attr_items) if tbl_attr_items else ''

    # Compose XML
    xml = []
    xml.append(f'<tbl{tbl_attr_str}>')
    xml.append('  <table>')
    xml.append(f'    <tgroup align="{table_fields.get("tgroup.align", "left")}" cols="{table_fields.get("tgroup.cols", "2")}">')
    for cs in colspecs:
        xml.append(f'      {cs}')
    if thead:
        xml.append('      <thead>')
        for row in thead:
            xml.append(f'        {row}')
        xml.append('      </thead>')
    if tbody:
        xml.append('      <tbody>')
        for row in tbody:
            xml.append(f'        {row}')
        xml.append('      </tbody>')
    xml.append('    </tgroup>')
    xml.append('  </table>')
    xml.append('</tbl>')
    for para in para_blocks:
        xml.append(para)
    return '\n'.join(xml)


# In[ ]:


# import re

# def table_content_to_xml(table_content, tbl_ident=None):
#     """
#     Converts a table node's content string to XML as per output sample.
#     """
#     # If input is a list, join using delimiter
#     if isinstance(table_content, list):
#         table_content = '►'.join(table_content)
    
#     # Split input into lines
#     lines = [line.strip() for line in table_content.split('►') if line.strip()]
    
#     # Store table-level fields
#     tbl_fields = {}
#     colspecs = []
#     rows = []
#     current_row_entries = []
#     current_row_attrs = {}
#     in_row = False
    
#     # Helper for extracting attributes from field strings
#     def field_to_dict(field_str):
#         m = re.match(r'(\w+\.\w+)="([^"]+)"', field_str)
#         if m:
#             return m.group(1), m.group(2)
#         return None, None

#     # Process lines
#     for line in lines:
#         # Find all <field>...</field> tags
#         field_tags = re.findall(r'<field>(.*?)</field>', line)
#         for ftag in field_tags:
#             key, val = field_to_dict(ftag)
#             if not key:
#                 continue
#             # Table-level fields
#             if key.startswith('tbl.'):
#                 tbl_fields[key] = val
#             # Colspec fields
#             elif key.startswith('colspec.'):
#                 # Temporarily collect colspec data
#                 if not colspecs or len(colspecs[-1]) == 3:
#                     colspecs.append({})
#                 last = colspecs[-1]
#                 if key == "colspec.colname":
#                     last['colname'] = val
#                 elif key == "colspec.colnum":
#                     last['colnum'] = val
#                 elif key == "colspec.colwidth":
#                     last['colwidth'] = val
#             # Row-level fields
#             elif key == "row.date.updated":
#                 # If we have a previous row, finish it
#                 if in_row and current_row_entries:
#                     rows.append((current_row_attrs.copy(), current_row_entries.copy()))
#                     current_row_entries = []
#                     current_row_attrs = {}
#                 current_row_attrs['date.updated'] = val
#                 in_row = True
#             # Entry-level fields
#             elif key.startswith('entry.'):
#                 # Store attributes for next entry
#                 if not 'entry_attrs' in current_row_attrs:
#                     current_row_attrs['entry_attrs'] = []
#                 current_row_attrs['entry_attrs'].append((key.replace('entry.', ''), val))
        
#         # Now, for entry values (outside <field> tags)
#         # Remove all <field>...</field> tags for remaining value
#         entry_value = re.sub(r'<field>.*?</field>', '', line).strip()
#         if entry_value:
#             entry_dict = {}
#             if 'entry_attrs' in current_row_attrs:
#                 for k, v in current_row_attrs['entry_attrs']:
#                     entry_dict[k] = v
#             current_row_entries.append((entry_dict, entry_value))
#             current_row_attrs['entry_attrs'] = []
    
#     # Finish last row
#     if in_row and current_row_entries:
#         rows.append((current_row_attrs.copy(), current_row_entries.copy()))

#     # Compose XML
#     tbl_attrs = []
#     for attr in ['ident', 'uuid', 'position', 'table.width', 'orient', 'date.updated']:
#         key = f'tbl.{attr}'
#         if key in tbl_fields:
#             tbl_attrs.append(f'{attr}="{tbl_fields[key]}"')
#     tbl_attr_str = ' ' + ' '.join(tbl_attrs) if tbl_attrs else ''

#     xml = []
#     xml.append(f'<tbl{tbl_attr_str}>')
#     xml.append('  <table>')
#     # Table attributes
#     table_attrs = []
#     if 'table.tabstyle' in tbl_fields:
#         table_attrs.append(f'tabstyle="{tbl_fields["table.tabstyle"]}"')
#     if 'table.resize' in tbl_fields:
#         table_attrs.append(f'resize="{tbl_fields["table.resize"]}"')
#     table_attr_str = ' ' + ' '.join(table_attrs) if table_attrs else ''
#     xml.append(f'    <tgroup align="{tbl_fields.get("tgroup.align", "left")}" cols="{tbl_fields.get("tgroup.cols", "2")}">')
#     # Colspecs
#     for cs in colspecs:
#         xml.append(f'      <colspec colname="{cs.get("colname","")}" colnum="{cs.get("colnum","")}" colwidth="{cs.get("colwidth","1*")}"/>')
#     # Body
#     xml.append('      <tbody>')
#     for row_attrs, entries in rows:
#         row_attr_str = f' date.updated="{row_attrs.get("date.updated","")}"' if 'date.updated' in row_attrs else ''
#         xml.append(f'        <row{row_attr_str}>')
#         for entry_attrs, entry_val in entries:
#             entry_attr_str = ''
#             if entry_attrs:
#                 entry_attr_str = ' ' + ' '.join(f'{k}="{v}"' for k, v in entry_attrs.items())
#             xml.append(f'          <entry{entry_attr_str}>{entry_val}</entry>')
#         xml.append('        </row>')
#     xml.append('      </tbody>')
#     xml.append('    </tgroup>')
#     xml.append('  </table>')
#     xml.append('</tbl>')
#     return '\n'.join(xml)


# In[ ]:


import re

def parse_designator_and_name(content):
    """
    Parse a heading line for label, designator, and name/title.
    Returns dict with keys: label, designator, name.
    """
    # ARTICLE
    m = re.match(r'ARTICLE\s+([IVXLCDM]+)\s+(.+)', content, re.IGNORECASE)
    if m:
        return {'label': 'ARTICLE', 'designator': m.group(1), 'name': m.group(2).strip()}
    # Section N. Title.
    m = re.match(r'Section\s+(\d+)\.\s*([^\n\.]+)', content)
    if m:
        return {'label': 'Section', 'designator': m.group(1), 'name': m.group(2).strip()}
    # N. Title (bare number heading)
    m = re.match(r'(\d+)\.\s*([^\n\.]+)', content)
    if m:
        return {'label': None, 'designator': m.group(1), 'name': m.group(2).strip()}
    # (a)., (1)., etc.
    m = re.match(r'\(([a-zA-Z0-9]+)\)\.', content)
    if m:
        return {'label': None, 'designator': f'({m.group(1)})', 'name': None}
    # Lettered: a. Foo bar.
    m = re.match(r'([a-zA-Z])\.\s*(.+)', content)
    if m:
        return {'label': None, 'designator': m.group(1), 'name': m.group(2).strip()}
    # Letter only: a. or a. 
    m = re.match(r'([a-zA-Z])\.\s*$', content)
    if m:
        return {'label': None, 'designator': m.group(1), 'name': None}
    # (a). Foo bar.
    m = re.match(r'(\([a-zA-Z0-9]+\))\.\s*(.+)', content)
    if m:
        return {'label': None, 'designator': m.group(1), 'name': m.group(2).strip()}
    # (1). Foo bar.
    m = re.match(r'(\([0-9]+\))\.\s*(.+)', content)
    if m:
        return {'label': None, 'designator': m.group(1), 'name': m.group(2).strip()}
    return {'label': None, 'designator': None, 'name': None}

def extract_form_paras(content):
    """
    Extract all <form.para ...>...</form.para> blocks from content.
    Returns a list of the XML blocks as strings.
    """
    # Remove leading '►' and trailing '►'
    content = content.strip('►\n ')
    # Find all form.para blocks
    blocks = re.findall(r'(<form\.para[\s\S]*?</form\.para>)', content)
    return [b.strip() for b in blocks]

def clean_heading(content):
    """
    Remove any trailing '►' and <form.para> blocks from the heading.
    """
    # Remove any <form.para ...>...</form.para> and after
    heading = re.split(r'<form\.para', content)[0]
    heading = heading.replace('►', '').strip()
    return heading

def dict_tree_to_xml_sig(tree, indent=0, top_level=True):
    """
    Recursively convert dict tree to XML lines.
    """
    xml_lines = []
    indent_str = "  " * indent
    if top_level:
        xml_lines.append(f'<form.unit>')

    for node in tree:
        node_type = node.get('type', '')
        content = node.get('content', '').strip() if 'content' in node else ''
        children = node.get('children', [])

        # Special: signature block at end
        if node_type == 'signature':
            dated_line, groups_content = parse_input(content)
            result = format_output(dated_line, groups_content)
            xml_lines.append(f'{result}')
            continue

        if node_type == "table":
            # tbl_ident = node.get("ident")  # If you have an ident field
            tbl_ident = node.get("ident", None)
            xml_lines.append(table_content_to_xml(content, tbl_ident))
            continue

        # If this is a "content" node with <form.para> only, emit as-is and continue
        if node_type == 'content':
            xml_lines.extend([f'{b}' for b in extract_form_paras(content)])
            continue

        # 1. Parse heading (label, designator, name)
        heading = clean_heading(content)
        headinfo = parse_designator_and_name(heading)

        # Only process as <form.item> if it's a section or has a designator/label
        if node_type == 'section' and (headinfo['designator'] or headinfo['label'] or node.get('level',0) > 1):
            xml_lines.append(f'<form.item>')
            # Add <head> for ARTICLES
            if headinfo['label'] == 'ARTICLE':
                xml_lines.append(f'<head>')
            xml_lines.append(f'<name.block>')
            if headinfo['label']:
                xml_lines.append(f'<label>{headinfo["label"]}</label>')
            if headinfo['designator']:
                xml_lines.append(f'<designator>{headinfo["designator"]}</designator>')
            if headinfo['name']:
                xml_lines.append(f'<name>{headinfo["name"]}</name>')
            xml_lines.append(f'</name.block>')
            if headinfo['label'] == 'ARTICLE':
                xml_lines.append(f'</head>')

            # For bare numbered N. Title, emit the title as a <form.para>
            if (headinfo['label'] in ('Section', None)) and headinfo['name']:
                xml_lines.append(f'<form.para>')
                xml_lines.append(f'<form.text>{headinfo["name"]}</form.text>')
                xml_lines.append(f'</form.para>')

            # Emit all <form.para> blocks found after the heading
            form_paras = extract_form_paras(content)
            for para in form_paras:
                xml_lines.append(f'{para}')

            # Recurse for children
            if children:
                # If children are all sections, use <form.unit>
                child_items = [c for c in children if c.get('type') == 'section']
                if child_items:
                    xml_lines.append(f'<form.unit>')
                    xml_lines.extend(dict_tree_to_xml_sig(children, indent + 3, top_level=False))
                    xml_lines.append(f'</form.unit>')
                else:
                    xml_lines.extend(dict_tree_to_xml_sig(children, indent + 2, top_level=False))
            xml_lines.append(f'</form.item>')
        else:
            # For para-only or non-section nodes, just emit <form.para> blocks
            form_paras = extract_form_paras(content)
            for para in form_paras:
                xml_lines.append(f'{para}')
            # Still process children
            if children:
                xml_lines.extend(dict_tree_to_xml_sig(children, indent + 1, top_level=False))

    if top_level:
        xml_lines.append(f'</form.unit>')
    return xml_lines


# In[ ]:


def replace_bracketed(text):
    """Replace [text] with <inline.instr>__lsqb__text__rsqb__</inline.instr>."""
    return re.sub(r'\[([^\]]+)\]', r'<inline.instr>&lsqb;\1&rsqb;</inline.instr>', text)


# In[ ]:


def find_table_ending(text):
    """Find the end of a table in the text."""
    for i, line in enumerate(text):
        if '<field>' not in line:
            return i
    return len(text)  # If no table found, return end of text


# In[ ]:


def find_fcap_ending(lines):
    """Find the end of a figure/caption block."""
    for i, line in enumerate(lines):
        if '<heading>' in line:
            return i
    return len(lines)  # If no non-fcap field found, return end of lines


# In[ ]:


def update_form_tags(lines):
    index_j = find_form_ending(lines)
    form_result = []
    # Extract form.fid
    fid_match = re.search(r'form\.fid="([^"]+)"', lines[0])
    fid = fid_match.group(1) if fid_match else ''

    # Extract agreement name (text after last </field>)
    name_match = re.search(r'</field>([^<]+)$', lines[0])
    name = name_match.group(1).strip() if name_match else ''
    
    form_result.append(f"<form uuid=\"{fid}\">")
    
    if name and "fcap.ref" not in lines[0]:
        form_result.append("<form.name.block>")
        form_result.append(f"<name>{name}</name>")
        form_result.append("</form.name.block>")
    print("------------------")
    print(lines)
    if "fcap.ref" in lines[0] or "fcap.ref" in lines[1]:
        refname = re.search(r'fcap.ref="([^"]+)"', lines[0] + lines[1]).group(1)
        form_result.append(f"<caption.block ref={refname} date.updated=\"0\">")
        if "fcap.ref" in lines[1]:
            name =  re.search(r'</field>([^<]+)$', lines[1]).group(1).strip() if name_match else ''
        form_result.append(f"<form.line align = \"c\">{name}</form.line>")
        fcap_index = find_fcap_ending(lines)
        # form_result.append("</caption.block>")

    updated_lines = lines[1:index_j]
    if "fcap.ref" in lines[1]:
        updated_lines = lines[2:index_j]
    #TODO check for para being continuation with form.du
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
    
    i = 0
    # print(f"Processing {updated_lines}")
    while i < len(updated_lines):
        line = updated_lines[i].strip()
        # Handle tables

        if 'table.resize=' in line or "tbl.ident" in line:
            table_index = find_table_ending(updated_lines[i:])
            table_result = table_content_to_xml(updated_lines[i:i + table_index + 1], tbl_ident=None)
            form_result.append(table_result)
            if "fcap.ref" in lines[0] or "fcap.ref" in lines[1]:
                form_result.append("</caption.block>")
            i += table_index + 1
            continue
        # Handle fi.lvl
        elif 'fi.lvl=' in line:
            # print(updated_lines[i:])
            temp_output = parse_fi_levels_with_signatures_and_tables(updated_lines[i:])
            temp_output_result = dict_tree_to_xml_sig(temp_output)
            form_result.append("\n".join(temp_output_result))
            break  # Stop processing after fi.lvl block
        elif ('fvs.amt' in line) or ('fal.lo' in line) or ('fsig.pos' in line):
            signature_index = find_table_ending(updated_lines[i:])
            dated_line, groups_content = parse_input(updated_lines[i:i + signature_index + 1])
            sig_result = format_output(dated_line, groups_content) 
            form_result.append(sig_result)
            i += signature_index + 1
            continue
        else:
            # Replace [placeholders] with <inline.instr>...</inline.instr>
            line = replace_bracketed(line)
            form_result.append(line)
            i += 1
    form_result.append("</form>")
    return "\n".join(form_result), index_j


# In[ ]:


def add_tags(lines):
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if "<field>" in line:
            # Search for <field>...</field> in the whole line
            match = re.search(r"<field>(.*?)</field>", line)
            if match:
                field_text = match.group(1)
                if "form.du" in field_text or "form.samp" in field_text or "fcap.ref" in field_text:
                    # Make sure update_form_tags is defined elsewhere
                    form_line, offset = update_form_tags(lines[i:])
                    # print("====================Form line found:", form_line)
                    result.append(form_line)
                    i += offset  # Skip processed lines
                    continue  # Avoid incrementing i again at the end
                else:
                    result.append(line)
            else:
                result.append(line)            
        else:
            result.append(line)
        i += 1
    
    headings_done = False
    heading_lines = []
        
    non_heading_lines = []
    # If any line contains "<form ", return as-is
    
    # if any("<form " in line for line in result):
    for line in result:
        if not headings_done and "<heading>" in line:
            heading_lines.append(line)
        else:
            headings_done = True
            non_heading_lines.append(line)
    return non_heading_lines, heading_lines


    # return result


# In[ ]:


def process_tip(lines):
    # Example processing: join lines, uppercase, split again
    updated_lines = []
    updated_lines.append("<feature.para.block>")
    updated_lines.append("<name.block>")
    updated_lines.append(f"<name>{lines[0].replace("<heading>","").replace("</heading>","")}</name>")
    updated_lines.append("</name.block>")
    for line in lines[1:]:
        line = line.strip()
        if line:
            updated_lines.append(line)
    updated_lines.append("</feature.para.block>")
    return updated_lines

def add_feature_tags(input_lines):
    output_lines = []
    i = 0
    while i < len(input_lines):
        if "<heading>Practice Tip".lower() in input_lines[i].lower():
            block = [input_lines[i]]
            i += 1
            # Collect until </para>
            while i < len(input_lines):
                block.append(input_lines[i])
                if "</para>" == input_lines[i]:
                    break
                i += 1
            # Process and extend output
            processed = process_tip(block)
            output_lines.extend(processed)
            i += 1
        else:
            output_lines.append(input_lines[i])
            i += 1
    return output_lines


# In[ ]:


def add_para_tags(text):
    lines = text.split('\n')
    result = []
    # print("Adding para tags to lines", lines)
    for i , line in enumerate(lines):
        if "<field>" not in line:

            if len(line.split()) > 4 and not line.startswith("<") and not line.startswith("</"):
                result.append("<para>")
                result.append("<para.text>")
                result.append(line.strip())
                result.append("</para.text>")
                result.append("</para>")
            elif ("<" not in line) or (">" not in line):
                result.append("<heading>" + line.strip().replace("\n", "").replace("\r","") + "</heading>")
            else:
                # print("\n\nNo <field> tag found in line:", line)
                result.append(line)
            continue
        match = re.search(r"<field>(.*?)</field>", line.strip().split(' ')[0])
        # match = re.search(r"<field>(.*?)</field>", line.strip().split(' ')[0])
        if match:
            field_text = match.group(1)
            if "p.ct.id" in field_text:
            #remove text between <field> and </field>
                print("Found p.ct.id in field text:", line)
                line = line.replace("<field>", "", 1)
                line = line.replace("</field>", ">\n<para.text>\n", 1)
                print("After p.ct.id replacement:", line)
                
                if ("st.ref.id" in line) or ("cc.ref.id" in line):
                    line = find_closing_tag_llm(line, workflow_id = "6c2542fd-bda9-47fa-8998-d86a0f6611e2")
                
                # Replace 'p.ct.id=' with '<para ct.id=' in the line

                if 'x.ref.id=' in line:
                    print("Before x.ref.id replacement:", line)
                    line = re.sub(r'<field>x\.ref\.id="[^"]*"</field>', '<x>', line.strip())
                    print("Found x.ref.id in line:", line)
                    # b = b.replace("</field>", "", -1)
                if 'url.ref.id=' in line:
                    line = re.sub(r'<field>url\.ref\.id="[^"]*"</field>', '', line.strip())
                    line = re.sub(r'<url>', '<url>', line.strip())
                    line = re.sub(r'</url>', '</url>', line.strip())
                    # b = b.replace("</field>", "", -1)
                # if 'rc.ref.id=' in line:
                #     line = re.sub(r'<field>rc\.ref\.id="[^"]*"</field>', '<rc>', line.strip())
                #     line = re.sub(r'<url>', '<cite type="url">', line.strip())
                #     line = re.sub(r'</url>', '</cite>', line.strip())
                print("Before p.ct.id replacement:", line)
                line = re.sub(r"<field>", "", line.strip(), 1)
                line = re.sub(r"</field>", ">", line.strip(), 1)
                line = re.sub(r'p\.ct\.id=', '<para ct.id=', line.strip())
                
                # Track if we already have para tags to avoid duplication
                para_already_added = False
                for l in line.split('\n'):
                    l = l.strip()
                    if l:
                        result.append(l)
                        # Check if this line already contains para opening tag
                        if '<para ct.id=' in l:
                            para_already_added = True
                
                if '<rc>' in line:
                    result.append('</rc>')
                if '<x>' in line:
                    result.append('</x>')
                
                # Only add closing para tags if we actually started a para block
                if para_already_added:
                    result.append("</para.text>")
                    result.append("</para>")
            else:
                # print("No 'p.ct.id' found in field text:", field_text)
                result.append(line.strip())
        else:
            result.append(line)
            continue


    result = [line for line in result if line.strip()!="<heading></heading>"]


    return result


# In[ ]:


def add_footnote_tags(lines):
    final_footer_added = []
    print("Footer processing lines:", lines)
    def footer_replace(match):
        f_result=[]
        for f in match.groups():
            f_result.append("\n<footnote>")
            # find text between <footnote.body> and </footnote.body>
            body_text = re.findall(r'<footnote\.body>(.*?)</footnote\.body>', f, re.DOTALL)
            if body_text:
                b_list = body_text[0].split('<f_break>')

                # appending footnote reference text

                if '<field>fn.fnref=' in b_list[1]:
                    field_text = re.findall(r'<field>(.*?)</field>',  b_list[1])[0] 
                    # Remove the <field> tags and extract the text
                    ref = field_text.replace('fn.fnref="', '').replace('"', '').strip()
                    f_result.append("<footnote.reference>"+ref+"</footnote.reference>")
                elif 'fn.fnref' in b_list[1]:
                    #find the text between fn.fnref=" and "
                    ref = b_list[1].split('fn.fnref="')[1].split('"')[0].strip()
                    f_result.append("<footnote.reference>"+ref+"</footnote.reference>")

                # Skip the first two elements which are the reference and the field and blank lines
                footnote_body_list = b_list[2:]  
                footnote_body_list = [line.strip() for line in footnote_body_list if line.strip()]  # Remove empty lines 
                f_result.append("<footnote.body>")
                # print(len(footnote_body_list))
                i=0
                while i < len(footnote_body_list) :
                    b = footnote_body_list[i].strip()
                    field_text = re.findall(r'<field>(.*?)</field>', b)[0] if '<field>' in b else ''

                    if "para ct.id" in field_text :
                        # print("Found para ct.id in footnote body:", b)
                        # Remove the <field> tags and extract the text
                        b = b.replace("<field>", "", 1)
                        b = b.replace("</field>", ">\n<para.text>\n", 1)
                        
                        if ("st.ref.id" in b) or ("cc.ref.id" in b):
                            print("st or cc foung in footnote body:")
                            b = find_closing_tag_llm(b, workflow_id = "6c2542fd-bda9-47fa-8998-d86a0f6611e2")
                        # Replace 'p.ct.id=' with '<para ct.id=' in the line

                        if 'x.ref.id=' in b:
                            b = re.sub(r'<field>x\.ref\.id=(.*)</field>', '<x>', b.strip())
                            # b = b.replace("</field>", "", -1)


                        # b = re.sub(r'p\.ct\.id=', '<para ct.id=', line.strip())
                        for l in b.split('\n'):
                            l = l.strip()
                            if l:
                                f_result.append(l)
                        # if '<x>' in b:
                        #     f_result.append("</x>")
                        # result.append(line)
                        f_result.append("</para.text>")
                        f_result.append("</para>")
                        i += 1
                        continue
                    
                    if "Research References" in b:   
                        # f_result.append(footnote_body_list[i])
                        r_block , j = add_research_tags(footnote_body_list[i:])
                        f_result.append(r_block)
                        i += j+1
                        continue
                    else:
                        i += 1
                        f_result.append(b)
                    

                # print("\n".join(footnote_body_list))
            else:
                print("No footnote body text found in:", f)
            f_result.append("</footnote.body>")
            f_result.append("</footnote>")
        return "\n".join(f_result)
    for line in lines:
        if "<footnote>" in line:
            footer_text = line.strip()
            footer_text = re.sub(r'<footnote>(.*?)</footnote>', footer_replace, footer_text, flags=re.DOTALL)
            final_footer_added.append(footer_text)
        else:
            final_footer_added.append(line.strip())
    return final_footer_added

    


# In[ ]:


# def modify_table_tags(lines):
#     # result = []
#     result.append("<tbl>")


# In[ ]:


# def add_tables(lines):
#     result = []
#     start_phrase = f"<field>table.resize"
#     table_lines = []
#     while i < len(lines):
#         line = lines[i].strip()
#         if line.startswith(start_phrase):
#             for j in range(i, len(lines)):
#                 if "<field>" in lines[j]:
#                     table_lines.append(lines[j].strip())
#                     i = j + 1
#                 else:
#                     break
#             modify_table_lines = modify_table_tags(table_lines)
#             result.append(modify_table_lines)
#         else:
#             result.append(line)
#             i += 1
#     return result
        


# In[ ]:


def build_reference_block(lines):
    """
    Processes a set of lines and returns the XML for a research.reference.block
    and the number of lines consumed.
    """
    block = []
    modified_text = []
    reference_text, j = find_r_block_ending(lines)
    block.append("<research.reference.block>")
    for l in reference_text:
        # Check for specific tags and replace them
        # l = l.replace("<field>", "", 1)
        # l = l.replace("</field>", "", 1)
        if "wd.ref.id" in l:
            wd_text = remove_text_between_tags(l,"<wd>")
            modified_text.append(wd_text+ "</wd></ref.text></reference.entry>")
        elif "tk.ref.id" in l:
            tk_text = remove_text_between_tags(l, "<tk>")
            modified_text.append(tk_text + "</tk></ref.text></reference.entry>")
            # modified_text.append(l.replace("tk.ref.id", "<cite type=\"topic.key\">") + "</cite>")
        elif "rc.ref.id" in l:
            rc_text = remove_text_between_tags(l, "<rc>")
            modified_text.append( rc_text + "</rc></ref.text></reference.entry>")
        else:
            modified_text.append(l.strip())
    block.append("\n".join(modified_text))
    block.append("</research.reference.block>")
    return "\n".join(block), j


# In[ ]:


def find_im_ending(lines):
    """
    Find the end of an 'im' block in the lines.
    Returns the index of the end of the block.
    """
    for i, line in enumerate(lines):
        if "<field>im" not in line:
            return i  # Include the closing tag
    return len(lines)  # If no closing tag found, return end of lines


# In[ ]:


import re

def add_images(lines):
    """
    Processes lines to find image tags and returns the modified lines.
    """
    result = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if "<field>im" in line:
            # Find the end of the image block
            im_i = find_im_ending(lines[i:])
            im_block = lines[i:i + im_i]
            im_block_str = "\n".join(im_block).strip()
            # Find all <field>im.id="..."></field> in the image block
            ids_iter = list(re.finditer(r'<field>im\.id="([^"]+)"</field>', im_block_str))
            if not ids_iter:
                print("No image IDs found.")
                exit()
            ids = [m.group(1) for m in ids_iter]

            # Find the first <para ct.id="..."> after the image block
            ct_id = 'UNKNOWN_CT_ID'
            for j in range(i + im_i, len(lines)):
                para_match = re.search(r'<para ct\.id="([^"]+)"', lines[j])
                if para_match:
                    ct_id = para_match.group(1)
                    break

            # Build the output block
            result.append(f'<image.block ct.id="{ct_id}">')
            for ident in ids:
                result.append(f'<image ident="{ident}"/>')
            result.append('</image.block>')

            i += im_i  # Move past the image block
        else:
            result.append(line)
            i += 1
    return result

# You must define find_im_ending for this to work.


# In[ ]:


def add_notes(lines):
    i = 0
    result = []
    while i < len(lines):
        line = lines[i].strip()
        # if "<heading>Notes to Form</heading>" in line or "<trace.deleted Drafter's Note />" in line:
        if ("<heading>Notes to Form</heading>" in line) or ("<trace>Notes to Form</trace>" in line) or ("<heading>Drafter's Note</heading>" in line):
            result.append("<note.block>")
            i += 1
            # Check if next line is a heading
            note_head = None
            if i < len(lines):
                match = re.match(r"<heading>(.*?)</heading>", lines[i].strip())
                if match:
                    note_head = match.group(1)
                    i += 1
            if note_head:
                if "tax notes" in note_head.lower():
                    result.append('<note.group note.head="taxnotes">')
                else:
                    result.append(f'<note.group note.head="none">')
            else:
                # result.append(lines[i].strip())
                if lines[i].strip() != "<research.reference.block>":
                    result.append('<note.group note.head="none">')
            # Collect note lines until <research.reference.block> is found
            while i < len(lines) and lines[i].strip() != "<research.reference.block>":
                if "Drafter's Note" not in lines[i]:
                    result.append(lines[i].strip())
                i += 1
            
            
            result.append("</note.group>")
            # Now add the research reference block (and its content)
            if i < len(lines) and lines[i].strip() == "<research.reference.block>":
                result.append("<research.reference.block>")
                i += 1
                # Collect lines inside the research reference block
                while i < len(lines) and lines[i].strip() != "</research.reference.block>":
                    result.append(lines[i].strip())
                    i += 1
                # Close research.reference.block
                if i < len(lines) and lines[i].strip() == "</research.reference.block>":
                    result.append("</research.reference.block>")
                    i += 1
            result.append("</note.block>")
            # result.append("</form>")  # Add form.unit after note.block - REMOVED: This was causing extra </para> tags
        else:
            result.append(line)
            i += 1
    return result


# In[ ]:


def add_comment_blocks(lines):
    i = 0
    result = []
    while i < len(lines):
        line = lines[i].strip()
        # if "<heading>Notes to Form</heading>" in line or "<trace.deleted Drafter's Note />" in line:
        if ("<heading>Author's Comment</heading>" in line) or ("<trace>Author's Comment</trace>" in line):
            # result.append("<note.block>")
            i += 1
            # Check if next line is a heading
            note_head = None
            if i < len(lines):
                match = re.match(r"<heading>(.*?)</heading>", lines[i].strip())
                if match:
                    note_head = match.group(1)
                    i += 1
            if note_head:
            #     if "tax notes" in note_head.lower():
            #         result.append('<note.group note.head="taxnotes">')
                # else:
                result.append(f'<commentary.note>')

                result.append(f'<head>')
                result.append(f'<name.block>')
                result.append(f'<name>')
                result.append(f'<bold>Author&apos;s Comment</bold>')
                result.append(f'</name>')
                result.append(f'</name.block>')
                result.append(f'</head>')
            # Now add the research reference block (and its content)
            # if i < len(lines) and lines[i].strip() == "<research.reference.block>":
            #     result.append("<research.reference.block>")
            #     i += 1
            #     # Collect lines inside the research reference block
            while i < len(lines) and lines[i].strip() != "<section>":
                result.append(lines[i].strip())
                i += 1
            #     # Close research.reference.block
            #     if i < len(lines) and lines[i].strip() == "</research.reference.block>":
            #         result.append("</research.reference.block>")
            #         i += 1
            result.append("</commentary.note>")
            # result.append("</form>")  # Add form.unit after note.block
        else:
            result.append(line)
            i += 1
    return result


# In[ ]:


def add_items_tags(lines):
    result = []
    pattern = re.compile(r'<heading>(.*?)</heading>')

    for line in lines:
        match = pattern.search(line)
        if match:
            content = match.group(1)
            l_content = content.split(" ")
            if len(l_content) > 1:
                # Replace <heading> and </heading> with <item> and </item>
                new_line = pattern.sub(f'<item.reference.block>\n<item.reference>\n<name.block>\n<label>{l_content[0]}</label>\n<designator>{l_content[1:]}</designator>\n</name.block></item.reference></item.reference.block>', line)
                result.append(new_line)
            else:
                result.append(line)
        else:
            result.append(line)
    return result


# In[ ]:


import re
import json

PREFIX_PATTERNS = [
 (r'^(\d+)\.', 'number'),                # 1.
    (r'^\(([a-z])\)', 'lower_letter'),      # (a)
    (r'^\(([A-Z])\)', 'upper_letter'),      # (A)
    (r'^\((\d+)\)', 'paren_number'),        # (1)
    (r'^\(([ivxlcdm]+)\)', 'roman'),        # (i) - lower roman
    (r'^\(([IVXLCDM]+)\)', 'roman_upper'),  # (I) - upper roman
    (r'^(\d+)\)', 'number_paren'),          # 1)
    (r'^([a-z])\.', 'lower_letter_dot'),    # a.
    (r'^([A-Z])\.', 'upper_letter_dot'),    # A.
    (r'^([a-z])\)', 'lower_letter_paren'),  # a)
    (r'^([A-Z])\)', 'upper_letter_paren'),  # A)
    (r'^([ivxlcdm]+)\.', 'roman_dot'),      # i.
    (r'^([IVXLCDM]+)\.', 'roman_upper_dot'),# I.
    (r'^([ivxlcdm]+)\)', 'roman_paren'),    # i)
    (r'^([IVXLCDM]+)\)', 'roman_upper_paren'), # I)
    (r'^(\d+\.\d+)\.', 'sub_number'),       # 1.1.
    (r'^(\d+\.\d+)\)', 'sub_number_paren'), # 1.1)
]

def get_prefix(text):
    text = text.strip()
    for pat, typ in PREFIX_PATTERNS:
        m = re.match(pat, text)
        if m:
            return typ, m.group(1), text[m.end():].strip()
    return None, None, text

def prefix_depth(prefix_type):
    order = ['number', 'lower_letter', 'paren_number', 'upper_letter', 'roman']
    try:
        return order.index(prefix_type)
    except ValueError:
        return len(order)

def parse_checklist_dynamic(input_text):
    # Split on each ►, reconstruct items
    items = re.split(r'(►)', input_text)
    items = ["".join(items[i:i+2]) for i in range(1, len(items), 2)]
    parsed_items = []
    for item in items:
        # Extract the full <para ...>...</para> block
        m = re.search(r'(<para[^>]*>.*?</para>)', item, re.DOTALL)
        if m:
            para_html = m.group(1)
            # Now extract the <para.text>...</para.text> for prefix detection and text
            m_text = re.search(r'<para\.text>\s*(.*?)\s*</para\.text>', para_html, re.DOTALL)
            if m_text:
                text = m_text.group(1).strip()
                typ, val, body = get_prefix(text)
                # Remove the prefix from para_html too
                para_html_clean = re.sub(
                    r'(<para\.text>\s*)' + re.escape(m_text.group(1)) + r'(\s*</para\.text>)',
                    r'\1' + body + r'\2',
                    para_html, count=1, flags=re.DOTALL
                )
                parsed_items.append({
                    'type': typ,
                    'value': val,
                    'text': body,
                    'para_html': para_html_clean
                })


    root = []
    stack = []

    for itm in parsed_items:
        depth = prefix_depth(itm['type'])
        node = {
            'text': itm['text'],
            'para_html': itm['para_html'],
        }
        if itm['type'] is not None:
            node['prefix'] = itm['value']
        node['children'] = []

        while stack and stack[-1][0] >= depth:
            stack.pop()
        if stack:
            stack[-1][1]['children'].append(node)
        else:
            root.append(node)
        stack.append((depth, node))

    def clean(node):
        res = {}
        if 'prefix' in node:
            res['prefix'] = node['prefix']
        res['text'] =  node['para_html']
        # res['para_html'] = node['para_html']
        if node['children']:
            res['children'] = [clean(child) for child in node['children']]
        return res

    return [clean(n) for n in root]

# For demonstration, usage:
# result = parse_checklist_dynamic(input_text)
# print(json.dumps(result, indent=2))


# In[ ]:


import re
import os


def extract_para_info(text):
    if not text or not isinstance(text, str):
        return '', ''
    ct_id_match = re.search(r'<para\s+ct\.id="([^"]+)"', text)
    para_text_match = re.search(r'<para\.text>(.*?)</para\.text>', text, re.DOTALL)
    ct_id = ct_id_match.group(1) if ct_id_match else ''
    para_text = para_text_match.group(1).strip() if para_text_match else ''
    return ct_id, para_text

def format_designator(prefix):
    if prefix is None:
        return ''
    try:
        int(prefix)
        return prefix
    except Exception:
        return f'({prefix})'

def process_node(node, indent=2):
    IND = ' ' * indent
    lines = []
    if not isinstance(node, dict):
        return ''
    prefix = node.get('prefix')
    ct_id, para_text = extract_para_info(node.get('text', ''))
    lines.append(f"{IND}<list.item>")
    if prefix is not None:
        lines.append(f"{IND}  <name.block>")
        lines.append(f"{IND}    <designator>{format_designator(prefix)}</designator>")
        lines.append(f"{IND}  </name.block>")
    if ct_id or para_text:
        lines.append(f'{IND}  <para ct.id="{ct_id}">')
        lines.append(f'{IND}    <para.text>{para_text}</para.text>')
        lines.append(f'{IND}  </para>')
    children = node.get('children', [])
    item_children = [ch for ch in children if isinstance(ch, dict) and 'prefix' in ch]
    para_children = [ch for ch in children if isinstance(ch, dict) and 'prefix' not in ch]
    if item_children:
        lines.append(f"{IND}  <list list.style=\"para\">")
        for ch in item_children:
            child_output = process_node(ch, indent+4)
            if child_output:
                lines.append(child_output)
        lines.append(f"{IND}  </list>")
    for ch in para_children:
        if isinstance(ch, dict):
            child_ct_id, child_para_text = extract_para_info(ch.get('text', ''))
            if child_ct_id or child_para_text:
                lines.append(f'{IND}  <para ct.id="{child_ct_id}">')
                lines.append(f'{IND}    <para.text>{child_para_text}</para.text>')
                lines.append(f'{IND}  </para>')
    lines.append(f"{IND}</list.item>")
    return '\n'.join(lines)

def convert(json_data):
    output = ['<list list.style="para">']
    for node in json_data:
        node_output = process_node(node, indent=2)
        if node_output:
            output.append(node_output)
    output.append('</list>')
    # return '\n'.join(output)
    return output



# In[ ]:


def add_checklist(input_lines):
    
    headings_done = False
    heading_lines = []
        
    non_heading_lines = []
    # If any line contains "<form ", return as-is
    
    if any("<form " in line for line in input_lines):
        for line in input_lines:
            if not headings_done and "<heading>" in line:
                heading_lines.append(line)
            else:
                headings_done = True
                non_heading_lines.append(line)
        return non_heading_lines, heading_lines


    

    # Separate out initial <heading> lines
    for line in input_lines:
        if not headings_done and "<heading>" in line:
            heading_lines.append(line)
        else:
            headings_done = True
            non_heading_lines.append(line)

    output_lines = []
    collecting = False
    collected_lines = []
    stop_markers = ["Drafter's Note", "<note.block>", "<research.reference.block>", "<form"]

    i = 0
    n = len(non_heading_lines)

    while i < n:
        line = non_heading_lines[i]
        stripped_line = line.strip()

        if not collecting:
            # Skip lines until we find a line that does NOT contain <heading>
            if "<heading>" not in stripped_line:
                # Start collecting from this line
                collecting = True
                # Don't append this line to output yet; collect it
                continue
            else:
                output_lines.append(line)
        else:
            # Check for stop markers
            if any(marker in stripped_line for marker in stop_markers):
                # Process collected lines and append to output
                if collected_lines:
                    output_lines.append('<check.list>')  # Start the form.unit
                    parse = parse_checklist_dynamic("\n".join(collected_lines))
                    processed = convert(parse)
                    output_lines.extend(processed)
                output_lines.append(line)
                output_lines.extend(input_lines[i+1:])
                output_lines.append('</check.list>')  # Close the form.unit
                break
                # collecting = False
                
            else:
                collected_lines.append(line)
        i += 1

    # In case the file ends and we're still collecting
    # if collecting and collected_lines:
    #     parse = parse_checklist_dynamic("\n".join(collected_lines))
    #     processed = convert(parse)
    #     output_lines.extend(processed)

    return output_lines, heading_lines


# In[ ]:





# In[ ]:


def process_x_lines(lines):
    result = []
    for line in lines:
        line = line.strip()
        if 'x.ref.id=' in line:
            # Replace x.ref.id with <cite type="secondaryxref">...</cite>
            line = re.sub(r'<field>x\.ref\.id=(.*)</field>', '<x>', line.strip())
            line = re.sub(r'</para.text></para>', '</x></para.text></para>', line.strip())
            result.append(line)
            # result.append('</cite>')
        elif 'x.ref.id' in line:
            # If it has x.ref.id but not in field, just keep the line
            result.append(line)
        else:
            result.append(line)
    # Append </cite> before the last </para.text> if present, but only if any line has 'secondaryxref'
    # if any('secondaryxref' in l for l in result):
    #     for i in range(len(result) - 1, -1, -1):
    #         if result[i] == '</para.text>':
    #             result.insert(i, '</cite>')
    #             break
    return result


# In[ ]:


#Execution starts here

def process_docx(docx_path):
    # docx_path = r"C:\Users\6122060\Downloads\AIML\XML Track Changes\Chapter conversion\Forms\Bound Volumes--Styled RTF\NYLB\docx_NYLB 30 (revision copy).docx"
    with zipfile.ZipFile(docx_path, 'r') as docx_zip:
        xml_content = docx_zip.read('word/document.xml')
        # Try to read footnotes.xml if it exists
        try:
            footnote_xml_content = docx_zip.read('word/footnotes.xml')
            footnote_tree = etree.fromstring(footnote_xml_content)
        except KeyError:
            footnote_xml_content = None
            footnote_tree = None

    doc_tree = etree.fromstring(xml_content)


    whole_text = extract_full_text_with_footnotes_track(doc_tree, footnote_tree)

    # # Parse the footnotes XML
    footnote_tree = etree.fromstring(xml_content)

    # Pretty print and save to a file
    pretty_footnote_xml = etree.tostring(
        footnote_tree,
        pretty_print=True,
        encoding='utf-8',
        xml_declaration=True
    )

    # with open("temp_files/doc_document_xml.xml", 'wb') as f:
    #     f.write(pretty_footnote_xml)

    # You can now use `raw_text` in another application or write it to a file
    # with open('temp_files/test_doc_iiioutput.txt', 'w', encoding="utf-8") as f:
    #     f.write(whole_text)

    return whole_text


def add_inital_tags(lines, xml_text, i):
    # Adding outline name block
    j=0
    if "Chapter".lower() in lines[i+1].lower():
        remainder_line = lines[i+1].split("Chapter")[-1].strip().split(" ")
        xml_text += f"\n<outline.name.block><label>Chapter</label><designator>{remainder_line[0]}</designator><name>{remainder_line[1]}</name></outline.name.block>"
        i += 1  # Skip the next line as it has been processed

    if "Scope Statement".lower() in lines[i+1].lower():
        xml_text += "\n<scope.statement.block>"
        xml_text += f"\n<para><para.text>{lines[i+2]}</para.text></para>"
        xml_text += "\n</scope.statement.block>"
        i += 2  # Skip the next two lines as they have been processed

    if "Treated Elsewhere".lower() in lines[i+1].lower():
        xml_text += "\n<treated.elsewhere.block>"
        treated_text, index = get_ending_treated(lines[i+2:])
        index = i + 2 + index  # Adjust index to account for the lines processed
        treated_text = process_x_lines(treated_text)
        xml_text += f"\n{("\n".join(treated_text))}"
        xml_text += "\n</treated.elsewhere.block>"
        i = index  # Skip the processed lines
    # print(i)
    if "Research References".lower() in lines[i].lower():
        # xml_text += "\n<research.reference.block>"
        # reference_text, j = find_r_block_ending(lines[i+1:])
        ref_block, j = build_reference_block(lines[i+1:])
        xml_text += "\n" + ref_block
        # xml_text += "\n".join(reference_text)
        # xml_text += "\n</research.reference.block>"

    xml_text += "\n</front>"
    i += j+1 # Skip the next j lines as they have been processed
    CHAPTER_NUMBER=remainder_line[0].split(".")[0].strip()
    return xml_text, i







# In[ ]:



def process_part(part, s_xml_text):
    """Processes a single part (by Roman numeral) and appends XML."""
    first_line = part.split("\n")[0].strip()
    s_xml_text.append("<analytical.level>")
    s_xml_text.append("<front>\n<outline.name.block>")
    s_xml_text.append(f"<designator>{first_line.split('. ')[0]}</designator>")
    s_xml_text.append(f"<name>{' '.join(first_line.split('. ')[1:])}</name>")
    s_xml_text.append("</outline.name.block>\n</front>")

    analytical_blocks = split_analytical_blocks(part.split("\n")[1:])
    s_xml_text.append("<analytical.level.body>")
    if analytical_blocks:
        for designator, lines in analytical_blocks.items():
            process_analytical_block(designator, lines, s_xml_text)
    else:
        print("No analytical blocks found in the part.")
        process_section_blocks(part.split("\n")[1:], s_xml_text)
    s_xml_text.append("</analytical.level.body>")
    s_xml_text.append("</analytical.level>")

def process_analytical_block(designator, lines, s_xml_text):
    """Processes an analytical block and appends XML."""
    s_xml_text.append("<analytical.level>")
    s_xml_text.append("<front>\n<outline.name.block>")
    s_xml_text.append(f"<designator>{designator}</designator>")
    s_xml_text.append(f"<name>{' '.join(lines[0].split('. ')[1:])}</name>")
    s_xml_text.append("</outline.name.block>\n</front>")

    number_sections = split_numeric_sections(lines[1:])
    s_xml_text.append("<analytical.level.body>")
    if number_sections:
        for n_section in number_sections:
            process_numeric_section(n_section, s_xml_text)
    else:
        process_section_blocks(lines[1:], s_xml_text)
    s_xml_text.append("</analytical.level.body>")
    s_xml_text.append("</analytical.level>")

def process_numeric_section(n_section, s_xml_text):
    """Processes a numeric section and appends XML."""
    s_xml_text.append("<analytical.level>")
    s_xml_text.append("<front>\n<outline.name.block>")
    s_xml_text.append(f"<designator>{n_section[0].split('.')[0]}</designator>")
    s_xml_text.append(f"<name>{' '.join(n_section[0].split('.')[1:])}</name>")
    s_xml_text.append("</outline.name.block>\n</front>")
    section_blocks = split_into_sections(n_section[1:])
    s_xml_text.append("<analytical.level.body>")
    process_section_blocks(section_blocks, s_xml_text)
    s_xml_text.append("</analytical.level.body>")
    s_xml_text.append("</analytical.level>")

def process_section_blocks(section_blocks, s_xml_text):
    """Processes section blocks (list of sections) and appends XML."""
    s_xml_text.append("<section.block>")
    for section in section_blocks:
        if not section:
            continue
        process_section(section, s_xml_text)
    s_xml_text.append("</section.block>")

def process_section(section, s_xml_text):
    """Processes a single section and appends XML."""
    designator = section[0].split(". ")[0]
    name = " ".join(section[0].split('. ')[1:])
    s_xml_text.append("<section>")
    s_xml_text.append("<section.front>")
    s_xml_text.append("<outline.name.block>")
    s_xml_text.append("<label>&sect;</label>")
    s_xml_text.append(f"<designator>{designator}</designator>")
    s_xml_text.append(f"<name>{name}</name>")
    s_xml_text.append("</outline.name.block>")

    rest_section = section[1:]
    if len(rest_section) > 1 and "research reference" in rest_section[0].lower():
        ref_block, j = build_reference_block(rest_section[1:])
        s_xml_text.append(ref_block)
        rest_section = rest_section[j+1:]

    research_tags_added, _ = add_research_tags(rest_section)
    para_tags_added = add_para_tags(research_tags_added)
    tagged, form_heading_lines = add_tags(para_tags_added)
    if form_heading_lines:
        s_xml_text.append("<online.view>")
        for heading in form_heading_lines:
            s_xml_text.append(heading.replace("<heading>","<online.view.item>").replace("</heading>","</online.view.item>").strip())
        s_xml_text.append("</online.view>")

    feature_tagged = add_feature_tags(tagged)
    footnote_tagged = add_footnote_tags(feature_tagged)
    image_tagged = add_images(footnote_tagged)
    note_tagged = add_notes(image_tagged)
    comment_tags_added = add_comment_blocks(note_tagged)

    # Checklist handling
    if "Checklist--" in name:
        list_tagged, heading_lines = add_checklist(comment_tags_added)
        if heading_lines:
            s_xml_text.append("<online.view>")
            for heading in heading_lines:
                s_xml_text.append(heading.replace("<heading>","<online.view.item>").replace("</heading>","</online.view.item>").strip())
            s_xml_text.append("</online.view>")
    else:
        list_tagged = note_tagged

    items_tagged = add_items_tags(list_tagged)
    s_xml_text.append("</section.front>")
    s_xml_text.append("<section.body>")
    s_xml_text.append("\n".join(items_tagged))
    s_xml_text.append("</section.body>")
    s_xml_text.append("</section>")


# In[ ]:




# In[ ]:
def handle_entities(final_xml):

    entity_mapping = {
        # '&dblsect;': '__dblsect__',
        # '&mdash;': '__mdash__',
        # '&ldquo;': '__ldquo__',
        # '&rdquo;': '__rdquo__',
        # '&sect;': '__sect__',
        # '&dblpara;': '__dblpara__',
        # '&dollar;': '__dollar__',
        # '&para;': '__para__',
        # '&percnt;': '__percnt__',
        # '&lsqb;': '__lsqb__',
        # '&rsqb;': '__rsqb__',
        # '&hellip;': '__hellip__',
        # '&brace;': '__brace__',
        # '&emsp;': '__emsp__',
        # '&ndash;': '__ndash__',
        # '&bull;': '__bull__',
        # '&ballot;': '__ballot__',
        '§':'',
        '&ss;': '&dblsect;',
        '&s;': '&sect;',
        '&pp;': '&dblpara;',
        '&p;': '&para;',
        '&b;': '&bull;',
        '[': '&lsqb;',
        ']': '&rsqb;',
        '<trace.deleted/><trace>': '<trace>',
        '<finstr>': '<inline.instr>',
        '</finstr>': '</inline.instr>',
        '►' : '',
        '&ldquo;': '',
        '&rdquo;': '',
        ' & ': ' &amp; ',
        '.</rc>':'</rc>.',
        '.</tk>':'</tk>.',
        '.</wd>':'</wd>.',
        '.</x>':'</x>.',
        '--':'<sep/>',
        '&percnt;': '',
        '<br>':'\n',
        '</form>\n</para>':'</form>'
    }

    def replace_entities(text, entity_mapping):
        # Replace all occurrences of entities in the text
        for entity, value in entity_mapping.items():
            text = text.replace(entity, value)
        return text

    decoded_text = replace_entities(final_xml, entity_mapping)
    return decoded_text

def process_chapter_body(second_set_lines, s_xml_text, lines):
    s_xml_text.append("<chapter.body>")

    parts = split_text_by_continuous_roman_numerals(second_set_lines)
    # parts = [parts[1]]  # Assuming you want to process only the second part as per your original code
    if parts:
        for i, part in enumerate(parts, start=1):
            #look for analytical block
            first_line = part.split("\n")[0].strip()
            s_xml_text.append("<analytical.level>")
            s_xml_text.append("<front>\n<outline.name.block>")
            s_xml_text.append(f"<designator>{first_line.split(". ")[0]}</designator>")
            s_xml_text.append(f"<name>{" ".join(first_line.split(". ")[1:])}</name>")
            s_xml_text.append("</outline.name.block>\n</front>")

            analytical_blocks = split_analytical_blocks(part.split("\n")[1:])  # Skip the first line which is the Roman numeral
            s_xml_text.append("<analytical.level.body>")
            if analytical_blocks:
                for designator, lines in analytical_blocks.items():
                    # print("Analytical block found")
                    # s_xml_text.append("<analytical.level.body>")
                    s_xml_text.append("<analytical.level>")
                    s_xml_text.append("<front>\n<outline.name.block>")
                    s_xml_text.append(f"<designator>{designator}</designator>")
                    s_xml_text.append(f"<name>{" ".join(lines[0].split(". ")[1:])}</name>")
                    s_xml_text.append("</outline.name.block>\n</front>")
                    
                    # print(f"Processing analytical block: {designator}")
                    number_section = split_numeric_sections(lines[1:])  # Skip the first line which is the designator
                    
                    if number_section:
                        # print("numeric sections found in analytical block:", designator)
                        # print("Number of numeric sections:", number_section)
                        s_xml_text.append("<analytical.level.body>")
                        
                        for n_section in number_section:
                            # s_xml_text.append("<analytical.level.body>")
                            s_xml_text.append("<analytical.level>")
                            s_xml_text.append("<front>\n<outline.name.block>")
                            s_xml_text.append(f"<designator>{n_section[0].split('.')[0]}</designator>")
                            s_xml_text.append(f"<name>{" ".join(n_section[0].split('.')[1:])}</name>")
                            s_xml_text.append("</outline.name.block>\n</front>")
                            # print(f"Processing section: {section[0]}")
                            # print(f"Lines in section: {len(section)}")
                            print("n_section", n_section)
                            section_blocks = split_into_sections(n_section[1:])
                            # print("Section blocks found:", section_blocks)
                            s_xml_text.append("<analytical.level.body>")
                            s_xml_text.append("<section.block>")
                            for section in section_blocks:
                                if not section:
                                    continue
                                designator = section[0].split(". ")[0]                    
                                
                                # s_xml_text.append("<section.block>")
                                s_xml_text.append("<section>")
                                s_xml_text.append("<section.front>")
                                s_xml_text.append("<outline.name.block>")
                                s_xml_text.append("<label>&sect;</label>")
                                s_xml_text.append(f"<designator>{designator}</designator>")
                                s_xml_text.append(f"<name>{" ".join(section[0].split('. ')[1:])}</name>")
                                s_xml_text.append("</outline.name.block>")
                                print("eSection",section)
                                j=0
                                rest_section = section[1:]
                                if "research reference" in section[1].lower():
                                    ref_block, j = build_reference_block(section[2:])
                                    s_xml_text.append(ref_block)
                                    rest_section = section[j+2:]


                                # print("Section j",rest_section)
                                # Process the section body for research tags
                                research_tags_added, k = add_research_tags(rest_section)

                                # print("Section after research tags:", research_tags_added)
                                #Process the section body for paragraph tags
                                para_tags_added = add_para_tags(research_tags_added)
                                # print("Paragraph tags added:", para_tags_added)
                                
                                #Process the section body for form, signature and table tags
                                tagged, form_heading_lines = add_tags(para_tags_added)
                                if form_heading_lines:
                                    s_xml_text.append("<online.view>")
                                    for heading in form_heading_lines:
                                        s_xml_text.append(heading.replace("<heading>","<online.view.item>").replace("</heading>","</online.view.item>").strip())
                                    s_xml_text.append("</online.view>")

                                feature_tagged = add_feature_tags(tagged) 
                                #Process the section body for footnote tags
                                footnote_tagged = add_footnote_tags(feature_tagged)

                                #Process images
                                image_tagged = add_images(footnote_tagged)

                                #Process note block
                                note_tagged = add_notes(image_tagged)

                                comment_tags_added = add_comment_blocks(note_tagged)

                                #Process checklist block
                                if "Checklist--" in " ".join(section[0].split('. ')[1:]):
                                    list_tagged, heading_lines = add_checklist(comment_tags_added)
                                    
                                    if heading_lines:
                                        s_xml_text.append("<online.view>")
                                        for heading in heading_lines:
                                            s_xml_text.append(heading.replace("<heading>","<online.view.item>").replace("</heading>","</online.view.item>").strip())
                                        s_xml_text.append("</online.view>")
                                        
                                else:
                                    list_tagged = note_tagged
                                
                                items_tagged = add_items_tags(list_tagged)
                                
                                s_xml_text.append("</section.front>")
                                
                                
                                s_xml_text.append("<section.body>")

                                s_xml_text.append("\n".join(items_tagged))
                                s_xml_text.append("</section.body>")
                                
                                s_xml_text.append("</section>")
                            s_xml_text.append("</section.block>")
                            s_xml_text.append("</analytical.level.body>")
                            s_xml_text.append("</analytical.level>")
                        
                        s_xml_text.append("</analytical.level.body>")
                    else:
                        # print("No numeric sections found in analytical block:", designator)
                        section_blocks = split_into_sections(lines[1:])
                        s_xml_text.append("<analytical.level.body>")
                        s_xml_text.append("<section.block>")
                        for section in section_blocks:
                            if not section:
                                continue
                            designator = section[0].split(". ")[0]                    
                            
                            s_xml_text.append("<section>")
                            s_xml_text.append("<section.front>")
                            s_xml_text.append("<outline.name.block>")
                            s_xml_text.append("<label>&sect;</label>")
                            s_xml_text.append(f"<designator>{designator}</designator>")
                            s_xml_text.append(f"<name>{" ".join(section[0].split('. ')[1:])}</name>")
                            s_xml_text.append("</outline.name.block>")
                            print(section)
                            j=0
                            rest_section = section[1:]
                            if "research reference" in section[1].lower():
                                ref_block, j = build_reference_block(section[2:])
                                s_xml_text.append(ref_block)
                                rest_section = section[j+2:]
                                                        # print("j:", j)
                                # print(f"Processing section after reseatch: {section[j+2:]}")
                            


                            # Process the section body for research tags
                            research_tags_added, k = add_research_tags(rest_section)
                            # print("Section after research tags:", research_tags_added)
                            #Process the section body for paragraph tags
                            para_tags_added = add_para_tags(research_tags_added)
                            # print("Paragraph tags added:", para_tags_added)
                            #Process the section body for form, signature and table tags
                            tagged, form_heading_lines = add_tags(para_tags_added)
                            if form_heading_lines:
                                s_xml_text.append("<online.view>")
                                for heading in form_heading_lines:
                                    s_xml_text.append(heading.replace("<heading>","<online.view.item>").replace("</heading>","</online.view.item>").strip())
                                s_xml_text.append("</online.view>")

                            feature_tagged = add_feature_tags(tagged) 
                            
                            #Process the section body for footnote tags
                            footnote_tagged = add_footnote_tags(feature_tagged)

                            #Process images
                            image_tagged = add_images(footnote_tagged)

                            #Process note block
                            note_tagged = add_notes(image_tagged)

                            comment_tags_added = add_comment_blocks(note_tagged)

                            #Process checklist block
                            if "Checklist--" in " ".join(section[0].split('. ')[1:]):
                                list_tagged, heading_lines = add_checklist(comment_tags_added)

                                if heading_lines:
                                    s_xml_text.append("<online.view>")
                                    for heading in heading_lines:
                                        s_xml_text.append(heading.replace("<heading>","<online.view.item>").replace("</heading>","</online.view.item>").strip())
                                    s_xml_text.append("</online.view>")
                            else:
                                list_tagged = note_tagged

                            items_tagged = add_items_tags(list_tagged)
                            
                            
                            s_xml_text.append("</section.front>")
                            
                            s_xml_text.append("<section.body>")
                            s_xml_text.append("\n".join(items_tagged))
                                
                            s_xml_text.append("</section.body>")
                            
                            s_xml_text.append("</section>")
                        s_xml_text.append("</section.block>")
                        s_xml_text.append("</analytical.level.body>")
                    s_xml_text.append("</analytical.level>")
                    # s_xml_text.append("</analytical.level.body>")
                    
            
            s_xml_text.append("</analytical.level.body>")
            s_xml_text.append("</analytical.level>")
        else:
            print("No analytical blocks found in the part.")
            section_blocks = split_into_sections(lines[1:])
            s_xml_text.append("<analytical.level.body>")
            s_xml_text.append("<section.block>")
            for section in section_blocks:
                if not section:
                    continue
                designator = section[0].split(". ")[0]                    
                
                s_xml_text.append("<section>")
                s_xml_text.append("<section.front>")
                s_xml_text.append("<outline.name.block>")
                s_xml_text.append("<label>&sect;</label>")
                s_xml_text.append(f"<designator>{designator}</designator>")
                s_xml_text.append(f"<name>{" ".join(section[0].split('. ')[1:])}</name>")
                s_xml_text.append("</outline.name.block>")
                print(section)
                j=0
                rest_section = section[1:]
                if "research reference" in section[1].lower():
                    ref_block, j = build_reference_block(section[2:])
                    s_xml_text.append(ref_block)
                    rest_section = section[j+2:]
                                            # print("j:", j)
                    # print(f"Processing section after reseatch: {section[j+2:]}")
                


                # Process the section body for research tags
                research_tags_added, k = add_research_tags(rest_section)
                # print("Section after research tags:", research_tags_added)
                #Process the section body for paragraph tags
                
                para_tags_added = add_para_tags(research_tags_added)
                # print("Paragraph tags added:", para_tags_added)
                #Process the section body for form, signature and table tags
                tagged, form_heading_lines = add_tags(para_tags_added)
                if form_heading_lines:
                    s_xml_text.append("<online.view>")
                    for heading in form_heading_lines:
                        s_xml_text.append(heading.replace("<heading>","<online.view.item>").replace("</heading>","</online.view.item>").strip())
                    s_xml_text.append("</online.view>")

                feature_tagged = add_feature_tags(tagged) 
                
                #Process the section body for footnote tags
                footnote_tagged = add_footnote_tags(feature_tagged)

                #Process images
                image_tagged = add_images(footnote_tagged)

                #Process note block
                note_tagged = add_notes(image_tagged)

                comment_tags_added = add_comment_blocks(note_tagged)

                #Process checklist block
                if "Checklist--" in " ".join(section[0].split('. ')[1:]):
                    list_tagged, heading_lines = add_checklist(comment_tags_added)

                    if heading_lines:
                        s_xml_text.append("<online.view>")
                        for heading in heading_lines:
                            s_xml_text.append(heading.replace("<heading>","<online.view.item>").replace("</heading>","</online.view.item>").strip())
                        s_xml_text.append("</online.view>")
                else:
                    list_tagged = note_tagged

                items_tagged = add_items_tags(list_tagged)
                
                
                s_xml_text.append("</section.front>")
                
                s_xml_text.append("<section.body>")
                s_xml_text.append("\n".join(items_tagged))
                    
                s_xml_text.append("</section.body>")
                
                s_xml_text.append("</section>")
            s_xml_text.append("</section.block>")
            s_xml_text.append("</analytical.level.body>")

    else:
        print("The Roman numerals are not continuous. No sections were extracted.")

    s_xml_text.append("</chapter.body>")
    s_xml_text.append("</chapter>")
    return s_xml_text



def rtf_to_docx(rtf_path, docx_path):
    pythoncom.CoInitialize()
    rtf_path = os.path.abspath(rtf_path)
    docx_path = os.path.abspath(docx_path)
    print(f"RTF Path: {rtf_path}")
    print(f"DOCX Path: {docx_path}")
    if not os.path.exists(rtf_path):
        raise FileNotFoundError(f"File not found: {rtf_path}")
    time.sleep(0.2)  # Optional: Give time for disk flush if just saved
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(rtf_path)
        doc.SaveAs(docx_path, FileFormat=16)
        doc.Close()
    except Exception as e:
        raise RuntimeError(f"Failed to convert: {e}")
    finally:
        word.Quit()

# if "__main__" == __name__:
#     input_folder = r".\Input"
#     output_folder = r".\Output"

#     for filename in os.listdir(input_folder):
#         if filename.lower().endswith(".docx"):
#             docx_path = os.path.join(input_folder, filename)
#             whole_text = process_docx(docx_path)
#             lines = whole_text.split('\n')

#             for i, line in enumerate(lines):
#                 if "<field>" in line:
#                     break        

#             xml_text = lines[i].split("</field>")[-1].strip()
#             xml_text += "\n<chapter>"

#             metadata_text = extract_text_between_tags(lines[i+1])[0]
#             if metadata_text.startswith("ch.rh"):
#                 metadata_value = metadata_text.split("=")[1].replace('"', '').replace("'", "").strip()
#                 xml_text += f"\n<metadata.block><metadata field=\"right.running.head\"><value>{metadata_value}</value></metadata></metadata.block>"
#             xml_text += "\n<front>"

#             xml_text, i = add_inital_tags(lines, xml_text, i)
#             second_set_lines = lines[i:]  
#             s_xml_text = [] 
#             print(xml_text)
#             s_xml_text = process_chapter_body(second_set_lines, s_xml_text)

#             final_xml = xml_text + '\n' + "\n".join(s_xml_text)

#             entities_handled = handle_entities(final_xml)

#             output_filename = os.path.splitext(filename)[0] + ".txt"
#             output_path = os.path.join(output_folder, output_filename)
#             with open(output_path, 'w', encoding="utf-8") as f:
#                 f.write(entities_handled)

if __name__ == "__main__":
    # Import your main conversion functions
    # from your_module import process_docx, handle_entities

    st.set_page_config(
        page_title="Track Changes RTF/DOCX to XML Converter",
        page_icon="📄",  # Professional document icon
        layout="wide",
        initial_sidebar_state="collapsed",  # Sidebar collapsed by default
    )

    # Custom CSS for a professional, clean look
    st.markdown("""
        <style>
        body, .reportview-container {
            background: #f7f7f7;
            color: #222;
            font-family: "Segoe UI", "Arial", sans-serif;
        }
        .sidebar .sidebar-content {
            background: #f2f2f2;
        }
        .stButton>button, .stDownloadButton>button {
            background-color: #ff9800;
            color: white;
            border-radius: 4px;
            font-size: 16px;
            font-weight: 500;
            padding: 0.4em 1.5em;
            border: none;
            transition: background 0.2s;
        }
        .stButton>button:hover, .stDownloadButton>button:hover {
            background-color: #fb8c00;
        }
        h1, h2, h3, h4 {
            color: #222;
            font-family: "Segoe UI", "Arial", sans-serif;
            font-weight: 600;
        }
        .stMarkdown {
            color: #444;
        }
        .status-ok {
            color: #388e3c;
            font-weight: 500;
        }
        .status-fail {
            color: #d32f2f;
            font-weight: 500;
        }
        .file-table td, .file-table th {
            padding: 0.5em 1em;
            font-size: 15px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("Track Changes RTF/DOCX → XML Converter")
    st.markdown(
        """
        <h4>Convert your Word/RTF files with tracked changes into structured XML using AI.</h4>
        <p>Upload multiple files. Each will be processed when you click the Run button.</p>
        """,
        unsafe_allow_html=True
    )

    uploaded_files = st.file_uploader(
        "Upload RTF or DOCX files",
        type=["docx", "rtf"],
        accept_multiple_files=True,
        help="Supports multiple files with track changes."
    )

    # Add the Run button
    run_conversion = st.button(
        "🚀 Run Conversion", 
        disabled=not uploaded_files,
        help="Click to start processing the uploaded files"
    )

    # Only process files when the button is clicked
    if uploaded_files and run_conversion:
        st.markdown("<h4>Processing Results</h4>", unsafe_allow_html=True)
        results_table = []
        for idx, uploaded_file in enumerate(uploaded_files):
            with st.spinner(f"Processing file {idx+1}/{len(uploaded_files)}: {uploaded_file.name}"):
                temp_dir = "temp_files"
                temp_folder = "temp_folder"  # Folder for converted DOCX files from RTF

                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                if not os.path.exists(temp_folder):
                    os.makedirs(temp_folder)

                temp_file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                # Ensure file is written and closed before next step
                temp_file_path = os.path.abspath(temp_file_path)
                print(f"Saved file to: {temp_file_path}")
                assert os.path.exists(temp_file_path), f"File does not exist after writing: {temp_file_path}"
                
                file_ext = os.path.splitext(uploaded_file.name)[1].lower()

                if file_ext == ".rtf":
                    # Store converted DOCX in temp_folder
                    converted_docx_path = os.path.join(
                        temp_folder,
                        os.path.splitext(uploaded_file.name)[0] + ".docx"
                    )
                    try:
                        rtf_to_docx(temp_file_path, converted_docx_path)
                        docx_path = converted_docx_path
                    except Exception as e:
                        st.markdown(
                            f"<div class='status-fail'>❌ {uploaded_file.name} failed to convert RTF to DOCX: {e}</div>",
                            unsafe_allow_html=True
                        )
                        continue  # Skip this file
                else:
                    # For DOCX uploads, process from temp_dir
                    docx_path = temp_file_path

                try:
                    whole_text = process_docx(docx_path)
                    lines = whole_text.split('\n')

                    for i, line in enumerate(lines):
                        if "<field>" in line:
                            break        

                    xml_text = lines[i].split("</field>")[-1].strip()
                    xml_text += "\n<chapter>"

                    metadata_text = extract_text_between_tags(lines[i+1])[0]
                    if metadata_text.startswith("ch.rh"):
                        metadata_value = metadata_text.split("=")[1].replace('"', '').replace("'", "").strip()
                        xml_text += f"\n<metadata.block><metadata field=\"right.running.head\"><value>{metadata_value}</value></metadata></metadata.block>"
                    xml_text += "\n<front>"

                    xml_text, i = add_inital_tags(lines, xml_text, i)
                    second_set_lines = lines[i:]  
                    s_xml_text = [] 
                    print(xml_text)
                    s_xml_text = process_chapter_body(second_set_lines, s_xml_text, lines)

                    final_xml = xml_text + '\n' + "\n".join(s_xml_text)

                    entities_handled = handle_entities(final_xml)

                    st.markdown(
                        f"<div class='status-ok'>✅ {uploaded_file.name} converted successfully.</div>",
                        unsafe_allow_html=True
                    )
                    with st.expander(f"Preview: {uploaded_file.name}", expanded=False):
                        st.code(final_xml[:5000], language="xml")
                    st.download_button(
                        label=f"Download XML for {uploaded_file.name}",
                        data=final_xml,
                        file_name=os.path.splitext(uploaded_file.name)[0] + ".txt",
                        mime="text/plain",
                        key=f"download_{uploaded_file.name}"
                    )
                except Exception as e:
                    st.markdown(
                        f"<div class='status-fail'>❌ {uploaded_file.name} failed: {e}</div>",
                        unsafe_allow_html=True
                    )
    elif uploaded_files and not run_conversion:
        st.info(f"📁 {len(uploaded_files)} file(s) uploaded. Click 'Run Conversion' to process them.", icon="📄")
    else:
        st.info("Please upload one or more RTF or DOCX files.", icon="📄")


# if __name__ == "__main__":
#     sys.argv = ['streamlit', 'run', 'app.py']
#     sys.exit(stcli.main())

