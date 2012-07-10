#!/usr/bin/env python

import sys
from PyQt4 import QtGui, QtCore, QtSql, Qsci
import signal
import database
import sqlparse
import os
import psql_api
import time
import pprint
import settings

debug = lambda self: pprint.pprint(
    dict((k, v)
    for k in dir(self)
    for v in [repr(getattr(self, k))]
    if ' method ' not in v)
)

signal.signal(signal.SIGINT, signal.SIG_DFL)

#MainBase = uic.loadUiType('ui/main.ui')[0]
#class Main(MainBase, QtGui.QMainWindow):

os.system('pyuic4 ui/main.ui -o ui/main.py')
from ui.main import Ui_MainWindow
import settings_panel


class QueryExecuter(QtCore.QThread):
    query_executed = QtCore.pyqtSignal(QtSql.QSqlQueryModel)

    def __init__(self, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.time = None

    @QtCore.pyqtSlot(QtCore.QString, QtSql.QSqlDatabase)
    def execute_query(self, query, connection):
        self.query = query
        self.connection = connection
        self.start()

    def run(self):
        self.time = time.time()
        self.query_model = QtSql.QSqlQueryModel()
        self.query_model.setQuery(self.query, self.connection)
        self.query_executed.emit(self.query_model)


class Editor(Ui_MainWindow):

    def set_filename(self, filename):
        self._filename = filename
        self.setWindowTitle(filename)

    def get_filename(self):
        return self._filename

    filename = property(get_filename, set_filename)

    def setupConnections(self):
        self.actionUnindent.setShortcut('Shift+TAB')

    def setupTextEditQuery(self):

        editor = self.textEditQuery
        scintilla = Qsci.QsciScintilla

        editor.setBackspaceUnindents(True)
        editor.setTabIndents(True)

        # Set the font
        self.font = QtGui.QFont()
        self.font.setFamily('terminus')
        self.font.setFixedPitch(True)
        self.font.setPointSize(11)
        editor.setFont(self.font)

        # Add line numbers
        self.font_metrics = QtGui.QFontMetrics(self.font)
        editor.setMarginsFont(self.font)
        editor.setMarginWidth(0, self.font_metrics.width('0000') + 5)
        editor.setMarginLineNumbers(0, True)

        # Add "maximum width" line
        editor.setEdgeMode(Qsci.QsciScintilla.EdgeLine)
        editor.setEdgeColumn(80)
        editor.setEdgeColor(QtGui.QColor(0xCCCCCC))

        # Add folding
        editor.setFolding(scintilla.BoxedTreeFoldStyle)

        # Highlight the matching brace
        editor.setBraceMatching(scintilla.SloppyBraceMatch)

        # Highlight our current line
        editor.setCaretLineVisible(True)
        editor.setCaretLineBackgroundColor(QtGui.QColor(0xE8F3FE))

        # Set the lexer to enable syntax highlighting
        self.lexer = Qsci.QsciLexerSQL(editor)
        self.lexer.setDefaultFont(self.font)
        editor.setLexer(self.lexer)

        # Create an autocompletion API
        self.api = psql_api.PSQLApi(self.lexer)

        # Autocompletion
        editor.setAutoIndent(True)
        editor.setCallTipsStyle(scintilla.CallTipsContext)
        editor.setAutoCompletionThreshold(1)
        editor.setAutoCompletionSource(scintilla.AcsAll)
        editor.setAutoCompletionFillupsEnabled(True)

        editor.setEolMode(scintilla.EolUnix)

        editor.setIndentationGuides(True)
        editor.setIndentationsUseTabs(False)
        editor.setTabIndents(True)
        editor.setTabWidth(4)

    @QtCore.pyqtSlot()
    def on_actionCut_triggered(self):
        self.textEditQuery.cut()

    @QtCore.pyqtSlot()
    def on_actionCopy_triggered(self):
        self.textEditQuery.copy()

    @QtCore.pyqtSlot()
    def on_actionPaste_triggered(self):
        self.textEditQuery.paste()

    @QtCore.pyqtSlot()
    def on_actionComment_triggered(self):
        editor = self.textEditQuery
        editor.beginUndoAction()

        if editor.hasSelectedText():
            begin_line, begin_pos, end_line, end_pos = editor.getSelection()
            editor.insertAt('/*', begin_line, begin_pos)
            editor.insertAt('*/', end_line, end_pos)
            editor.setSelection(begin_line, begin_pos, end_line, end_pos + 2)
        else:
            line, pos = editor.getCursorPosition()
            editor.insertAt('--', line, pos)
            editor.setSelection(line, pos, line + 1, 0)

        editor.endUndoAction()

    @QtCore.pyqtSlot()
    def on_actionUncomment_triggered(self):
        editor = self.textEditQuery
        editor.beginUndoAction()

        if not editor.hasSelectedText():
            line, pos = editor.getCursorPosition()
            editor.setSelection(line, pos, line + 1, 0)

        begin_line, begin_pos, end_line, end_pos = editor.getSelection()

        editor.insertAt('/*', begin_line, begin_pos)
        editor.insertAt('*/', end_line, end_pos)
        editor.endUndoAction()

    @QtCore.pyqtSlot()
    def on_actionUnindent_triggered(self):
        editor = self.textEditQuery
        if editor.hasSelectedText():
            begin_line, _, end_line, _ = editor.getSelection()
        else:
            begin_line, _ = editor.getCursorPosition()
            end_line = begin_line + 1

        for line in range(begin_line, end_line):
            editor.unindent(line)

    @QtCore.pyqtSlot()
    def on_actionOpen_triggered(self):
        filename = unicode(QtGui.QFileDialog.getOpenFileName(
            parent=self,
            caption='Open SQL File',
            filter='SQL Files (*.sql);;All Files (*.*)',
        ))
        if filename:
            try:
                fh = open(filename)
                self.textEditQuery.setText(fh.read())
                fh.close()
                self.filename = filename
                return filename
            except IOError, e:
                QtGui.QErrorMessage.showMessage('Unable to open %s. Error: %s'
                    % (filename, e))

    @QtCore.pyqtSlot()
    def on_actionSave_triggered(self, open_dialog=False):
        if self.filename and not open_dialog:
            filename = self.filename
        else:
            filename = unicode(QtGui.QFileDialog.getSaveFileName(
                parent=self,
                caption='Open SQL File',
                filter='SQL Files (*.sql);;All Files (*.*)',
            ))

        if filename:
            try:
                fh = open(filename, 'w')
                fh.write(self.textEditQuery.text())
                fh.close()
                self.filename = filename
                return filename
            except IOError, e:
                QtGui.QErrorMessage.showMessage('Unable to write to %s. '
                    'Error: %s' % (filename, e))

    @QtCore.pyqtSlot()
    def on_actionSaveAs_triggered(self):
        return self.on_actionSave_triggered(True)

    @QtCore.pyqtSlot()
    def on_actionNew_triggered(self):
        return self.textEditQuery.setText('')

    @QtCore.pyqtSlot()
    def on_actionFormat_triggered(self):
        self.textEditQuery.setText(sqlparse.format(
            unicode(self.textEditQuery.text()),
            keyword_case='upper',
            identifier_case='lower',
            reindent=True,
            indent_width=4,
        ))

    @QtCore.pyqtSlot()
    def on_actionExecute_triggered(self):
        connection = self.get_connection()
        if connection:
            # 67 is totally arbitrary, but looks better ;)
            self.statusbar_updater.start(67)
            self.query_executed.emit(self.textEditQuery.text(), connection)


class Main(Editor, QtGui.QMainWindow):
    query_executed = QtCore.pyqtSignal(QtCore.QString, QtSql.QSqlDatabase)

    def __init__(self, application):
        QtGui.QMainWindow.__init__(self)
        self._filename = None
        self.application = application
        self.database_menu = database.DatabaseMenu(application.settings)
        self.query_executer = QueryExecuter(self)
        self.query_model = QtSql.QSqlQueryModel(self)
        self.statusbar_updater = QtCore.QTimer()
        self.setupUi()
        self.setupConnections()

    def show(self):
        QtGui.QMainWindow.show(self)
        self.application.restore_state()

    def closeEvent(self, event):
        self.application.save_state()

    def setupUi(self):
        Ui_MainWindow.setupUi(self, self)
        self.tableViewDataOutput.setModel(self.query_model)
        self.database_menu.get_database_layout(self.treeWidgetDatabaseLayout)
        self.toolBar.addWidget(self.database_menu.get_combo_box(self.toolBar))
        self.setupTextEditQuery()

    @QtCore.pyqtSlot()
    def on_actionSettings_triggered(self):
        self.settings_widget = settings_panel.Settings(self.application)
        self.settings_widget.setupUi()
        self.settings_widget.show()

    @QtCore.pyqtSlot(QtSql.QSqlQueryModel)
    def set_query_model(self, query_model):
        self.statusbar_updater.stop()

        error = query_model.lastError()
        self.tableViewDataOutput.setModel(query_model)
        self.tableViewDataOutput.resizeColumnsToContents()
        self.tableViewDataOutput.resizeRowsToContents()
        self.messagesBrowser.setPlainText(error.text())
        if error.isValid():
            self.dockWidgetMessages.show()
            self.dockWidgetMessages.raise_()
            self.statusbar.showMessage(error.text().split('\n')[0])
        else:
            self.dockWidgetDataOutput.show()
            self.dockWidgetDataOutput.raise_()

            self.update_statusbar()
            if self.last_query_duration > 1:
                self.statusbar.showMessage('%d rows in %.3f seconds' % (
                    query_model.rowCount(), self.last_query_duration))
            else:
                self.statusbar.showMessage('%d rows in %dms' % (
                    query_model.rowCount(), self.last_query_duration * 1000))

    def setupConnections(self):
        self.query_executed.connect(self.query_executer.execute_query)
        self.query_executer.query_executed.connect(self.set_query_model)
        self.statusbar_updater.timeout.connect(self.update_statusbar)

        Editor.setupConnections(self)

    def get_connection(self):
        if self.database_menu.current_database:
            return self.database_menu.current_database
        else:
            QtGui.QMessageBox.warning(
                self,
                self.trUtf8('Select a database'),
                self.trUtf8('Please select a database first'),
            )

    @QtCore.pyqtSlot()
    def update_statusbar(self):
        if self.query_executer.time:
            self.last_query_duration = time.time() - self.query_executer.time
            if self.last_query_duration > 1:
                self.statusbar.showMessage('Query executing: %.3fs' %
                    self.last_query_duration)
            else:
                self.statusbar.showMessage('Query executing: %dms' %
                    (self.last_query_duration * 1000))

    def save_state(self):
        QVar = QtCore.QVariant

        setVal = self.application.settings.setValue
        setVal('main/state', QVar(self.saveState()))
        setVal('main/query', QVar(self.textEditQuery.text()))
        setVal('main/database', QVar(
            self.database_menu.current_database.databaseName()))

    def restore_state(self):
        val = self.application.settings.value
        self.textEditQuery.setText(val('main/query').toString())
        self.database_menu.change_database(val('main/database').toString())

        self.restoreState(val('main/state').toByteArray())

        self.api.add_table_names(self.get_connection())
        self.api.prepare()


class Application(QtGui.QApplication):

    def __init__(self, argv):
        QtGui.QApplication.__init__(self, argv)
        self.settings = settings.Settings()
        self.main = Main(application=self)
        self.restore_state()

    def saveState(self, manager):
        self.save_state()
        manager.release()

    def confirmClose(self, manager=None):
        buttons = QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard
        if manager:
            buttons |= QtGui.QMessageBox.Cancel

        ret = QtGui.QMessageBox.warning(
            self.main,
            self.trUtf8('QtQuery'),
            self.trUtf8('Do you want to save your current session?'),
            buttons,
        )

        if ret == QtGui.QMessageBox.Save:
            if manager:
                manager.release()
            self.save_state()
        elif ret == QtGui.QMessageBox.Cancel and manager:
            manager.cancel()
        elif manager:
            manager.release()

    def commitData(self, manager):
        if manager.allowsInteraction():
            self.requestClose(manager)
        else:
            self.main.save_state()

    def remove_state(self):
        self.settings.remove('')

    def save_state(self):
        for widget in self.allWidgets():
            if hasattr(widget, 'saveState') and widget.objectName():
                k = 'main/widgets/%s_state' % widget.objectName()
                v = QtCore.QVariant(widget.saveState())
                self.settings.setValue(k, v)

        self.main.save_state()

    def restore_state(self):
        for widget in self.allWidgets():
            if hasattr(widget, 'restoreState') and widget.objectName():
                k = 'main/widgets/%s_state' % widget.objectName()
                v = self.settings.value(k).toByteArray()
                widget.restoreState(v)

        self.main.restore_state()


if __name__ == '__main__':
    app = Application(sys.argv)
    app.main.show()
    #app.main.on_actionSettings_triggered()
    sys.exit(app.exec_())

