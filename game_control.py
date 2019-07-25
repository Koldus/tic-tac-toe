import time

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


    def play(self, board):
        
        # Check if the game hasn't ended by human's move
        cur_status = self.evaluate_board(board)
        if cur_status == None:
            depth = len(self.empty_cells(board))
            move = self.minimax(board, depth, self.robot)
            
            # Evaluate also the status after robot's move
            board[move[0]][move[1]] = self.robot
            move[2] = self.evaluate_board(board)
            self.logger.info('Robot\'s move: ' + str(move) )

            return move
        else:
            return [None, None, cur_status]


    ## -------------------------------------------------------------
    #    SUPPORTING FUNCTIONS
    ## -------------------------------------------------------------
    
    def evaluate_board(self, board):
        depth = len(self.empty_cells(board))
        evaluate_state = self.is_win(board)
        if depth == 0 or evaluate_state:
            if evaluate_state == self.max:
                return self.robot
            elif evaluate_state == self.min:
                return self.human
            return self.tie
        return None


    def is_win(self, board):
        '''
        Function to determing number of open fields
        - state ... the state of the current board
        return ... winner represenation if game over, or false if nots
        '''
        win_state = [
            [board[0][0], board[0][1], board[0][2]],
            [board[1][0], board[1][1], board[1][2]],
            [board[2][0], board[2][1], board[2][2]],
            [board[0][0], board[1][0], board[2][0]],
            [board[0][1], board[1][1], board[2][1]],
            [board[0][2], board[1][2], board[2][2]],
            [board[0][0], board[1][1], board[2][2]],
            [board[2][0], board[1][1], board[0][2]],
        ]

        if [self.robot, self.robot, self.robot] in win_state:
            return self.max
        elif [self.human, self.human, self.human] in win_state:
            return self.min
        else:
            return False


    def empty_cells(self, board):
        '''
        Function to determing number of open fields
        - state ... the state of the current board
        return ... a list of empty cells
        '''
        cells = []
        for x, row in enumerate(board):
            for y, cell in enumerate(row):
                if cell == 0:
                    cells.append([x, y])

        return cells


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
            best = [-1, -1, -1000]
        else:
            best = [-1, -1, +1000]
        
        # No more open fields or game over
        evaluate_state = self.is_win(state)
        if depth == 0 or evaluate_state:
            return [-1, -1, evaluate_state]

        # Loop over empty cells
        for cell in self.empty_cells(state):
            x, y = cell[0], cell[1]
            state[x][y] = player
            score = self.minimax(state, depth-1, -player)
            state[x][y] = 0
            score[0], score[1] = x, y

            if player == self.robot:
                if score[2] > best[2]:
                    best = score  # max value
            else:
                if score[2] < best[2]:
                    best = score # min value

        return best


    def render(self, state):
        """
        Print the board on console
        :param state: current state of the board
        """
        str_line = '---------------'

        print(str_line)
        for row in state:
            row_rendered = ''
            for cell in row:
                if cell == +1:
                    row_rendered = row_rendered + '| x |'
                elif cell == -1:
                    row_rendered = row_rendered + '| o |'
                else:
                    row_rendered = row_rendered + '|   |'
            print(row_rendered)
            print(str_line)