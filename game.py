from enum import Enum
import random
import json

from myio import IO
from utils.color import color, color_print, EColor
from utils.utils import shuffle

SHOP_VOLUME = 5
# class TileStyle(Enum):
BIRD = 1
FISH = 2
INSECT = 4
MAMMAL = 8
FLOWER = 15

TILE_STYLE_NAME = {1: '鸟', 2: '鱼', 4: '虫', 8: '兽', 15: '花'}

class Player:
  def __init__(self, inp, out) -> None:
    self.score = 0
    self.extra = 0

    # 拥有的每种瓷砖的数量
    self.hand = [0 for i in range(0, 16)]
    # 输入方式
    self._inp = inp
    self._out = out

  def input(self, message=dict()):
    if len(message) > 0:
      self.output(json.dumps(message))
    return self._inp()

  def output(self, message: dict):
    return self._out(json.dumps(message))

class Game:
  @staticmethod
  def make_message(op: str, p: int, data, req: bool=False) -> dict:
    """

    :param op: 操作名
    :param p: 操作者是否为我
    :return: 
    """
    return {'op': op, 'p': p, 'data': data, 'req': req}

  def __init__(self, client: bool, io: IO, scale: int = 4) -> None:
    self.client = client
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
    self.shop = list()
    # 瓷砖池
    self.pool = [x for i in range(6) for x in [BIRD, FISH, INSECT, MAMMAL]]
    # 服务端是否为先手
    self.sp = 1
    self.win = -1

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
    for y in range(0, self.scale):
      for x in range(0, self.scale):
        if x+2 < self.scale:
          if l[y][x+2] & l[y][x+1] & l[y][x]:
            ret[y][x+2] = True
            ret[y][x+1] = True
            ret[y][x] = True
        if y+2 < self.scale:
          if l[y+2][x] & l[y+1][x] & l[y][x]:
            ret[y+2][x] = True
            ret[y+1][x] = True
            ret[y][x] = True
        if (x+1 < self.scale) & (y+1 < self.scale):
          if l[y+1][x] & l[y][x+1] & l[y+1][x+1] & l[y][x]:
            ret[y+1][x] = True
            ret[y][x+1] = True
            ret[y+1][x+1] = True
            ret[y][x] = True
    return ret

  def _rand_expect_board(self):
    rand_pool = [x for i in range(self.scale) for x in [BIRD, FISH, INSECT, MAMMAL]]
    shuffle(rand_pool)

    for x in range(0, self.scale):
      for y in range(0, self.scale):
        self.expect_board[y][x] = rand_pool[y * self.scale + x]
    
    if self._have_pattern(self.expect_board):
      self._rand_expect_board()
    else:
      for p in self.players:
        p.output(Game.make_message('rst_brd', 0, self.expect_board))

  def _init_hand(self):
    self.players[0].hand[BIRD | FISH | INSECT | MAMMAL] = 2
    self.players[1].hand[BIRD | FISH | INSECT | MAMMAL] = 2
    for i in range(0, 8):
      style = self.pool.pop()
      self.players[0].hand[style] += 1
      style = self.pool.pop()
      self.players[1].hand[style] += 1

  def _replenish(self):
    """
    商店补货
    """
    for i in range(0, SHOP_VOLUME - len(self.shop)):
      if len(self.pool) == 0:
        pool = [x for i in range(2) for x in [FLOWER, BIRD, FISH, INSECT, MAMMAL]]
        shuffle(pool)
        self.pool.extend(pool)
      self.shop.append(self.pool.pop())

  def start(self):
    if not self.client:
      self._rand_expect_board()
      shuffle(self.pool)
      self.sp = random.randint(0, 1)
      if self.sp == 0:
        self.players[0] = self.p2
        self.players[1] = self.p1
        self.p1 = self.players[0]
        self.p2 = self.players[1]
      self.p1.output(Game.make_message('dcd_sp', 1, None))
      self.p2.output(Game.make_message('dcd_sp', 0, None))
      # 后手初始获得1分
      self.p2.score = 1

      self._init_hand()
      self._replenish()

      while True:
        win = self.action(self.players[0])
        if win > -1:
          break
        win = self.action(self.players[1])
        if win > -1:
          break
    while self.win == -1:
      self._translate_and_print(self.io.recv())

  def action(self, p: Player) -> int:
    # 返回值：-1 未决出胜负 0 先手玩家胜 1 后手玩家胜
    while True:
      try:
        cmd = p.input()
      except Exception as ex:
        pass
    return -1

  def _print_board(self):
    """
    打印当前局面。
    """
    s = ''
    for y in range(0, self.scale):
      for x in range(0, self.scale):
        if self.board[x][y] is not None:
          s += '{}({}) '.format(color(TILE_STYLE_NAME[self.board[y][x]], EColor.EMPHASIS),
                                color(TILE_STYLE_NAME[self.expect_board[y][x]]))
        else:
          s += '{}({}) '.format('空', color(TILE_STYLE_NAME[self.expect_board[y][x]]))
      color_print(s)

  def _translate_and_print(self, recv):
    recv = json.loads(recv)
    if recv['op'] == 'rst_brd':
      if self.client:
        self.expect_board = json.loads(recv['data'])
      self._print_board()
    elif recv['op'] == 'dcd_sp':
      if recv['p']:
        if self.client:
          self.players[1].score = 1
        color_print('您获得了先手!', EColor.EMPHASIS)
      else:
        if self.client:
          self.players[0] = self.p2
          self.players[1] = self.p1
          self.p1 = self.players[0]
          self.p2 = self.players[1]
          self.players[1].score = 1
        color_print('对方获得了先手!', EColor.EMPHASIS)
      