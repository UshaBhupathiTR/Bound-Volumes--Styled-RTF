import pandas as pd

#read a text file
with open("C:\\Users\\6122060\\Downloads\\doc_NYLB 32 (revision copy) (1).txt", "r", encoding="utf-8") as file:
    content = file.read()

with open("C:\\Users\\6122060\\Downloads\\doc_NYLB 32_up.txt", "w", encoding="utf-8") as file:
    file.write(content.replace('\n', ''))