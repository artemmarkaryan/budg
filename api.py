import sqhelp


class Api:
	def __init__(self, chat_id):
		self.chat_id = chat_id

	def set_balance(self, total):
		with sqhelp.Connection() as curs:
			curs.execute('update usr set balance = %s where id = %s',
			             [total, self.chat_id])


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
				{'type': type_, 'total': total, 'user_id': self.chat_id,
				 'category': category})
			curs.execute(
				f'update usr set balance = balance {operator} %s where id = %s',
				[total, self.chat_id]
			)

	def __get_operations(self, type_, category=None, how_many=10):
		with sqhelp.Connection() as curs:
			if category:
				query = curs.mogrify(
					f'''
					select op.total, 
					to_char(op.date :: date, 'DD.MM'), 
					to_char(op.time :: time, 'HH24:MI' ) 
					from operation op inner join category cat on op.category_id = cat.id
					where op.type = %(type)s
						and op.user_id = %(user_id)s
						and cat.name = %(category)s 
					order by date desc, time desc    
					limit {how_many} 
					''',
					{'type': type_, 'user_id': self.chat_id, 'category': category}
				)
			else:
				query = curs.mogrify(
					f'''
					select op.total,
	                to_char(op.date :: date, 'DD.MM'), 
					to_char(op.time :: time, 'HH24:MI'), 
					cat.name  
					from operation op inner join category cat on op.category_id = cat.id
					where op.type = %(type)s
						and op.user_id = %(user_id)s
					order by date desc, time desc    
					limit {how_many} 
					''',
					{'type': type_, 'user_id': self.chat_id}
				)
			curs.execute(query)
			fetch = curs.fetchall()
			return fetch

	def get_operations(self, type_, category=None, how_many=10):
		fetch = self.__get_operations(type_, category, how_many)
		row_str = f'<b>Последние {how_many}</b>\n'
		if category:
			for row in fetch:
				row_str += f'\n<b>{row[0]}₽</b> {row[1]} {row[2]}'
		else:
			for row in fetch:
				row_str += f'\n<b>{row[0]}₽</b> {row[1]} {row[2]} — {row[3]}'
		return row_str



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