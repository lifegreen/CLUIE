import os, argparse, sys
import re
from shutil import copyfile

from Screen import *
from Selection import *


################################################################################
#									FUNCTIONS
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


# def opResize(width, height, add=False):
# 	if add:
# 		def operation(item, value): item['position'] = value
# 	else:
# 		def operation(item, value): item['position'] += value






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
################################################################################
	def __init__(self, filePath=None):
		if filePath:
			self.filePath = filePath
			self.Screen = Screen(filePath, VB=1)
			print(f"Starting Editor with {repr(self.Screen)}")
	

	def applyStyleToWidgets(self, styleSheet, style, widgets=None, RegEx=None):
		if widgets:
			widgets = Selection(widgets)

		elif RegEx:
			# name = re.compile(RegEx)

			query = qAND(qNamedWidget(), qNameMatch(RegEx))
			# def rule(value): 
			# 	if isinstance(value, Widget) and value.hasName():
			# 		return name.match(value['name'])
			# 	else:
			# 		return False

			widgets = Selection(root=self.Screen['Screen'], rule=query)

		else:
			raise Exception("Widget set not specified")


		widgets.edit(opApplyStyle(styleSheet, style))

		return widgets





################################################################################
class Directory():
################################################################################
	def __init__(self, directory):
		self.dir = os.path.expandvars(directory)

	def get(self, screenName):
		return os.path.join(self.dir, screenName + ".screen")







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


E = Editor(filePath)





################################################################################
#									MAIN
################################################################################
if __name__ == "__main__":
	pass