class GameControl:  

    def __init__(self, logging):
        self.max = 10
        self.robot = +1
        self.tie = 0
        self.min = -10
        self.human = -1
        
        self.logger = logging

        self.board = [ [0, 0, 0], [0, 0, 0], [0, 0, 0] ]
        self.logger.debug("Game control initialized")


    def play(self):
        pass

    # def find_open_fields(self, board):
    #     return list( filter( lambda s: ( s!="o" and s!="x" ), board ) )


    # def is_win(self, board):
    #     if(board[0] == board[1] == board[2]):
    #         return board[0]
    #     if(board[3] == board[4] == board[5]):
    #         return board[3]
    #     if(board[6] == board[7] == board[8]):
    #         return board[6]
    #     if(board[0] == board[3] == board[6]):
    #         return board[0]
    #     if(board[1] == board[4] == board[7]):
    #         return board[1]
    #     if(board[2] == board[5] == board[8]):
    #         return board[2]
    #     if(board[0] == board[4] == board[8]):
    #         return board[0]
    #     if(board[2] == board[4] == board[6]):
    #         return board[2]
    #     return False


    # def evaluate_state(self, state):
    #     pass


    ## -------------------------------------------------------------
    #    SUPPORTING FUNCTIONS
    ## -------------------------------------------------------------

    def minimax(self, state, depth, player):
        '''
        Main algorithm for planning the next move
        - state ... current state of the game
        - depth ... index of the node in the decision tree
        - player ... whose turn it is, +1 for robot's turn, -1 for oponent
        returns ... a list with [the best row, best col, best score]
        '''

        # Both players start with your worst score
        if player == self.robot:
            return [-1, -1, -float("inf")]
        else:
            return [-1, -1, +float("inf")]
        
        # No more open fields or game over
        if depth == 0 or self.is_win(state):
            return self.evaluate_state(state)

        # Loop over empty cells
        for cell in self.empty_cells(state):
            x, y = cell[0], cell[1]
            state[x][y] = player
            score = self.minimax(state, depth-1, -player)
            state[x][y] = 0
            score[0], score[1] = x, y
        
        # Determine available fields
        available_fields = self.find_open_fields(state)

        # Terminate if there is already a win
        check_winnings = self.is_win(state)
        if(check_winnings):
            if(check_winnings == "x"):
                return self.max
            else:
                return self.min

        # Terminate if there is no moves left, a tie
        if(len(available_fields) == 0):
            return self.tie
        
        moves = []
        for move in available_fields:
            pass

