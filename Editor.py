import os, sys
import pandas as pd
import re

from Screen import *
from Selection import *





################################################################################
#								FUNCTIONS
################################################################################
def resolvePath(path):
	return os.path.realpath(os.path.abspath(os.path.expandvars(os.path.expanduser(path))))




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
	asList = isinstance(value, Widget)
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





################################################################################
#									CLASSES
################################################################################
class Editor():
	def __init__(self, filePath=None, datPath=None):
		if filePath:
			filePath = resolvePath(filePath)

			if os.path.isfile(filePath):
				self.filePath = os.path.basename(filePath)
				self.screen = Screen(filePath, VB=1)
				print(f"Starting Editor with {repr(self.screen)}")
			else:
				err = f"File: '{filePath}' DOES NOT EXIST"
				raise Exception(err)


		if datPath:
			datPath = resolvePath(datPath)

			if os.path.isdir(datPath):
				self.datPath = datPath
			else:
				err = f"Directory: '{filePath}' DOES NOT EXIST"
				raise Exception(err)

		else: 
			self.datPath = None

	

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


	def generateDatFile(self, outPath=None):
		def getRange(ids):
			ids = list(set(ids))
			ids.sort()
			limits = roundRange(min(ids), max(ids))
			return ids, limits

		def roundRange(_min, _max):
			# Round down to nearest fifty
			start = (_min // 50) * 50 
			end = (_max // 50) * 50

			# Round up unless it divides equally or if we only have a single value
			if (_max % 50) or (_max == _min) : end += 50 
			end -= 1 # The range has to end on 1 less than a multiple of 50
			return (start, end)

		def datFileHeader():
			# Dat file boiler plate
			header = '/' * 69 + '\n' 
			header += "// Generated with CLUIE\n\n"
			header += f"filerange {limits[0]} {limits[1]}\n\n"
			header += '/' * 69 + '\n' # nice
			header += f"// UI Screen: {self.screen.key}\n\n"
			return header



		ids, limits = getRange(List.IDs)

		# TODO: Deal with bad lines
		strings = pd.read_table(LOC_FILE_PATH
								, encoding='utf-16'
								, delimiter='\t'
								, index_col=0
								, names=['ID', 'String']
								, on_bad_lines='warn'
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
					return None

			elif self.datPath:
				outDir = self.datPath

			# Loop until we get a valid directory
			if not outDir:
				print(f"Please provide output directory: ", end='')
				newPath = input()

				if newPath:	outPath = resolvePath(newPath)
				else:		return None # If user entered and empty line return


		path = os.path.join(outDir, outName)

		with open(path, 'w') as file:
			file.write(datFileHeader())
			file.write(f"rangestart {limits[0]} {limits[1]}\n")

			for id in ids:
				if id in strings.index:	file.write(f"{id}\t{strings.loc[id].item()}\n")
				else:					file.write(f"{id}\t${id} - Doesn't exist\n")

			file.write("rangeend\n")

		return path
################################################################################





################################################################################
class Directory():
	def __init__(self, directory):
		self.dir = os.path.expandvars(directory)

	def get(self, screenName):
		return os.path.join(self.dir, screenName + ".screen")
################################################################################





################################################################################
#									SETUP
################################################################################
# directory = r"C:\Users\Mark\Desktop\MUIEGA"
# directory = r"/home/mfomenko/Desktop/MUIEGA"
directory = r"$FERAL_SVN_ROOT/Feral/Development/Products/CompanyOfHeroes/Feral/OverrideData/art/ui/screens"
screenName = "feral_skirmish_menu"
outputName = "_" + screenName

D = Directory(directory)

filePath   = D.get(screenName)
outputPath = D.get(outputName)

LOC_FILE_PATH = os.path.expandvars("$FERAL_SVN_DATA_ROOT/CompanyOfHeroes/Data/CompanyOfHeroesData/Data/coh/engine/locale/english/reliccoh.english.ucs")



# E = Editor(filePath)





################################################################################
#									MAIN
################################################################################
if __name__ == "__main__":
	def isNamed(value):
		C = issubclass(type(value), List)
		N = value.hasName() if C else False
		# print(f"C:{C} N:{N}")
		return C and N

	# widgets = Selection(root=E.screen['Screen'], rule=isNamed)

	# print(widgets)
