from PyQt4 import QtCore
import utils


class Settings(QtCore.QSettings):
    def __init__(self):
        QtCore.QSettings.__init__(self, 'WoLpH', 'QtQuery')

    def __setitem__(self, key, value):
        if isinstance(value, (list, tuple)):
            self.write_dict(key, value)
        else:
            self.setValue(key, utils.qstr(unicode(value)))
        self.sync()

    def write_dict(self, dict_):
        for k, v in dict_.iteritems():
            self[k] = v

    def write_list(self, key, list_):
        self.beginWriteArray(key)
        for i, dict_ in enumerate(list_.iteritems()):
            self.setArrayIndex(i)
            self.write_dict(dict_)
        self.endArray()
