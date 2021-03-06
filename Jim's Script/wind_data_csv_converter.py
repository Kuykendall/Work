#!/usr/bin/env python -u
# -*- coding: utf-8 -*-

"""
Usage:

	Simply run it from the command line with no arguments.

This script merges all CSV files in **current working directory** into a single file, assumes all
have the same header.

"""

__author__ = 'Dave Wilkie'
__copyright__ = 'Copyright (c) 2013, University of Hawaii Smart Energy Project'
__license__ = 'https://raw.github' \
              '.com/Hawaii-Smart-Energy-Project/Maui-Smart-Grid/master/BSD-LICENSE.txt'

import csv
from datetime import datetime
import os
import re

# Returns true if timestring2 represents a time earlier than timestring1
def compareTimestamp(timeString1, timeString2):
    pattern = '(\d+)/(\d+)/(\d+)\s+(\d+):(\d+)'
    matches1 = re.search(pattern, timeString1)
    dt1 = datetime(int(matches1.group(3)), int(matches1.group(1)),
    	int(matches1.group(2)), int(matches1.group(4)), int(matches1.group(5)))
    matches2 = re.search(pattern, timeString2)
    dt2 = datetime(int(matches2.group(3)), int(matches2.group(1)),
    	int(matches2.group(2)), int(matches2.group(4)), int(matches2.group(5)))
    #print dt1, dt2, dt2 <= dt1
    return dt2 <= dt1

# Make a system call "dir" to see what files are in the folder and capture the output.

# Command removed for cross platform.
#output = subprocess.Popen(["ls"],stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True).communicate()[0]

output = os.listdir(os.path.dirname(os.path.abspath(__file__)))

# Split the string by lines.

# Command removed for cross platform.
#output = output.split("\n")

count = 0

fileNames = []
for line in output:
	line = line.split(" ")
	# for each element find the file name of the files in that folder with the
	# extension *.txt
	for element in line:
		if ".csv" in element.lower():
			#if you found a valid filename, put it in a list
			fileNames.append(element)

if not fileNames:
        print "No filenames were found... Quiting..."
	exit()

output = open("DATAWIND_pivot_turbine.csv", "wb")
output2 = open("DATAWIND_pivot_weather.csv", "wb")
writer1 = csv.writer(output)
writer2 = csv.writer(output2)
print "Opening writers..."

with open(fileNames[0],"r") as f:
	reader = csv.reader(f)
	header1 = reader.next()
	header1 = ["datetime", "t14", "t15", "t16", "t17", "t18"]
	header2 = ["datetime", "speed_min", "speed_avg", "speed_max", \
			   "speed_std_deviation", "direction_min", "direction_avg", \
			   "direction_max", "direction_std_deviation"]
	writer1.writerow(header1)
	writer2.writerow(header2)

for filename in fileNames:
	with open(filename,"r") as f:
		reader = csv.reader(f)
		# Dump the header.
		reader.next()
		# Dump the first row of data. They cause dup problems.
		reader.next()

		first = True
		for row in reader:
			# Any row with fewer than five columns is corrupt, so we skip it.
			if len(row) < 5:
				print "Corrupted data detected at ", row[0]
   				continue

			timeString2 = row[0]
			if first:
				timeString1 = timeString2

			# Skip any row out of sequence, i.e. w/ a later timestamp than the previous
			if compareTimestamp(timeString1, timeString2):
				if not first:
					continue
			count = count + 1
			row2 = [row[0]]
			if len(row) is 8 and (row[-2] != "missing" and row[-2] != ""
								  and row[-1] != "missing" and row[-1] != ""):
				if row[-2] != "missing" and row[-2] != "":
				 	speed_nums = row[-2].split("&")
					# Correction coefficient of 1.53 is used to correct wind speed.
					correct_speed_nums = [float(x) * 1.53 for x in speed_nums[0:3]]
					correct_speed_nums.append(speed_nums[3])
					row2.extend(correct_speed_nums)
				else:
					row2.extend(["", "", "", ""])

				if row[-1] != "missing" and row[-2] != "":
					direction_nums = row[-1].split("&")
					row2.extend(direction_nums)
				else:
					row2.extend(["", "", "", ""])
				writer2.writerow(row2)

			# To filter out 'missing' values, we are going to give them
			# negative values temporarily.
			for i in range(1, 6):
				if row[i] == "missing" or row[i] == "":
					row[i] = -1

			# Conversion factor of 10 for turbine wattage measurements.
			correct_turbine_nums = []
			for x in row[1:6]:
				try:
					correct_turbine_nums.append(int(x) * 10)
				except ValueError:
					correct_turbine_nums.append(x)
			row = [row[0]]
			row.extend(correct_turbine_nums)
			for i in range(1, 6):
				if row[i] < 0:
					row[i] = ""

			writer1.writerow(row)
			timeString1 = timeString2
			first = False
print "There were ", count
