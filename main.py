import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

from google.appengine.api import app_identity
import cloudstorage as gcs
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

from google.appengine.api import mail
from twilio.rest import TwilioRestClient

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


#Data Model
class User(ndb.Model):
  usr_id = ndb.StringProperty()
  email = ndb.StringProperty()
  phone = ndb.StringProperty()

class SharedFile(ndb.Model):
  file_name = ndb.StringProperty()
  owner = ndb.UserProperty()
  recipients = ndb.StringProperty(repeated=True)
  

class MainPage(webapp2.RequestHandler):
  def get(self):
 
    #login
    usr = users.get_current_user()
    if not usr:
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login'
      self.redirect(users.create_login_url(self.request.uri))
    else:
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
      
      #testing users deb model
      userlist = User.query().fetch(5)
      
      #get files from bucket for the user
      bucket_name = "/"+os.environ.get('BUCKET_NAME',app_identity.get_default_gcs_bucket_name())+"/"+str(usr)
      l_files=gcs.listbucket(bucket_name)

      #get shared files of the user
      sh_files = SharedFile.query(SharedFile.recipients == usr.email())
      result = sh_files.fetch(1000)

      template_values = {
        'url': url,
        'url_linktext': url_linktext,
        'user_name': usr,
        'files': l_files,
        'users': userlist,
        'shared_files': sh_files,
      }

      template = JINJA_ENVIRONMENT.get_template('index.html')
      self.response.write(template.render(template_values))

class ShFiles(webapp2.RequestHandler):
  def post(self):
    #get selected file for sharing
    print "file to share!!!!!!!!!!!!!!!!!!!"
    file_to_share = self.request.get('filelist')
    print file_to_share

    #get users selected for sharing
    print "users to share!!!!!!!!!!!!!!!!"
    users_to_share = self.request.get_all('userlist')
    email_list=[]
    phone_list=[]
    for user in users_to_share:
      u = User.query(User.email==user).fetch(1)
      email_list.append(u[0].email)
      phone_list.append(u[0].phone)
    print email_list

    #get logged user
    usr = users.get_current_user()
    print usr.email()

    #insert shared file in ndb
    shf = SharedFile()
    shf.file_name = file_to_share
    shf.owner = usr
    shf.recipients = users_to_share
    shf.put()
    
    #get notification type
    noti_type = self.request.get('notification')
    print noti_type
    #Send Mail Notifications
    if noti_type == 'email' or noti_type == 'both': 
      sender_address = usr.email()
      subject = "New File Share Notification"
      body = "The user: {0} has shared the file: {1} with you.".format(usr,file_to_share)
      mail.send_mail(sender_address, email_list, subject, body)
    
    if noti_type == 'sms' or noti_type == 'both':
      body = "The user: {0} has shared the file: {1} with you.".format(usr,file_to_share)
      #send sms notification (using trial account phone number)
      account = "ACb6f059b49ec437302bfa8ea2f0075639"
      token = "46a53226c48c45d71269b0c1903e75f8"
      smsclient = TwilioRestClient(account, token)
      for phone in phone_list:
        message = smsclient.messages.create(to="+1"+phone, from_="+19792021603", body=body)

    #redirect to main page
    query_params = {'selected_file' : file_to_share }
    self.redirect('/?'+urllib.urlencode(query_params))

class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
  def get(self):
  
    filename = self.request.get('sharedfilelist')
    blob_key = blobstore.create_gs_key('/gs'+filename)
    self.send_blob(blob_key)

class testU(webapp2.RequestHandler):
  def get(self):
    #create testusers and test files
    usr = users.get_current_user()
    bucket_name = "/"+os.environ.get('BUCKET_NAME',app_identity.get_default_gcs_bucket_name())+"/"+str(usr)
    newf = gcs.open(bucket_name+"/testfile1.txt", 'w')
    newf.write('this is a test file')
    newf.close()
    newf = gcs.open(bucket_name+"/testfile2.txt", 'w')
    newf.close()
    newf = gcs.open(bucket_name+"/testfile3.txt", 'w')
    newf.close()

    user = User(usr_id="angelo102",email="angelo102@gmail.com",phone="6822084557")
    user.put()
    user = User(usr_id="user2",email="angelo102@gmail.com",phone="6822084557")
    user.put()
    user = User(usr_id="user3",email="angel.romerojerez@mavs.uta.edu",phone="6822084557")
    user.put()
    user = User(usr_id="user4",email="angel.romerojerez@mavs.uta.edu",phone="6822084557")
    user.put()
    user = User(usr_id="user5",email="angel.romerojerez@mavs.uta.edu",phone="6822084557")
    user.put()

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/share', ShFiles),
    ('/test', testU),
    ('/download', ServeHandler),
    #('/serve/([^/]+)?', ServeHandler),
], debug=True)




    
    
