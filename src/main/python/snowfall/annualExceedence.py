"""
 Copyright (c) 2022-2022, Roderick Flores <roderick.flores+murmuration@gmail.com>
 All rights reserved.
"""
import argparse
import csv
import re
from math import ceil
from sys import stderr
from tabnanny import verbose
from typing import Final

def main(config: dict) -> None:
	"""
	Calculates three annual excedence probability curves using data obtained from
	https://www.ncdc.noaa.gov/cdo-web/search. These are:

	1. Number of data events in a given winter season
	2. Amount of the data throughout a given winter season
	3. Amount of the data on a given day throughout a given winter season

	Parameters
	----------
	input file: str
		File that will be read to create the curves

	Returns
	----------
	3 dictionaries:
		1. annual exceedence (CMF) of the number of the data events that occur
	       in a given year
		2. annual exceedence (CMF) of the total amount of the data in a given
		   year
		3. annual exceedence (CMF) of the total amount of the data in a given
		   day per year

	TODO
	----------
	Remove redundant values in the cumulative mass function -- only keep the main observation
	"""
	# list of headings in the CSV file
	headers: Final[list[str]] = []
	# data imported from the CSV file
	data: Final[dict] = {}
	# data events in a season
	season_events: Final[dict] = {}
	# regular express for the expected date format
	date_expression: Final[re.Pattern] = re.compile( '\d{4}-\d{1,2}-\d{1,2}' )
	# start of season for year
	season_start: Final[set] = set({})
	# end of season for year
	season_end: Final[set] = set({})
	# column with the date in it
	date_column: Final[int] = config['date_column']
	# column with the data in it
	data_column: Final[int] = config['data_column']

	# load the data
	with open(config['input']) as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')

		# store the data as key-value pairs with date as key and data (e.g. snowfall)
		# amount as the value
		for row in csv_reader:
			# capture the header row -- it should contain station ID, name,
			# date as YYYY-MM-DD, and total of the data (e.g. snowfall)
			if len(headers) == 0:
				for header in row:
					headers.append(header)

				if config['verbose']:
					print(f'INFO: Date column header label is "{row[date_column]}"', file=stderr)
					print(f'INFO: Data column header label is "{row[data_column]}"', file=stderr)
			else:
				if date_expression.match( row[date_column] ) == None:
					raise DataError(
						f'ERROR: expected date to have the format of YYYY-MM-DD but got {row[date_column]}'
					)

				# assume 0" if the data is omitted
				if len(row[data_column]) > 0:
					data[row[date_column]] = float(row[data_column])
				else:
					data[row[date_column]] = 0.0

	# loop over all days in the data
	for string_date in data.keys():
		# get the data for a given date
		date_data = data[string_date]

		# split thd date into year, month, and day
		# we verified that the date string is YYYY-MM-DD when we loaded it
		date: Final[list[str]] = string_date.split('-')
		year: Final[int] = int(date[0])
		month: Final[int] = int(date[1])
		day: Final[int] = int(date[2])

		# determnie the season (winter is september through the following summer)
		season: int
		if( month > 8 ):
			season = year + 1
		else:
			season = year

		# note the season start
		if month == 9 and day == 1:
			season_start.add(season)

		# note the season end
		if month == 5 and day == 31:
			season_end.add(season)

		# ignore days without any snowfall
		if date_data < 0.01:
			continue

		# gather the data events into an array for the season
		if season not in season_events:
			season_events[season] = []
		season_events[season].append(date_data)


	# seasons where data exists for both the start and end dates
	full_seasons: Final[list] = season_start & season_end
	min_season: Final[int] = min(full_seasons)
	max_season: Final[int] = max(full_seasons)

	bin_estimate_counts: Final[list] = []
	bin_estimate_totals: Final[list] = []
	bin_estimate_max: Final[list] = []
	for season in season_events.keys():
		bin_estimate_counts.append( len(season_events[season]) )
		bin_estimate_totals.append( sum(season_events[season]) )
		bin_estimate_max.append( max(season_events[season]) )

	# total amount of the data (e.g. snowfall) per season
	yearbins: Final[list[int]] = range(0, int(ceil(max(bin_estimate_totals))) + 1)
	year_amount_hist: dict = {}

	# total number of days with measurable (e.g. snowfall) in a season
	eventbins: Final[list[int]] = range(1, max(bin_estimate_counts) + 1)
	day_events_hist: dict = {}

	# total amount of the data (e.g. snowfall) per day
	step: Final[float] = config['step']
	bins: list[float] = []
	for bin in range(1, int(ceil(max(bin_estimate_max) / step) + 1)):
		bins.append(round(bin * step * 100000.0) / 100000.0)
	day_amount_hist: dict = {}

	# output the years without events
	if config['verbose']:
		no_data: Final[set] = full_seasons - set(season_events.keys())
		print(
			f"INFO: the following {len(no_data)} seasons had no {config['label']}: {no_data}",
			file=stderr
		)

	# loop over all of eason event years
	for season in season_events.keys():
		# ignore data for years where the data set is not complete (i.e. from
		# 1 September until 31 May of the following year)
		if season not in full_seasons:
			if config['verbose']:
				print( f'INFO: season {season} was not a full weather year', file=stderr )
			continue

		# calculate the annual exceedence (CMF) for the number of events
		# that occur in  a given year
		for bin in eventbins:
			length: int = len( season_events[season] )
			if length >= bin:
				day_events_hist[bin] = day_events_hist.get(bin,0) + 1

		# calculate the annual exceedence (CMF) for the total amount of data in
		# a given year 
		for bin in yearbins:
			total: float = sum(season_events[season])
			if total > bin:
				year_amount_hist[bin] = year_amount_hist.get(bin,0) + 1

		# calculate the histogram for the total amount of data in
		# a given day per year
		for bin in bins:
			for amount in season_events[season]:
				if amount >= bin:
					day_amount_hist[bin] = day_amount_hist.get(bin,0) + 1
					break

	# determine the total number of years in the data
	total_years: Final[float] = float(max_season - min_season)
	if config['verbose']:
		print( f'INFO: {int(total_years)} seasons of data range from {min_season} to {max_season}', file=stderr )

	# convert histogram for the number of events that occur in  a
	# given year into annual exceedence (CMF) 
	for bin in day_events_hist.keys():
		day_events_hist[bin] = float(day_events_hist[bin]) / total_years

	# convert histogram for the total amount in events in a given year
	# into the annual exceedence (CMF)
	for bin in year_amount_hist.keys():
		year_amount_hist[bin] = float(year_amount_hist[bin]) / total_years

	# convert histogram for the total amount in events in a given day per
	# year into annual exceedence (CMF) 
	for bin in day_amount_hist.keys():
		day_amount_hist[bin] = float(day_amount_hist[bin]) / total_years

	# return the 3 annual execedene dictionaries
	return day_events_hist, year_amount_hist, day_amount_hist

def check_positive(value):
	"""
	Verifies that the supplied value is greaterr than zero

	Parameters
	----------
	String value that must be greater than zero

	Returns
	----------
	float
		String cast to a floating-point value
	"""
	try:
		if float(value) <= 0:
			raise argparse.ArgumentTypeError(f"step of {value} is not greater than zero")
	except ValueError:
		raise Exception(f"{value} is not a floating-point number")
	return float(value)

def parse_arguments() -> dict :
	"""
	Sets the command arguments and then processes them into a dictionary
	of argument key-value pairs

	Parameters
	----------
	None

	Returns
	----------
	dict
		Dictionary containing the command-line arguments or defaults
	"""
	parser = argparse.ArgumentParser(description="Annueal Excedence Calculation",
		formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	# Default data was obtained from https://www.ncdc.noaa.gov/cdo-web/search
	parser.add_argument(
		"-i", "--input",
		type=str,
		default='src/test/resources/3122642.csv',
		help="set the input file name"
	)

	parser.add_argument(
		"--date-column",
		type=int,
		default=2,
		help="set the column where the date field is located"
	)

	parser.add_argument(
		"--data-column",
		type=int,
		default=3,
		help="set the column where the data field is located"
	)

	parser.add_argument(
		"--label",
		type=str,
		default='Snowfall',
		help="label for the data being analyzed"
	)

	parser.add_argument(
		"--step",
		type=check_positive,
		default=0.1,
		help="step size of the bins used to aggregate daily events; must be greater than zero"
	)

	parser.add_argument(
		"-v", "--verbose",
		default=False,
		action='store_true',
		help="turn on verbose output"
	)

	args = parser.parse_args()
	config = vars(args)

	return config

class DataError(Exception): 
    """
	Exception raised when there are issues parsing the annual excedence input data

    Attributes:
        msg: The unformatted error message
    """

    def __init__(self, msg: str):
        self.msg: Final[str] = msg
        super().__init__(msg)

if __name__ == "__main__":
	"""
	Entry point to the application

	Outputs 3 CSV data sets:
		1. annual exceedence (CMF) of the number of weather events that occur
	       in a given year
		2. annual exceedence (CMF) of the total amount of weather event type in a given
		   year
		3. annual exceedence (CMF) of the total amount of weather event type in a given
		   day per year
	"""
	try:
		config: Final[dict] = parse_arguments()
		day_events_hist, year_amount_hist, day_amount_hist = main(config)

		# print the annual exceedence (CMF) for the number of data (e.g. snowfall)
		# events that occur in  a given year
		print( f"Annual Excedence, Annual {config['label']} Days Likelihood" )
		for bin in day_events_hist.keys():
			print( day_events_hist[bin], bin, sep=',' )

		# whitespace
		print()

		# print the annual exceedence (CMF) for the total amount of the data
		# (e.g. snowfall) in a given year 
		print( f"Annual Excedence, Annual {config['label']} Total Likelihood")
		for bin in year_amount_hist.keys():
			print( year_amount_hist[bin], bin, sep=',' )

		# whitespace
		print()

		# print the annual exceedence (CMF) for the total amount of the data 
		# (e.g. snowfall) in a given day per year
		print( f"Annual Excedence, Daily {config['label']} Total Likelihood")
		for bin in day_amount_hist.keys():
			print( day_amount_hist[bin], bin, sep=',' )
	except DataError as error:
		print( error.msg )