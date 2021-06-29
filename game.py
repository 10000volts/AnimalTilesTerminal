from enum import Enum
import random

from myio import IO
from utils.color import color, color_print, EColor

class TileStyle(Enum):
  BIRD = 1
  FISH = 2
  INSECT = 4
  MAMMAL = 8
  FLOWER = 15

class Player:
  def __init__(self) -> None:
    self.score = 0
    self.extra = 0
    self.hand = list()

class Game:
  def __init__(self, io: IO, scale: int = 4) -> None:
    self.io = io

    self.scale = scale
    self.expect_board = [[None for i in range(scale)] for j in range(scale)]
    self.board = [[None for i in range(scale)] for j in range(scale)]
    self.p1 = Player()
    self.p2 = Player()
    self.players = [self.p1, self.p2]
    # 初始瓷砖池
    self.pool = [x for i in range(6) for x in [TileStyle.BIRD, TileStyle.FISH, TileStyle.INSECT, TileStyle.MAMMAL]]

  @staticmethod
  def _shuffle(l: list):
    for i in range(0, len(l)):
      j = random.randint(0, len(l) - 1)
      temp = l[i]
      l[i] = l[j]
      l[j] = temp

  def _rand_expect_board(self):
    rand_pool = [x for i in range(self.scale) for x in [TileStyle.BIRD, TileStyle.FISH, TileStyle.INSECT, TileStyle.MAMMAL]]
    Game._shuffle(rand_pool)
    print(rand_pool)

    for x in range(0, self.scale):
      for y in range(0, self.scale):
        self.expect_board[x][y] = rand_pool 

  def start(self):
    self._rand_expect_board()