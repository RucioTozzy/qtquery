from PyQt4 import QtSql, QtCore, QtGui
import functools

LIST_DATABASES = '''
SELECT
    "database"."datname",
    pg_size_pretty(pg_database_size("database"."datname"))
FROM
    pg_catalog.pg_database AS "database"
LEFT JOIN
    pg_catalog.pg_user AS "user"
ON
    "database"."datdba" = "user"."usesysid"
-- WHERE
--     "user"."usename" IS NULL
--     OR "user"."usename" != 'postgres'
ORDER BY
    "datname"
'''

LIST_TABLES = '''
SELECT
    c.relname,
    pg_size_pretty(pg_total_relation_size(c.relname::text))
FROM
    pg_catalog.pg_class c
LEFT JOIN
    pg_catalog.pg_namespace n ON n.oid = c.relnamespace
WHERE
    c.relkind = 'r'
    AND nspname='public'
ORDER BY
    c.relname
'''


class Database(QtCore.QObject):
    @classmethod
    def get(cls, name):
        if QtSql.QSqlDatabase.contains(name):
            return QtSql.QSqlDatabase.database(name)
        else:
            db = QtSql.QSqlDatabase.addDatabase('QPSQL', name)
            db.setDatabaseName(name)
            #db.setHostName('marktexpert_ontwikkel')
            #db.setUserName('me_qvw')
#            db.setPassword()
#            db.setPort()
#            db.setConnectOptions()
            db.open()
            return db

get = Database.get


class DatabaseMenu(QtCore.QObject):
    database_changed = QtCore.pyqtSignal(QtSql.QSqlDatabase)

    def __init__(self, settings):
        self.settings = settings
        self.database = Database(settings)
        self.databases = {}
        QtCore.QObject.__init__(self)

    def refresh(self, menu):
        menu.clear()
        for database in self.list_databases():
            action = menu.addAction(database)
            action.setCheckable(True)

            database = unicode(database)
            action.triggered.connect(functools.partial(self.change_database,
                database))

            if database == self.current_database:
                action.setChecked()

    def get_combo_box(self, parent=None):
        db = Database.get('postgres')
        self.query_model = QtSql.QSqlQueryModel()
        self.query_model.setQuery(LIST_DATABASES, db)

        self.combo_box = QtGui.QComboBox(parent)
        self.combo_box.setModel(self.query_model)
        self.connect(self.combo_box, QtCore.SIGNAL('activated(QString)'),
            self.change_database)
        self.combo_box.setCurrentIndex(-1)
        return self.combo_box

    def get_database_layout(self, tree_widget):
        system_db = Database.get('postgres')

        self.databases = {}
        query = QtSql.QSqlQuery(LIST_DATABASES, system_db)
        
        print self.settings
        
#        databases = QtGui.QTreeWidgetItem(tree_widget)
#        databases.setText(0, 'Databases')
#        databases.setExpanded(True)
#
#        while query.next():
#            database_name = str(query.value(0).toString())
#            database = QtGui.QTreeWidgetItem(databases)
#            database.setText(0, database_name)
#            database.setText(1, query.value(1).toString())
#            self.databases[database_name] = database

        tree_widget.resizeColumnToContents(0)

    @QtCore.pyqtSlot(QtCore.QString)
    def change_database(self, database_name):
        database_name = str(database_name)
        index = self.combo_box.findText(database_name)
        self.combo_box.setCurrentIndex(index)

        self.current_database = Database.get(database_name)
        self.database_changed.emit(self.current_database)

        database = self.databases.get(database_name)
        if database and not database.childCount():
            tables = QtGui.QTreeWidgetItem(database)

        elif database_name:
            QtGui.QMessageBox.warning(
                self.combo_box,
                self.trUtf8('Unable to find database'),
                self.trUtf8(('The requested database (%r) is not accessible.'
                ' This should not happen unless you are using old settings')
                    % database_name))

