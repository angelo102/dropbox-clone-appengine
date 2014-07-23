import logging
import os
import cloudstorage as gcs
import webapp2

from google.appengine.api import app_identity

bucket_name = 'brilliant-vent-626.appspot.com'

gcs_file = gcs.open('t.txt','w')