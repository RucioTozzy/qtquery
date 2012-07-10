from PyQt4 import Qsci, QtSql

class PSQLApi(Qsci.QsciAPIs):
    def __init__(self, lexer):
        Qsci.QsciAPIs.__init__(self, lexer)
        self.add_lexer_keywords()

    def add_lexer_keywords(self):
        for word in self.lexer().keywords(1).split():
            self.add(word)
            self.add(word.upper())

    def add_table_names(self, connection):
        result = QtSql.QSqlQuery('SELECT tablename FROM pg_tables', connection)
        while result.next():
            self.add(result.value(0).toString())
        self.prepare()
