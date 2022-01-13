import os
import email
import sys
import getopt
import json
import zipfile
import logging
from datetime import datetime
from datetime import date, timedelta
from time import sleep, time

'''
Creating logger
'''
mylogs = logging.getLogger(__name__)
mylogs.setLevel(logging.DEBUG)

today = datetime.now()
YYYY = today.strftime("%Y")
MM   = today.strftime("%m")
NOW  = today.strftime("%Y%m%d")
# BASE_LOG = "/data/logs/read_webbounce/"
BASE_LOG = "C:/Users/LTAPPS01/temp/webbounce_emails"


LOG_NAME = BASE_LOG + "/" + YYYY + "/" + MM + "/" + NOW +'_read_webbounce.log'

try:
    os.makedirs(BASE_LOG + "/" + YYYY + "/" + MM )
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
            print(i)
            parseEmail(i,zip_file)
            break
# def extract_message_payload(mes, parent_subject=None):
#     """
#     Extracts recursively the payload of the messages contained in :mes:
#     When a message is embedded in another, it uses the parameter :parent_subject:
#     to set the subject properly (it uses the parent's subject)
#     """
#     extracted_messages = []
#     if mes.is_multipart():
#         if parent_subject is None:
#             subject_for_child = mes.get('Subject')
#         else:
#             subject_for_child = parent_subject
#         for part in mes.get_payload():
#             extracted_messages.extend(extract_message_payload(part, subject_for_child))
#     else:
#         extracted_messages.append(CustomMessage(mes.get_payload(decode=True), parent_subject,  mes.get_content_type()))
#     return extracted_messages

def getContent(msgObj):

    for part in msgObj:
        for subpart in part.get_payload():
            print(subpart.get('X-Tap-ID'))
    else:
        body = msgObj.get_payload(decode=True)


def parseEmail(email_file,zippa):
    with zipfile.ZipFile(zippa,'r') as zip:
        # with zip.open(email_file) as singlefile:
        #     # for row in singlefile:
        #     #     print(row)
        imgdata = zip.read(email_file)
        if isinstance(imgdata, bytes):
            msg = email.message_from_bytes(imgdata)

        elif isinstance(imgdata, str):
            msg = email.message_from_string(imgdata)
        else:
            raise TypeError('Invalid message type: %s' % type(imgdata))
        if msg.is_multipart():
            # subject = msg.get('Subject')
            # print(len(msg.get_payload()))
            # for a in msg.get_payload():
            #     if a.is_multipart():
            #         for b in a.get_payload():
            #             print(b)
            #
            # print(subject)
            for m in msg.walk():
                getContent(m.get_payload())
                break

        else:
            body = msg.get_payload(decode=True)



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
        opts, args = getopt.getopt(argv,"hp:",["zipfile="])
    except getopt.GetoptError:
        print (f"read_webbouce -p <zipfile>")
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

