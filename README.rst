QtQuery, the PGAdmin3 alternative
----------------------------------------------------------------------

Even though QtQuery is not as extensive as PGAdmin3 yet, it does offer a few
conveniences such as:

 - Smart autocompletion (based on the words in your files, the tables, the
   columns, etc.)
 - Automatic saving of the current query in case of crashes
 - Built-in documentation browser


 To run simply run
 
 ..
 
    python main.py

Requirements:
=====================

 - PyQt4
 - QScintilla
 - sqlparse

To install and run on OS X:

..

    git clone https://github.com/WoLpH/qtquery.git
    brew install qscintilla2 pyqt
    pip install sqlparse
    python qtquery/main.py
