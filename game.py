from enum import Enum
from os import set_blocking
import random
import json
import re

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
TILE_COST = {1: 0, 2: 0, 4: 0, 8: 0, 15: 1}

class Player:
  def __init__(self, inp, out) -> None:
    self.score = 0
    self.extra = 0

    # 拥有的每种瓷砖的数量
    self.hand = [0 for i in range(0, 16)]
    # 仅客户端模式时有用
    self.hand_count = 0
    # 输入方式
    self._inp = inp
    self._out = out
    self.sp = 0

  def input(self, message=dict()):
    if len(message) > 0:
      self.output(message)
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
    self.expect_board = [[0 for i in range(scale)] for j in range(scale)]
    self.board = [[0 for i in range(scale)] for j in range(scale)]
    # 服务端
    def out1(m):
      self._translate_and_print(m)
    self.p1 = Player(input, out1)
    # 客户端
    self.p2 = Player(io.recv, io.send)
    self.players = [self.p1, self.p2]
    # 下一个行动的玩家
    self.act_next = 0
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
      client = self.players[self.sp]
      client.output(Game.make_message('rst_brd', 0, self.expect_board))

  def _init_hand(self):
    self.players[0].hand[BIRD | FISH | INSECT | MAMMAL] = 2
    self.players[1].hand[BIRD | FISH | INSECT | MAMMAL] = 2
    count = 2
    for i in range(0, 8):
      style = self.pool.pop()
      self.players[0].hand[style] += 1
      style = self.pool.pop()
      self.players[1].hand[style] += 1
      count += 1
    # 只给客户端发送
    client = self.players[self.sp]
    client.output(Game.make_message('rst_hnd', 1, client.hand))
    client.output(Game.make_message('rst_hnd', 0, count))

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
    client = self.players[self.sp]
    client.output(Game.make_message('rst_shp', 0, self.shop))

  def start(self):
    if not self.client:
      self.sp = random.randint(0, 1)
      if self.sp == 0:
        self.players[0] = self.p2
        self.players[1] = self.p1
        self.p1 = self.players[0]
        self.p2 = self.players[1]
      self.p1.sp = 1
      self.p2.sp = 0
      self.p1.output(Game.make_message('dcd_sp', 1, None))
      self.p2.output(Game.make_message('dcd_sp', 0, None))
      # 后手初始获得1分
      self.p2.score = 1

      self._rand_expect_board()
      shuffle(self.pool)

      self._init_hand()
      self._replenish()
      for p in self.players:
        p.output(Game.make_message('init', 0, None))

      while True:
        win = self._action(self.players[self.act_next])
        if win > -1:
          break
        win = self._action(self.players[self.act_next])
        if win > -1:
          break
    else:
      while self.win == -1:
        self._translate_and_print(self.io.recv())

  def _put(self, p: Player, style, x, y):
    f = False

    p.hand[style] -= 1
    self.board[y][x] = style
    if style & self.expect_board[y][x]:
      p.score += 1 + p.extra
      p.extra += 1
      f = True
    # 消除
    if self._have_pattern(self.board):
      l = self._find_pattern(self.board)
      for _y in range(0, self.scale):
        for _x in range(0, self.scale):
          if l[_y][_x] and (_y != y or _x != x):
            self.board[_y][_x] = 0
      self.players[p.sp].extra -= 1
      # 跳过对方的下个回合
      self.act_next = 1-self.act_next

      f = True
    if not f:
      p.score -= 1
      p.extra = 0
    for _p in self.players:
      _p.output(Game.make_message('put', p is _p, [style, x, y, p.score, p.extra,
                                                   self.players[p.sp].extra, self.board]))
  
  def _buy(self, p: Player, count, cost):
    p.score -= cost
    p.extra = int(p.extra / 2)
    for i in range(0, count):
      p.hand[self.shop.pop(0)] += 1
    self._replenish()
    for _p in self.players:
      if p is _p:
        _p.output(Game.make_message('buy', 1, [p.score, p.extra, p.hand, self.shop]))
      else:
        _p.output(Game.make_message('buy', 0, [p.score, p.extra, count, self.shop]))

  def _action(self, p: Player) -> int:
    # 返回值：-1 未决出胜负 0 先手玩家胜 1 后手玩家胜
    flag = True
    while flag:
      cmd = p.input(Game.make_message('req_act', 1, None, True))
      m = re.search('put ([FBfIM]) ([0-{}]) ([0-{}])'.format(self.scale-1, self.scale-1), cmd)
      if m is not None:
        style = {'F': 15, 'B': 1, 'f': 2, 'I': 4, 'M': 8}
        if p.hand[style[m.group(1)]]:
          x = int(m.group(2))
          y = int(m.group(3))
          if self.board[y][x] == 0:
            self._put(p, style[m.group(1)], x, y)
            break
      m = re.search('buy ([1-{}])'.format(SHOP_VOLUME), cmd)
      if m is not None:
        count = int(m.group(1))
        cost = -1
        for c in range(0, count):
          cost += TILE_COST[self.shop[c]] + 1
        if p.score >= cost:
          self._buy(p, count, cost)
          break
      p.output(Game.make_message('err', 1, '输入有误qaq'))
    if p.score < 0:
      return p.sp
    
    # 被填满时结束游戏
    for y in range(0, self.scale):
      for x in range(0, self.scale):
        if self.board[y][x] == 0:
          self.act_next = 1 - self.act_next
          return -1
    return self.p1.score < self.p2.score

  def _print_board(self):
    """
    打印当前局面。
    """
    op = self.players[self.sp]
    p = self.players[1 - self.sp]
    count = op.hand_count
    if not self.client:
      for hand in op.hand:
        count += hand
    color_print("对手分数: {} 对手剩余瓷砖数: {} 对方额外得分数: {}".format(
      color(op.score, EColor.NUMBER), 
      color(count, EColor.NUMBER),
      color(op.extra, EColor.NUMBER)
    ))
    for y in range(0, self.scale):
      s = ''
      for x in range(0, self.scale):
        if self.board[y][x] > 0:
          s += '{}({}) '.format(color(TILE_STYLE_NAME[self.board[y][x]], EColor.EMPHASIS),
                                color(TILE_STYLE_NAME[self.expect_board[y][x]]))
        else:
          s += '{}({}) '.format(color('空', EColor.NONE), 
                                color(TILE_STYLE_NAME[self.expect_board[y][x]]))
      color_print(s)
    s = '商店: '
    cost = 0
    for i in range(0, SHOP_VOLUME):
      s += '{} {}|'.format(color(TILE_STYLE_NAME[self.shop[i]], EColor.EMPHASIS), color(str(cost), EColor.NUMBER))
      cost += 1 + TILE_COST[self.shop[i]]
    count = 0
    for hand in p.hand:
      count += hand
    color_print(s)
    color_print("您的分数: {} 剩余瓷砖数: {} 额外得分数: {}".format(
      color(p.score, EColor.NUMBER), 
      color(count, EColor.NUMBER),
      color(p.extra, EColor.NUMBER)
    ))
    s = '您的瓷砖: '
    for style in TILE_STYLE_NAME.keys():
      s += '{} {}, '.format(color(TILE_STYLE_NAME[style], EColor.EMPHASIS), color(p.hand[style], EColor.NUMBER))
    color_print(s)
    print("")

  def _translate_and_print(self, recv):
    recv = json.loads(recv)
    if recv['op'] == 'rst_brd':
      self.expect_board = recv['data']
    elif recv['op'] == 'rst_shp':
      self.shop = recv['data']
    elif recv['op'] == 'rst_hnd':
      if recv['p']:
        self.players[1-self.sp].hand = recv['data']
      else:
        self.players[self.sp].hand_count = recv['data']
    elif recv['op'] == 'dcd_sp':
      if recv['p']:
        if self.client:
          self.sp = 1
          self.p1.sp = 1
          self.players[1].score = 1
        color_print('您获得了先手!', EColor.EMPHASIS)
      else:
        if self.client:
          self.sp = 0
          self.players[0] = self.p2
          self.players[1] = self.p1
          self.p1 = self.players[0]
          self.p2 = self.players[1]
          self.p1.sp = 1
          self.players[1].score = 1
        color_print('对方获得了先手!', EColor.EMPHASIS)
    elif recv['op'] == 'init':
      self._print_board()
    elif recv['op'] == 'req_act':
      color_print('轮到您行动!', EColor.EMPHASIS)
      if self.client:
        cmd = input()
        self.io.send(cmd)
    elif recv['op'] == 'err':
      color_print('出错辣qaq: {}'.format(recv['data']), EColor.ERROR)
    elif recv['op'] == 'put':      
      color_print('在({}, {})放下了瓷砖!'.format(
        color(recv['data'][1], EColor.NUMBER),
        color(recv['data'][2], EColor.NUMBER),
      ))
      if self.client:
        if recv['p']:
          self.players[1-self.sp].hand[recv['data'][0]] -= 1
          self.players[1-self.sp].score = recv['data'][3]
          self.players[1-self.sp].extra = recv['data'][4]
          self.players[self.sp].extra = recv['data'][5]
        else:
          self.players[self.sp].hand_count -= 1
          self.players[self.sp].score = recv['data'][3]
          self.players[self.sp].extra = recv['data'][4]
          self.players[1-self.sp].extra = recv['data'][5]
        self.board = recv['data'][6]
      self._print_board()
    elif recv['op'] == 'buy':
      color_print('购买了瓷砖!', EColor.EMPHASIS)
      if self.client:
        if recv['p']:
          self.players[1-self.sp].score = recv['data'][0]
          self.players[1-self.sp].extra = recv['data'][1]
          self.players[1-self.sp].hand = recv['data'][2]
        else:
          self.players[self.sp].score = recv['data'][0]
          self.players[self.sp].extra = recv['data'][1]
          self.players[self.sp].hand_count += recv['data'][2]
        self.shop = recv['data'][3]
      self._print_board()
