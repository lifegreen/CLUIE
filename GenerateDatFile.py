import os
import sys
import argparse
import re


def GenerateDatFile(screen, locFile=None, outPath=None):
	IDs, limits = getRange(getStringIDs(screen))

	name = os.path.splitext(os.path.basename(args.path))[0]
	path = f"Text.UI.{name}.dat"

	if outPath: path = os.path.join(outPath, path)

	with open(path, 'w') as file:
		file.write(datFileHeader(name, limits))

		file.write(f"rangestart {limits[0]} {limits[1]}\n")
		for ID in IDs:
			if locFile:
				if ID in strings.index:	file.write(f"{ID}\t{strings.loc[ID].item()}\n")
				else:					file.write(f"{ID}\t${ID} - Doesn't exist\n")
			else:
				file.write(f"{ID}\t${ID}\n")
		file.write("rangeend\n")


def getStringIDs(screen):
	textEntry = re.compile(r'\s*text = "(.+)"')
	stringID = re.compile(r'\$(\d+)')

	ids = []
	for i, line in enumerate(open(screen)):
		if lineMatch := textEntry.match(line):
			if stringMatch := stringID.match(lineMatch[1]):
				ids.append(int(stringMatch[1]))
			else:
				# This can cause issues when using UI editor (I think)
				print(f'[Warning] String literal in text entry on line {i}: {lineMatch[0]}')

	return ids


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
	if (_max % 50) == 0: end += 50

	# The range has to end on 1 less than a multiple of 50
	end -= 1
	return (start, end)

def datFileHeader(name, limits):
	# Dat file boiler plate
	header = '/' * 69 + '\n'
	header += "// Generated with CLUIE\n\n"
	header += f"filerange {limits[0]} {limits[1]}\n\n"
	header += '/' * 69 + '\n' # nice
	header += f"// UI Screen: {name}\n\n"
	return header



if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Generate .dat file (for UI editor) from a .screen file')

	parser.add_argument('path',
						help='Path to the screen file')

	parser.add_argument('-d', '--dest',
						help='Destination for the .dat file',
						metavar='outPath')

	args = parser.parse_args()



	if os.path.isfile(args.path):
		GenerateDatFile(args.path)

		# [print(i) for i in getStringIDs(args.path)]

	elif os.path.isdir(args.path):
		print("DIR")

	else:
	    print('The path specified does not exist')
	    sys.exit()



