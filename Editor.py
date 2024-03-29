import os, sys
import pandas as pd

from Screen import *
from Selection import *




################################################################################
#							CONSTANTS
################################################################################
LOC_FILE_PATH = r"$FERAL_SVN_DATA_ROOT/CompanyOfHeroes/Data/CompanyOfHeroesData/Data/coh/engine/locale/english/reliccoh.english.ucs"
# LOC_FILE_PATH = r"C:\Users\Mark\Google Drive\Coding\CLUIE\test files\reliccoh.english.ucs"




################################################################################
#								FUNCTIONS
################################################################################
def resolvePath(path):
	return os.path.realpath(os.path.abspath(os.path.expandvars(os.path.expanduser(path))))


def GenerateDatFile(screenFile, outPath, locFile=LOC_FILE_PATH):
	Editor(screenFile, outPath).generateDatFile(locFilePath=locFile)

def GenerateDatFiles(directory, outPath, locFile=LOC_FILE_PATH):
	directory = resolvePath(directory)

	if os.path.isdir(directory):
		editor = Editor(datPath=outPath)

		for entry in os.scandir(directory):
			if entry.is_file() and entry.name.endswith('.screen'):
				screen = Screen(entry.path)

				if screen:
					editor.screen = screen
					editor.generateDatFile(locFilePath=locFile)

	else: print(f"[Error] \"{directory}\" is not a directory")





################################################################################
#							OPERATION FACTORIES
################################################################################
def edit(items, operation):
	return list(map(operation, items))

# Edit Operation Factories
def opRemoveAttrsByKey(keys):
	if hasattr(keys, '__iter__'):		
		def remove(item): 
			for key in keys: 
				del item[key]
	else:
		def remove(item): 
			del item[keys]
	return remove


def opRemoveItem():
	return lambda item: item.remove()

def opAddAttr(key, value):
	asList = type(value) is Widget
	return lambda item: item.addAttr(key, value, asList)

def opApplyStyle(styleSheet, style):
	def apply(item):
		item['style'] = [styleSheet, style]
		if 'Presentation' in item:
			del item['Presentation']

		if 'size' in item:
			del item['size']
	return apply


def opTransform(size=None, pos=None, add=False):
	if add:
		def modify(item, key, idx, value): 
			if value is not None: item[key][idx] += value
	else:
		def modify(item, key, idx, value):
			if value is not None: item[key][idx] = value


	def translate(item):
		if 'position' in item:
			modify(item, 'position', 0, pos[0])
			modify(item, 'position', 1, pos[1])

		else: raise Exception("Object has no 'position' attribute")

	def resize(item):
		if 'size' in item:
			modify(item, 'size', 0, size[0])
			modify(item, 'size', 1, size[1])

		else: raise Exception("Object has no 'size' attribute")

	if pos and size:
		return lambda item: translate(item) and resize(item)
	elif pos:
		return translate
	elif size:
		return resize


def opRename(newName, regex=None):
	return lambda item: item.hasName() and item.rename(newName)



#							OPERATION FACTORIES





################################################################################
#									CLASSES
################################################################################
class Editor():
	def __init__(self, screen=None, datPath=None):
		self.screen = None
		self.datPath = None

		self.openScreen(screen, datPath)


		contents = ""
		if self.screen: contents += repr(self.screen) + "\n"
		if self.datPath: contents += "datPath:" + (self.datPath) + "\n"

		if contents: print("Starting Editor with", contents, end="")

	def __call__(self, screen, datPath=None):
		self.openScreen(screen, datPath)

	def openScreen(self, screen, datPath):
		if screen:
			if type(screen) is Screen:
				self.screen = screen

			elif type(screen) is str:
				filePath = resolvePath(screen)

				if os.path.isfile(filePath):
					self.screen = Screen(filePath)
				else:
					err = f"File: '{filePath}' DOES NOT EXIST"
					raise Exception(err)

			else:
				err = f"Invalid 'screen' argument type: '{type(screen)}'"
				raise Exception(err)

		if datPath:
			datPath = resolvePath(datPath)

			if os.path.isdir(datPath):
				self.datPath = datPath
			else:
				err = f"Directory: '{datPath}' DOES NOT EXIST"
				raise Exception(err)

	def getSelection(self, rule):
		return Selection(self.screen.search(rule), root=self.screen)


	def check(self, rule, cond, true=[], false=[]):
		if cond != "any" and cond != "all":
			print(f"[Error] Invalid argument '{cond}'")
			return

		if len(true) or len(false):
			print("[Warning] The passed in containers are not empty")

		t, f = self.screen.check(rule)
		true.extend(t)
		false.extend(f)

		tCount = len(true)
		fCount = len(false)

		print(f"{tCount}/{tCount+fCount} follow the rule")

		if cond == "any":	return     bool(tCount)
		else:				return not bool(fCount)
	

	def applyStyleToWidgets(self, styleSheet, style, widgets=None, RegEx=None):
		if widgets:
			widgets = Selection(widgets)

		elif RegEx:
			query = qAND(qNamedWidget(), qNameMatch(RegEx))

			widgets = Selection(root=self.screen['Screen'], rule=query)

		else:
			raise Exception("Widget set not specified")


		widgets.edit(opApplyStyle(styleSheet, style))

		return widgets


	def generateDatFile(self, outPath=None, locFilePath=LOC_FILE_PATH):
		def getRange(ids):
			ids = list(set(ids))
			ids.sort()
			limits = roundRange(min(ids), max(ids))
			return ids, limits

		def roundRange(_min, _max):
			# Round down to nearest fifty
			start = (_min // 50) * 50
			end   = (_max // 50) * 50

			# Round up unless it divides equally
			if (_max % 50) != 0: end += 50

			# The range has to end on 1 less than a multiple of 50
			end -= 1
			return (start, end)

		def datFileHeader():
			# Dat file boiler plate
			header = '/' * 69 + '\n'
			header += '// Generated with CLUIE\n\n'
			header += f'filerange {limits[0]} {limits[1]}\n\n'
			header += '/' * 69 + '\n' # nice
			header += f'// UI Screen: {name}\n\n'
			return header

		if self.screen is None:
			print("[Error] Editor doesn't have a screen")
			return


		# TODO: Deal with bad lines
		strings = pd.read_table(resolvePath(locFilePath)
								, encoding='utf-16'
								, delimiter='\t'
								, index_col=0
								, names=['ID', 'String']
								, on_bad_lines='skip'
								)

		# Make sure we have an output directory
		outDir = None
		outName = f"Text.UI.{self.screen.key}.dat"
		while outDir == None:
			if outPath:
				if os.path.isdir(outPath):
					outDir = outPath
				elif os.path.isfile(outPath) and outPath.endswtih(".dat"):
					outDir = os.path.dirname(outPath)
					outName = os.path.basename(outPath)
				else:
					print(f"[Error] Invalid output path: '{outPath}'")
					return

			elif self.datPath:
				outDir = self.datPath

			# Get the directory from the user
			if not outDir:
				print(f"Please provide output directory or press 'Enter' to return\n>", end='')
				newPath = input()

				if newPath:	outPath = resolvePath(newPath)
				else:		return # If user entered and empty line return

		path = os.path.join(outDir, outName)

		ids, limits = getRange(List.IDs)

		with open(path, 'w') as file:
			file.write(datFileHeader())

			file.write(f"rangestart {limits[0]} {limits[1]}\n")
			for id in ids:
				if id in strings.index:	file.write(f"{id}\t{strings.loc[id].item()}\n")
				else:					file.write(f"{id}\t${id} - Doesn't exist\n")
			file.write("rangeend\n")

		print(f"Generated: {path}")

		return path
################################################################################





################################################################################
class Directory():
	def __init__(self, directory):
		self.dir = os.path.expandvars(directory)

	def get(self, screenName):
		return os.path.join(self.dir, screenName + ".screen")
################################################################################
#									CLASSES






################################################################################
#									SETUP
################################################################################
# directory = r"C:\Users\Mark\Google Drive\Coding\CLUIE\test files"
# datDirectory = r"C:\Users\Mark\Google Drive\Coding\CLUIE\test files\dat files"
# locFilePath = r"C:\Users\Mark\Google Drive\Coding\CLUIE\test files\reliccoh.english.ucs"

directory = r"$FERAL_SVN_ROOT/Feral/Development/Products/CompanyOfHeroes/Feral/OverrideData/art/ui/screens"
datDirectory = r"/Volumes/DEVSSD14/feraldev/tools/UIeditor/BIA/Root/CoH/Locale/English"
locFilePath = r"$FERAL_SVN_DATA_ROOT/CompanyOfHeroes/Data/CompanyOfHeroesData/Data/coh/engine/locale/english/reliccoh.english.ucs"

screenName = "feral_lobby_browser"
outputName = "_" + screenName

D = Directory(directory)

filePath   = D.get(screenName)
outputPath = D.get(outputName)

#									SETUP




################################################################################
#									MAIN
################################################################################
if __name__ == "__main__":
	E = Editor(filePath, datDirectory)





#									MAIN