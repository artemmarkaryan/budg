import telebot
from telebot.types import ReplyKeyboardMarkup
import sqhelp
import psycopg2.errors
import api

bot = telebot.TeleBot("841171845:AAEkcKnkMkZrA8YEs8cfP3l5rcDxV9KI4_I")



def make_kb(options:list = None):
	if options and len(options):
		kb = ReplyKeyboardMarkup(True, True, row_width=1)
		kb.add(*options)
	else:
		kb = None
	return kb

def get_text(m, callback, title = '->', options: list = None):
	"""
	:param m: message: key to a chat/user
	:param callback: will be called after user puts in a name: callback(m, name)
	:param title: text to send to ask for a reply
	:param options: select from
	:return: -
	"""

	def handler(m):
		callback(m, m.text)

	bot.send_message(m.chat.id, title, reply_markup=make_kb(options))
	bot.register_next_step_handler(m, handler)

def get_num(m, callback, title, options: list = None):
	"""
	:param m: message: key to a chat/user
	:param callback: will be called after user puts in a name: callback(m, name)
	:param title: text to send to ask for a reply
	:param options: select from
	:return: -
	"""

	def handler(m):
		if m.text.isdigit():
			callback(m, m.text)
		else:
			bot.send_message(m.chat.id, 'Только цифры')
			get_sum(m, callback, options)

	bot.send_message(m.chat.id, title, reply_markup=make_kb(options))
	bot.register_next_step_handler(m, handler)



@bot.message_handler(commands=['start'])
def start(m):
	chat_id: int = m.chat.id
	with sqhelp.Connection() as curs:
		# 	curs.execute("select chat_id from \"user\" where chat_id = %d", [chat_id])
		try:
			curs.execute("insert into usr (id) values (%s)", [chat_id])
		except psycopg2.errors.UniqueViolation:
			pass
	menu(m)


def menu(m):
	commands = {
		'Доход': income,
		'Расход': expense,
		'Редактировать': edit
	}
	kb = ReplyKeyboardMarkup(True, True, row_width=1)
	kb.add(*commands.keys())
	text = 'Баланс: ' + str(api.Api(m.chat.id).get_balance())
	bot.send_message(m.chat.id, text, reply_markup=kb)

	def handler(m):
		# call method from commands, else: call menu
		commands.get(m.text, menu)(m)

	bot.register_next_step_handler(m, handler)


def income(m):
	sources = api.Api(m.chat.id).get_source_list()
	results = []
	def total_cb(m, total):
		api.Api(m.chat.id).add_income(results[0], total)
		bot.send_message(m.chat.id, '✓')
		menu(m)

	def name_cb(m, category):
		results.append(category)
		get_num(m, total_cb, 'Сумма:')

	get_text(m, callback=name_cb, title='Источник:', options=sources)


def expense(m):
	categories = api.Api(m.chat.id).get_category_list()
	results = []
	def total_cb(m, total):
		api.Api(m.chat.id).add_expence(results[0], total)
		bot.send_message(m.chat.id, '✓')
		menu(m)

	def name_cb(m, category):
		results.append(category)
		get_num(m, total_cb, 'Сумма')

	get_text(m, callback=name_cb, title='Категория:', options=sources)

@bot.message_handler(func=lambda m: m.text == 'Редактировать')
def edit(m):
	api_ = api.Api(m.chat.id)
	commands = {
		'показать категории': show_categories,
		'показать источники': show_sources,
		'+ категория расходов': add_category,
		'- категория расходов': del_category,
		'+ источник доходов': add_source,
		'- источник доходов': del_source,
		'В меню': menu
	}
	kb = ReplyKeyboardMarkup(True, True, row_width=1)
	kb.add(*commands.keys())

	def handler(m):
		# call method from commands, else: call menu
		command = commands.get(m.text)
		if command:
			command(m)
		else:
			menu(m)

	bot.send_message(m.chat.id, '->', reply_markup=kb)
	bot.register_next_step_handler(m, handler)

def show_categories(m):
	bot.send_message(
		m.chat.id,
		text='\n'.join(api.Api(m.chat.id).get_category_list())
	)
	edit(m)

def show_sources(m):
	bot.send_message(
		m.chat.id,
		text='\n'.join(api.Api(m.chat.id).get_source_list())
	)
	edit(m)

def add_category(m):
	def cb(m, cat_name):
		api.Api(m.chat.id).add_category(cat_name)
		bot.send_message(m.chat.id, '✓')
		menu(m)

	get_text(m, callback=cb, title='Название категории')

def del_category(m):
	pass

def add_source(m):
	pass

def del_source(m):
	pass




bot.polling()
