import os, sys
import re
import weakref





################################################################################
#									GLOBALS
################################################################################

DEFAULT_LOCALE_PATH=r"/home/mfomenko/UIeditor/BIA/Root/CoH/Locale/English"


DEBUG = 0	# Toggle for all Debug output
LINES = 1	# Print contents of lines as they are being processed
FCALL = 0	# Print names of parsing functions when they are being called
CCALL = 0	# Print names of classes when they are being created


# RegEx patterns
number 	= r'(-?\d+(\.\d\d\d\d\d)?)'
string 	= r'"?([ !#-~]*)"?' # Any printable char except double quotes

start	= r'^\t*' # Leading white space
key		= r'(\w+) = '
brace	= r'^\t*{\n'

# Single-line
numberPattern = re.compile(start + key + number + ',\n')
stringPattern = re.compile(start + key + string + ',\n')

numEntryPattern = re.compile(start + number + ',\n')
strEntryPattern = re.compile(start + string + ',\n')

# Two-line
listPattern   = re.compile(r'(?m)' + start + key + '( \n)' + brace)
widgetPattern = re.compile(r'(?m)' + start +       '( \n)' + brace)

#									GLOBALS





################################################################################
#									FUNCTIONS
################################################################################

def lNum(i): return i + 1 # Convert line index to line number

def findMatchingBrace(lines, start):
	length = len(lines)
	braceCount = 0
	i = start
	indentLvlStack = []
	openingBrace = re.compile(r'^\t*({)')
	closingBrace = re.compile(r'^\t*(})')

	while i < length:

		if match := openingBrace.match(lines[i]):
			indentLvlStack.append(match.start(1))
			braceCount += 1

		elif match := closingBrace.match(lines[i]):
			if (match.start(1) != indentLvlStack.pop()):
				print(f"Funky looking brace at line {lNum(i)}")

			braceCount -= 1
			if braceCount == 0:
				return i

		i += 1

	errMsg = f"Couldn't find matching brace starting at line {lNum(start)}\n"
	raise Exception(errMsg)
	return -1


def printLine(i, line):
	print(f"[{lNum(i)}]\t{line}", end='')

def printConsecLine(i, line):
	if DEBUG and LINES:
		printLine(i, line)

		if i != printConsecLine.counter+1:
			warning = "Non consecutive lines"
			warning += f" {lNum(printConsecLine.counter)}->{lNum(i)}\n"
			raise Exception(warning)
			print(f"Warning: {warning}")

		printConsecLine.counter = i
printConsecLine.counter = -1

def dispValue(value):
	if type(value) is float:
		if (value % 1) == 0:	return f"{value:g}" # Whole numbers
		else: 					return f"{value:1.3f}"
	else:
		return value

#									FUNCTIONS






################################################################################
#									CLASSES
################################################################################

class List():
	strings = []
	IDs = []
	def __init__(self, parent=None, key=None, lines=None, start=None):
		self.attrs 	= {}
		self.parent = parent
		self.key 	= key # The key under which this instance is stored in the parents dictionary

		if None not in (lines, start):
			self.parseSelf(lines, start)
			self.parsed = True

		elif key is not None:
			self.parsed = False

		else:
			print(bool(lines), start, repr(parent), key)
			print()
			raise Exception("Insufficient arguments passed")


	def __setitem__(self, key, value):	self.attrs[key] = value
	def __getitem__(self, key):			return self.attrs[key]
	def __delitem__(self, key):			del self.attrs[key]
	def __contains__(self, key):		return key in self.attrs


# Parsing screen files
	def parseSelf(self, lines, start):
		if DEBUG and CCALL: print(f"New List @{lNum(start)}")

		if not (match := listPattern.match(''.join(lines[start:start+2]))):
			printLine(start,   lines[start])
			printLine(start+1, lines[start+1])
			raise Exception("Invalid list starting line")

		self.key 		= match[1]
		self.start 		= start
		self.end 		= findMatchingBrace(lines, start)
		self.indentLvl	= match.start(1)			# Number of tabs in front of opening brace
		self.indent 	= '\t' * (self.indentLvl+1) # String for formatting attribute list

		self.parse(lines, start + 2, self.end)  # skip the opening brace line

		if   'name' in self: self.dispName = self['name']
		else:				 self.dispName = self.key 


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
				print(f"Unrecognised attribute @{lNum(i)} ")
				sys.exit()
				break

			i += 1


	def parseList(self, lines, listStart, listEnd, listName):
		printConsecLine(listStart+1, lines[listStart+1])
		if DEBUG and FCALL: print("parseList")

		# Empty list
		if "}," in lines[listStart+2]:
			self.addAttr(listName, None)
			return

		j = listStart + 2 # Skip the list name and the opening brace
		while j < listEnd:

			# Number list entry
			if valueMatch := numEntryPattern.match(lines[j]):
				self.addAttr(listName, float(valueMatch[1]), asList=True)

				printConsecLine(j, lines[j])

			# String list entry
			elif valueMatch := strEntryPattern.match(lines[j]):
				self.addAttr(listName, valueMatch[1], asList=True)

				printConsecLine(j, lines[j])

			# Widget list entry (Widgets are always contained in a list)
			elif widgetPattern.match("".join(lines[j:j+2])):
				printConsecLine(j, lines[j])
				printConsecLine(j+1, lines[j+1])

				child = Widget(self, listName, lines, j)
				self.addAttr(listName, child, asList=True)
				j = child.end

				printConsecLine(j, lines[j])

			# A new List
			elif '=' in lines[j]:
				# If '=' is present then it's either a single line attribute
				# or another List. In both cases we want to create a new List
				# object and let it parse these lines instead.

				# Create a new List instance which will parse itself
				childList = List(self, listName, lines, listStart)
				self.addAttr(listName, childList)

				break

			# Error
			else:
				printConsecLine(j, lines[j])
				print(f"Unrecognised list entry @{lNum(j)}:")
				sys.exit()
				break

			j += 1



# Utility methods
	def getScreen(self):
		node = self

		while(node.parent): node = node.parent

		if not type(node) is Screen: raise Exception("Root is not a Screen")

		return node

	def hasType(self):
		return 'type' in self

	def hasName(self):
		return 'name' in self

	def hasAttrs(self, attrs):
		return all(map(lambda x: x in self, attrs))




# Searching the screen
	def search(self, rule):
		results = []

		# Check for match
		if rule(self):	results.append(weakref.ref(self))

		# Search children
		for value in self.attrs.values():

			if isinstance(value, List):
				results.extend(value.search(rule))

			elif type(value) is list:
				for item in value:
					if isinstance(item, List):
						results.extend(item.search(rule))

		return results

	def check(self, rule):
		true = []
		false = []

		# Check for match
		if rule(self):	true.append(weakref.ref(self))
		else:			false.append(weakref.ref(self))

		# Search children
		for value in self.attrs.values():

			if isinstance(value, List):
				t, f = value.check(rule)
				true.extend(t)
				false.extend(f)

			elif type(value) is list:
				for item in value:
					if isinstance(item, List):
						t, f = item.check(rule)
						true.extend(t)
						false.extend(f)

		return (true, false)


	def searchAttrs(self, rule):
		results = []
		for value in self.attrs.values():

			if rule(value):
				results.append(weakref.ref(value))

		return results


	def findAttrByKey(self, attrKey):
		def isKeyMatch(value):
			return value.key == attrKey

		return self.search(isKeyMatch)

	def findWidgetWithName(self, name):
		def isNameMatch(value):
			return isinstance(value, List) \
			and value.hasName() \
			and value['name'] == name

		return self.search(isNameMatch)



# Manipulating data
	def addAttr(self, key, value, asList=False):
		if key == 'text' and '$' in value:
			List.strings.append((weakref.ref(self), value))

			ids = re.findall(r"\$(\d+)", value)
			if DEBUG and CCAL: print(value, '=>', ids)

			for i in ids:
				List.IDs.append(int(i))


		# If adding a new attribute value then add it as a single item
		# If further values are added then the attribute turns into a list
		# If asList is set then attribute will always be a list
		if key in self:
			if type(self[key]) is list:	self[key].append(value)
			else:							self[key] = [self[key], value]
		else:
			if asList:						self[key] = [value]
			else:							self[key] = value


	def rename(self, name):
		if self.hasName():
			self['name'] = name
			self.dispName = name
		else:
			print("[Warning] Trying to rename a widget with no name")


	def remove(self):
		if self.parent:
			del self.parent[self.key]
		else:
			raise Exception("Removing List with no parent")


	def attachChildren(self, key, children):
		if not isinstance(children, List): raise Exception("Can only attach List subclasses")
		if not type(children) is list: children = [ children ]

		for child in children:
			asList = type(child) is Widget
			self.addAttr(key, child, asList)
			child.parent = self
			child.key = key




# Outputting screen file 
	def write(self, file, LE='\n'):
		# Opening/Closing brace and the list name
		indent = '\t' * self.indentLvl

		file.write(f"{indent}{self.key} =  {LE}")
		file.write(f"{indent}{{{LE}")

		self.writeAttrs(file, LE)

		file.write(f"{indent}}},{LE}")



	def writeAttrs(self, file, LE='\n'):
		for key, value in self.attrs.items():
			if type(value) is list:
				file.write(f"{self.indent}{key} =  {LE}")
				file.write(f"{self.indent}{{{LE}")

				for item in value:
					if isinstance(item, List):
						item.write(file, LE)
					else:
						file.write(f"{self.indent}\t{self.formatAttr(key, item)},{LE}")

				file.write(f"{self.indent}}},{LE}")

			elif isinstance(value, List):
				value.write(file, LE)

			elif value is None:
				# If none print the list name and braces
				file.write(f"{self.indent}{key} =  {LE}")
				file.write(f"{self.indent}{{{LE}")
				file.write(f"{self.indent}}},{LE}")

			else:
				file.write(f"{self.indent}{key} = {self.formatAttr(key, value)},{LE}")

	def formatAttr(self, key, value):
		if type(value) is float:
			if (value % 1) == 0:	return f"{value:1.0f}" # Whole numbers
			else: 					return f"{value:1.5f}"

		elif type(value) is str:
			if value == 'true' or value == 'false':	return value
			else:									return f"\"{value}\""

		elif value == None:
			return ''

		else:
			raise Warning("Couldn't format attribute")
			return 'ERR'


# String representations
	def printShape(self):
		string = ""
		if 'position' in self:
			pos = self['position']
			string += f"({dispValue(pos[0])}, {dispValue(pos[1])})"

		if 'size' in self:
			siz = self['size']
			string += f"[{dispValue(siz[0])} x {dispValue(siz[1])}]"

		return string


	def __repr__(self):
		prefix = "W" if type(self) is Widget else "L"

		name = self.dispName

		# Add the shape info to the name if the widget is not named
		if not self.hasName():
			if shape := self.printShape():
				name += ' ' + shape

		loc = f"({lNum(self.start)}|{self.end-self.start}|{self.indentLvl})"

		attr = f"{{{len(self.attrs)}}}"

		return f"{prefix}: {name} {loc}{attr}"

	def __str__(self):
		string = self.__repr__()

		if 'Children' in self:
			if type(self['Children']) is list:
				childCount = len(self["Children"])
			elif self['Children'] != None:
				childCount = 1

			string += f" Children:{childCount}"

		# Print Attributes
		if len(self.attrs) <= 32:
			string += "\n"
			for key, value in self.attrs.items():


				if isinstance(value, List):
					objectStr = value.__str__()
					string += key + ": " + objectStr.replace("\n", "\n\t")
					string = string[:-1]

				elif type(value) is list:
					string += key

					if key == 'Children':
						string += f" [{len(self[key])}]"

					if len(value) <= 2:
						string += f": {value}\n"

					else:
						string += ": \n"
						for item in value:
							string += '\t' + item.__repr__() + '\n'

				else:
					string += f"{key}: {self.formatAttr(key, value)}\n"

		return string

################################################################################

class Widget(List):
	def parseSelf(self, lines, start):
		if DEBUG and CCALL: print(f"New Widget @{lNum(start)}")

		if not (match := widgetPattern.match(''.join(lines[start:start+2]))):
			printLine(start, lines[start])
			printLine(start+1, lines[start+1])
			raise Exception('Invalid widget starting line')

		self.start 		= start
		self.end 		= findMatchingBrace(lines, start)
		self.indentLvl 	= match.start(1)
		self.indent 	= '\t' * (self.indentLvl + 1)

		self.parse(lines, start + 2, self.end) # Skip the opening brace line

		if   'name' in self: self.dispName = self['name']
		elif 'type' in self: self.dispName = self['type']
		else:				 self.dispName = self.key 

	def remove(self):
		if self.parent:
			if type(self.parent[self.key]) is list:
				self.parent.remove(self)

				widgetInfo = self.getWidgetInfo()

				for info in list(widgetInfo):
					if info.hasName() and info['name'] == self['name']:
						widgetInfo.remove(info)

			else:
				raise Exception("Looks like you can have widget attributes...")
		else:
			raise Exception("Removing widget without a parent")

	def getWidgetInfo(self):
		return self.getScreen()['ToolInfo']['WidgetInfo']



	def write(self, file, LE='\n'):
			# Opening/Closing brace indent
			indent = '\t' * self.indentLvl

			file.write(f"{indent} {LE}")
			file.write(f"{indent}{{{LE}")

			self.writeAttrs(file, LE)

			file.write(f"{indent}}},{LE}")


	def hasEssntials(self):
		return self.hasAttrs(['type', 'size', 'position'])

################################################################################

class Screen(Widget):
	def __new__(cls, filePath, VB=0, DB=DEBUG):
		screen = super().__new__(cls)

		if match := re.match(r"([\w\s_-]+)\.screen", os.path.basename(filePath)):
			screen.key = match[1]
		else:
			print(f"[Error] Invalid screen file name: {filePath}")
			return None

		screen.VB = VB # Verbose level (currently used as a bool)

		screen.parent = None
		screen.filePath = filePath
		screen.indentLvl = 0
		screen.indent = '\t'

		return screen


	def __init__(self, filePath, VB=0, DB=DEBUG):
		 # Allow debugging to be enabled per screen
		global DEBUG # We have to use a global value since printline is a separate function
		self.DBold = DEBUG
		DEBUG = DB

		self.openScreen(filePath)

		DEBUG = self.DBold

	def __repr__(self):
		prefix = "Screen"
		name = self.key
		return f"{prefix}: {name} ({lNum(self.start)}-{lNum(self.end)})"

	def __str__(self):
		return self.__repr__() + '\n' + str(self.attrs)


	def openScreen(self, filePath):
		if self.VB: print(f"Opening {filePath}")
		with open(filePath) as file:
			self.lines = file.readlines()

		self.length = len(self.lines)
		self.end = self.length - 1
		self.start = 0

		if self.lines[0] == "Screen =  \n" and \
		   self.lines[1] == "{\n":

			if self.VB: 
				print(f"Looks good so far...")

				# Display first few lines
				for i in range(4):
					printLine(i, self.lines[i])
				print("...\n")

				print(f"Scanning {self.length} lines...")
		else:
			print(self.lines[0])
			print("Doesn't look like a screen file...")
			sys.exit()

		self.scanLines(self.lines)

	def scanLines(self, lines):
		# Reset consecutive line counter
		printConsecLine.counter = -1

		line = self.start
		self.attrs = {}
		while line < self.length:
			printConsecLine(line, lines[line])
			printConsecLine(line+1, lines[line+1])
			lst = List(self, lines=lines, start=line)
			self[lst.key] = lst

			printConsecLine(lst.end, lines[lst.end])
			line = lst.end + 1
		if self.VB: print("Done")

		if 'Screen'   not in self:
			print("[Warning] 'Screen' missing")

		if 'ToolInfo' not in self:
			print("[Warning] 'ToolInfo' missing")

		if len(self.attrs) != 2:
			warning = f"Unexpected number of lists {list(self.attrs.keys())}\n"
			raise Exception(warning)
			print("[Warning]", warning)



	def write(self, outputPath, DOS=False):
		if DOS: LE = '\r\n'
		else:   LE = '\n'

		with open(outputPath, 'w') as file:
			# Opening/Closing brace indent
			indent = '\t' * self.indentLvl

			for key, section in self.attrs.items():
				# Screen object should only contain Lists (Screen & ToolInfo)
				file.write(f"{key} =  {LE}")
				file.write(f"{{{LE}")

				section.writeAttrs(file, LE)

				file.write(f"}}{LE}")

#								CLASSES