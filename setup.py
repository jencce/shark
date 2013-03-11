#! /usr/bin/env python
''' setup script for shark'''

from distutils.core import setup

setup(  name = 'shark',
        version = '0.2',
        author = 'jencce',
        author_email = 'jencce2002@gmail.com',
        url = 'https://github.com/jencce/shark',
        py_modules = ['sharkserver','sharkclient'],
     )
