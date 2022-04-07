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