import os
import email
import sys
import getopt
import json
import re
import zipfile
import logging
import mailparser
from datetime import datetime
from datetime import date, timedelta
from time import sleep, time

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
    BASE_LOG = "/data/webbounce_emails"
else:
    BASE_LOG = "C:/Users/LTAPPS01/temp/webbounce_emails"

LOG_NAME = BASE_LOG + "/" + YYYY + "/" + MM + "/" + NOW + '_read_webbounce.log'

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
            parseEmail(i, zip_file)
            # break


def getContent(msgObj):
    for part in msgObj:
        for subpart in part.get_payload():
            print(subpart.get('X-Tap-ID'))
    else:
        body = msgObj.get_payload(decode=True)


def parseEmail(email_file, zippa):
    with zipfile.ZipFile(zippa, 'r') as zip:
        # read file in zip
        imgdata = zip.read(email_file)
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
        # print("-", end='')
        if email_file == "email_backup.021/506220_87a2ceedfetg@esa8_utexas_iphmx_com.eml":
            print("pl")
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
        regex = r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"

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
        if recipient_email == 'not found' and email_from != '':
            recipient_email = email_from

        elif msg.body:
            matches = re.search(regex, msg.body, re.MULTILINE | re.IGNORECASE)
            if matches is not None or matches == 'Not found':
                if matches.group():
                    recipient_email = matches.group()


        print(f"{email_file}|Date: {email_data}|from: {email_from}|mail:{recipient_email}|mail_id: {mailid}")
        if email_from == '' and mailid == '' and recipient_email == '':
            mylogs.info(f"{email_file}|Date: {email_data}|from: {email_from}|mail:{recipient_email}|mail_id: {mailid}")
        # print(f"Subj: {msg.subject}")


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
    try:
        opts, args = getopt.getopt(argv, "hp:", ["zipfile="])
    except getopt.GetoptError:
        print(f"read_webbouce -p <zipfile>")
        sys.exit(2)
    opt_papername = ''
    for opt, arg in opts:
        if opt == '-h':
            print(f"read_webbouce -p <zipfile>")
            sys.exit()
        elif opt in ("-p", "--zipfile") and arg != '':
            opt_papername = arg
    if opt_papername == '':
        print(f"read_webbouce -p <zipfile>")
        sys.exit()
    dozip(BASE_LOG + "/" + opt_papername)
    # for subdir, dirs, files in os.walk(root_dir):
    #     for file in files:
    #         print( os.path.join(subdir, file))
    #         with open(os.path.join(subdir, file), 'r') as mail_file:
    #             mail_file_obj = email.message_from_file(mail_file)
    #             print(mail_file_obj)
    #         exit(1)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])

    except KeyboardInterrupt:
        mylogs.error("Process interrupted by KeyboardInterrupt")

