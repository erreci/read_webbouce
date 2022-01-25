import os
import email
import sys
import getopt
import argparse
#import json
import re
import zipfile
import logging
import mailparser
from datetime import datetime
#from datetime import date, timedelta
#from time import sleep, time

from database import Database


__version__ = '0.1'
'''
 using wrapper https://github.com/SpamScope/mail-parser
'''

'''
multipart/mixed
 |
 +- multipart/related
 |   |
 |   +- multipart/alternative
 |   |   |
 |   |   +- text/plain
 |   |   +- text/html
 |   |      
 |   +- image/png
 |
 +-- application/msexcel


 multipart/alternative
 |
 +- text/plain
 +- multipart/related
      |
      +- text/html
      +- image/jpeg

'''
'''
bounce-type:
policy-related
bad-connection
routing-errors
other
bad-mailbox
bad-domain
quota-issues
inactive-mailbox
relaying-issues
no-answer-from-host
spam-related
message-expired
'''

'''
Creating logger
'''
mylogs = logging.getLogger(__name__)
mylogs.setLevel(logging.DEBUG)

today = datetime.now()
YYYY = today.strftime("%Y")
MM = today.strftime("%m")
NOW = today.strftime("%Y%m%d")
# BASE_LOG = "/data/logs/read_webbounce/"

if sys.platform == 'darwin':
    BASE_LOG = "/Users/macmini/data/webbounce_emails"
elif sys.platform == 'linux':
    BASE_LOG = "/data/log/webbounce_emails"
else:
    BASE_LOG = "C:/Users/LTAPPS01/temp/webbounce_emails"

LOG_NAME = BASE_LOG + "/" + YYYY + "/" + MM + "/" + NOW + '_read_webbounce.log'
USE_DB = 0

try:
    os.makedirs(BASE_LOG + "/" + YYYY + "/" + MM)
except FileExistsError:
    # directory already exists
    pass

# on file
onfile = logging.FileHandler(LOG_NAME)
fileformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
onfile.setLevel(logging.DEBUG)
onfile.setFormatter(fileformat)

# on console
onstream = logging.StreamHandler()
streamformat = logging.Formatter("%(levelname)s:%(message)s")
onstream.setLevel(logging.DEBUG)
onstream.setFormatter(streamformat)
# Adding all handlers to the logs
mylogs.addHandler(onfile)
mylogs.addHandler(onstream)


def dozip(zip_file):
    if not os.path.exists(zip_file):
        mylogs.info("The File %s it's not present " % zip_file)
        exit()
    filesinzip = unzipl(zip_file)
    if filesinzip:
        print("found: %d" % len(filesinzip))
        for i in filesinzip:
            # print(i)
            parseEmailZip(i, zip_file)
            # break


def getContent(msgObj):
    for part in msgObj:
        for subpart in part.get_payload():
            print(subpart.get('X-Tap-ID'))
    else:
        body = msgObj.get_payload(decode=True)


def parseEmailZip(email_file, zippa):
    with zipfile.ZipFile(zippa, 'r') as zip:
        # read file in zip
        imgdata = zip.read(email_file)
        parseEmail(imgdata,email_file)
        exit(1)


def parseEmailFile(email_file):
    with open(email_file, 'rb') as emfile:
        imgdata = emfile.read()
        parseEmail(imgdata, email_file)
        # exit(1)

def parseEmail(imgdata,email_file):

        try:
            # print(type(imgdata))
            # msg_raw = email.message_from_bytes(imgdata)

            if isinstance(imgdata, bytes):
                # msg = email.message_from_bytes(imgdata)
                msg = mailparser.parse_from_bytes(imgdata)
            elif isinstance(imgdata, str):
                msg = mailparser.parse_from_string(imgdata)
            else:
                raise TypeError('Invalid message type: %s' % type(imgdata))
        except mailparser.MailParser.MailParserError as sss:
            print(sss)
        print("-", end='')

        # if msg.text_not_managed:   # rfc822-header  content
        #     print(f"ddddd {msg.text_not_managed}" )
        '''
            get email data
        '''
        email_data = msg.date
        '''
             get from from autoreply email  filter the mail server address              
        '''
        email_from = msg.headers.get('From')
        if re.search(r'postmaster',email_from, re.IGNORECASE):
            email_from = ''
        elif re.search(r'MAILER-DAEMON',email_from, re.IGNORECASE):
            email_from = ''
        elif re.search(r'AntiSpam',email_from, re.IGNORECASE):
            email_from = ''
        '''
            get message id 
        '''
        mailid = ''
        regex = r"X-Tap-ID:\s*([^\n\r]+)"
        matches = re.search(regex, msg.body, re.MULTILINE | re.IGNORECASE)

        if matches is not None or matches == 'Not found':
            mailid = matches.group(1)
        else:
            #  try to get from html using message_id as value
            regex = r"message_id=\s*([^\"\&\s]+)"
            if msg.text_html:
                matches = re.search(regex, msg.text_html[0], re.MULTILINE | re.IGNORECASE)
                if matches is not None or matches == 'Not found':
                    mailid = matches.group(1)
            else:
                mailid = "not found"
        #    get recipient mail
        recipient_email = 'not found'
        #regex = r"[a-z0-9]+[\._]?[a-z0-9]+[@][\w\-]+[.]\w{2,3}"
        regex = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
        mail_text = ''
        if msg.text_plain:
            if len(msg.text_plain) > 0:
                matches = re.search(regex, msg.text_plain[0], re.MULTILINE | re.IGNORECASE)
                if matches is not None or matches == 'Not found':
                    if matches.group():
                        recipient_email = matches.group()
            else:
                matches = re.search(regex, msg.text_plain, re.MULTILINE | re.IGNORECASE)
                if matches is not None or matches == 'Not found':
                    if matches.group():
                        recipient_email = matches.group()
            mail_text = msg.text_plain
        elif msg.body:
            mail_text = msg.text_plain
            matches = re.search(regex, msg.body, re.MULTILINE | re.IGNORECASE)
            if matches is not None or matches == 'Not found':
                if matches.group():
                    recipient_email = matches.group()
        if recipient_email == 'not found' and email_from != '':
            recipient_email = email_from


        #print(f"{email_file}|Date: {email_data}|from: {email_from}|mail:{recipient_email}|mail_id: {mailid}")
        if msg.body:
            mail_text = filterBody(msg.body)
        if mail_text == '':
            mail_text = msg.body[0:1000]
        info_email = {'date': email_data,'email_from': email_from, 'mail':recipient_email,'mail_id':mailid, 'mail_text': mail_text}

        if mailid == '' or recipient_email == '':
            mylogs.info(f"{email_file}|Date: {info_email['date']}|from: {info_email['email_from']}|mail:{info_email['mail']}|mail_id: {info_email['mail_id']}|text: {info_email['mail_text']}")
        if mailid != '':
            if USE_DB == 1:
                updatedb(info_email)

        print(f"filter: {mail_text}")

def filterBody(body):
    ''' pass text from multiple re for filter bouncing error '''

    found = ''
    # body = body.replace('\n', ' ').replace('\r', '')

    regex = r"(reported error\s*[^\r]+)"
    matches = re.search(regex, body, re.MULTILINE | re.IGNORECASE)
    if matches is not None or matches == 'Not found':
        if matches.group():
            found = matches.group()
    if found == '':
        regex = r"(abuse report\s*[^\n]+)"
        matches = re.search(regex, body, re.MULTILINE | re.IGNORECASE)
        if matches is not None or matches == 'Not found':
            if matches.group():
                found = matches.group()
    if found == '':
        regex = r"(remote Server returned.+?;)"
        matches = re.search(regex, body, re.MULTILINE | re.IGNORECASE)
        if matches is not None or matches == 'Not found':
            if matches.group():
                found = matches.group()
    if found == '':
        regex = r"remote Server returned(.+?)original"
        matches = re.search(regex, body, re.IGNORECASE | re.DOTALL)
        if matches is not None or matches == 'Not found':
            if matches.group():
                found = matches.group()
    if found == '':
        regex = r"(The following recipient\(s\) could not be reached.+)"
        matches = re.search(regex, body, re.MULTILINE | re.IGNORECASE | re.DOTALL )
        if matches is not None or matches == 'Not found':
            if matches.group():
                found = matches.group()
    if found == '':
        regex = r"Your message wasn't delivered to.+"
        matches = re.search(regex, body, re.MULTILINE | re.IGNORECASE  )
        if matches is not None or matches == 'Not found':
            if matches.group():
                found = matches.group()
    if found == '':
        regex = r"(the mail system\s*\n.*said:.*)\n---"
        matches = re.search(regex, body, re.IGNORECASE | re.DOTALL)
        if matches is not None or matches == 'Not found':
            if matches.group():
                found = matches.group()
    if found == '':
        regex = r"The response from the remote server was:\s*\n+(.+)\n+"
        matches = re.search(regex, body, re.IGNORECASE)
        if matches is not None or matches == 'Not found':
            if matches.group():
                found = matches.group()
    if found == '':
        regex = r">>>(.+?)(\n{2}|---)"
        matches = re.search(regex, body, re.IGNORECASE | re.DOTALL)
        if matches is not None or matches == 'Not found':
            if matches.group():
                found = matches.group(1)
    if found == '':
        regex = r"Delivery has failed to these recipients or groups:\n{2}(.+\n.+)\n+"
        matches = re.search(regex, body, re.MULTILINE | re.IGNORECASE)
        if matches is not None or matches == 'Not found':
            if matches.group():
                found = matches.group(1)
    if found == '':
        regex = r"The following addresses had permanent fatal errors(.+)---\s*mail_boundary\s*---"
        matches = re.search(regex, body,  re.IGNORECASE | re.DOTALL)
        if matches is not None or matches == 'Not found':
            if matches.group():
                found = matches.group(1)
    if found == '':
        regex = r"reason:(.+)\n*"
        matches = re.search(regex, body, re.IGNORECASE | re.MULTILINE)
        if matches is not None or matches == 'Not found':
            if matches.group():
                found = matches.group()
    if found == '':
        regex = r"Sorry, we were unable to deliver your message to the following address.(.+)--- mail_boundary ---"
        matches = re.search(regex, body,  re.IGNORECASE | re.DOTALL)
        if matches is not None or matches == 'Not found':
            if matches.group():
                found = matches.group(1)
    return found


def updatedb(info_email):
    # check if present in first db
    Database.execute("SELECT id WHERE id = %s", (info_email['mail_id'],))
    if Database.rowcount() > 0:


    Database.execute("UPDATE  mail_email SET status = IF(status = 'sent', 'bounced', status) WHERE id = %s", (info_email['mail_id'],))
    Database.commit()
    if Database.rowcount() > 0:
        mylogs.info(f"Updated mail_id: {info_email['mail_id']}")
    
def unzipl(zip_file):
    zippath = zip_file
    zip_files = []
    if not zipfile.is_zipfile(zippath):
        mylogs.info("The File %s it's not present " % zip_file)
        return False
    try:
        test_zip_file = zipfile.ZipFile(zippath)
        if test_zip_file.testzip() is not None:
            print(f"Zip error on {zip_file}")
        else:
            with test_zip_file as zip:
                for a in zip.infolist():
                    if a.filename.endswith('/'):
                        continue
                    zip_files.append(a.filename)
    except Exception as e:
        print(f"e: Zip error on {zip_file} {e}")
        return False
    return zip_files

def main(argv):
    if argv.db == 1:
        USE_DB = 1
        first_db = Database.connect("usamaildb8", "8bdliamasu", "mail", "usamaildb8.ceiimqxfndkz.us-east-1.rds.amazonaws.com", "3306")
        second_db =  Database.connect("root", "", "mail", "localhost", "3307")
        if first_db and second_db:
            print("db ok")
        else:
            print('failed to connect db')
            exit(1)


    if argv.zip:
       dozip(argv.zip)
    elif argv.path:
        if os.path.isdir(argv.path):
            for subdir, dirs, files in os.walk(argv.path):
                for file in files:
                    # print( os.path.join(subdir, file))    with open(email_file, 'rb') as emfile:
                    #         # read file in zip
                    #         imgdata = emfile.read()
                    parseEmailFile(os.path.join(subdir, file))
                    # exit(1)
        else:
            print(f"The path {argv.path} doesnt exist")
            exit(1)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("-z", "--zip", type=str, help="using zip file")
        parser.add_argument("-p", "--path", type=str, help="path of unzipped files" )
        parser.add_argument("-d", "--db", type=int, help="1 use db", required=True)
        parser.add_argument('-v', '--version', action='version', version='%(prog)s {} by ErreCi (2022)'.format(__version__))
        args = parser.parse_args()
        main(args)

    except KeyboardInterrupt:
        mylogs.error("Process interrupted by KeyboardInterrupt")

