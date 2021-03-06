from Editor import *

# directory = r"C:\Users\Mark\Desktop\MUIEGA"
# directory = r"/home/mfomenko/Desktop/MUIEGA"
directory = r"$FERAL_SVN_ROOT/Feral/Development/Products/CompanyOfHeroes/Feral/OverrideData/art/ui/screens"
screenName = "feral_skirmish_menu"
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





ax_dlc_00 = re.compile(r"upgrade_\d\d_btn_2")
def rule(value):
	C = isinstance(value, List)
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



def checkAssumtions(filePath):
	E = Editor(filePath)

	widgetWithoutType = lambda item: (type(item) is Widget) and not item.hasType()
	listWithType = lambda item: (type(item) is List) and item.hasType()

	a = Selection()
	b = Selection()
	print("All Widgets have a type -", E.check(widgetWithoutType, "all", a, b))
	a = Selection()
	b = Selection()
	print("Lists may have a type -", E.check(listWithType, "any", a, b))


	for item in a:
		if item.hasType():
			print(item['type'], item.__repr__())
		else:
			print("Exception:", item.__repr__())


def getAllTypesInFile(file):
	file = resolvePath(file)

	types = set()

	# sel = Editor(file).getSelection(lambda x: x.hasType() and types.add(x['type']))
	sel = Editor(file).getSelection(lambda item: item.hasType())
	sel.edit(lambda item: types.add(item['type']))

	return types

def fetAllTypesInFolder(folder):
	folder = resolvePath(folder)

	if os.path.isdir(folder):
		types = set()

		for entry in os.scandir(folder):
			if entry.is_file() and entry.name.endswith('.screen'):
					types.update(getAllTypesInFile(entry.path))


		return types


	else: print(f"[Error] \"{directory}\" is not a directory")

def testTypes(directory):
	types = fetAllTypesInFolder(directory)
	print(types)

	# All types from feral_lobby_browser
	allTypes = {'RadioButton',
				'ScrollBar',
				'Button',
				'ArtLabel',
				'Group',
				'Graphic',
				'Component',
				'CustomListBoxItem',
				'CheckButton',
				'CustomListBox',
				'Rectangle',
				'TextLabel',
				'Text'}

	if allTypes == types:
		print("[PASS] All types have been found")

	elif allTypes > types:
		print(f"[FAIL] Failed to find the following types: {allTypes - types}")

	else:
		print(f"[UNEXPECTED] Found new types: {types - allTypes}")