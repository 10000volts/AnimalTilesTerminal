from enum import Enum
import random
import json

from myio import IO
from utils.color import color, color_print, EColor
from utils.utils import shuffle

# class TileStyle(Enum):
BIRD = 1
FISH = 2
INSECT = 4
MAMMAL = 8
FLOWER = 15

class Player:
  def __init__(self, inp, out) -> None:
    self.score = 0
    self.extra = 0

    # 拥有的每种瓷砖的数量
    self.hand = [0 for i in range(0, 16)]
    # 输入方式
    self.inp = inp
    self.out = out

  def input(self, message=dict()):
    if len(message) > 0:
      self.output(json.dumps(message))
    return self.inp()

  def output(self, message: dict):
    return self.out(json.dumps(message))

class Game:
  def __init__(self, io: IO, scale: int = 4) -> None:
    self.io = io

    self.scale = scale
    self.expect_board = [[None for i in range(scale)] for j in range(scale)]
    self.board = [[None for i in range(scale)] for j in range(scale)]
    # 服务端
    def out1(m):
      self._translate_and_print(m)
    self.p1 = Player(input, out1)
    # 客户端
    self.p2 = Player(io.recv, io.send)
    self.players = [self.p1, self.p2]
    # 瓷砖池
    self.pool = [x for i in range(6) for x in [BIRD, FISH, INSECT, MAMMAL]]
    # 服务端是否为先手
    self.sp = 1

  def _have_pattern(self, l: list) -> bool:
    for x in range(0, self.scale):
      for y in range(0, self.scale):
        if y+2 < self.scale:
          if l[x][y+2] & l[x][y+1] & l[x][y]:
            return True
        if x+2 < self.scale:
          if l[x+2][y] & l[x+1][y] & l[x][y]:
            return True
        if (y+1 < self.scale) & (x+1 < self.scale):
          if l[x+1][y] & l[x][y+1] & l[x+1][y+1] & l[x][y]:
            return True
    return False

  def _find_pattern(self, l: list) -> list:
    ret = [[False for i in range(self.scale)] for j in range(self.scale)]
    for x in range(0, self.scale):
      for y in range(0, self.scale):
        if y+2 < self.scale:
          if l[x][y+2] & l[x][y+1] & l[x][y]:
            ret[x][y+2] = True
            ret[x][y+1] = True
            ret[x][y] = True
        if x+2 < self.scale:
          if l[x+2][y] & l[x+1][y] & l[x][y]:
            ret[x+2][y] = True
            ret[x+1][y] = True
            ret[x][y] = True
        if (y+1 < self.scale) & (x+1 < self.scale):
          if l[x+1][y] & l[x][y+1] & l[x+1][y+1] & l[x][y]:
            ret[x+1][y] = True
            ret[x][y+1] = True
            ret[x+1][y+1] = True
            ret[x][y] = True
    return ret

  def _rand_expect_board(self):
    rand_pool = [x for i in range(self.scale) for x in [BIRD, FISH, INSECT, MAMMAL]]
    shuffle(rand_pool)

    for x in range(0, self.scale):
      for y in range(0, self.scale):
        self.expect_board[x][y] = rand_pool[x * self.scale + y]
    
    if self._have_pattern(self.expect_board):
      self._rand_expect_board()

  def _init_hand(self):
    self.players[0].hand[BIRD | FISH | INSECT | MAMMAL] = 2
    self.players[1].hand[BIRD | FISH | INSECT | MAMMAL] = 2
    for i in range(0, 8):
      style = self.pool.pop()
      self.players[0].hand[style] += 1
      style = self.pool.pop()
      self.players[1].hand[style] += 1

  def start(self):
    self._rand_expect_board()
    shuffle(self.pool)
    self.sp = random.randint(0, 1)
    if self.sp == 0:
      self.players[0] = self.p2
      self.players[1] = self.p1
      self.p1 = self.players[0]
      self.p2 = self.players[1]
    self._init_hand()
    print(self.players[0].hand)
    print(self.players[1].hand)
    print(self.pool)
    while True:
      win = self.action(self.players[0])
      if win > -1:
        break
      win = self.action(self.players[1])
      if win > -1:
        break

  def action(self, p: Player) -> int:
    # 返回值：-1 未决出胜负 0 先手玩家胜 1 后手玩家胜
    while True:
      try:
        cmd = p.input()
      except Exception as ex:
        pass
    return -1

  def _translate_and_print(self, recv):
    color_print(recv)