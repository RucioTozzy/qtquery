import os
import utils
os.system('pyuic4 -x ui/settings.ui -o ui/settings.py')

from PyQt4 import QtGui, QtCore, QtSql
from ui.settings import Ui_SettingsTabWidget


class Settings(Ui_SettingsTabWidget, QtGui.QTabWidget):

    def __init__(self, application):
        self.application = application
        self._loading = True
        QtGui.QTabWidget.__init__(self)

    def connectSignals(self):
        self.databasesTreeWidget.itemSelectionChanged.connect(
            self.select_database)

        self.plainTextEditService.textChanged.connect(self.save_item)
        self.plainTextEditOptions.textChanged.connect(self.save_item)
        self.lineEditPort.textChanged.connect(self.save_item)
        self.lineEditHost.textChanged.connect(self.save_item)
        self.lineEditName.textChanged.connect(self.save_item)
        self.lineEditPass.textChanged.connect(self.save_item)
        self.lineEditUser.textChanged.connect(self.save_item)
        self.spinBoxConnectTimeout.valueChanged.connect(self.save_item)
        self.checkBoxRequireSSL.stateChanged.connect(self.save_item)
        self.buttonTest.clicked.connect(self.testDatabase)

    def testDatabase(self):
        items = self.databasesTreeWidget.selectedItems()
        if not items:
            return

        item = items[0]
        database = self.databases[item]
        if not database['name']:
            self.labelTestOutput.setText(
                '''The database doesnt have a name yet''')
            return

        options = {}
        options['connect_timeout'] = database['timeout']
        options['options'] = database['options']
        options['requiressl'] = database['requireSSL']
        options['service'] = database['service']

        try:
            db = QtSql.QSqlDatabase.addDatabase('QPSQL', database['name'])
            db.setDatabaseName('template1')
            db.setHostName(database['host'])
            db.setPort(int(database['port']))
            db.setUserName(database['user'])
            db.setPassword(database['pass'])
            db.setConnectOptions(';'.join('%s=%s' % (k, v)
                for k, v in options.iteritems() if k and v))

            if db.open():
                self.labelTestOutput.setText('Successfully connected to %s' %
                    database['name'])
            else:
                self.labelTestOutput.setText(db.lastError().text())
        finally:
            # Manually close and clean everything so we don't have dangling
            # databases
            db.close()
            del db
            QtSql.QSqlDatabase.removeDatabase(database['name'])

    def show(self):
        QtGui.QTabWidget.show(self)

    def load(self, settings):
        self._loading = True
        self.databases = {}
        self.databasesTreeWidget.clear()

        for i in range(settings.beginReadArray('databases')):
            settings.setArrayIndex(i)

            database = {}
            database['service'] = settings.value('service').toString()
            database['port'] = settings.value('port', 5432).toString()
            database['host'] = settings.value('host').toString()
            database['timeout'] = settings.value('timeout', 10).toString()
            database['options'] = settings.value('options').toString()
            database['requireSSL'] = settings.value('requireSSL').toString()
            database['pass'] = settings.value('pass').toString()
            database['user'] = settings.value('user').toString()
            database['name'] = settings.value('name').toString()

            item = QtGui.QTreeWidgetItem(self.databasesTreeWidget)
            self._update_tree_widget_item(item, database)
            self.databases[item] = database

        settings.endArray()
        self._loading = False

    def _update_tree_widget_item(self, item, database):
        '''Update the given item with the given database'''
        item.setText(0, utils.qstr(database['name']))
        item.setText(1, utils.qstr(database['host']))
        item.setText(2, utils.qstr(database['port']))
        item.setText(3, utils.qstr(database['user']))
        item.setFlags(
            QtCore.Qt.ItemIsSelectable
            | QtCore.Qt.ItemIsEditable
            | QtCore.Qt.ItemIsDragEnabled
            | QtCore.Qt.ItemIsUserCheckable
            | QtCore.Qt.ItemIsEnabled
        )

    def save_item(self, *args, **kwargs):
        if self._loading:
            return

        items = self.databasesTreeWidget.selectedItems()
        if not items:
            return

        item = items[0]
        database = self.databases[item]

        database['service'] = self.plainTextEditService.toPlainText()
        database['port'] = self.lineEditPort.text()
        database['host'] = self.lineEditHost.text()
        database['timeout'] = self.spinBoxConnectTimeout.value()
        database['options'] = self.plainTextEditOptions.toPlainText()
        database['requireSSL'] = self.checkBoxRequireSSL.isChecked()
        database['pass'] = self.lineEditPass.text()
        database['user'] = self.lineEditUser.text()
        database['name'] = self.lineEditName.text()
        self._update_tree_widget_item(item, database)
        self.save(self.application.settings)

    def select_database(self, *args, **kwargs):
        if self._loading:
            return

        self._loading = True
        items = self.databasesTreeWidget.selectedItems()
        if items:
            item = items[0]
            database = self.databases[item]

            self.plainTextEditService.setPlainText(database['service'])
            self.lineEditPort.setText(database['port'])
            self.lineEditHost.setText(database['host'])
            self.spinBoxConnectTimeout.setValue(int(database['timeout']))
            self.plainTextEditOptions.setPlainText(database['options'])
            self.checkBoxRequireSSL.setChecked(bool(database['requireSSL']))
            self.lineEditPass.setText(database['pass'])
            self.lineEditUser.setText(database['user'])
            self.lineEditName.setText(database['name'])
        self._loading = False

    def setupUi(self):
        Ui_SettingsTabWidget.setupUi(self, self)
        self.connectSignals()
        self.load(self.application.settings)

    def save(self, settings):
        settings['databases'] = self.databases.values()
#        settings.beginWriteArray('databases')
#        for i, (item, database) in enumerate(self.databases.iteritems()):
#            settings.setArrayIndex(i)
#            for k, v in database.iteritems():
#                settings.setValue(k, utils.qstr(unicode(v)))
#
#        settings.endArray()
#        settings.sync()
