import re


# RegEx patterns
number 	= r'(-?\d+(\.\d\d\d\d\d)?)'
string 	= r'"?([ !#-~]*)"?' # Any printable char except double quotes

start	= r'^\t*' # Leading white space
key		= r'(\w+) = '
brace	= r'^\t*{\n'


# Compiled patterns

# Single-line
numberPattern = re.compile(start + key + number + ',\n')
stringPattern = re.compile(start + key + string + ',\n')

numEntryPattern = re.compile(start + number + ',\n')
strEntryPattern = re.compile(start + string + ',\n')

# Multi-line
listPattern   = re.compile(r'(?m)' + start + key + '( \n)' + brace)
widgetPattern = re.compile(r'(?m)' + start +       '( \n)' + brace)