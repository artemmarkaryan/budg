import sqhelp

class Api:
	def __init__(self, chat_id):
		self.chat_id = chat_id

	def get_balance(self):
		with sqhelp.Connection() as curs:
			curs.execute('select balance from usr where id = %s', [self.chat_id])
			return curs.fetchone()[0]


	def get_category_list(self):
		with sqhelp.Connection() as curs:
			curs.execute('select name from expense_category where user_id = %s',
			             [self.chat_id])
			fetch = curs.fetchall()
		return [i[0] for i in fetch]

	def get_source_list(self):
		with sqhelp.Connection() as curs:
			curs.execute('select name from income_source where user_id = %s',
			             [self.chat_id])
			fetch = curs.fetchall()
		return [i[0] for i in fetch]



	def add_income(self, source, sum_):
		with sqhelp.Connection() as curs:
			curs.execute(
				"""insert into income (source_id, sum, user_id)
				   values (
				   (select id from income_source where name = %s),
				   %s, %s
			   )""", [source, sum_, self.chat_id]
			)
			curs.execute('update usr set balance = balance + %s where id = %s', [sum_, self.chat_id])


	def add_expense(self, category, sum_):
		with sqhelp.Connection() as curs:
			curs.execute(
				"""insert into expense (category_id, sum, user_id)
				   values (
				   (select id from expense_category where name = %s),
				   %s, %s
			   )""", [category, sum_, self.chat_id]
			)
			curs.execute('update usr set balance = balance - %s where id = %s', [sum_, self.chat_id])


	def add_category(self, category):
		with sqhelp.Connection() as curs:
			curs.execute(
				"insert into expense_category (name, user_id) values (%s, %s)",
				[category, self.chat_id]
			)

	def add_source(self, source):
		with sqhelp.Connection() as curs:
			curs.execute(
				"insert into income_source (name, user_id) values (%s, %s)",
				[source, self.chat_id]
			)


	def del_category(self, category):
		with sqhelp.Connection() as curs:
			curs.execute('delete from expense_category where name = %s and user_id = %s',
			             [category, self.chat_id])

	def del_source(self, source):
		with sqhelp.Connection() as curs:
			curs.execute('delete from income_source where name = %s and user_id = %s',
			             [source, self.chat_id])
