#! /usr/bin/env python

'''
strategies: minimax, negascout, negamax, minimax w/ab cutoff
compile: python setup.py py2exe (+ add font and background)
'''

from copy import deepcopy # http://www.wellho.net/resources/ex.php4?item=y111/deepcop.py
import random # http://effbot.org/pyfaq/how-do-i-generate-random-numbers-in-python.htm

# gui imports
import pygame # import pygame package
from pygame.locals import * # import values and constants
from sys import exit # import exit function
import time 
import os 

######################## VARIABLES ########################

turn = 'white' # keep track of whose turn it is
selected = (0, 1) # a tuple keeping track of which piece is selected
board = 0 # link to our 'main' board
move_limit = [150, 0] # move limit for each game (declares game as draw otherwise)

# artificial intelligence related
best_move = () # best move for the player as determined by strategy
black, white = (), () # black and white players

# gui variables
window_size = (256, 256) # size of board in pixels 
background_image_filename = 'board_brown.png' # image for the background
title = 'pyCheckers 1.1.2.3 final' # window title
board_size = 8 # board is 8x8 squares
left = 1 # left mouse button
fps = 5 # framerate of the scene (to save cpu time)
pause = 5 # number of seconds to pause the game for after end of game
start = True # are we at the beginnig of the game?

# experiment variables 
round = 0
geneticTime = 0 
minimaxTime = 0 
geneticWins = 0 
minimaxWins = 0 
draws = 0
genetic_ply = 1
minimax_ply = 1
fileNum = 1

# delete all test files 
for i in range(1,7):
	exists = os.path.isfile("C:\\pycheckers\\ply"+str(i)+".txt")
	if exists:
		os.remove("C:\\pycheckers\\ply"+str(i)+".txt")

######################## CLASSES ########################

# class representing piece on the board
class Piece(object):
	def __init__(self, color, king):
		self.color = color
		self.king = king

# class representing player
class Player(object):
	def __init__(self, type, color, strategy, ply_depth):
		self.type = type # cpu or genetic
		self.color = color # black or white
		self.strategy = strategy # choice of strategy: minimax, negascout, negamax, minimax w/ab
		self.ply_depth = ply_depth # ply depth for algorithms

# class representing move 
class Move(object):
	def __init__(self, moveCoordinates, board, player):
		self.moveCoordinates = moveCoordinates 
		self.board = board 
		self.player = player 
		self.score = None
		self.id = None 

# class gene object
class Gene(object):
	def __init__(self, move):
		self.nodeId = 0 
		self.move = move
		self.score = 0 

	def getId(self):
		return self.nodeId 

	def getMove(self):
		return self.move 

	def getScore(self):
		return self.score 

	def setId(self, id):
		self.nodeId = id 

	def setMove(self, move):
		self.move = move 

	def setScore(self, score):
		self.score = score 

# class representing chromosome
class Chromosome(object): 
	def __init__(self):
		self.genes = [] 
		self.geneticScore = 0  
		#self.leafBoard = None

	def addGene(self, move):
		gene = Gene(move) 
		self.genes.append(gene) 

	def getGenes(self):
		return self.genes 

	def getGeneticScore(self):
		return self.geneticScore 

	def setGenes(self, genes):
		self.genes = genes 

	def setGeneticScore(self, geneticScore):
		self.geneticScore = geneticScore 

	def crossover(self, other):
		c1 = Chromosome() 
		c2 = Chromosome() 
		if self.genes[0].getMove().moveCoordinates == other.genes[0].getMove().moveCoordinates:
			# The genes are compatible so they can mate 
			for i in range(len(self.genes)):
				if self.genes[i].getMove().moveCoordinates == other.genes[i].getMove().moveCoordinates:
					c1.addGene(self.genes[i].getMove())
					c2.addGene(other.genes[i].getMove()) 
				else:
					break 
			for j in range(i, len(self.genes)):
				c1.addGene(other.genes[j].getMove())
				c2.addGene(self.genes[j].getMove()) 
		else:
			# The genes are not compatible so they reject each other and don't mate 
			for i in range(len(self.genes)):
				c1.addGene(self.genes[i].getMove()) 
				c2.addGene(other.genes[i].getMove()) 

		return (c1,c2) 

	def mutate(self):
		c = Chromosome()
		i = random.randint(1,len(self.genes)) if len(self.genes) >= 1 else random.randint(0,len(self.genes)) 
		for j in range(0,i):
			c.addGene(self.genes[j].move)
		subChromosome = buildChromosome(self.genes[j].getMove().board, self.genes[j].getMove().player, j, Chromosome()) 
		if subChromosome != None:
			for k in range(0, len(subChromosome.getGenes())):
				c.addGene(subChromosome.getGenes()[k].getMove())  
		return c 

# class reservation node 
class ReservationNode(object):
	def __init__(self, id, level, parent):
		self.id = id 
		self.level = level
		self.children = [] 
		self.gene = None  
		self.parent = parent 
		self.minimaxScore = 0 
		self.bestScore = -10000 
		self.bestMove = None 
		self.player = None 

	def addChild(self, child):
		self.children.append(child) 

	def getGene(self):
		return self.gene 

	def getChildren(self):
		return self.children 

	def getId(self):
		return self.id 

	def getLevel(self):
		return self.level 

	def getMinimaxScore(self):
		return self.minimaxScore 

	def getPlayer(self):
		return self.player 

	def getBestScore(self):
		return self.bestScore 

	def getBestMove(self):
		return self.bestMove 

	def setGene(self, gene):
		self.gene = gene

	def setMinimaxScore(self, minimaxScore):
		self.minimaxScore = minimaxScore 

	def setPlayer(self, player):
		self.player = player 

	def setBestScore(self, bestScore):
		self.bestScore = bestScore 

	def setBestMove(self, bestMove):
		self.bestMove = bestMove 

	def moveExists(self, move):
		if self.gene.move.moveCoordinates == move.moveCoordinates:
			return True 
		return False 

# class representing reservation tree 
class ReservationTree(object):
	def __init__(self):
		self.root = ReservationNode(0,0,0) 
		self.lastNodeId = 0

	def addChild(self, parent, gene):
		self.lastNodeId = self.lastNodeId + 1
		node = ReservationNode(self.lastNodeId, parent.getLevel()+1, parent)  
		gene.setId(self.lastNodeId)
		node.setGene(gene) 
		node.setPlayer(gene.move.player) 
		parent.addChild(node) 
		return node 

	def addChromosome(self, chromosome):
		parent = self.root 
		for i in range(len(chromosome.getGenes())):
			found = False 
			if len(parent.getChildren()) == 0:
				parent = self.addChild(parent, chromosome.getGenes()[i])
			else:
				for child in parent.getChildren():
					if child.moveExists(chromosome.getGenes()[i].move):
						found = True 
						parent = child 
						break 
				if found == False:
					# Add node to the tree 
					parent = self.addChild(parent, chromosome.getGenes()[i]) 
		

######################## INITIALIZE ########################

# will initialize board with all the pieces
def init_board():
	global move_limit
	move_limit[1] = 0 # reset move limit
	
	result = [
	[ 0, 1, 0, 1, 0, 1, 0, 1],
	[ 1, 0, 1, 0, 1, 0, 1, 0],
	[ 0, 1, 0, 1, 0, 1, 0, 1],
	[ 0, 0, 0, 0, 0, 0, 0, 0],
	[ 0, 0, 0, 0, 0, 0, 0, 0],
	[-1, 0,-1, 0,-1, 0,-1, 0],
	[ 0,-1, 0,-1, 0,-1, 0,-1],
	[-1, 0,-1, 0,-1, 0,-1, 0]
	] # initial board setting
	for m in range(8):
		for n in range(8):
			if (result[m][n] == 1):
				piece = Piece('black', False) # basic black piece
				result[m][n] = piece
			elif (result[m][n] == -1):
				piece = Piece('white', False) # basic white piece
				result[m][n] = piece
	return result

# initialize players
def init_player(type, color, strategy, ply_depth):
	return Player(type, color, strategy, ply_depth)

######################## FUNCTIONS ########################

# will return array with available moves to the player on board
def avail_moves(board, player):
    moves = [] # will store available jumps and moves

    for m in range(8):
        for n in range(8):
            if board[m][n] != 0 and board[m][n].color == player: # for all the players pieces...
                # ...check for jumps first
                if can_jump([m, n], [m+1, n+1], [m+2, n+2], board) == True: moves.append([m, n, m+2, n+2])
                if can_jump([m, n], [m-1, n+1], [m-2, n+2], board) == True: moves.append([m, n, m-2, n+2])
                if can_jump([m, n], [m+1, n-1], [m+2, n-2], board) == True: moves.append([m, n, m+2, n-2])
                if can_jump([m, n], [m-1, n-1], [m-2, n-2], board) == True: moves.append([m, n, m-2, n-2])

    if len(moves) == 0: # if there are no jumps in the list (no jumps available)
        # ...check for regular moves
        for m in range(8):
            for n in range(8):
                if board[m][n] != 0 and board[m][n].color == player: # for all the players pieces...
                    if can_move([m, n], [m+1, n+1], board) == True: moves.append([m, n, m+1, n+1])
                    if can_move([m, n], [m-1, n+1], board) == True: moves.append([m, n, m-1, n+1])
                    if can_move([m, n], [m+1, n-1], board) == True: moves.append([m, n, m+1, n-1])
                    if can_move([m, n], [m-1, n-1], board) == True: moves.append([m, n, m-1, n-1])

    return moves # return the list with available jumps or moves
                
# will return true if the jump is legal
def can_jump(a, via, b, board):
    # is destination off board?
    if b[0] < 0 or b[0] > 7 or b[1] < 0 or b[1] > 7:
        return False
    # does destination contain a piece already?
    if board[b[0]][b[1]] != 0: return False
    # are we jumping something?
    if board[via[0]][via[1]] == 0: return False
    # for white piece
    if board[a[0]][a[1]].color == 'white':
        if board[a[0]][a[1]].king == False and b[0] > a[0]: return False # only move up
        if board[via[0]][via[1]].color != 'black': return False # only jump blacks
        return True # jump is possible
    # for black piece
    if board[a[0]][a[1]].color == 'black':
        if board[a[0]][a[1]].king == False and b[0] < a[0]: return False # only move down
        if board[via[0]][via[1]].color != 'white': return False # only jump whites
        return True # jump is possible

# will return true if the move is legal
def can_move(a, b, board):
    # is destination off board?
    if b[0] < 0 or b[0] > 7 or b[1] < 0 or b[1] > 7:
        return False
    # does destination contain a piece already?
    if board[b[0]][b[1]] != 0: return False
    # for white piece (not king)
    if board[a[0]][a[1]].king == False and board[a[0]][a[1]].color == 'white':
        if b[0] > a[0]: return False # only move up
        return True # move is possible
    # for black piece
    if board[a[0]][a[1]].king == False and board[a[0]][a[1]].color == 'black':
        if b[0] < a[0]: return False # only move down
        return True # move is possible
    # for kings
    if board[a[0]][a[1]].king == True: return True # move is possible

# make a move on a board, assuming it's legit
def make_move(a, b, board):
    board[b[0]][b[1]] = board[a[0]][a[1]] # make the move
    board[a[0]][a[1]] = 0 # delete the source
    
    # check if we made a king
    if b[0] == 0 and board[b[0]][b[1]].color == 'white': board[b[0]][b[1]].king = True
    if b[0] == 7 and board[b[0]][b[1]].color == 'black': board[b[0]][b[1]].king = True
    
    if (a[0] - b[0]) % 2 == 0: # we made a jump...
        board[(a[0]+b[0])//2][(a[1]+b[1])//2] = 0 # delete the jumped piece

######################## CORE FUNCTIONS ########################

# will evaluate board for a player
def evaluate(game, player):

	''' this function just adds up the pieces on board (100 = piece, 175 = king) and returns the difference '''
	def simple_score(game, player):
		black, white = 0, 0 # keep track of score
		for m in range(8):
			for n in range(8):
				if (game[m][n] != 0 and game[m][n].color == 'black'): # select black pieces on board
					if game[m][n].king == False: black += 100 # 100pt for normal pieces
					else: black += 175 # 175pts for kings
				elif (game[m][n] != 0 and game[m][n].color == 'white'): # select white pieces on board
					if game[m][n].king == False: white += 100 # 100pt for normal pieces
					else: white += 175 # 175pts for kings
		if player != 'black': return white-black
		else: return black-white

	''' this function will add bonus to pieces going to opposing side '''
	def piece_rank(game, player):
		black, white = 0, 0 # keep track of score
		for m in range(8):
			for n in range(8):
				if (game[m][n] != 0 and game[m][n].color == 'black'): # select black pieces on board
					if game[m][n].king != True: # not for kings
						black = black + (m*m)
				elif (game[m][n] != 0 and game[m][n].color == 'white'): # select white pieces on board
					if game[m][n].king != True: # not for kings
						white = white + ((7-m)*(7-m))
		if player != 'black': return white-black
		else: return black-white

	''' a king on an edge could become trapped, thus deduce some points '''
	def edge_king(game, player):
		black, white = 0, 0 # keep track of score
		for m in range(8):
			if (game[m][0] != 0 and game[m][0].king != False):
				if game[m][0].color != 'white': black += -25
				else: white += -25
			if (game[m][7] != 0 and game[m][7].king != False):
				if game[m][7].color != 'white': black += -25
				else: white += -25
		if player != 'black': return white-black
		else: return black-white
	
	multi = random.uniform(0.97, 1.03) # will add +/- 3 percent to the score to make things more unpredictable

	return (simple_score(game, player) + piece_rank(game, player) + edge_king(game, player)) * 1

# have we killed the opponent already?
def end_game(board):
	black, white = 0, 0 # keep track of score
	for m in range(8):
		for n in range(8):
			if board[m][n] != 0:
				if board[m][n].color == 'black': black += 1 # we see a black piece
				else: white += 1 # we see a white piece

	return black, white

######################## GENETIC ALGORITHM CODE ########################

def printReservationTree(reservationNode):
	if len(reservationNode.getChildren()) == 0:
		return 
	else:
		for child in reservationNode.getChildren():
			print(child.getGene().move.moveCoordinates," Id: ",child.getId()," Parent: ",child.parent.id, " Gene: ", child.getGene())
			printReservationTree(child) 

def evaluateChromosomesHelper(reservationTree):
	def minimaxEval(reservationNode):
		if len(reservationNode.getChildren()) == 0:
			score = evaluate(reservationNode.getGene().move.board, reservationNode.getGene().move.player) 
			reservationNode.setMinimaxScore(score) 
			return score 
		else: 
			if reservationNode.getId() == 0:
				# Set the best move here 
				for child in reservationNode.getChildren():
					minimaxEval(child)
				for child in reservationNode.getChildren():
					if child.getMinimaxScore() >= child.getBestScore():
						reservationNode.setBestScore(child.getMinimaxScore())
						reservationNode.setBestMove(child.getGene().getMove().moveCoordinates) 
			else:
				if reservationNode.getPlayer() == 'black':
					alpha = -10000 
					for child in reservationNode.getChildren():
						temp_alpha = minimaxEval(child) 
						if temp_alpha > alpha:
							alpha = temp_alpha 
						reservationNode.setMinimaxScore(alpha) 
					return alpha 
				else:
					beta = 10000 
					for child in reservationNode.getChildren(): 
						temp_beta = minimaxEval(child) 
						if temp_beta < beta:
							beta = temp_beta 
						reservationNode.setMinimaxScore(beta) 
					return beta 

	def getAllPaths(reservationNode):
		if len(reservationNode.getChildren()) == 0:
			score = reservationNode.getMinimaxScore() 
			value = reservationNode.getGene() 
			value.setScore(score)
			return [[value]]
		paths = [] 
		for child in reservationNode.getChildren():
			for path in getAllPaths(child):
				score = child.getMinimaxScore() 
				value = child.getGene() 
				value.setScore(score) 
				paths.append([value] + path)
		return paths 

	def convertPathsToChromosomes(paths):
		chromosomes = []
		for path in paths:
			chromosome = Chromosome() 
			chromosome.setGenes(path) 
			chromosomes.append(chromosome) 
		return chromosomes 

	def geneticEval(chromosomes):
		for chromosome in chromosomes:
			leafVal = chromosome.getGenes()[len(chromosome.getGenes())-1]
			for gene in chromosome.getGenes()[::-1]:
				if gene.getScore() == leafVal:
					chromosome.setGeneticScore(chromosome.getGeneticScore()+1) 
		return chromosomes 

	minimaxEval(reservationTree.root) 
	bestScore = reservationTree.root.getBestScore()
	bestMove = reservationTree.root.getBestMove() 
	paths = getAllPaths(reservationTree.root) 
	chromosomes = convertPathsToChromosomes(paths) 
	chromosomes = geneticEval(chromosomes) 

	return (chromosomes, bestScore, bestMove)  

def evaluateChromosomes(reservationTree):
	chromosomes, bestScore, bestMove = evaluateChromosomesHelper(reservationTree) 
	while len(chromosomes) > 1:
		reservationTree = buildReservationTree(chromosomes) 
		chromosomes, bestScore, bestMove = evaluateChromosomesHelper(reservationTree) 
		chromosomes.sort(key=lambda x: x.getGeneticScore()) 
		chromosomes.pop() 

	if len(chromosomes) == 1:
		return (chromosomes[0], bestScore, bestMove)
	else:
		return (None,0,0)

def buildReservationTree(chromosomes):
	reservationTree = ReservationTree()
	# crossover 
	if len(chromosomes) > 1:
		for i in range(0, len(chromosomes)-1):
			if len(chromosomes[i].getGenes()) == len(chromosomes[i+1].getGenes()):
				c1, c2 = chromosomes[i].crossover(chromosomes[i+1]) 
				chromosomes[i] = c1 
				chromosomes[i+1] = c2 

	# mutation 
	for i in range(0, len(chromosomes)):
		if random.uniform(0,1) >= 0.5:
			c = chromosomes[i].mutate()
			chromosomes[i] = c
	
	for chromosome in chromosomes:
		reservationTree.addChromosome(chromosome) 

	return reservationTree

def buildChromosome(board, player, ply, chromosome):
	ply_depth = 0 
	if player != 'black': ply_depth = white.ply_depth 
	else: ply_depth = black.ply_depth 

	end = end_game(board) 

	if ply >= ply_depth or end[0] == 0 or end[1] == 0:
		chromosome.leafBoard = board 
		return 
 
	moves = avail_moves(board, player) 
	if len(moves) <= 0:
		return None 
	i = random.randint(0, len(moves)-1)
	new_board = deepcopy(board)
	make_move((moves[i][0], moves[i][1]), (moves[i][2], moves[i][3]), new_board) 

	move = Move([(moves[i][0], moves[i][1]), (moves[i][2], moves[i][3])], new_board, player) 
	chromosome.addGene(move)

	if player == 'black': player = 'white' 
	else: player = 'black' 

	buildChromosome(new_board, player, ply+1, chromosome)

	return chromosome 

def getAllChromosomes(board, player, ply, numChromosomes):
	chromosomeList = []  
	counter = 0 
	while counter < numChromosomes:
		chromosomeList.append(buildChromosome(board, player, ply, Chromosome())) 
		counter = counter + 1 
	return chromosomeList 

######################## GENETIC ALGORITHM CODE ########################

# will generate possible moves and board states until a given depth
''' http://en.wikipedia.org/wiki/Minimax '''
''' function minimax(node, depth) '''
def minimax(board, player, ply):
	global best_move
	# find out ply depth for player
	ply_depth = 0
	if player != 'black': ply_depth = white.ply_depth
	else: ply_depth = black.ply_depth

	end = end_game(board)

	''' if node is a terminal node or depth = CutoffDepth '''
	if ply >= ply_depth or end[0] == 0 or end[1] == 0: # are we still playing?
		''' return the heuristic value of node '''
		score = evaluate(board, player) # return evaluation of board as we have reached final ply or end state
		return score
		
	''' if the adversary is to play at node '''
	if player != turn: # if the opponent is to play on this node...
		
		''' let beta := +infinity '''
		beta = +10000
		
		''' foreach child of node '''
		moves = avail_moves(board, player) # get the available moves for player
		for i in range(len(moves)):
			# create a deep copy of the board (otherwise pieces would be just references)
			new_board = deepcopy(board)
			make_move((moves[i][0], moves[i][1]), (moves[i][2], moves[i][3]), new_board) # make move on new board
			
			''' beta := min(beta, minimax(child, depth+1)) '''
			# ...make a switch of players for minimax...
			if player == 'black': player = 'white'
			else: player = 'black'
								
			temp_beta = minimax(new_board, player, ply+1)
			if temp_beta < beta:
				beta = temp_beta # take the lowest beta

		''' return beta '''
		return beta
	
	else: # else we are to play
		''' else {we are to play at node} '''
		''' let alpha := -infinity '''
		alpha = -10000
		
		''' foreach child of node '''
		moves = avail_moves(board, player) # get the available moves for player
		for i in range(len(moves)):
			# create a deep copy of the board (otherwise pieces would be just references)
			new_board = deepcopy(board)
			make_move((moves[i][0], moves[i][1]), (moves[i][2], moves[i][3]), new_board) # make move on new board
							
			''' alpha := max(alpha, minimax(child, depth+1)) '''							
			# ...make a switch of players for minimax...
			if player == 'black': player = 'white'
			else: player = 'black'
			
			temp_alpha = minimax(new_board, player, ply+1)
			if temp_alpha > alpha:
				alpha = temp_alpha # take the highest alpha
				if ply == 0: best_move = (moves[i][0], moves[i][1]), (moves[i][2], moves[i][3]) # save the move as it's our turn

		''' return alpha '''
		return alpha

''' http://en.wikipedia.org/wiki/Negascout '''
''' function negascout(node, depth, alpha, beta) '''
def negascout(board, ply, alpha, beta, player):
	global best_move

	# find out ply depth for player
	ply_depth = 0
	if player != 'black': ply_depth = white.ply_depth
	else: ply_depth = black.ply_depth

	end = end_game(board)
	
	''' if node is a terminal node or depth = 0 '''
	if ply >= ply_depth or end[0] == 0 or end[1] == 0: # are we still playing?
		''' return the heuristic value of node '''
		score = evaluate(board, player) # return evaluation of board as we have reached final ply or end state
		return score
	''' b := beta '''
	b = beta

	''' foreach child of node '''
	moves = avail_moves(board, player) # get the available moves for player
	for i in range(len(moves)):
		# create a deep copy of the board (otherwise pieces would be just references)
		new_board = deepcopy(board)
		make_move((moves[i][0], moves[i][1]), (moves[i][2], moves[i][3]), new_board) # make move on new board

		''' alpha := -negascout (child, depth-1, -b, -alpha) '''
		# ...make a switch of players
		if player == 'black': player = 'white'
		else: player = 'black'

		alpha = -negascout(new_board, ply+1, -b, -alpha, player)
		''' if alpha >= beta '''
		if alpha >= beta:
			''' return alpha '''
			return alpha # beta cut-off
		''' if alpha >= b '''
		if alpha >= b: # check if null-window failed high

			''' alpha := -negascout(child, depth-1, -beta, -alpha) '''
			# ...make a switch of players
			if player == 'black': player = 'white'
			else: player = 'black'

			alpha = -negascout(new_board, ply+1, -beta, -alpha, player) # full re-search
			''' if alpha >= beta '''
			if alpha >= beta:
				''' return alpha '''
				return alpha # beta cut-off
		''' b := alpha+1 '''
		b = alpha+1 # set new null window
	''' return alpha '''
	if ply == 0: best_move = (moves[i][0], moves[i][1]), (moves[i][2], moves[i][3]) # save the move
	return alpha

''' http://en.wikipedia.org/wiki/Negamax '''
''' function negamax(node, depth, alpha, beta) '''
def negamax(board, ply, alpha, beta, player):
	global best_move

	# find out ply depth for player
	ply_depth = 0
	if player != 'black': ply_depth = white.ply_depth
	else: ply_depth = black.ply_depth

	end = end_game(board)

	''' if node is a terminal node or depth = 0 '''
	if ply >= ply_depth or end[0] == 0 or end[1] == 0: # are we still playing?
		''' return the heuristic value of node '''
		score = evaluate(board, player) # return evaluation of board as we have reached final ply or end state
		return score

	''' else '''
	''' foreach child of node '''
	moves = avail_moves(board, player) # get the available moves for player
	for i in range(len(moves)):
		# create a deep copy of the board (otherwise pieces would be just references)
		new_board = deepcopy(board)
		make_move((moves[i][0], moves[i][1]), (moves[i][2], moves[i][3]), new_board) # make move on new board

		''' alpha := max(alpha, -negamax(child, depth-1, -beta, -alpha)) '''
		# ...make a switch of players
		if player == 'black': player = 'white'
		else: player = 'black'

		temp_alpha = -negamax(new_board, ply+1, -beta, -alpha, player)
		if temp_alpha >= alpha:
			if ply == 0: best_move = (moves[i][0], moves[i][1]), (moves[i][2], moves[i][3]) # save the move
			alpha = temp_alpha

		''' {the following if statement constitutes alpha-beta pruning} '''
		''' if alpha>=beta '''
		if alpha >= beta:
			''' return beta '''
			if ply == 0: best_move = (moves[i][0], moves[i][1]), (moves[i][2], moves[i][3]) # save the move
			return beta
	''' return alpha '''
	return alpha

''' http://www.ocf.berkeley.edu/~yosenl/extras/alphabeta/alphabeta.html '''
''' alpha-beta(player,board,alpha,beta) '''
def alpha_beta(player, board, ply, alpha, beta):
	global best_move
	# find out ply depth for player
	ply_depth = 0
	if player != 'black': ply_depth = white.ply_depth
	else: ply_depth = black.ply_depth

	end = end_game(board)

	''' if(game over in current board position) '''
	if ply >= ply_depth or end[0] == 0 or end[1] == 0: # are we still playing?
		''' return winner '''
		score = evaluate(board, player) # return evaluation of board as we have reached final ply or end state
		return score

	''' children = all legal moves for player from this board '''
	moves = avail_moves(board, player) # get the available moves for player

	''' if(max's turn) '''
	if player == turn: # if we are to play on node...
		''' for each child '''
		for i in range(len(moves)):
			# create a deep copy of the board (otherwise pieces would be just references)
			new_board = deepcopy(board)
			make_move((moves[i][0], moves[i][1]), (moves[i][2], moves[i][3]), new_board) # make move on new board

			''' score = alpha-beta(other player,child,alpha,beta) '''
			# ...make a switch of players for minimax...
			if player == 'black': player = 'white'
			else: player = 'black'

			score = alpha_beta(player, new_board, ply+1, alpha, beta)

			''' if score > alpha then alpha = score (we have found a better best move) '''
			if score > alpha:
				if ply == 0: best_move = (moves[i][0], moves[i][1]), (moves[i][2], moves[i][3]) # save the move
				alpha = score
			''' if alpha >= beta then return alpha (cut off) '''
			if alpha >= beta:
				#if ply == 0: best_move = (moves[i][0], moves[i][1]), (moves[i][2], moves[i][3]) # save the move
				return alpha

		''' return alpha (this is our best move) '''
		return alpha

	else: # the opponent is to play on this node...
		''' else (min's turn) '''
		''' for each child '''
		for i in range(len(moves)):
			# create a deep copy of the board (otherwise pieces would be just references)
			new_board = deepcopy(board)
			make_move((moves[i][0], moves[i][1]), (moves[i][2], moves[i][3]), new_board) # make move on new board

			''' score = alpha-beta(other player,child,alpha,beta) '''
			# ...make a switch of players for minimax...
			if player == 'black': player = 'white'
			else: player = 'black'

			score = alpha_beta(player, new_board, ply+1, alpha, beta)

			''' if score < beta then beta = score (opponent has found a better worse move) '''
			if score < beta: beta = score
			''' if alpha >= beta then return beta (cut off) '''
			if alpha >= beta: return beta
		''' return beta (this is the opponent's best move) '''
		return beta

# end turn
def end_turn():
	global turn # use global variables

	if turn != 'black':	turn = 'black'
	else: turn = 'white'

# play as a computer
def cpu_play(player):
	global minimaxTime
	startTime = time.time() 
	global board, move_limit# global variables

	# find and print the best move for cpu
	if player.strategy == 'minimax': alpha = minimax(board, player.color, 0)
	elif player.strategy == 'negascout': alpha = negascout(board, 0, -10000, +10000, player.color)
	elif player.strategy == 'negamax': alpha = negamax(board, 0, -10000, +10000, player.color)
	elif player.strategy == 'alpha-beta': alpha = alpha_beta(player.color, board, 0, -10000, +10000)
	#print player.color, alpha
	if alpha == -10000: # no more moves available... all is lost
		if player.color == white: 
			show_winner("black")
		else: 
			show_winner("white")

	make_move(best_move[0], best_move[1], board) # make the move on board

	move_limit[1] += 1 # add to move limit

	end_turn() # end turn
	endTime = time.time() 
	minimaxTime += (endTime - startTime)

# genetic cpu 
def genetic_cpu(player):
	global geneticTime
	startTime = time.time() 
	global board, move_limit# global variables

	# find and print the best move for cpu
	if player.strategy == 'minimax': alpha = minimax(board, player.color, 0)
	elif player.strategy == 'negascout': alpha = negascout(board, 0, -10000, +10000, player.color)
	elif player.strategy == 'negamax': alpha = negamax(board, 0, -10000, +10000, player.color)
	elif player.strategy == 'alpha-beta': alpha = alpha_beta(player.color, board, 0, -10000, +10000)
	elif player.strategy == 'genetic':
		chromosomes = getAllChromosomes(board, player.color, 0, 4) 
		if len(chromosomes) == 0 or None in chromosomes:
			'''if player.color == white: 
				show_winner("black")
			else: 
				show_winner("white")'''
			move_limit[1] += 1 
			end_turn() 
			endTime = time.time() 
			geneticTime += (endTime - startTime)
			return 
		else:
			reservationTree = buildReservationTree(chromosomes) 
			chromosome,alpha,best_move = evaluateChromosomes(reservationTree) 
			if chromosome == None and alpha == 0 and best_move == 0:
				'''if player.color == white: 
					show_winner("black")
				else: 
					show_winner("white")'''
				move_limit[1] += 1 
				end_turn() 
				endTime = time.time() 
				geneticTime += (endTime - startTime)
				return 

	if alpha == -10000: # no more moves available... all is lost
		if player.color == white: 
			show_winner("black")
		else: 
			show_winner("white")

	make_move(best_move[0], best_move[1], board) # make the move on board

	move_limit[1] += 1 # add to move limit

	end_turn() # end turn
	endTime = time.time() 
	geneticTime += (endTime - startTime) 

# make changes to ply's if playing vs genetic (problem with scope)
def ply_check():
	global black, white

	''' if genetic has higher ply_setting, cpu will do unnecessary calculations '''
	if black.type != 'cpu': black.ply_depth = white.ply_depth
	elif white.type != 'cpu': white.ply_depth = black.ply_depth

# will check for errors in players settings
def player_check():
	global black, white

	if black.type != 'cpu' or black.type != 'genetic': black.type = 'cpu'
	if white.type != 'cpu' or white.type != 'genetic': white.type = 'cpu'

	if black.ply_depth <0: black.ply_depth = 1
	if white.ply_depth <0: white.ply_depth = 1

	if black.color != 'black': black.color = 'black'
	if white.color != 'white': white.color = 'white'

	if black.strategy != 'minimax' or black.strategy != 'negascout':
		if black.strategy != 'negamax' or black.strategy != 'alpha-beta': black.strategy = 'alpha-beta'
	if white.strategy != 'minimax' or white.strategy != 'negascout':
		if white.strategy != 'negamax' or white.strategy != 'alpha-beta': white.strategy = 'alpha-beta'

# initialize players and the boardfor the game
def game_init(difficulty):
	global black, white # work with global variables
	if difficulty == '6':
		black = init_player('cpu', 'black', 'minimax', 6) # init black player
		white = init_player('genetic', 'white', 'minimax', 6) # init white player
		board = init_board()
	elif difficulty == '5':
		black = init_player('cpu', 'black', 'minimax', 5) # init black player
		white = init_player('genetic', 'white', 'minimax', 5) # init white player
		board = init_board()
	elif difficulty == '4':
		black = init_player('cpu', 'black', 'minimax', 4) # init black player
		white = init_player('genetic', 'white', 'minimax', 4) # init white player
		board = init_board()
	elif difficulty == '3':
		black = init_player('cpu', 'black', 'minimax', 3) # init black player
		white = init_player('genetic', 'white', 'minimax', 3) # init white player
		board = init_board()
	elif difficulty == '2':
		black = init_player('cpu', 'black', 'minimax', 2) # init black player
		white = init_player('genetic', 'white', 'minimax', 2) # init white player
		board = init_board()
	else:
		black = init_player('cpu', 'black', 'minimax', 1) # init black player
		white = init_player('genetic', 'white', 'minimax', 1) # init white player
		board = init_board()

	return board			

######################## GUI FUNCTIONS ########################

# function that will draw a piece on the board
def draw_piece(row, column, color, king):
	# find the center pixel for the piece
	posX = int(((window_size[0]/8)*column) - (window_size[0]/8)/2)
	posY = int(((window_size[1]/8)*row) - (window_size[1]/8)/2)
	
	# set color for piece
	if color == 'black':
		border_color = (255, 255, 255)
		inner_color = (0, 0, 0)
	elif color == 'white':
		border_color = (0, 0, 0)
		inner_color = (255, 255, 255)
	
	pygame.draw.circle(screen, border_color, (posX, posY), 12) # draw piece border
	pygame.draw.circle(screen, inner_color, (posX, posY), 10) # draw piece
	
	# draw king 'status'
	if king == True:
		pygame.draw.circle(screen, border_color, (posX+3, posY-3), 12) # draw piece border
		pygame.draw.circle(screen, inner_color, (posX+3, posY-3), 10) # draw piece

# show message for user on screen
def show_message(message):
	text = font.render(' '+message+' ', True, (255, 255, 255), (120, 195, 46)) # create message
	textRect = text.get_rect() # create a rectangle
	textRect.centerx = screen.get_rect().centerx # center the rectangle
	textRect.centery = screen.get_rect().centery
	screen.blit(text, textRect) # blit the text

# show countdown on screen
def show_countdown(i):
	while i >= 0:
		tim = font_big.render(' '+repr(i)+' ', True, (255, 255, 255), (20, 160, 210)) # create message
		timRect = tim.get_rect() # create a rectangle
		timRect.centerx = screen.get_rect().centerx# center the rectangle
		timRect.centery = screen.get_rect().centery +50
		screen.blit(tim, timRect) # blit the text
		pygame.display.flip() # display scene from buffer
		i-=1
		pygame.time.wait(1000) # pause game for a second

# will display the winner and do a countdown to a new game
def show_winner(winner):
	global board, round, minimaxWins, geneticWins, draws, geneticTime, minimaxTime, fileNum, genetic_ply, minimax_ply
	if genetic_ply > 6:
		exit() 
	if winner == "black":
		minimaxWins += 1 
	if winner == "white":
		geneticWins += 1
	if winner == "draw":
		draws += 1
	round += 1 
	print("Round: ",round) 
	print("Genetic Time: ",geneticTime/round) 
	print("Minimax Time: ",minimaxTime/round) 
	print("Winner is: ",winner)  
	print("Minimax Wins: ",minimaxWins)  
	print("Genetic Wins: ",geneticWins)  
	print("Draws: ",draws)  
	print("---------------------------")
	exists = os.path.isfile("C:\\pycheckers\\ply"+str(fileNum)+".txt")
	if exists:
		file = open("ply"+str(fileNum)+".txt","a")
		file.write("Round: "+str(round)+'\n') 
		file.write("Genetic Time: "+str(geneticTime/round)+'\n') 
		file.write("Minimax Time: "+str(minimaxTime/round)+'\n') 
		file.write("Winner is: "+str(winner)+'\n')  
		file.write("Minimax Wins: "+str(minimaxWins)+'\n')  
		file.write("Genetic Wins: "+str(geneticWins)+'\n')  
		file.write("Draws: "+str(draws)+'\n')  
		file.write("---------------------------\n\n")
		file.close() 
	else:
		file = open("ply"+str(fileNum)+".txt","w")
		file.write("Round: "+str(round)+'\n')  
		file.write("Genetic Time: "+str(geneticTime/round)+'\n') 
		file.write("Minimax Time: "+str(minimaxTime/round)+'\n') 
		file.write("Winner is: "+str(winner)+'\n')  
		file.write("Minimax Wins: "+str(minimaxWins)+'\n')  
		file.write("Genetic Wins: "+str(geneticWins)+'\n')  
		file.write("Draws: "+str(draws)+'\n')  
		file.write("---------------------------\n\n")
		file.close() 
	if winner == 'draw': show_message("draw, press 'F1' to exit")
	else: show_message(winner+" wins, press 'F1' to exit")
	pygame.display.flip() # display scene from buffer
	show_countdown(pause) # show countdown for number of seconds
	board = init_board() # ... and start a new game
	if round == 100: 
		print("Moving on to ply: ",genetic_ply+1) 
		print("---------------------------")
		round = 0 
		geneticTime = 0 
		geneticWins = 0 
		genetic_ply += 1 
		minimaxTime = 0 
		minimaxWins = 0 
		minimax_ply += 1
		fileNum += 1
		draws = 0 
		board = game_init(minimax_ply)

# running the genetic algorithm 
def runGenetic(strategy, ply_depth):
	if turn != 'black' and white.type != 'cpu':
		white.strategy = strategy 
		white.ply_depth = ply_depth 
		genetic_cpu(white) 
	elif turn != 'black' and black.type != 'cpu':
		black.strategy = strategy 
		black.ply_depth = ply_depth 
		genetic_cpu(black) 

######################## START OF GAME ########################

pygame.init() # initialize pygame

board = game_init(minimax_ply) # initialize players and board for the game

#player_check() # will check for errors in player settings
ply_check() # make changes to player's ply if playing vs genetic

screen = pygame.display.set_mode(window_size) # set window size
pygame.display.set_caption(title) # set title of the window
clock = pygame.time.Clock() # create clock so that game doesn't refresh that often

background = pygame.image.load(background_image_filename).convert() # load background
font = pygame.font.Font('freesansbold.ttf', 11) # font for the messages
font_big = pygame.font.Font('freesansbold.ttf', 13) # font for the countdown

while True: # main game loop
	for event in pygame.event.get(): # the event loop
		if event.type == QUIT:
			exit() # quit game
		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_F1: 
				exit()
	if start == False:
		runGenetic('genetic', genetic_ply) 

	screen.blit(background, (0, 0)) # keep the background at the same spot
	
	# draw pieces on board
	for m in range(8):
		for n in range(8):
			if board[m][n] != 0:
				draw_piece(m+1, n+1, board[m][n].color, board[m][n].king)

	# show intro
	if start == True:
		show_message('Welcome to '+title)
		show_countdown(pause)
		start = False

	# check state of game
	end = end_game(board)
	if end[1] == 0:	show_winner("black")
	elif end[0] == 0: show_winner("white")

	# check if we breached the threshold for number of moves	
	elif move_limit[0] == move_limit[1]: show_winner("draw")

	else: pygame.display.flip() # display scene from buffer

	# cpu play	
	if turn != 'black' and white.type == 'cpu': cpu_play(white) # white cpu turn
	elif turn != 'white' and black.type == 'cpu': cpu_play(black) # black cpu turn
	
	clock.tick(fps) # saves cpu time