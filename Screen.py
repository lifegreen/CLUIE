import os, argparse, sys
import re
from shutil import copyfile
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
string 	= r'"?([\w\s\d\\/_\-$/*]*)"?'

key 	= r'(\w+) = '
brace 	= r'\t*({)\n'

# Single-line
numberPattern = re.compile(r'^\t*' + key + number + ',\n')
stringPattern = re.compile(r'^\t*' + key + string + ',\n')

numEntryPattern = re.compile(r'^\t*' + number + ',\n')
strEntryPattern = re.compile(r'^\t*' + string + ',\n')
# entryPattern  = re.compile(r'^\t*(\w+) = (' + string + '|' + number + '),\n')

# Two-line
listPattern   = re.compile(r'^\t*(\w+) =\s*\n\t*({)\n')
widgetPattern = re.compile(r'^\t*( \n)\t*({)\n')





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


		# if "{" in lines[i]:
		# 	braceCount += 1

		# elif "}" in lines[i]:
		# 	braceCount -= 1
		# 	if braceCount == 0:
		# 		return i

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
	if isinstance(value, float):
		if (value % 1) == 0:	return f"{value:g}" # Whole numbers
		else: 					return f"{value:1.3f}"
	else:
		return value




################################################################################
#									CLASES
################################################################################
class List():
################################################################################
	# objs = []
	strings = []
	IDs = []
	def __init__(self, parent=None, key=None, lines=None, start=None):
		# List.objs.append(self)
		self.attrs 	= {}
		self.parent = parent
		self.key 	= key

		if None not in (lines, start):
			self.parseSelf(lines, start)
			self.parsed = True

		elif key is not None:
			self.parsed = False

		else:
			print(bool(lines), start, repr(parent), key)
			print()
			raise Exception("Insufficient arguments passed")


	def __setitem__(self, key, value):
		self.attrs[key] = value

	def __getitem__(self, key):
		return self.attrs[key]

	def __delitem__(self, key):
		del self.attrs[key]

	def __contains__(self, key):
		return key in self.attrs


	def remove(self):
		if self.parent:
			del self.parent[self.key]
		else:
			raise Exception("Removing List with no parent")

	def valid(self):
		return 'type' in self

	def hasName(self):
		return 'name' in self

	def hasAttr(self, attr):
		return all(map(lambda x: x in self, attr))


	def parseSelf(self, lines, start):
		if DEBUG and CCALL: print("New List")

		if not (match := listPattern.match(''.join(lines[start:start+2]))):
			printLine(start, ''.join(lines[start:start+2]))
			raise Exception("Invalid list starting line")

		self.key 		= match[1]
		self.start 		= start
		self.end 		= findMatchingBrace(lines, start)
		self.indentLvl	= match.start(1)			# Number of tabs in front of opening brace
		self.indent 	= '\t' * (self.indentLvl+1) # String for formatting attribute list

		self.parse(lines, start + 2, self.end)  # skip the opening brace line

		if   'name' in self: self.name = self['name']
		else:				 self.name = self.key 


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
		if DEBUG and FCALL:print("parseList")

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
			# elif listPattern.match( "".join(lines[j:j+2])) or \
			# 	 entryPattern.match("".join(lines[j:j+2])):
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


	def addAttr(self, key, value, asList=False):
		if key == 'text' and '$' in value:
			List.strings.append((weakref.ref(self), value))
			List.IDs.append(int(value[1:]))


		if key in self:
			if isinstance(self[key], list):	self[key].append(value)
			else:							self[key] = [self[key], value]
		else:
			if asList:						self[key] = [value]
			else:							self[key] = value


	def attach(self, key, children):
		if not issubclass(type(children), List): raise Exception("Can only attach List subclasses")
		if not isinstance(children, list): children = [ children ]
		
		for child in children:
			asList = isinstance(child, Widget)
			self.addAttr(key, child, asList)
			child.parent = self
			child.key = key


	def search(self, rule):
		results = []

		# Check for match
		if rule(self):
			results.append(weakref.ref(self))

		# Search children
		for value in self.attrs.values():

			if issubclass(type(value), List):
				results.extend(value.search(rule))

			elif isinstance(value, list):
				for item in value:
					if issubclass(type(item), List):
						results.extend(item.search(rule))

		return Selection(results)

	def searchAttrs(self, rule):
		results = []
		for value in self.attrs.values():

			if rule(value):
				results.append(weakref.ref(value))

		return Selection(results)


	def findAttrByKey(self, attrKey):
		def isKeyMatch(value):
			return value.key == attrKey

		return self.search(isKeyMatch)

	def findWidgetWithName(self, name):
		def isNameMatch(value):
			# return isinstance(value, Widget) \
			return issubclass(type(value), List) \
			and value.hasName() \
			and value['name'] == name

		# results = self.search(isNameMatch)
		# if len(results) == 0:
		# 	results = self.searchAttrs(qNameMatch)
		return self.search(isNameMatch)



	def write(self, file, LE='\n'):
		# Opening/Closing brace and the list name
		indent = '\t' * self.indentLvl

		file.write(f"{indent}{self.key} =  {LE}")
		file.write(f"{indent}{{{LE}")

		self.writeAttrs(file, LE)

		file.write(f"{indent}}},{LE}")



	def writeAttrs(self, file, LE='\n'):
		for key, value in self.attrs.items():
			if isinstance(value, list):
				file.write(f"{self.indent}{key} =  {LE}")
				file.write(f"{self.indent}{{{LE}")

				for item in value:
					if issubclass(type(item), List):
						item.write(file, LE)
					else:
						file.write(f"{self.indent}\t{self.formatAttr(key, item)},{LE}")

				file.write(f"{self.indent}}},{LE}")

			elif issubclass(type(value), List):
				value.write(file, LE)

			elif value is None:
				# If none print the list name and braces
				file.write(f"{self.indent}{key} =  {LE}")
				file.write(f"{self.indent}{{{LE}")
				file.write(f"{self.indent}}},{LE}")

			else:
				file.write(f"{self.indent}{key} = {self.formatAttr(key, value)},{LE}")

	def formatAttr(self, key, value):
		if isinstance(value, float):
			if (value % 1) == 0:	return f"{value:1.0f}" # Whole numbers
			else: 					return f"{value:1.5f}"

		elif isinstance(value, str):
			if value == 'true' or value == 'false':	return value
			else:									return f"\"{value}\""

		elif value == None:
			return ''

		else:
			raise Warning("Couldn't format attribute")
			return 'ERR'



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

		name = self.name

		# Add the shape info to the name if the widget is not named
		if not self.hasName():
			if shape := self.printShape():
				name += ' ' + shape

		loc = f"({self.start+1}|{self.end-self.start}|{self.indentLvl})"

		attr = f"{{{len(self.attrs)}}}"

		return f"{prefix}: {name} {loc}{attr}"

	def __str__(self):
		string = self.__repr__()

		if 'Children' in self:
			if isinstance(self['Children'], list):
				childCount = len(self["Children"])
			elif self['Children'] != None:
				childCount = 1

			string += f" Children:{childCount}"

		# Print Attributes
		if len(self.attrs) <= 32:
			string += "\n"
			for key, value in self.attrs.items():


				if issubclass(type(value), List):
					objectStr = value.__str__()
					string += key + ": " + objectStr.replace("\n", "\n\t")
					string = string[:-1]

				elif isinstance(value, list):
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
################################################################################
	def parseSelf(self, lines, start):
		if DEBUG and CCALL: print("New Widget")

		if not (match := widgetPattern.match(''.join(lines[start:start+2]))):
			printConsecLine(start, ''.join(lines[start:start+2]))
			errMsg = f"Invalid widget starting line:{start}"
			raise Exception(errMsg)

		self.start 		= start
		self.end 		= findMatchingBrace(lines, start)
		self.indentLvl 	= match.start(1)
		self.indent 	= '\t' * (self.indentLvl + 1)

		self.parse(lines, start + 2, self.end) # skip the opening brace line

		if   'name' in self: self.name = self['name']
		elif 'type' in self: self.name = self['type']
		else:				 self.name = self.key 

	def remove(self):
		if self.parent:
			if isinstance(self.parent[self.key], list):
				self.parent[self.key].remove(self)

				widgetInfo = self.getWidgetInfo()

				for info in list(widgetInfo):
					# print(repr(info))
					if info.hasName() and info['name'] == self['name']:
						widgetInfo.remove(info)

			else:
				raise Exception("Looks like you can have widget attributes...")
		else:
			raise Exception("Removing widget without a parent")

	def getWidgetInfo(self):
		return self.getScreen()['ToolInfo']['WidgetInfo']


	def getScreen(self):
		node = self

		while(node.parent):
			node = node.parent

		if not isinstance(node, Screen): raise Exception("Root is not a Screen")

		return node


	def write(self, file, LE='\n'):
			# Opening/Closing brace indent
			indent = '\t' * self.indentLvl

			file.write(f"{indent} {LE}")
			file.write(f"{indent}{{{LE}")

			self.writeAttrs(file, LE)

			file.write(f"{indent}}},{LE}")


	def hasEssntials(self):
		return self.hasAttr(['type', 'size', 'position'])





################################################################################
class Screen(Widget):
################################################################################
	def __init__(self, filePath, VB=0, DB=DEBUG):
		# Allow debugging to be enabled per screen
		global DEBUG
		self.DBold = DEBUG
		DEBUG = DB 

		self.VB = VB

		self.parent = None
		self.filePath = filePath
		self.indentLvl = 0
		self.indent = '\t'

		if match := re.match(r"([\w\s_-]+)\.screen", os.path.basename(filePath)):
			self.key = match[1]
		else:
			raise Exception("Invalid screen file name")

		# Make a backup
		# copyfile(filePath, filePath + ".bak");

		self.openScreen(filePath)
		DEBUG = self.DBold

	def __repr__(self):
		prefix = "Screen"
		name = self.key
		return f"{prefix}: {name} ({self.start+1}-{self.end+1})"

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
		line = self.start
		self.attrs = {}
		while line < self.length:
			printConsecLine(line, lines[line])
			printConsecLine(line+1, lines[line+1])
			lst = List(self, lines=lines, start=line)
			self[lst.key] = lst
				# print("Fail")

			printConsecLine(lst.end, lines[lst.end])
			line = lst.end + 1
		if self.VB: print("Done")

		if 'Screen'   not in self:
			print("Warning: 'Screen' missing")

		if 'ToolInfo' not in self:
			print("Warning: 'ToolInfo' missing")

		if len(self.attrs) != 2:
			warning = f"Unexpected number of lists {list(self.attrs.keys())}\n"
			raise Exception(warning)
			print("Warning:", warning)




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

	def generateDatFile(self):
		ids, range = getRange(List.IDs)

		fileName = f"Text.UI.{self.key}.dat"
		with open(fileName, 'w') as file:
			file.write(
f'''/////////////////////////////////////////////////////////////////////
// Generated with python UIEditor

filerange {range[0]} {range[1]}

/////////////////////////////////////////////////////////////////////
// UI Screen: {self.key}

''')
			file.write(f"rangestart {range[0]} {range[1]}\n")
			for id in ids:
				file.write(f"{id}\t${id}\n")
			file.write("rangeend\n")
		return fileName

def getRange(ids):
	ids = list(set(ids))
	ids.sort()
	overall = roundRange(min(ids), max(ids))
	return ids, overall

def roundRange(_min, _max):
	# Round down to nearest fifty
	start = (_min // 50) * 50 
	end = (_max // 50) * 50

	# Round up unless it divides equally or if we only have a single value
	if (_max % 50) or (_max == _min) : end += 50 
	end -= 1 # the range ends on 1 less than a multiple of 50
	return (start, end)

# Query Factories
def qNameMatch(name):
	pattern = re.compile(name)
	def nameMatch(item):
		return issubclass (type(item), List) \
				and item.hasName() \
				and	pattern.search(item['name'])
	return nameMatch

def qAttrMatch(key, value):
	def nameMatch(item):
		return issubclass(type(item), List) \
				and item.hassAttr(key) \
				and item[key] == value


def qList():
	return lambda item: isinstance(item, List)

def qWidget():
	return lambda item: isinstance(item, Widget)

def qNamedWidget():
	return lambda item: qWidget()(item) and item.hasName()

def qUIElement():
	return lambda item: issubclass(type(item), List) and item.hasName()


def qAND(*queries):
	# return lambda item: A(item) and B(item)
	def combo(item):
		for query in queries:
			if not query(item): return False
		return True

	return combo

def qOR(*querries):
	# return lambda item: A(item) or B(item)
	def combo(item):
		for query in queries:
			if query(item): return True
		return False

	return combo





################################################################################
class Selection:
################################################################################
	def __init__(self, sel=None, rule=None, root=None):
		self.root = root
		if sel is not None:
			if isinstance(sel, Selection):
				self.items = sel.items
				self.root  = sel.root

			elif isinstance(sel, list):
				self.items = sel

			else:
				raise Exception('Invalid Selection passed')

		elif rule and root and issubclass(type(root), List):
			self.items = root.search(rule)

		else:
			self.items = []


	def __setitem__(self, i, value):
		self.items[i] = value

	def __getitem__(self, i):
		return self.items[i]

	def __delitem__(self, i):
		del self.items[i]

	def __contains__(self, value):
		return weakref.ref(value) in self.items

	def __len__(self):
		return len(self.items)

	def __repr__(self):
		return self.__str__()
		# return str(self.items)

	def __str__(self):
		string = "Selection:\n"
		for item in self.items:
			string += repr(item()) + '\n'
		return string


	@property
	def length(self):
		return self.__len__()



	def edit(self, operation):
		# return list(map(operation, self.items))
		for item in self:
			operation(item()) # Call 'item' to dereference weakref

	def subSelect(self, rule):
		sub = []
		for ref in self.items:
			item = ref()
			if rule(item):
				sub.append(item)
		return Selection(sub)

	# Remove items which DO NOT follow the rule
	def filter(self, rule):
		removed = []
		passed	= []

		for ref in self:
			if rule(ref()):	passed.append(ref)
			else: 			removed.append(ref)

		self.items 	= passed
		return Selection(removed)

	# Add items which follow the rule
	def extend(self, selection=None, rule=None, root=None):
		if not (selection or (rule and root)):
			raise Exception("Not enough arguments specified")
		else:
			new = Selection(items=selection, rule=rule, root=root)

		self.items.extend(new.items)
		return new
