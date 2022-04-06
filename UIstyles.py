import os, argparse, sys
import re
from shutil import copyfile


DEBUG = 0
LINES = 1
FCALL = 1
CCALL = 1


# RegEx patterns
number 	= r'(-?\d+(\.\d\d\d\d\d)?)'
string 	= r'"?([\w\s\d\\_\-$]*)"?'

key 	= r'(\w+) = ' 
brace 	= r'\t*({)\n'

# Single-line
numberPattern = re.compile(r'^\t*' + key + number + ',\n')
stringPattern = re.compile(r'^\t*' + key + string + ',\n')

numEntryPattern = re.compile(r'^\t*' + number + ',\n')
strEntryPattern = re.compile(r'^\t*' + string + ',\n')
# entryPattern  = re.compile(r'^\t*(\w+) = (' + string + '|' + number + '),\n')

# Two-line
listPattern   = re.compile(r'^\t*(\w+) =  \n\t*({)\n')
widgetPattern = re.compile(r'^\t*( \n)\t*({)\n')



def findMatchingBrace(lines, start):
	length = len(lines)
	braceCount = 0
	i = start

	while i < length:

		if "{" in lines[i]:
			braceCount += 1

		elif "}" in lines[i]:
			braceCount -= 1
			if braceCount == 0:
				return i

		i += 1

	raise Exception(f"Couldn't find matching brace starting at line {start+1}")
	return -1


def printLine(i, line):
	print(f"[{i+1}]\t{line}", end='')

def printConsecLine(i, line):
	if DEBUG and LINES:
		printLine(i, line)
		# if line == "\tWidgets =  \n": raise Exception(f"E @{i+1}")
		if i != printConsecLine.counter+1:
			print("Warning: Non consecutive lines")
		printConsecLine.counter = i
printConsecLine.counter = 0



class List():
	def __init__(self, lines, start, parent=None):
		if DEBUG and CCALL: print("New List")

		if not (match := listPattern.match(''.join(lines[start:start+2]))):
			printConsecLine(start, ''.join(lines[start:start+2]))
			raise Exception("Invalid list starting line")

		self.attrs 		= {}
		self.parent 	= parent
		self.name 		= match[1]
		self.start 		= start
		self.end 		= findMatchingBrace(lines, start)
		self.indentLvl	= match.start(1)			# Number of tabs in front of opening brace
		self.indent 	= '\t' * (self.indentLvl+1) # String for formatting list contents

		self.parse(lines, start + 2, self.end)  # skip the opening brace line


	def parse(self, lines, start, end):
		if DEBUG and FCALL: print("parse")
		i = start
		while i < end:
			printConsecLine(i, lines[i])

			# Number attribute
			if attrMatch := numberPattern.match(lines[i]):
				self.addAttr(attrMatch[1], float(attrMatch[2]))

			# String attribute
			elif attrMatch := stringPattern.match(lines[i]):
				self.addAttr(attrMatch[1], attrMatch[2])

			# Multi-line attribute
			elif attrMatch := listPattern.match(''.join(lines[i:i+2])):

				listEnd = findMatchingBrace(lines, i)

				self.parseList(lines, i, listEnd, attrMatch[1])

				i = listEnd
				printConsecLine(i, lines[i])

			# Error
			else:
				print(f"Unrecognised attribute @{i+1} ")
				sys.exit()
				break

			i += 1


	def parseList(self, lines, listStart, listEnd, attrName):
		printConsecLine(listStart+1, lines[listStart+1])
		if DEBUG and FCALL:print("parseList")

		# Empty list
		if "}," in lines[listStart+2]:
			self.addAttr(attrName, None)
			return

		j = listStart + 2 # Skip the list name and the opening brace
		while j < listEnd:

			# Number list entry
			if valueMatch := numEntryPattern.match(lines[j]):
				self.addAttr(attrName, float(valueMatch[1]), asList=True)

				printConsecLine(j, lines[j])

			# String list entry
			elif valueMatch := strEntryPattern.match(lines[j]):
				self.addAttr(attrName, valueMatch[1], asList=True)

				printConsecLine(j, lines[j])

			# A new Widget
			elif widgetPattern.match("".join(lines[j:j+2])):
				printConsecLine(j, lines[j])
				printConsecLine(j+1, lines[j+1])

				child = Widget(lines, j, attrName, self)
				self.addAttr(attrName, child, asList=True)
				j = child.end

				printConsecLine(j, lines[j])

			# A new List 
			# elif listPattern.match( "".join(lines[j:j+2])) or \
			# 	 entryPattern.match("".join(lines[j:j+2])):
			elif '=' in lines[j]:
				# If '=' is present then it's either a single line attribute
				# or another list. In both cases we want to create a new list 
				# object and let it parse these lines instead. 

				# Create a new List instance which will parse itself
				childList = List(lines, listStart, self)
				self.addAttr(attrName, childList)

				j = childList.end

			# Error
			else:
				printConsecLine(j, lines[j])
				print(f"Unrecognised list entry @{j+1}:")
				sys.exit()
				break

			j += 1


	def addAttr(self, key, value, asList=False):
		if key in self.attrs:
			if isinstance(self.attrs[key], list):	self.attrs[key].append(value)
			else:									self.attrs[key] = [self.attrs[key], value]
		else:
			if asList:								self.attrs[key] = [value]
			else:									self.attrs[key] = value
		# if key in self.attrs:	self.attrs[key].append(value)
		# else:					self.attrs[key] = [value]



	# print(f"{key}: - {issubclass(type(value), List)}")
	# def searchByAttrKey
	# def searchByAttrName
	def searchAttr(self, attrKey, attrName):
		if DEBUG: print("Searching...")
		results = []

		for key, value in self.attrs.items():
			if key == attrKey:
				if issubclass(type(value), List):
					if value.name == attrName:
						results.append(value)
					results.extend(value.searchAttr(attrKey, attrName))

			elif isinstance(value, list):
				for item in value:
					if issubclass(type(value), List):
						results.extend(value.searchAttr(attrKey, attrName))

			elif issubclass(type(value), List):
				results.extend(value.searchAttr(attrKey, attrName))

		return results

	def search(self, rule):
		results = []
		for key, value in self.attrs.items():
			# Check for match
			if rule(key, value):
				results.append(value)

			# Search children
			if issubclass(type(value), List):
				results.extend(value.search(rule))

			elif isinstance(value, list):
				for item in value:
					if rule(key, item):
						results.append(item)


					if issubclass(type(item), List):
						results.extend(item.search(rule))

		return results


	def write(self, file):
			# Opening/Closing brace and the list name
			indent = '\t' * self.indentLvl

			file.write(f"{indent}{self.name} =  \n")
			file.write(f"{indent}{{\n")

			self.writeAttrs(file)

			file.write(f"{indent}}},\n")

	def writeAttrs(self, file):

		for key, value in self.attrs.items():
			if isinstance(value, list):
				file.write(f"{self.indent}{key} =  \n")
				file.write(f"{self.indent}{{\n")

				for item in value: 
					if issubclass(type(item), List):
						item.write(file)
					else:
						# print(f"{key}: {type(item)}")
						file.write(f"{self.indent}\t{self.formatAttr(item, key)},\n")

				file.write(f"{self.indent}}},\n")

			elif issubclass(type(value), List):
				value.write(file)

			elif value is None:
				# If none print the list name and braces
				file.write(f"{self.indent}{key} =  \n")
				file.write(f"{self.indent}{{\n")
				file.write(f"{self.indent}}},\n")

			else:
				file.write(f"{self.indent}{key} = {self.formatAttr(value, key)},\n")

	def formatAttr(self, value, key):
		if isinstance(value, float):
			if (value % 1) == 0:	return f"{value:1.0f}" # Whole numbers
			else: 					return f"{value:1.5f}"

		elif isinstance(value, str):
			if value == 'true' or value == 'false':	return value
			else:									return f"\"{value}\""

		elif value == None:
			return ''

		else:
			return 'ERR'



	def valid(self):
		return 'type' in self.attrs

	def hasName(self):
		return 'name' in self.attrs

	def hasAttr(self, attr):
		return all(map(lambda x: x in self.attrs, attr))

	def __setitem__(self, key, value):
		self.attrs[key] = value

	def __getitem__(self, key):
		return self.attrs[key]

	def __delitem__(self, key):
		del self.attrs[key]

	def __repr__(self):
		prefix = "W" if type(self) is Widget else "L"

		if 'name' in self.attrs:
			name = self.attrs['name']
		elif self.hasAttr(['position', 'size']): #and self.attrs['type'] == "Rectangle":
			name = self.name + " [%g,%g|%gx%g]" %  (float(self.attrs['position'][0]),
													float(self.attrs['position'][1]),
													float(self.attrs['size'][0]),
													float(self.attrs['size'][1]))
		else:
			name = self.name

		return f"{prefix}: {name} ({self.start+1}|{self.end-self.start}|{self.indentLvl})"

	def __str__(self):
		string = self.__repr__()

		string += f" Attributes:{len(self.attrs)}"

		if 'Children' in self.attrs:
			if isinstance(self.attrs['Children'], list):
				childCount = len(self.attrs["Children"])
			elif self.attrs['Children'] != None:
				childCount = 1

			string += f" Children:{childCount}"

		# Print Attributes
		if len(self.attrs) <= 32:
			string += "\n"
			for key, value in self.attrs.items():

				if key == 'Children':
					string += f"{key}: \n"
					for child in value:
						string += '\t' + child.__repr__() + '\n'

				elif isinstance(value, Widget) or \
					isinstance(value, List):
					objectStr = value.__str__()
					string += key + ": " + objectStr.replace("\n", "\n\t")
					string = string[:-1]

				else:
					string += f"{key}: {value}\n"

		return string

class Widget(List):
	def __init__(self, lines, start, attrName, parent):
		if DEBUG and CCALL: print("New Widget")

		if not (match := widgetPattern.match(''.join(lines[start:start+2]))):
			printConsecLine(start, ''.join(lines[start:start+2]))
			raise Exception(f"Invalid widget starting line:{start}")


		self.attrs 		= {}
		self.parent 	= parent
		self.name 		= attrName
		self.start 		= start
		self.end 		= findMatchingBrace(lines, start)
		self.indentLvl 	= match.start(1)
		self.indent 	= '\t' * (self.indentLvl + 1)

		self.parse(lines, start + 2, self.end) # skip the opening brace line

		if 'name' in self.attrs:
			self.name = self.attrs['name']
		elif 'type' in self.attrs:
			self.name = self.attrs['type']

		# if not self.hasEssntials(): print(f"Widget {self.__repr__()} missing essential attributes")

	def write(self, file):
			# Opening/Closing brace indent
			indent = '\t' * self.indentLvl

			file.write(f"{indent} \n")
			file.write(f"{indent}{{\n")

			self.writeAttrs(file)

			file.write(f"{indent}}},\n")


	def hasEssntials(self):
		return self.hasAttr(['type', 'size', 'position'])

class Screen(Widget):
	def __init__(self, filePath, outputName):
		self.indentLvl = 0
		self.indent = '\t'

		if match := re.match(r"([\w\s_-]+)\.screen", os.path.basename(filePath)):
			self.name = match[1]
		else:
			raise Exception("Invalid screen file name")

		self.filePath = filePath
		self.outputName = outputName

		# Make a backup 
		# copyfile(filePath, outputName);

		self.openScreen(filePath)


	def openScreen(self, filePath):
		with open(filePath) as file:
			self.lines = file.readlines()
			# print(stringPattern.match(self.lines[6]))

		self.length = len(self.lines)
		self.end = self.length - 1
		self.start = 0

		if self.lines[0] == "Screen =  \n" and \
		   self.lines[1] == "{\n":

			print(f"Looks good so far... \n")

			# Display first few lines
			for i in range(4):
				printLine(i, self.lines[i])

			print("...")
			print(f"Scanning {self.length} lines...")
		else:
			print(self.lines[0])
			print("Doesn't look like a screen file...")
			sys.exit()

		self.scanLines(self.lines)

	def scanLines(self, lines):

		line = self.start
		self.attrs = {}
		while line < self.length:
			printConsecLine(line, self.lines[line])

			lst = List(self.lines, line, self)
			self.attrs[lst.name] = lst
				# print("Fail")

			line = lst.end + 1

		if len(self.attrs) == 2:
			if 'Screen'   not in self.attrs:
				print("Warning: 'Screen' missing")

			if 'ToolInfo' not in self.attrs:
				print("Warning: 'ToolInfo' missing")



	def findWidget(self, widget):
		return self.searchAttr('widget', widget)



	def write(self, outputPath):
		with open(outputPath, 'w') as file:
			# Opening/Closing brace indent
			indent = '\t' * self.indentLvl

			for key, section in self.attrs.items():
				# Screen object should only contain Lists (Screen & ToolInfo)
				file.write(f"{key} =  \n")
				file.write(f"{{\n")

				section.writeAttrs(file)

				file.write(f"}}\n")


	def findAttrByKey(self, attrKey): 
		def isKeyMatch(key, value):
			if key == attrKey: 	return True
			else:				return False

		return self.search(isKeyMatch)

	def findAttrWithName(self, name):
		def isNameMatch(key, value):
			if issubclass(type(value), List) and value.hasName() and \
			value['name'] == name: 	
				return True
			else:
				return False

		return self.search(isNameMatch)



	def __repr__(self):
		prefix = "Screen"
		name = self.name
		return f"{prefix}: {name} ({self.start+1}-{self.end+1})"

	def __str__(self):
		return self.__repr__() + '\n' + str(self.attrs)




directory = r"/home/mfomenko/Desktop/UIstyles"
screenName = "feral_command_branch"
outputName = "test_result"
filePath = os.path.join(directory, screenName + ".screen")
outputPath = os.path.join(directory, outputName + ".screen")

if __name__ == "__main__":
	S = Screen(filePath, outputPath)

	print()
	print(S)
	print()
	print(S.attrs['Screen']['Widgets'])
	print()
	print(S.attrs['Screen']['Widgets']['Children'][0])
	rule = lambda key, value: (value['name'] == 'upgrade_00_btn_2') if issubclass(type(value), List) and value.hasAttr('name') else False
# key == "Widgets" and
	# print(S.search(rule))
	print(S.findAttrWithName('upgrade_01_btn_al_arm')[0])

	print(S.hasAttr(['name', 'size']))
	S.write(S.outputName)