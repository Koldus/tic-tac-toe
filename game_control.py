from game_logging import GameLogger

class GameControl:  

    def __init__(self):
        self.max = 10
        self.tie = 0
        self.min = -10

        self.logger = GameLogger()

        self.board = [0,1,2,3,4,5,6,7,8]
        self.logger.message("g", "Game control initialized")


    def find_open_fields(self, board):
        return list( filter( lambda s: ( s!="o" and s!="x" ), board ) )


    def is_win(self, board):
        if(board[0] == board[1] == board[2]):
            return board[0]
        if(board[3] == board[4] == board[5]):
            return board[3]
        if(board[6] == board[7] == board[8]):
            return board[6]
        if(board[0] == board[3] == board[6]):
            return board[0]
        if(board[1] == board[4] == board[7]):
            return board[1]
        if(board[2] == board[5] == board[8]):
            return board[2]
        if(board[0] == board[4] == board[8]):
            return board[0]
        if(board[2] == board[4] == board[6]):
            return board[2]
        return False


    def minimax(self, state, player):
        
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

