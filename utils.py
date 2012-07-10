from PyQt4 import QtCore
import pprint


def qstr(var):
    if isinstance(var, basestring):
        return QtCore.QString.fromUtf8(var)
    elif isinstance(var, QtCore.QVariant):
        return var.toString()
    else:
        print type(var), repr(var)
    return var


def debug(var, name=None):
    print 'Printing %r' % (name or '')
    for k in dir(var):
        v = getattr(var, k)
        e = None
        if callable(v):
            try:
                v = v()
            except Exception, e:
                pass

        if v and not callable(v):
            v = pprint.pformat(v)
            if e:
                v = '%s :: %r' % (v, e)
            print '\t%s: %r' % (k, v)
