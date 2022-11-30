import os
import sys
import argparse
import re
import pandas as pd

def lNum(i): return i + 1 # Convert line index to line number

def GenerateDatFile(screen, locFile=None, outPath=None, fixScreen=True):
	strings = None
	if locFile:
		# Load original strings
		# TODO: Deal with bad lines
		strings = pd.read_table(locFile,
								encoding='utf-16',
								delimiter='\t',
								index_col=0,
								names=['ID', 'String'],
								on_bad_lines='skip')

		assert strings is not None


	# Process the screen file
	print(f'\n[INFO] Processing: "{screen}"')
	IDs, limits, newStrings = parseScreenStrings(screen, strings, fixScreen)


	name = os.path.splitext(os.path.basename(screen))[0]
	path = f'Text.UI.{name}.dat'

	# Output the dat file in the current directory if no output path is specified
	if outPath: path = os.path.join(outPath, path)


	with open(path, 'w') as file:
		file.write(datFileHeader(name, limits))

		file.write(f'rangestart {limits[0]} {limits[1]}\n')

		# Where the IDs generated by us start
		newIDsStart = max(IDs) - len(newStrings) + 1

		for ID in IDs:
			if ID >= newIDsStart:
				# Add new strings directly instead of trying to look up the IDs
				file.write(f'{ID}\t{newStrings[ID - newIDsStart][1]}\n')
			elif strings is not None:
				if ID in strings.index:	file.write(f'{ID}\t{strings.loc[ID].item()}\n')
				else:					file.write(f'{ID}\t${ID} - Does not exist\n')
			else:
				file.write(f'{ID}\t${ID}\n')

		file.write('rangeend\n')


	print(f'[INFO] Generated: "{path}"')


def parseScreenStrings(screen, strings=None, fixScreen=False):
	textEntry = re.compile(r'(\s*)(tooltip_text|text) = "(.+)"')
	stringID = re.compile(r'\$(\d+)')

	with open(screen) as file:
		lines = file.readlines()
		LE = file.newlines

	IDs = []
	newStrings = []
	needsFixing = False

	# Extract all string IDs used in the file
	for i, line in enumerate(lines):
		if textMatch := textEntry.match(line):
			if idMatch := stringID.match(textMatch[3]):
				IDs.append(int(idMatch[1]))
			else:
				''' 
				UI editor doesn't like string literals in screen files and will replace them with string
				IDs from the .dat file. If it can't find a matching string in the .dat file, it will 
				add the string literal to the .dat file under the first unused string ID.
				''' 
				print(f'[WARNING] String literal in text entry on line {lNum(i)}: {textMatch[0].strip()}')
				needsFixing = True

				if fixScreen:
					# Check if the string exists in the original localisation file
					if (strings is not None) and (textMatch[3] in strings['String'].values):
						'''
						This horrible looking line simply gets the index of the first occurrence
						of textMatch[3] in the 'strings' DataFrame.
						In other words, get the original string ID of the text inside the double quotes
						'''
						newID = strings.index.values[strings['String'] == textMatch[3]][0]

						print(f'Substituting "{textMatch[3]}" with ${newID}')

						# Replace the string with an existing string ID
						lines[i] = re.sub(textEntry, rf'\1\2 = "${newID}"', line)
						IDs.append(int(newID))

					else:
						# Make a note of the string so that we can add it to the end of the dat file
						newStrings.append((i, textMatch[3]))

	if not IDs:
		print("[WARNING] No IDs were found in the screen file")
		# If no IDs were found just add something to the list so that it's not empty
		IDs.append(1)

	# If we have detected string literals that aren't original strings then Generate IDs for them
	if newStrings:
		newID = max(IDs)
		for i, string in newStrings:
			newID += 1
			lines[i] = re.sub(textEntry, rf'\1\2 = "${newID}"', lines[i])
			IDs.append(int(newID))

			print(f'Assigning new ID [{newID}] for "{string}" (line {lNum(i)})')



	IDs = list(set(IDs))
	IDs.sort()
	limits = roundRange(min(IDs), max(IDs))


	# Get the screen's "LocaleRange"
	start = r'^\t*'
	for i in range(len(lines)-3, -1, -1): # Searching in reverse since the range is at the end of the file
		if re.match(re.compile('^\t\tLocaleRange =  '), lines[i]):
			match = re.match(r'(?m)' + \
							 start + r'\{\n' + \
							 start + r'(\d+),\n' + \
							 start + r'(\d+),\n' + \
							 start + r'\},\n',
							 "".join(lines[i+1:i+5]))

			localeRange = (int(match[1]), int(match[2]))
			rangePos = (i+2, i+3) # Line numbers of the range values
			break


	if  localeRange is None: raise Exception('[ERROR] Could not find "LocaleRange"')

	if localeRange != limits:
		needsFixing = True
		if fixScreen:
			print('[INFO] Updating LocaleRange:', localeRange, '->', limits)

			lines[rangePos[0]] = re.sub(r'\d+', str(limits[0]), lines[rangePos[0]])
			lines[rangePos[1]] = re.sub(r'\d+', str(limits[1]), lines[rangePos[1]])

		else: print('[WARNING] New "LocaleRange" does not match the range in the Screen file')


	if needsFixing:
		if fixScreen:
			print(f'[INFO] Overwriting: "{screen}"')
			with open(screen, 'w', newline=LE) as file: file.writelines(lines)
		else:
			print('[INFO] Errors detected in the screen file. You can fix them by passing "--fix" to this script.')


	return IDs, limits, newStrings


def roundRange(_min, _max):
	# Round down to nearest fifty
	start = (_min // 50) * 50

	# Round up and subtract 1 (upper bound has to be one less than a multiple of 50)
	end = (_max // 50) * 50 + 49

	return (start, end)



def datFileHeader(name, limits):
	# Dat file boiler plate
	header = '/' * 69 + '\n'
	header += '// Generated with CLUIE\n\n'
	header += f'filerange {limits[0]} {limits[1]}\n\n'
	header += '/' * 69 + '\n' # nice
	header += f'// UI Screen: {name}\n\n'
	return header



def getScreenFiles(paths):
	# Get all valid screen file paths from command line arguments
	screens = []
	for path in paths:
		if os.path.isfile(path):
			if path.endswith('.screen'):
				screens.append(path)
			else:
				print(f'[ERROR] Not a screen file: "{path}"')

		elif os.path.isdir(path):
			for entry in os.scandir(path):
				if entry.name.endswith('.screen') and entry.is_file():
					screens.append(entry.path)

		else:
			print(f'[ERROR] The path does not exist: "{path}"')

	return screens



if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Generates .dat file (for UI editor) from a .screen file. Also detects and fixes invalid strings in screen files.')

	parser.add_argument('paths',
						nargs='+',
						help='Path(s) to the screen files or directory(ies) containing screen files')

	parser.add_argument('-d', '--dest',
						help='Output directory for the .dat file (e.g. UIEditor/BIA/Root/CoH/Locale/English)',
						metavar='outPath')

	parser.add_argument('-l', '--locFile',
						default=os.path.expandvars('$FERAL_SVN_DATA_ROOT/CompanyOfHeroes/Data/CompanyOfHeroesData/Data/coh/engine/locale/english/reliccoh.english.ucs'),
						help='''Localisation file containing original strings. By default the file is located using the "FERAL_SVN_DATA_ROOT" env var.
								Pass "None" or "no" if you wish to not use original strings. will make the UI Editor display the string IDs in place of all the strings''',
						metavar='locFile')

	parser.add_argument('--fix',
						action=argparse.BooleanOptionalAction,
						help='Fix the errors in the screen file (overrides original screen file)')

	args = parser.parse_args()


	# Validate parameters
	if args.dest and not os.path.isdir(args.dest):
		print(f'[ERROR] Directory does not exist: "{args.dest}"')
		sys.exit()

	if args.locFile:
		if args.locFile.lower in ['none','no','null']:
			args.locFile = None

		elif not os.path.isfile(args.locFile):
			print(f'[ERROR] File does not exist: "{args.locFile}"')
			sys.exit()

		elif not args.locFile.endswith('.ucs'):
			print(f'[ERROR] Not a localisation (.ucs) file: "{args.locFile}"')

	else:
		print(f'[INFO] Localisation file not specified, would you like to use the default')


	if args.fix and not args.locFile:
		print(f'[WARNING] Fixing screens without localisation file will make the UI Editor display the string IDs in place of all the strings')
		while True:
			answer = input("Do you wish to proceed? [y/N]")

			if answer.lower() in ['y','yes']:		break
			elif answer.lower() in ['n','no','']:	sys.exit()
			else:									print('[ERROR] Invalid input')


	for screen in getScreenFiles(args.paths):
		GenerateDatFile(screen, args.locFile, args.dest, args.fix)


