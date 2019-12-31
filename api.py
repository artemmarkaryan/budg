import sqhelp


class Api:
	def __init__(self, chat_id):
		self.chat_id = chat_id

	def get_balance(self):
		with sqhelp.Connection() as curs:
			curs.execute('select balance from usr where id = %s',
			             [self.chat_id])
			return curs.fetchone()[0]

	def get_category_list(self, type_):
		"""
		:param type_: True for income, False for expense
		:return:
		"""
		with sqhelp.Connection() as curs:
			curs.execute(
				'select name from category where user_id = %s and type = %s',
				[self.chat_id, type_])
			fetch = curs.fetchall()
		return [i[0] for i in fetch]

	def add_operation(self, type_, category, total):
		"""
		:param type_: True for income, False for expense
		:param category:
		:param total:
		"""
		operator = '+' if type_ else '-'
		with sqhelp.Connection() as curs:
			curs.execute(
				'insert into operation (type, total, user_id, category_id) '
				'values (%(type)s, %(total)s, %(user_id)s, '
				'(select id from category '
				'where category.user_id = %(user_id)s '
				'and category.type = %(type)s '
				'and category.name = %(category)s))',
				{'type': type_, 'total': total, 'user_id': self.chat_id, 'category': category})
			curs.execute(
				f'update usr set balance = balance {operator} %s where id = %s', [total, self.chat_id]
			)

	def add_category(self, type_, name):
		"""
		:param type_: True for income, False for expense
		:param name:
		"""

		with sqhelp.Connection() as curs:
			query = curs.mogrify(
				"insert into category (name, type, user_id) values (%s, %s, %s)",
				[name, type_, self.chat_id]
				)
			curs.execute(query)
			# print(query)

	def del_category(self, type_, name):
		"""
		:param type_: True for income, False for expense
		:param name:
		"""
		with sqhelp.Connection() as curs:
			curs.execute(
				"delete from category where name = %s and type = %s and user_id = %s",
				[name, type_, self.chat_id]
			)
