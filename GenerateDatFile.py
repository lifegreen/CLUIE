import os
import sys
import argparse
import re
import pandas as pd


def GenerateDatFile(screen, locFile=None, outPath=None):
	strings = None
	if locFile:
		# TODO: Deal with bad lines
		strings = pd.read_table(locFile
								, encoding='utf-16'
								, delimiter='\t'
								, index_col=0
								, names=['ID', 'String']
								, on_bad_lines='skip'
								)

	# Process the screen file
	IDs, limits = getRange(getStringIDs(screen, strings))

	name = os.path.splitext(os.path.basename(args.path))[0]
	path = f"Text.UI.{name}.dat"

	# Output the dat file in the current directory if no output path is specified
	if outPath: path = os.path.join(outPath, path)

	with open(path, 'w') as file:
		file.write(datFileHeader(name, limits))

		file.write(f"rangestart {limits[0]} {limits[1]}\n")

		for ID in IDs:
			if strings:
				if ID in strings.index:	file.write(f"{ID}\t{strings.loc[ID].item()}\n")
				else:					file.write(f"{ID}\t${ID} - Doesn't exist\n")
			else:
				file.write(f"{ID}\t${ID}\n")

		file.write("rangeend\n")


def getStringIDs(screen, strings=None):
	textEntry = re.compile(r'(\s*)text = "(.+)"')
	stringID = re.compile(r'\$(\d+)')

	with open(screen) as file:
		lines = file.readlines()

	ids = []
	for i, line in enumerate(lines):
		if textMatch := textEntry.match(line):
			if idMatch := stringID.match(textMatch[2]):
				ids.append(int(idMatch[1]))
			else:
				# This can cause issues when using UI editor (I think)
				print(f'[Warning] String literal in text entry on line {i}: {textMatch.[0]}')

				if strings:
					if textMatch[2] in strings.Strings:
						lines[i] = re.sub(textEntry, rf'\1text = "\${newID}"', line)
					else:
						# Make a note of the string and add it to the end of dat file


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
	if (_max % 50) != 0: end += 50

	# The range has to end on 1 less than a multiple of 50
	end -= 1
	return (start, end)

def datFileHeader(name, limits):
	# Dat file boiler plate
	header = '/' * 69 + '\n'
	header += '// Generated with CLUIE\n\n'
	header += f'filerange {limits[0]} {limits[1]}\n\n'
	header += '/' * 69 + '\n' # nice
	header += f'// UI Screen: {name}\n\n'
	return header



if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Generate .dat file (for UI editor) from a .screen file')

	parser.add_argument('path',
						help='Path to the screen file')

	parser.add_argument('-d', '--dest',
						help='Destination for the .dat file',
						metavar='outPath')

	parser.add_argument('-l', '--locFile',
						help='File containing original strings',
						metavar='locFile')

	args = parser.parse_args()


	# Validate parameters
	if args.dest and not os.path.isdir(args.dest):
		print(f"[Error] Is not a directory: {args.dest}")
		sys.exit()

	if args.locFile:
		if not os.path.isfile(args.locFile):
			print(f'[Error] File doesn\'t exist: {args.locFile}')
			sys.exit()

		elif not args.locFile.endswith('.ucs'):
			print(f'[Error] Not a localisation (.ucs) file: {args.locFile}')
			sys.exit()


	if os.path.isfile(args.path):
		GenerateDatFile(args.path, args.locFile, args.dest)

	elif os.path.isdir(args.path):
		print('DIR')

	else:
	    print('The path specified does not exist')
	    sys.exit()



