#libararies for game
import pygame
import random
from enum import Enum
import copy
import math

pygame.init()
pygame.font.init()

WIN_WIDTH = 600
WIN_HEIGHT = 800+100
COLOURS = [(0,0,0),(255,0,0),(255,128,0),(255,255,0),(0,255,0),(0,255,255),(0,0,255),(127,0,255)]
font = pygame.font.Font('freesansbold.ttf', 16)

INCREASE_OVER_TIME = 1
INCREASE_ON_PLACEMENT = 0
LOSE_ON_LOSS = 50


class UserIn(Enum):
    EMPTY = -1
    LEFT = 0
    RIGHT = 1
    ROTATE = 2
    SPACE = 3
    HOLD = 4
    DOWN = 5
    SWAPLEFT = 6
    SWAPRIGHT = 7
    
class Board: 
    def __init__(self):
        self.stackTiles = [[0 for _ in range(10)] for _ in range(20)]
        self.allTiles = [[0 for _ in range(10)] for _ in range(20)]
        self.lost = False
        self.points = 0
        self.placedHeight = -1
        self.rowsCleared = 0
        
    def writeBoard(self, piece):
        piece.setCoords()
        coords = piece.getCoords()
        colour = piece.pType
        
        for i in range(20):
            for j in range(10):
                self.allTiles[i][j] = self.stackTiles[i][j]
        
        for coord in coords:
            x = coord[0]
            y = coord[1]
            
            if x>=0 and x<=9 and y>=0 and y<=19:
                self.allTiles[y][x] = colour
                
    def clearBoard(self):
        for i in range(20):
            for j in range(10):
                self.allTiles[i][j] = 0
        
    def fullyClearBoard(self):
        for i in range(20):
            for j in range(10):
                self.stackTiles[i][j] = 0
                self.allTiles[i][j] = 0
        
    def printBoard(self):
        for row in self.allTiles:
            for tile in row:
                print(tile, end=" ")
            print()
            
    def checkCollision(self, piece):
        for i in range(20):
            for j in range(10):
                for coord in piece.getCoords():
                    if((self.stackTiles[i][j]!=0 and coord[0]==j and coord[1]==i) or coord[1]>=20):
                        return True
        return False
    
    def addPiece(self, piece):
        for coord in piece.getCoords():
            x = coord[0]
            y = coord[1]
            if x >= 0 and y >= 0 and x < 10 and y < 20:
                self.stackTiles[y][x] = piece.pType
            
    def clearRow(self, index):
        for i in range(index,0,-1):
            for j in range(10):
                self.stackTiles[i][j] = self.stackTiles[i-1][j]
        for i in range(10):
            self.stackTiles[0][i] = 0
    
    def checkRowClear(self):
        count = 0
        
        for i in range(20):
            row = self.stackTiles[i]
            full = True
            for tile in row:
                if tile==0:
                    full = False
            
            if full:
                self.clearRow(i)
                count+=1
                self.rowsCleared += 1
        
        if count == 1:
            self.points += 40
        elif count == 2:
            self.points += 100
        elif count == 3:
            self.points += 300
        elif count == 4:
            self.points += 1200
                
    def checkLoss(self, piece):
        for coord in piece.getCoords():
            if coord[1]<0:
                self.lost = True
                return
                
    def getLost(self):
        return self.lost
    
    def restart(self, piece):
        self.fullyClearBoard()
        piece.newPiece(self)
        self.lost = False
        self.points = 0
        self.rowsCleared = 0
    
    def getPoints(self):
        return self.points
 
    def getHoles(self, heights):
        holesNum = 0
        
        for i in range(1,20):
            for j in range(10):
                if self.stackTiles[i][j] == 0 and i>heights[j]:
                    holesNum += 1
        
        return holesNum
    
    def getPlacedHeight(self):
        return self.placedHeight
    
    def getRowHeights(self):
        heights = [0]*10
        
        for x in range(10):
            for y in range(20):
                if self.stackTiles[y][x] != 0:
                    heights[x] = 20-y
                    break
        
        return heights
        
    def getRowTransitions(self, heights):
        transNum = 0
        
        for i in range(9):
            if heights[i] != heights[i+1]:
                transNum += 1
        
        return transNum
    
    def getBumpiness(self, heights):
        bumpiness = 0
        
        for i in range(9):
            bumpiness += abs(heights[i] - heights[i+1])
        
        return bumpiness
    
    def getTotalHeight(self, heights):
        totalHeight = 0
        
        for i in range(10):
            totalHeight += heights[i]
        
        return totalHeight
    
    def getRowsJustCleared(self, oldRowsCleared):
        return self.rowsCleared-oldRowsCleared
    
    def getWells(self, heights):
        wells = 0
        
        if abs(heights[0]-heights[1])>2:
            wells += 1
        
        if abs(heights[9]-heights[8])>2:
            wells += 1
        
        for i in range(1,9):
            if abs(heights[i]-heights[i-1])>2 and abs(heights[i]-heights[i+1])>2:
                wells += 1
        
        return wells
 
class Piece:
    def __init__(self, board):
        self.pType = random.randrange(1,8)
        self.x = 5
        self.y = 1
        self.rot = 0
        self.setCoords()
        self.lineUp = [random.randrange(1,8),random.randrange(1,8),random.randrange(1,8)]
        self.hold = random.randrange(1,8)
        self.board = board
            
    def moveSideways(self, direction):
        oldPos = self.x
        
        if(direction):
            self.x += 1
        else:
            self.x -= 1 
        self.setCoords()
        
        if self.board.checkCollision(self) or self.checkWallCollision():
            self.x = oldPos
            self.setCoords()
            
    def moveDown(self, board):
        oldPos = self.y
        
        self.y += 1
        self.setCoords()
        
        if board.checkCollision(self):
            self.y = oldPos
            self.setCoords()
            board.placedHeight = self.y
            board.addPiece(self)
            self.newPiece(board)
            board.checkRowClear()
            return False
        return True
            
    def rotate(self, board):
        oldRot = self.rot
        
        self.rot = (self.rot+1)%4
        self.setCoords()
        
        if board.checkCollision(self) or self.checkWallCollision():
            self.rot = oldRot
            self.setCoords()
            
    def holdPiece(self, board):
        oldPiece = self.pType
        oldHold = self.hold
        oldRot = self.rot
        
        if oldHold == 0:
            self.pType = self.lineUp[0]
            self.rot = 0
            self.setCoords()
            self.hold = self.pType
            self.lineUp[0]=self.lineUp[1]
            self.lineUp[1]=self.lineUp[2]
            self.lineUp[2]=random.randrange(1,8)
            
            if board.checkCollision(self) or self.checkWallCollision():
                self.lineUp[2]=self.lineUp[1]
                self.lineUp[1]=self.lineUp[0]
                self.lineUp[0]=self.pType
                self.pType = oldPiece
                self.hold = 0
                self.rot = oldRot
                self.setCoords()
            
        else:
            self.hold = oldPiece
            self.pType = oldHold
            self.setCoords()
        
            if board.checkCollision(self) or self.checkWallCollision():
                self.hold = oldHold
                self.pType = oldPiece
                self.setCoords()
        
    def drop(self, board):
        keepGoing = True
        
        while(keepGoing):
            keepGoing = self.moveDown(board)
            
    def setCoords(self):
        x = self.x
        y = self.y
        
        #red z
        if (self.pType == 1):
            if (self.rot == 2):
                self.coords = [[x,y],[x-1,y],[x,y+1],[x+1,y+1]]
            elif (self.rot == 3):
                self.coords = [[x,y],[x,y-1],[x-1,y],[x-1,y+1]]
            elif (self.rot == 0):
                self.coords = [[x,y],[x,y-1],[x-1,y-1],[x+1,y]]
            elif (self.rot == 1):
                self.coords = [[x,y],[x+1,y-1],[x+1,y],[x,y+1]]
        
        # orange L
        elif (self.pType == 2):
            if (self.rot == 0):
                self.coords = [[self.x,self.y],[self.x-1,self.y],[self.x+1,self.y],[self.x+1,self.y-1]]
            elif (self.rot == 1):
                self.coords = [[self.x,self.y],[self.x,self.y-1],[self.x,self.y+1],[self.x+1,self.y+1]]
            elif (self.rot == 2):
                self.coords = [[self.x,self.y],[self.x-1,self.y],[self.x+1,self.y],[self.x-1,self.y+1]]
            elif (self.rot == 3):
                self.coords = [[self.x,self.y],[self.x,self.y-1],[self.x,self.y+1],[self.x-1,self.y-1]]
                
        #yellow square
        if (self.pType == 3):
            self.coords = [[x,y],[x+1,y],[x,y+1],[x+1,y+1]]
        
        #green s
        if (self.pType == 4):
            if (self.rot == 0):
                self.coords = [[x,y],[x+1,y],[x-1,y+1],[x,y+1]]
            elif (self.rot == 1):
                self.coords = [[x,y],[x-1,y],[x-1,y-1],[x,y+1]]
            elif (self.rot == 2):
                self.coords = [[x,y],[x-1,y],[x,y-1],[x+1,y-1]]
            elif (self.rot == 3):
                self.coords = [[x,y],[x,y-1],[x+1,y],[x+1,y+1]]
                
        # I
        elif (self.pType == 5):
            if (self.rot == 0):
                self.coords = [[self.x,self.y],[self.x-1,self.y],[self.x+1,self.y],[self.x+2,self.y]]
            elif (self.rot == 1):
                self.coords = [[self.x,self.y],[self.x,self.y-1],[self.x,self.y+1],[self.x,self.y+2]]
            elif (self.rot == 2):
                self.coords = [[self.x,self.y],[self.x-1,self.y],[self.x+1,self.y],[self.x-2,self.y]]
            elif (self.rot == 3):
                self.coords = [[self.x,self.y],[self.x,self.y-1],[self.x,self.y+1],[self.x,self.y-2]]
                
        #blue L
        if (self.pType == 6):
            if (self.rot == 0):
                self.coords = [[x,y],[x+1,y],[x-1,y],[x-1,y-1]]
            elif (self.rot == 1):
                self.coords = [[x,y],[x,y+1],[x,y-1],[x+1,y-1]]
            elif (self.rot == 2):
                self.coords = [[x,y],[x+1,y],[x-1,y],[x+1,y+1]]
            elif (self.rot == 3):
                self.coords = [[x,y],[x,y+1],[x,y-1],[x-1,y+1]]
                
        #purple bump
        if (self.pType == 7):
            if (self.rot == 0):
                self.coords = [[x,y],[x+1,y],[x-1,y],[x,y-1]]
            elif (self.rot == 1):
                self.coords = [[x,y],[x,y+1],[x,y-1],[x+1,y]]
            elif (self.rot == 2):
                self.coords = [[x,y],[x+1,y],[x-1,y],[x,y+1]]
            elif (self.rot == 3):
                self.coords = [[x,y],[x,y+1],[x,y-1],[x-1,y]]
    
    def getCoords(self):
        return self.coords
    
    def newPiece(self, board):
        self.x = 5
        self.y = 1
        self.pType = self.lineUp[0]
        self.rot = 0
        self.setCoords()
        
        keepGoing = True
        while keepGoing:
            if board.checkCollision(self):
                self.y-=1
                self.setCoords()
            else:
                keepGoing = False
        
        self.setCoords()
        board.checkLoss(self)
        
        self.lineUp[0]=self.lineUp[1]
        self.lineUp[1]=self.lineUp[2]
        self.lineUp[2]=random.randrange(1,8)
        
    def checkWallCollision(self):
        for coord in self.coords:
            x = coord[0]
            if(x>9 or x<0):
                return True
        return False
    
    def printCoords(self):
        for coord in self.coords:
            print("[" + str(coord[0]) + "," + str(coord[1]) + "] ")
            
    def getLineUp(self):
        return self.lineUp
    
    def getHold(self):
        return self.hold
    
class Player:
    def __init__(self):
        self.board = Board()
        self.piece = Piece(self.board)
    
    def doAction(self, action):
        
        hold = math.floor(action/40)
        action = action%40
        r = math.floor(action/10)
        x = action % 10
        
        if hold == 1:
            self.piece.holdPiece(self.board)
        
        for i in range(4):
            self.piece.rotate(self.board)
            if self.piece.rot == r:
                break
        
        for i in range(5):
            if self.piece.x < x:
                self.piece.moveSideways(True)
            elif self.piece.x > x:
                self.piece.moveSideways(False)    
            elif self.piece.x == x:
                break
        
        if(self.board.checkCollision(self.piece)):
            self.board.lost = True
        
        self.piece.drop(self.board)
        
    
    def getStats(self, oldRowsCleared):
        board = self.board
        heights = board.getRowHeights()
        
        return (board.getHoles(heights), board.getBumpiness(heights), board.getTotalHeight(heights), board.getRowsJustCleared(oldRowsCleared))


        
def drawWindow(win,board,piece):
    tiles = board.allTiles
    
    text = font.render('TETRIS', True, (255,255,255), (0,0,0))
    textRect = text.get_rect()
    textRect.center = (WIN_WIDTH/2, 50)
    
    win.fill((0,0,0))
    win.blit(text, textRect)
    
    for i in range(20):
            for j in range(10):
                
                colour = COLOURS[tiles[i][j]]
                rect = [j*40,100+i*40,40,40]
                pygame.draw.rect(win, colour, rect, width=0)
    
    for i in range(20):
        pygame.draw.line(win, (255,255,255), (0,60+40*(i+1)), (400,60+40*(i+1)), width=1)
        
    for i in range(10):
        pygame.draw.line(win, (255,255,255), (40*(i+1),100), (40*(i+1), 900), width=1)
    
    pygame.draw.line(win, (255,255,255), (400,100), (600,100), width=1)
    text = font.render('hold', True, (255,255,255), (0,0,0))
    textRect = text.get_rect()
    textRect.center = (500, 125)
    win.blit(text, textRect)
    colour = COLOURS[piece.getHold()]
    pygame.draw.rect(win, (255,255,255), [472,172,56,56], width=6)
    pygame.draw.rect(win, colour, [475,175,50,50], width=0)
    
    
    pygame.draw.line(win, (255,255,255), (400,300), (600,300), width=1)
    text = font.render('next', True, (255,255,255), (0,0,0))
    textRect = text.get_rect()
    textRect.center = (500, 325)
    win.blit(text, textRect)
    for i in range(3):
        colour = COLOURS[piece.getLineUp()[i]]
        pygame.draw.rect(win, (255,255,255), [472,372+i*100,56,56], width=2)
        pygame.draw.rect(win, colour, [475,375+i*100,50,50], width=0)
        
    pygame.draw.line(win, (255,255,255), (400,700), (600,700), width=1)
    text = font.render('points', True, (255,255,255), (0,0,0))
    textRect = text.get_rect()
    textRect.center = (500, 725)
    win.blit(text, textRect)
    text = font.render(str(round(board.getPoints(),4)), True, (255,255,255), (0,0,0))
    textRect = text.get_rect()
    textRect.center = (500, 750)
    win.blit(text, textRect)
    
    pygame.display.update()
    
def drawWindowPaused(win):
    text = font.render('Click SPACE to unpause', True, (255,255,255), (0,0,0))
    textRect = text.get_rect()
    textRect.center = (WIN_WIDTH/2, WIN_HEIGHT/2)
    
    win.fill((0,0,0))
    win.blit(text, textRect)
    
    pygame.display.update()
    
def drawWindowLost(win):
    text = font.render('You lose.', True, (255,255,255), (0,0,0))
    textRect = text.get_rect()
    textRect.center = (WIN_WIDTH/2, WIN_HEIGHT/2)
    
    win.fill((0,0,0))
    win.blit(text, textRect)
    
    pygame.display.update()
    
class Tetris:
    
    def __init__(self):
        self.player = Player()
        self.lost = False
        self.nextIn = UserIn.EMPTY
        
        self.win = pygame.display.set_mode((WIN_WIDTH,WIN_HEIGHT))
        self.count = 0
        self.speed = 30
        self.speedUpRate = 3000
        reward = 0
        
    def step(self, action):
        oldPoints = self.player.board.points
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        
        board = self.player.board
        piece = self.player.piece
        
        #movements
        self.player.doAction(action)

        if not self.lost:
            board.points += INCREASE_OVER_TIME
            if self.count%self.speed==0:
                piece.moveDown(board)
            if self.count%self.speedUpRate==0:
                if self.speed > 5:
                    self.speed-=1
            
        if board.getLost():
            self.lost = True
            board.points -= LOSE_ON_LOSS
        
        if not self.lost:
            board.writeBoard(piece)
            
        self.count+=1
        
        #reset button press
        self.nextIn = UserIn.EMPTY
        
        placements = [item for sublist in self.checkAllPlacements() for item in sublist]
        
        #print(str(board.points)+" - "+str(oldPoints)+" = "+str(board.points-oldPoints))
        
        return placements, board.points-oldPoints, self.lost
    
    def humanStep(self, pause):
        oldPoints = self.player.board.points
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.nextIn = UserIn.LEFT.value
                elif event.key == pygame.K_RIGHT:
                    self.nextIn = UserIn.RIGHT.value
                elif event.key == pygame.K_DOWN:
                    self.nextIn = UserIn.DOWN.value
                elif event.key == pygame.K_UP:
                    self.nextIn = UserIn.ROTATE.value
                elif event.key == pygame.K_SPACE:
                    self.nextIn = UserIn.SPACE.value
                elif event.key == pygame.K_c:
                    self.nextIn = UserIn.HOLD.value
                elif event.key == pygame.K_ESCAPE:
                    pause = not pause
                elif event.key == pygame.K_1:
                    self.player.doAction(13)
        
        board = self.player.board
        piece = self.player.piece
        
        #movements
        if self.nextIn == UserIn.LEFT.value and not self.lost:
            piece.moveSideways(False)
        elif self.nextIn == UserIn.RIGHT.value and not self.lost:
            piece.moveSideways(True)
        elif self.nextIn == UserIn.ROTATE.value and not self.lost:
            piece.rotate(board)
        elif self.nextIn == UserIn.DOWN.value and not self.lost:
            piece.moveDown(board)
        elif self.nextIn == UserIn.HOLD.value and not self.lost:
            piece.holdPiece(board)
        elif self.nextIn == UserIn.SPACE.value and not self.lost:
            piece.drop(board)

        if not self.lost and not pause:
            if self.count%self.speed==0:
                piece.moveDown(board)
                board.points += 10*INCREASE_OVER_TIME
            if self.count%self.speedUpRate==0:
                if self.speed > 5:
                    self.speed-=1
            
        if board.getLost():
            self.lost = True
        
        if not self.lost:
            board.writeBoard(piece)
            
        self.count+=1
        
        #reset button press
        self.nextIn = UserIn.EMPTY
        
        placements = self.checkAllPlacements()
        #placements = [item for sublist in placements for item in sublist]
        #placements = [0 if x == 0 else 1 for x in placements]
        
        return placements, board.points-oldPoints, self.lost, pause
    
    def reset(self):
        self.player.board.restart(self.player.piece)
        self.lost = False
        self.nextIn = UserIn.EMPTY
        self.count = 0
        self.speed = 30
        
        placements = [item for sublist in self.checkAllPlacements() for item in sublist]
        
        return placements, False
    
    def getRandomAction(self):
        return random.randint(0, 79)
    
    def checkPlacement(self, r, x):
        legal = 1
        oldBoard = copy.deepcopy(self.player.board)
        oldRowsCleared = self.player.board.rowsCleared
        pieceType = self.player.piece.pType
        
        self.player.piece.rot = r
        self.player.piece.x = x
        self.player.piece.setCoords()
        if self.player.piece.checkWallCollision() or self.player.board.checkCollision(self.player.piece):
            legal = 0
        
        self.player.piece.drop(self.player.board)
        
        if legal == 0:
            stats = (999, 999, 999,-1)
        else:
            stats = self.player.getStats(oldRowsCleared)
        
        self.player.board = oldBoard
        self.player.piece.pType = pieceType
        
        return stats
    
    def checkAllPlacements(self):
        placements = []
        
        for i in range(4):
            for j in range(10):
                placements.append(self.checkPlacement(i, j))
        
        self.player.piece.holdPiece(self.player.board)
        
        for i in range(4):
            for j in range(10):
                placements.append(self.checkPlacement(i, j))
        
        self.player.piece.holdPiece(self.player.board)
        
        return placements
                

    def drawWindow(self):
        tiles = self.player.board.allTiles
    
        text = font.render('TETRIS', True, (255,255,255), (0,0,0))
        textRect = text.get_rect()
        textRect.center = (WIN_WIDTH/2, 50)
        
        self.win.fill((0,0,0))
        self.win.blit(text, textRect)
        
        for i in range(20):
                for j in range(10):
                    
                    colour = COLOURS[tiles[i][j]]
                    rect = [j*40,100+i*40,40,40]
                    pygame.draw.rect(self.win, colour, rect, width=0)
        
        for i in range(20):
            pygame.draw.line(self.win, (255,255,255), (0,60+40*(i+1)), (400,60+40*(i+1)), width=1)
            
        for i in range(10):
            pygame.draw.line(self.win, (255,255,255), (40*(i+1),100), (40*(i+1), 900), width=1)
        
        pygame.draw.line(self.win, (255,255,255), (400,100), (600,100), width=1)
        text = font.render('hold', True, (255,255,255), (0,0,0))
        textRect = text.get_rect()
        textRect.center = (500, 125)
        self.win.blit(text, textRect)
        colour = COLOURS[self.player.piece.getHold()]
        pygame.draw.rect(self.win, (255,255,255), [472,172,56,56], width=6)
        pygame.draw.rect(self.win, colour, [475,175,50,50], width=0)
        
        
        pygame.draw.line(self.win, (255,255,255), (400,300), (600,300), width=1)
        text = font.render('next', True, (255,255,255), (0,0,0))
        textRect = text.get_rect()
        textRect.center = (500, 325)
        self.win.blit(text, textRect)
        for i in range(3):
            colour = COLOURS[self.player.piece.getLineUp()[i]]
            pygame.draw.rect(self.win, (255,255,255), [472,372+i*100,56,56], width=2)
            pygame.draw.rect(self.win, colour, [475,375+i*100,50,50], width=0)
            
        pygame.draw.line(self.win, (255,255,255), (400,700), (600,700), width=1)
        text = font.render('points', True, (255,255,255), (0,0,0))
        textRect = text.get_rect()
        textRect.center = (500, 725)
        self.win.blit(text, textRect)
        text = font.render(str(round(self.player.board.getPoints(),4)), True, (255,255,255), (0,0,0))
        textRect = text.get_rect()
        textRect.center = (500, 750)
        self.win.blit(text, textRect)
        
        pygame.display.update()
        
        
def main():
    stop = False
    pause = False
    clock = pygame.time.Clock()
    env = Tetris()
    
    while not stop:
        clock.tick(30)
        placements, _, stop, pause = env.humanStep(pause)
        if pause:
            print(placements[1])
            pass
        env.drawWindow()
    
    pygame.quit()
    quit()