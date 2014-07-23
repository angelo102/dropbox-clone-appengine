import ConfigParser
import pyinotify
import os
import sys
import subprocess
import time
from DropboxFileSigner import DocSigner


class EventHandler(pyinotify.ProcessEvent):

	def process_IN_ACCESS(self, event):
		print "ACCESS event:", event.pathname

	def process_IN_ATTRIB(self, event):
		print "ATTRIB event:", event.pathname

	def process_IN_CLOSE_WRITE(self, event):
		print "CLOSE_WRITE event:", event.pathname

		#get settrings for gsutil command
		config = ConfigParser.ConfigParser()
		config.read("settings.ini")
		watch_dir = config.get("SectionOne","watch_dir")
		bucket = config.get("SectionTwo","bucketpath")
		gsutilpath = config.get("SectionTwo","gsutilpath")
		user = config.get("SectionTwo","user")
		signfileOption = config.get("SectionOne","sign_file")
		encryptFileOption = config.get("SectionOne","encrypt_file")
		encfolder = config.get("SectionOne","encryptfolderpath")
		signfolder = config.get("SectionOne","signedfolderpath")
		
		docSigner = DocSigner()
		docSigner.getSettings()
		
		filename = os.path.split(event.pathname)[-1]

		#if option selected in settings.ini
		if signfileOption == "True":
			signedFile=docSigner.signFile(event.pathname)
			#delete file from folder
			os.remove(event.pathname)
			filename = os.path.split(event.pathname)[-1]
			f = open(signfolder+'/'+filename,'wb+')
			f.write(signedFile.data)
			f.close()

			dest_path = "gs://"+bucket+"/"+user+"/"+filename
			#run the import process
			outp=subprocess.check_call([gsutilpath,
			"cp",
			signfolder+'/'+filename,
			dest_path
			])

		elif encryptFileOption == "True":
			filename = os.path.split(event.pathname)[-1]
			
			encryptFile=docSigner.encryptFile(event.pathname)
			#delete file from folder
			os.remove(event.pathname)
			
			dest_path = "gs://"+bucket+"/"+user+"/"+filename
			
			#run process gsutil
			outp=subprocess.check_call([gsutilpath,
			"cp",
			encfolder+'/encryptedfile',
			dest_path
			])

		else:
			dest_path = "gs://"+bucket+"/"+user+"/"+filename
			#run the import process
			outp=subprocess.check_call([gsutilpath,
			"cp",
			event.pathname,
			dest_path
			])
			
			print outp
			print "file uploaded!!!!"

		#sync with cloud

		#Remove watch only while performing sync
		global wm,wdd
		wm.rm_watch(wdd[watch_dir])

		src_url = "gs://"+bucket+"/"+user
		dst_url = watch_dir
		syncp=subprocess.call([gsutilpath,
			"rsync",
			src_url,
			dst_url
			])
		
		#Watch Folder Again
		wdd = wm.add_watch(watch_dir, pyinotify.ALL_EVENTS, rec=True)

	def process_IN_CREATE(self, event):
		print "CREATE event:", event.pathname

	def process_IN_ONESHOT(self, event):
		print "ONESHOT event:", event.pathname

	def process_IN_MOVE_SELF(self, event):
		print "MOVE_SELF event:", event.pathname

	def process_IN_DELETE(self, event):
		print "DELETE event:", event.pathname

	def process_IN_MODIFY(self, event):
		print "MODIFY event:", event.pathname

		
'''
Main for running the watch on the aplication folder
'''

#get folder to watch
config = ConfigParser.ConfigParser()
config.read("settings.ini")
watch_dir = config.get("SectionOne","watch_dir")

# watch manager
wm = pyinotify.WatchManager()
docSigner = DocSigner()
#docSigner.getSettings()

# event handler
eh = EventHandler()
# notifier
notifier = pyinotify.ThreadedNotifier(wm, eh)
wdd = wm.add_watch(watch_dir, pyinotify.ALL_EVENTS, rec=True)
notifier.start()

