#! /usr/bin/env python

import sys
import os
from gi.repository import Gtk
#import gobject

class HW:

	def __init__(self):
		try:
			builder = Gtk.Builder()
			builder.add_from_file("shark.glade")
			builder.connect_signals(self)
		except Exception as ex:
			print type(ex)
			print ex.args
			print ex
			sys.exit(1)

		self.window = builder.get_object("MainWindow")
		if (self.window):
			self.window.connect("destroy", Gtk.main_quit)

	def main(self):
		self.window.show_all()
		Gtk.main()

if __name__ == "__main__":
	hw = HW()
	hw.main()
