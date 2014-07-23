from Tkinter import *
from tkFileDialog import *
import dropbox
import gnupg
import ConfigParser
import sys
import os
import webbrowser
import pyinotify

'''
Class handling signing and verification using gnuog and uploading to dropbox
through dropbox api calls
'''
class DocSigner():
    #Get settings values from settings.ini
    def getSettings(self):
        try:
            config = ConfigParser.ConfigParser()
            config.read("settings.ini")
            self.app_key = config.get("SectionOne","app_key")
            self.app_secret = config.get("SectionOne","app_secret")
            self.access_token = config.get("SectionOne","access_token")
            self.dropbox_dir= config.get("SectionOne","dropbox_directory")
        except IOError:
            print "Error opening file"
            sys.exit(1)

    #Signs a file using the provided private key
    def signFile(self,filepath):
        f = open(filepath,'rb')
        gpg = gnupg.GPG()
        gpg.encoding = 'utf-8'
        print f.encoding
        signed_file=gpg.sign_file(f,keyid=u'C8A6413ACCDF1579')
        print signed_file.stderr
        return signed_file

    #Signs a file using the provided private key
    def encryptFile(self,filepath):
        f = open(filepath,'rb')
        gpg = gnupg.GPG()
        gpg.encoding = 'utf-8'
        print f.encoding
        signed_file=gpg.encrypt_file(f,recipients=['angelo102@gmail.com'],output='encryptedfile')
        print signed_file.stderr
        return signed_file

    #Verifies digital signature of a file
    def verifyFile(self,filepath):
        f = open(filepath,'rb')
        gpg = gnupg.GPG()
        gpg.encoding = 'utf-8'
        verified_file=gpg.verify_file(f)
        print verified_file.stderr
        return verified_file

    #Uploads file to Dropbox
    def uploadToDropbox(self,filename,filedata):
        try:
            flow = dropbox.client.DropboxOAuth2FlowNoRedirect(self.app_key, self.app_secret)
            self.client = dropbox.client.DropboxClient(self.access_token)
            print 'linked account: ', self.client.account_info()
            response = self.client.put_file(filename,filedata)
            print 'File Uploaded Info: '
            print response
            return response
        except:
            print "Unexpected Error", sys.exc_info()
            print "Make sure app_key, app_secret and access_token are set in settings.ini"
            sys.exit(1)

    #Download file from Dropbox
    def downloadFromDropbox(self,filename):
        try:
            flow = dropbox.client.DropboxOAuth2FlowNoRedirect(self.app_key, self.app_secret)
            self.client = dropbox.client.DropboxClient(self.access_token)
            print 'linked account: ', self.client.account_info()

            out=open(filename,'wb')
            f,meta = self.client.get_file_and_metadata('/'+filename)
            with f:
                out.write(f.read())
            
            print 'File Downloaded Info: '
            print meta
            return f
        except:
            print "Unexpected Error", sys.exc_info()
            print "Make sure app_key, app_secret and access_token are set in settings.ini"
            sys.exit(1)
        
'''
Application Class handling GUI elements usink TKinter as a wrapper for TCL
'''
class Application(Frame):
    #Initializes GUI
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.ds = DocSigner()
        self.grid()
        self.createWidgets()
        self.ds.getSettings()
       
    #Configures GUI Controls   
    def createWidgets(self):
        #Sign button
        self.signButton = Button(self)
        self.signButton["width"]=25
        self.signButton["text"] = "Open File for Signing"
        self.signButton["command"] = self.opendialogm
        self.signButton.grid(row=1,column=0,sticky=W)

        #Verify Button
        self.verifyButton = Button(self)
        self.verifyButton["width"]=25
        self.verifyButton["text"] = "Open File for Verification"
        self.verifyButton["command"] = self.opendialogRet
        self.verifyButton.grid(row=2,column=0,sticky=W) 

        #text widget
        self.textW = Text(self, width=100, height=20)
        self.textW.insert('1.0','')
        self.textW.grid(row=3,column=0,sticky=W)

        #close app button
        self.quitButton = Button(self, text="QUIT", fg="red", command=self.master.destroy)
        self.quitButton.grid(row=4,column=0,sticky=W)

    #Opens a file to be signed and uploaded to dropbox
    def opendialogm(self):
        filepath = askopenfilename()
        filename = os.path.split(filepath)[-1]
        #Sign File before uploading to dropbox
        signed_file = self.ds.signFile(filepath)
        self.textW.delete('1.0',END)
        self.textW.insert('1.0', signed_file.stderr + "\n")
        #uploadfile to dropbox
        self.ds.uploadToDropbox(filename,signed_file.data)

    #Opens a file for digital verification
    def opendialogRet(self):
        filepath = askopenfilename(initialdir=self.ds.dropbox_dir)
        filename = os.path.split(filepath)[-1]
        #Verify File
        verified_file=self.ds.verifyFile(filepath)
        self.textW.delete('1.0',END)
        self.textW.insert('1.0', verified_file.stderr + "\n")
      
def main(): 
    root = Tk()
    root.title("Dropbox File Signer")
    app = Application(master=root)
    app.mainloop()

if __name__ == '__main__':
    main()
