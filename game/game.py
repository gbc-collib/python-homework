import argparse
import copy
import cmd
import logging
import shlex
import random

#create a monster and put it at a random position and need a function see if a enemy is there
#add all enemies to game engine

__version__ = '0.1'

def xfrange(start, stop, step):
	while start < stop:
		yield start
		start += step

class Player(object):
	def __init__(self, name, position = None):
		self.map = Map()
		if not position:
			self.position = self.map.get_random_position()
		else:
			self.position = position
		self.logger = logging.getLogger('Player')
		self.logger.debug('player started at ' + str(self.position))
		self.health = 100.0
		self.items = []
		self.name = name
		self.money = 0

		ocarina = Item('Ocarina')
		self.items.append(ocarina)
		wooden_sword = Weapon('sword')
		wooden_sword.damage = 5
		self.items.append(wooden_sword)

	def move_latitude(self, adjust):
		self.position.latitude = self.position.latitude + adjust

	def move_longitude(self, adjust):
		self.position.longitude = self.position.longitude + adjust

	def move_altitude(self, adjust):
		self.position.altitude = self.position.altitude + adjust

class Position(object):
	def __init__(self, latitude, longitude, altitude):
		self.latitude = latitude
		self.longitude = longitude
		self.altitude = altitude

	def __str__(self):
		return '(' + str(self.latitude) + ', ' + str(self.longitude) + ', ' + str(self.altitude) + ')'

	def __cmp__(self, other):
		if not isinstance(other, Position):
			return -1
		if not self.latitude == other.latitude:
			return -1
		if not self.longitude == other.longitude:
			return -1
		if not self.altitude == other.altitude:
			return -1
		return 0

class GameEngine(object):
	def __init__(self, player):
		self.player = player
		self.logger = logging.getLogger('GameEngine')
		self.logger.info('GameEngine created')
		self.map = Map()
		elf = EnemyElf()
		elf.position = self.map.get_random_position()
		self.logger.debug('Put Elf at ' + str(elf.position))
		treasure = Item('Treasure Chest')
		treasure.position = self.map.get_random_position()
		self.logger.debug('Put treasure chest at ' + str(treasure.position))
		self.all_enemies = []
		self.all_enemies.append(elf)
		self.all_items = []
		self.all_items.append(treasure)

	def pre_move(self):
		pass

	def post_move(self):
		self.logger.debug('player moved to ' + str(self.player.position))

	def get_items_for_position(self, position):
		items = []
		for item in self.all_items:
			if item.position == position:
				items.append(item)
		return items

	def get_enemies_for_position(self, position):
		enemies = []
		for enemy in self.all_enemies:
			if enemy.position == position:
				enemies.append(enemy)
		return enemies

	def attack(self, enemy, weapon):
		weapon_damage = self.get_low_damage(weapon)
		enemy.health -= weapon_damage
		if enemy.health <= 0:
			enemy.position = None
		return weapon_damage

	def get_low_damage(self, weapon):
		weapon_low_damage = float(weapon.damage) / 2.0
		possible_damages = list(xfrange(weapon_low_damage, weapon.damage, 0.5))
		possible_damages.append(weapon.damage)
		return random.choice(possible_damages)

class Enemy(object):
	def __init__(self, name):
		self.damage = 2
		self.health = 25
		self.name = name
		self.position = None

class EnemyElf(Enemy):
	def __init__(self, id = 0):
		name = 'Elf'
		if id:
			name += ' ' + str(id)
		super(EnemyElf, self).__init__(name)
		self.damage = 3
		self.health = 15

class EnemySpider(Enemy):
	def __init__(self, id = 0):
		name = 'Spider'
		if id:
			name += ' ' + str(id)
		super(EnemySpider, self).__init__(name)
		self.damage = 5
		self.health = 10

class Interface(cmd.Cmd, object):
	def __init__(self, name):
		super(Interface, self).__init__()
		self.player = Player(name)
		self.game_engine = GameEngine(self.player)
		self.map = Map()
		self.player.position = self.player.position
		self.logger = logging.getLogger('status')

	def do_go(self, args):
		self.game_engine.pre_move()
		position = self.player.position
		old_position = copy.copy(position)
		if args == 'north':
			position.latitude += 1
		elif args == 'east':
			position.longitude += 1
		elif args == 'south':
			position.latitude -= 1
		elif args == 'west':
			position.longitude -= 1
		elif args == 'up':
			position.altitude += 1
		elif args == 'down':
			position.altitude -= 1
		if not self.map.is_valid_position(position):
			self._print('Invalid position')
			self.player.position = old_position
			return
		self.game_engine.post_move()
		self.show_items_in_position(position)
		self.show_enemies_in_position(position)

	def show_items_in_position(self, position):
		for item in self.game_engine.get_items_for_position(position):
			self._print('There is a ' + item.name + ' here.')

	def show_enemies_in_position(self, position):
		for enemy in self.game_engine.get_enemies_for_position(position):
			self._print('There is a ' + enemy.name + ' here.')

	def do_attack(self, args):
		weapon = None
		args = args.lower()
		args = args.strip()
		args_list = shlex.split(args)
		weapon_name = args_list[2]
		target_enemy = args_list[0]
		for item in self.player.items:
			if item.name.lower() == weapon_name.lower():
				weapon = item
				break
		if not weapon:
			self._print('There is no ' + weapon_name)
			return
		if not isinstance(weapon, Weapon):
			self._print('That is not a weapon')
			return
		self.logger.debug('Player tried using ' + weapon_name)

		enemies = self.game_engine.get_enemies_for_position(self.player.position)
		if not enemies:
			self._print('There are no enemies to attack')
			return 0
		enemy_attacked = False
		for enemy in enemies:
			if target_enemy == enemy.name.lower():
				enemy_attacked = True
				damage_dealt = self.game_engine.attack(enemy, weapon)
				break
		if not enemy_attacked:
			self._print('There is no ' + target_enemy + ' here')
			return
		self._print('You dealt ' + str(damage_dealt) + ' to ' + target_enemy)
		if enemy.health <= 0:
			self._print('You killed the ' + target_enemy)

	def __str__(self):
		for item in self.game_engine.all_items:
			return item.name

	def do_take(self, args):
		args = args.lower()
		args = args.strip()
		items = self.game_engine.get_items_for_position(self.player.position)
		if not items:
			self._print('There are no items to take')
			return 0
		if args:
			item_found = False
			for item in items:
				if args == item.name.lower():
					self.add_to_inventory(item)
					item_found = True
					break
			if not item_found:
				self._print('There is no ' + args + ' here')
		elif len(items) == 1:
			self.add_to_inventory(items[0])
		else:
			self.show_items_in_position(self.player.position)

	def add_to_inventory(self, item):
		self._print('Added ' + item.name + ' to your inventory')
		item.position = None
		self.player.items.append(item)


	def _print(self, message):
		print(message)

class Map(object):
	def __init__(self):
			#latitude, longitude, altitude
			self.map_size = [[5, 5, 5], [-5, -5, -5]]

	def is_valid_position(self, position):
		if not (position.latitude >= self.map_size[1][0] and position.latitude <= self.map_size[0][0]):
			return False
		if not (position.longitude >= self.map_size[1][1] and position.longitude <= self.map_size[0][1]):
			return False
		if not (position.altitude >= self.map_size[1][2] and position.altitude <= self.map_size[0][2]):
			return False
		return True

	def get_random_position(self):
		latitude = random.randint(self.map_size[1][0], self.map_size[0][0])
		longitude = random.randint(self.map_size[1][1], self.map_size[0][1])
		altitude = random.randint(self.map_size[1][2], self.map_size[0][2])
		position = Position(latitude, longitude, altitude)
		return position

class Item(object):
	def __init__(self, name):
		self.name = name
		self.worth = 0
		self.weight = 1
		self.position = None

class Weapon(Item):
	def __init__(self, name):
		super(Weapon, self).__init__(name)
		self.durabilty = 100
		self.damage = 1

def main():
	parser = argparse.ArgumentParser(description = '', conflict_handler = 'resolve')
	parser.add_argument('-v', '--version', action = 'version', version = parser.prog + ' Version: ' + __version__)
	parser.add_argument('-L', '--log', dest = 'loglvl', action = 'store', choices = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default = 'INFO', help = 'set the logging level')
	parser.add_argument('-n', '--name', dest = 'name', required = True, help = 'Choose player name')
	arguments = parser.parse_args()

	logging.getLogger('').setLevel(logging.DEBUG)
	console_log_handler = logging.StreamHandler()
	console_log_handler.setLevel(getattr(logging, arguments.loglvl))
	console_log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s"))
	logging.getLogger('').addHandler(console_log_handler)

	interface = Interface(arguments.name)
	interface.cmdloop()
	return 0

if __name__ == '__main__':
	main()

