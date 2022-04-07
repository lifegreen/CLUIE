import os, argparse, sys
import re
from shutil import copyfile

from Screen import *


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


class Editor():
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


class Directory():
	def __init__(self, directory):
		self.dir = directory

	def get(self, name):
		return os.path.join(self.dir, name + ".screen")

# directory = r"C:\Users\Mark\Desktop\MUIEGA"
# directory = r"/home/mfomenko/Desktop/MUIEGA"
directory = r"$FERAL_SVN_ROOT/Feral/Development/Products/CompanyOfHeroes/Feral/OverrideData/art/ui/screens"
screenName = "feral_skirmish_setup"
outputName = "_" + screenName

D = Directory(directory)

filePath   = D.get(screenName)
outputPath = D.get(outputName)


E = Editor(filePath)
# grp_b = E.Screen.findWidgetWithName('group_branches')[0]()




# sizes = []
# total = 0 
# for obj in List.objs:
# 	size = sys.getsizeof(obj) #/ 1024
# 	sizes.append(size)
# 	total += size


# for item in E.Screen['ToolInfo']['WidgetInfo']:
# 	if item.hasName():
# 		name = item['name']
# 		results = E.Screen['Screen'].findWidgetWithName(name)
# 		if len(results):
# 			if len(results) > 1:
# 				print()
# 				print(f'Found a few for {name}:')
# 				for w in results:
# 					print(repr(w()))
# 		else:
# 			print()
# 			print('NO WIDGET FOUND FOR:', repr(item))

# 	else:
# 		print()
# 		print('No Name\t', repr(item))


if __name__ == "__main__":

	ax_dlc_00 = re.compile(r"upgrade_\d\d_btn_2")
	def rule(value):
		C = issubclass(type(value), List)
		N = value.hasName() if C else False
		M = ax_dlc_00.search(value['name']) if N else False
		# print(f"C:{C} N:{N} M:{M}\n")
		rule.count += 1
		return C and N and M
	rule.count = 0


	widgets = E.applyStyleToWidgets("feral", "branch_ability", RegEx=r"upgrade_\d\d_btn_[^2]+$")
	widgets = Selection(root=E.Screen['Screen'], rule=rule)
	print("Selection length:", widgets.length)

	widgets.edit(opRemoveItem())
	# sub = widgets.extend(rule=rule, root=E.Screen['Screen'])
	# print("Selection length after:", widgets.length)


	print("Modified widgets are:")
	for widget in widgets:
		print(repr(widget()))
											

	# print()
	# print("Rule count:", rule.count)
	# print("Sub selection length", len(sub))
	# for i in sub:
	# 	print(repr(i))
	

	E.Screen.write(outputPath)

	check = Selection(root=E.Screen['Screen'], rule=rule)
	print("Checking widgets...")
	for c in check:
		print(repr(c()), c()['style'])


	# print()
	# print(S)
	# print()
	# print(S.attrs['Screen']['Widgets'])
	# print()
	# print(S.attrs['Screen']['Widgets']['Children'])
	# print()
	# print(S.findWidgetWithName('upgrade_01_btn_al_arm'))
	# print()
	# print(S.findWidgetWithName('upgrade_01_btn_al_arm')[0])


	# print('version' in S['Screen'])

	# S.write(outputPath)

