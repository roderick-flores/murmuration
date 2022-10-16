"""
 Copyright (c) 2022-2022, Roderick Flores <roderick.flores+murmuration@gmail.com>
 All rights reserved.
"""
import argparse
import numpy
import random
import matplotlib.pyplot as plt
from typing import Final

def evaluate_winnings(
	bankroll: float,
	flips: int,
	payout: float = 0.50,
	loss: float = 0.40
) -> float:
	"""
	Evaluates the coin toss game to determine the winnings after the
	specified number of flips

	Parameters
	----------
	bankroll: float
		Starting amount of money
	flips: int
		Number of coin tosses
	payout:
		Percentage: the bankroll is increased on a win
	loss:
		Percentage: the bankroll is decreased on a loss

	Returns
	----------
	float
		Final amount of money after flips coin tosses
	"""
	for i in range(flips) :
		draw: bool = bool(random.choice([True, False]))
		if draw:
			bankroll = round((1.00 + payout) * bankroll, 2)
		else:
			bankroll = round((1.00 - loss) * bankroll, 2)

		if bankroll == 0.00:
			break

	return bankroll

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
	parser = argparse.ArgumentParser(description="Coin Flip Risk Calculation",
		formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	parser.add_argument(
		"--people",
		type=int,
		default=10000,
		help="set the number of people who are playing"
	)

	parser.add_argument(
		"-b", "--bank",
		type=float,
		default=1000.0,
		help="set the starting bank roll"
	)

	parser.add_argument(
		"-f", "--flips",
		type=int,
		default=50,
		help="set the number of coin flips"
	)

	parser.add_argument(
		"-s", "--seed",
		type=int,
		default=random.randrange(100000000),
		help="set the random number generator seed"
	)

	parser.add_argument(
		"-m", "--me",
		nargs="+",
		type=int,
		help="set who is playing"
	)

	parser.add_argument(
		"-p", "--plot",
		default=False,
		action='store_true',
		help="plot the results as a log-log histogram"
	)

	parser.add_argument(
		"--win",
		type=float,
		default=0.50,
		help="the win percentage"
	)

	parser.add_argument(
		"--loss",
		type=float,
		default=0.40,
		help="the loss percentage"
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

def plot(
		population_winnings: list,
		bankroll: float,
		flips: int,
		house_bank: float,
		winner_count: int,
		seed: int,
		verbose_flag: bool
	) -> None:
	"""
	Plots a log-log histogram of the winnings of the members of the population

	Parameters
	----------
	population_winnings:
		List containing the amount of money each player in the population has
	bankroll: float
		Starting amount of money
	flips: int
		Number of coin tosses
	house_bank:
		Net amount of money the bank earned hosting the game
	winner_count:
		Number of people in the population who ended with more money than they started
	seed:
		Random number generator seed
	verbose_flag:
		Flag indicating whether to output additional information

	Returns
	----------
	None
	"""
	# histogram smallest bin start, as a power of 10
	start: Final[int] = -2
	# histogram largest bin end, as a power of 10
	end: Final[int] = 10
	# create 4 steps between each order of magnitude
	steps: Final[int] = 4*(end-start)
	# if the steps cross zero, add an additional step
	if start * end < 0:
		steps += 1

	hist: Final[list]
	bins: Final[list]
	hist, bins, patches = plt.hist(
		population_winnings,
		bins=numpy.logspace(start, end, steps),
		log=True,
		color='0.4',
		rwidth=0.8
	)
	plt.gca().set_xscale("log")

	if verbose_flag:
		print('bin, Count')
		for index in range(0,len(hist)):
			print( f"{bins[index+1]}, {hist[index]}" )

	title: Final[str] = \
		f'Flips={flips}; Original Cash={"{:,}".format(int(bankroll))}; Seed={"{:,}".format(seed)}'
	subtitle: Final[str] = \
		f'Winners={"{:,}".format(winner_count)}; House={"{:,}".format(int(house_bank))}'

	plt.suptitle(title)
	plt.title(subtitle)
	plt.ylabel('Occurrences')
	plt.xlabel('Money at End of the Game')

	# mark the bars red if it is a loss for the player
	loss_bins = list(filter(lambda bin: bin < bankroll, bins))
	for i in range(0,len(loss_bins)):
		patches[i].set_facecolor('r')

	plt.show()

def main(config: dict) -> None:
	"""
	Plots a log-log histogram of the winnings of the members of the population

	Parameters
	----------
	dict:
		Dictionary containing the configuration populated with command line
		argument values

	Returns
	----------
	None
	"""
	# random number generator seed
	seed: Final[int] = config['seed']
	random.seed(seed)

	# determine the payout and loss percentages
	win: Final[float] = config['win']
	loss: Final[float] = config['loss']

	# amount of money the player starts with
	bankroll: Final[float] = config['bank']
	# number of coin tosses the player must complete
	flips: Final[int] = config['flips']
	# number of people in the population
	people: Final[int] = config['people']
	# flag indicating whether to output additional information
	verbose_flag: Final[bool] = config['verbose']
	# flag indicating whether to plot the results as a log-log histogram
	plot_flag: Final[bool] = config['plot']
	# list of player numbers in the population
	me: Final[set] = set(config['me'])

	# List containing the amount of money each player in the population has
	# at the end of the game
	population_winnings: Final[list] = []
	# total amount of money won
	total_winnings: float = 0.0
	# Number of people in the population who ended with more money than they started
	winner_count: int = 0

	# play the game for every person in the population
	for person in range(people):
		winnings: Final[float] = evaluate_winnings(bankroll, flips, win, loss)
		population_winnings.append(winnings)
		total_winnings += winnings

		# by default, the player loses
		winner: str = "lose"

		# determine the outcome
		if(winnings >= bankroll):
			# the player wins
			winner_count += 1
			winner = "win"

		# declare the outcome for the people in the me list 
		if person in me:
			print( f'Player {person} ended with a total of ${"{:,}".format(round(winnings,2))}: you {winner}!' )

	# Net amount of money the bank earned hosting the game
	house_bank: Final[float] = round(float(people) * bankroll - round(total_winnings,2),2)

	# determine how much the average player has
	average: Final[float] = round(total_winnings/float(people),2)

	# output the average if verbose or "me" is in
	if verbose_flag or len(me) > 0:
		# determine if the team wins or loses
		team: str = "loses"
		if house_bank < 0.0:
			team = "wins"

		print( f'On average, every player ended with ${"{:,}".format(round(average,2))}: the team {team}!' )

	# output the overall outcome of the came
	if verbose_flag:
		print( f'     total: ${"{:,}".format(round(total_winnings,2))}' )
		print( f'   average: ${"{:,}".format(average)}' )
		print( f'house bank: ${"{:,}".format(house_bank)}' )
		print( f'   winners: {winner_count}' )

	# create a histogram plot, if requested
	if plot_flag:
		plot(population_winnings, bankroll, flips, house_bank, winner_count, seed, verbose_flag)

if __name__ == "__main__":
	"""
	Entry point to the application

	seed = 85616075 produces 1 winner after 1,000 flips
	"""
	main(parse_arguments())
