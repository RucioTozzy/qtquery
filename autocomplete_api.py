from PyQt4 import Qsci

class PostgresAPI(Qsci.QsciAPIs):
    def __init__(self, lexer):
        Qsci.QsciAPIs.__init__(self, lexer)
        self.init()

    def init(self):
        # Create an autocompletion API
        self.load('psql.api')
        self.add('table')

    def updateAutoCompletionList(self, context, autocomplete):
        print 'context: %r' % context.join(', ')
        print 'autocomplete list: %r' % autocomplete.join(', ')
        return Qsci.QsciAPIs.updateAutoCompletionList(self, context, autocomplete)

    def autoCompletionSelected(self, selection):
        print 'selection: %r' % selection
        return Qsci.QsciAPIs.autoCompletionSelected(self, selection)
