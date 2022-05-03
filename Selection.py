import re
import weakref

from Screen import *





################################################################################
#							QUERY FACTORIES
################################################################################
def qNameMatch(name):
	pattern = re.compile(name)
	def nameMatch(item):
		return isinstance(item, List) \
				and item.hasName() \
				and	pattern.search(item['name'])
	return nameMatch

def qAttrMatch(key, value):
	def nameMatch(item):
		return isinstance(item, List) \
				and item.hassAttr(key) \
				and item[key] == value


def qList():
	return lambda item: type(item) is List

def qWidget():
	return lambda item: type(item) is Widget

def qNamedWidget():
	return lambda item: qWidget()(item) and item.hasName()

def qUIElement():
	return lambda item: isinstance(item, List) and item.hasName()

def qNOT(query):
	return lambda item: not query(item)

def qAND(*queries):
	def combo(item):
		for query in queries:
			if not query(item): return False
		return True

	return combo

def qOR(*querries):
	def combo(item):
		for query in queries:
			if query(item): return True
		return False

	return combo






################################################################################
class Selection:
	def __init__(self, sel=None, rule=None, root=None):
		self.root = root
		if sel is not None:
			if type(sel) is Selection:
				self.items = sel.items
				self.root  = sel.root

			elif type(sel) is list:
				self.items = sel

			else:
				raise Exception('Invalid Selection passed')

		elif rule and root and isinstance(root, List):
			self.items = root.search(rule)

		elif not any((sel, rule, root)):
			# Empty Selection
			self.items = []

		else:
			raise Exception('Invalid/not enough arguments specified')


	def __setitem__(self, i, value):
		self.items[i] = weakref.ref(value)

	def __getitem__(self, i):
		return self.items[i]() # Call 'item' to dereference weakref

	def __delitem__(self, i):
		del self.items[i]

	def __contains__(self, value):
		return weakref.ref(value) in self.items

	def __len__(self):
		return len(self.items)

	def __repr__(self):
		return self.__str__()

	def __str__(self):
		string = "Selection:\n"
		for item in self.items:
			string += repr(item()) + '\n'
		return string


	@property
	def length(self):
		return self.__len__()



	def edit(self, operation):
		[operation(item) for item in self]


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
			new = Selection(selection, rule, root)

		self.items.extend(new.items)
		return new
################################################################################		