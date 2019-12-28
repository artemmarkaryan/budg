import psycopg2
import psycopg2.errors
import psycopg2.extensions

from urllib import parse
import logging
logging.basicConfig(level=logging.WARNING)

class Connection:
    global_connection = [None]

    def __init__(self):
        logging.info('Database.__init__()')
        self.url = "postgres://upbjmjwiftowux:d9f71e9645f36ca61581f92aad633b8a14b574cd65a27fdcbb3d5bb12e2dd421@ec2-54-246-100-246.eu-west-1.compute.amazonaws.com:5432/df8bv9e8s26a59"
        self.parsed_url = parse.urlparse(self.url)
        self.curs = None
        self.autocommit = True

    def __enter__(self):
        logging.info('Database.__enter__()')
        self.__establish_connection()
        self.__create_cursor()
        return self.curs

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.info('Database.__exit__()')
        if not self.autocommit:
            self.curs.commit()

    def __create_cursor(self):
        logging.info('Database._create_cursor()')
        self.curs = self.global_connection[0].cursor()

    def __establish_connection(self):
        logging.info('Database._establish_connection()')
        logging.info('global_connection: '+str(self.global_connection[0]))
        current_global_connection = self.global_connection[0]
        if current_global_connection:
            if not current_global_connection.closed:
                return

        con = psycopg2.connect(
            database=self.parsed_url.path[1:],
            user=self.parsed_url.username,
            password=self.parsed_url.password,
            host=self.parsed_url.hostname,
            port=self.parsed_url.port
        )
        con.autocommit = self.autocommit
        self.global_connection[0] = con
        logging.info('new connection' + str(con))

    def connection_closed(self):
        logging.info('Database.connection_closed()')
        return self.global_connection[0].closed() if self.global_connection[0] else False

    def get_cursor(self):
        logging.info('Database.get_cursor()')
        return self.curs


class Database(Connection):
    def __init__(self):
        logging.info('Tables.__init__()')
        super(Database, self).__init__()
        self._list_of_tables = []
        self.__update_table_list()

    def list_tables(self):
        return self._list_of_tables

    def __update_table_list(self):
        """
        use when manipulate with tables: add or delete
        """
        with super().__enter__() as curs:
            curs.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            fetch = [i[0] for i in curs.fetchall()]
            logging.info('Database._all(): ' + str(fetch))
            self._list_of_tables = fetch

    def __create_table(self, name: str, columns: [str] = None):
        if not columns:
            columns = []
        assert type(columns) is list, "'columns' must be a list"
        with super().__enter__() as curs:
            columns= ', '.join(columns)
            expression = f'create table {name} ({columns})'
            logging.info(f'Tables._create_table(): {expression}')
            curs.execute(expression)

    def create_table(self, name: str, columns: [str] = None):
        self.__create_table(name, columns)
        self.__update_table_list()

    def __drop_table(self, name: str):
        logging.warning(f'Tables._get_column_list()')
        with super().__enter__() as curs:
            curs.execute(
                f'''
                DROP table {name}
                '''
            )

    def drop_table(self, name: str):
        self.__drop_table(name)
        self.__update_table_list()


class Table:
    def __init__(self, table_name):
        assert table_name in Database().list_tables()
        self.name = table_name
        self.column_list = []
        self.__update_columns_list()

    def __get_columns_list(self):
        """
        :return: empty list if no columns
        """
        logging.info(f'Table._get_column_list()')
        with Connection() as curs:
            curs.execute(
                """
				SELECT column_name FROM information_schema.columns 
				WHERE table_schema = 'public' AND table_name = %s
				""",
                [self.name]
            )
            fetch = [i[0] for i in curs.fetchall()]
            return fetch

    def __update_columns_list(self):
        """
        must ne called if columns are added or dropped
        :return: None
        """
        self.column_list = self.__get_columns_list()

    def __check_columns_in_column_list(self, columns: [str]):
        return all([c in self.column_list for c in columns])

    def check_columns_in_table(self, columns: [str]):
        return self.__check_columns_in_column_list(columns)

    def __add_column(self, columns: [str]):
        """
        :param columns: ['<name> <type> additional params', ...]
        """
        for column in columns:
            column_name = column.split(' ')[0] #column name is the first word
            if column_name in self.column_list:
                raise errors.ColumnException(f'column with name {column} already exists')

        add_column_string = ', add column '.join(columns)
        with Connection() as curs:
            curs.execute(f"alter table {self.name} add column {add_column_string}")

    def add_column(self, columns: [str]):
        self.__add_column(columns)
        self.__update_columns_list()

    def __drop_column(self, columns: [str]):
        columns = [f"drop column {column}" for column in columns]
        columns = ', '.join(columns)

        with Connection() as curs:
                curs.execute(f'alter table {self.name} {columns}')

    def drop_column(self, columns: [str]):
        self.__drop_column(columns)
        self.__update_columns_list()

    def __select(self, columns: [str] = None):
        logging.info(f'Table._select()')
        if columns:
            if not self.__check_columns_in_column_list(columns):
                raise errors.ColumnException
        try:
            with Connection() as curs:
                if columns is None:
                    columns = '*'
                else:
                    columns = '(' + ','.join(columns) + ')'
                curs.execute(f'select {columns} from {self.name}')
                return curs.fetchall()
        except psycopg2.errors.SyntaxError:
            raise errors.SQLSyntaxException

    def select(self, columns: [str] = None):
        """
        :param columns: which columns to fetch
        :return: list of rows
        """
        return self.__select(columns)

    def select_string(self, columns: [str] = None):
        """
        same as select(), but returns string
        :param columns: which columns to fetch
        :return: str ( list ofr rows )
        """
        result: str = ''
        if columns is None:
            columns = self.column_list
        title_row = ', '.join(columns)
        result += title_row
        for row in self.__select(columns):
            row = row[0][1:-1]
            row = row.split(',')
            row = ', '.join(row)
            # row = ', '.join(row)
            result += '\n' + row
        return result

    def __insert(self, values: list, columns: [str] = None):
        if columns is None:
            columns = self.column_list

        if len(values) != len(columns):
            raise errors.SQLSyntaxException('amount of values != amount of columns')
        with Connection() as curs:
            columns = ', '.join(columns)
            values_placeholder = ', %s' * len(values)
            values_placeholder = values_placeholder[2:]
            try:
                curs.execute(
                    f'insert into {self.name} ({columns}) values ({values_placeholder})',
                    values)
            except psycopg2.errors.UniqueViolation:
                raise errors.UniqueValueException

        logging.info(f'Table._insert()' + ', '.join([str(i) for i in values]))

    def insert(self, values: list, columns: [str] = None):
        self.__insert(values, columns)

    def __save_to_file(self, path, columns: [str] = None):
        if columns is None:
            columns = self.column_list
        with Connection() as curs:
            f = open(path, 'wb')
            curs.copy_to(file=f, table=self.name, sep=',', columns=columns)
            f.close()
            f = open(path, 'r+')
            content = f.read()
            f.seek(0, 0)
            f.write(','.join(columns) + '\n' + content)
            f.close()

    def save_to_file(self, path, columns: [str] = None):
        self.__save_to_file(path, columns)
