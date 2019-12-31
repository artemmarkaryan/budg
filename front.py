import telebot
from telebot.types import ReplyKeyboardMarkup
import sqhelp
import psycopg2.errors
import api

bot = telebot.TeleBot("841171845:AAEkcKnkMkZrA8YEs8cfP3l5rcDxV9KI4_I")

texts = {
	'menu': 'В меню',
	'back': 'Назад',
	'success': 'Готово ✓',
	'default arrow': '↘️',
	'income': 'Доход',
	'expense': 'Расход'
}

def make_kb(options:list = None):
	if options and len(options):
		kb = ReplyKeyboardMarkup(True, True, row_width=1)
		kb.add(*options)
	else:
		kb = None
	return kb

def get_text(m, callback, title = texts['default arrow'], options: list = None ):
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

def get_num(m, callback, title = texts['default arrow'], options: list = None):
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

def success_text(m):
	bot.send_message(m.chat.id, texts['success'])

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

@bot.message_handler(func=lambda m: m.text == texts['menu'])
def menu(m):
	commands = {
		# user_text: function
		'Доход': add_income,
		'Расход': add_expense,
		'Мои категории': show_categories,
	}
	kb = ReplyKeyboardMarkup(True, True, row_width=1)
	kb.add(*commands.keys())
	text = 'Баланс: ' + str(api.Api(m.chat.id).get_balance())
	bot.send_message(m.chat.id, text, reply_markup=kb)

	def handler(m):
		# call method from commands, else: call menu
		commands.get(m.text, menu)(m)

	bot.register_next_step_handler(m, handler)

def add_operation(type_, m):
	"""
	:param type_: True for income, False for expense
	:param m:
	:return:
	"""
	categories = api.Api(m.chat.id).get_category_list(type_)
	chosen_category = []

	def total_cb(m, total):
		if total != texts['back']:
			api.Api(m.chat.id).add_operation(type_, chosen_category[0], total)
			bot.send_message(m.chat.id, '✓')
			menu(m)

	def name_cb(m, user_choice):
		if user_choice == texts['back']:
			menu(m)
		else:
			chosen_category.append(user_choice)
			get_num(m, total_cb, 'Сумма')

	get_text(m, callback=name_cb, title='Категория:', options=categories + [texts['back']])

@bot.message_handler(func=lambda m: m.text == texts['income'])
def add_income(m):
	add_operation(True, m)

@bot.message_handler(func=lambda m: m.text == texts['expense'])
def add_expense(m):
	add_operation(False, m)

def show_categories(m):
	bot.send_message(
		m.chat.id,
		text='<b>Доходов:</b>\n\n'+
		     '\n'.join(api.Api(m.chat.id).get_category_list(True)),
		parse_mode='html'
	)
	bot.send_message(
		m.chat.id,
		text='<b>Расходов:</b>\n\n'+
		     '\n'.join(api.Api(m.chat.id).get_category_list(False)),
		parse_mode='html'
	)
	commands = {
		'Добавить категорию': add_category,
		'Удалить категорию': del_category,
		texts['menu']: menu
	}
	kb = make_kb(list(commands.keys()))

	def handler(m):
		# call method from commands, else: call menu
		commands.get(m.text, menu)(m)

	bot.send_message(m.chat.id, texts['default arrow'], reply_markup=kb)
	bot.register_next_step_handler(m, handler)

def add_category(m):
	types_to_choose = {
		'Доходов': True,
		'Расходов': False
	}
	chosen_type = []

	def cat_name_cb(m, user_choice):
		if user_choice == texts['back']:
			add_category(m)
		else:
			api.Api(m.chat.id).add_category(chosen_type[0], user_choice)
			bot.send_message(m.chat.id, texts['success'])
			menu(m)

	def cat_type_cb(m, user_choice):
		if user_choice in types_to_choose.keys():
			chosen_type.append(types_to_choose[user_choice])
			get_text(m, cat_name_cb,
			         title='Как называется категория?',
			         options=[texts['back']])

		elif user_choice == texts['back']:
			show_categories(m)
		else:
			add_category(m)


	get_text(m, cat_type_cb,
	         title='Категория чего?',
	         options=list(types_to_choose.keys()) + [texts['back']])

def del_category(m):

	types_to_choose = {
		'Доходов': True,
		'Расходов': False
	}
	chosen_type = []
	category_list = []

	def cat_name_cb(m, user_choice):
		if user_choice == texts['back']:
			del_category(m)
		elif user_choice in category_list:
			api.Api(m.chat.id).del_category(chosen_type[0], user_choice)
			success_text(m)
			menu(m)
		else:
			bot.send_message(m.chat.id, 'Нет такой категории')
			ask_for_category_name(m)

	def cat_type_cb(m, user_choice):
		if user_choice in types_to_choose.keys():
			chosen_type.append(types_to_choose[user_choice])
			ask_for_category_name(m)
		elif user_choice == texts['back']:
			show_categories(m)
		else:
			del_category(m)

	def ask_for_category_name(m):
		categories_from_db = api.Api(m.chat.id).get_category_list(chosen_type[0])
		for cat in categories_from_db:
			category_list.append(cat)

		get_text(m, cat_name_cb,
		         title='Как называется категория?',
		         options=category_list + [texts['back']])

	get_text(m, cat_type_cb,
	         title='Категория чего?',
	         options=list(types_to_choose.keys()) + [texts['back']])


bot.polling()
