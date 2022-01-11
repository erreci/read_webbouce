import os
import email

def main():

    root_dir = 'C:/Users/LTAPPS01/temp/webbounce_emails'

    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            print( os.path.join(subdir, file))
            with open(os.path.join(subdir, file), 'r') as mail_file:
                mail_file_obj = email.message_from_file(mail_file)
                print(mail_file_obj)
            exit(1)


if __name__ == '__main__':
    main()

