"""
TGTS Result ResultUpload Bot

1. Download results from EP/PP to Local Drive under SESSION_ID folder
2. Upload results to LRUS Government Portal
3. File results 

Triggers:
1. Time-based trigger

Manual Check & Emergency Stops
1. Googlesheet "Ready to Upload" checker
2. Validation scripts & logging

Logging:
1. # of success cases
2. Alerts

Reporting:
1. Business Exceptions
2. Alertx

"""
#File var init
__creator__ = "Nam & Myron"
__updated_by__ = "Billy"
__reviewer__ = "Raymond & Billy"
__update_date__ = "2022-08-12"
__version__ = "1.0.6"
__status__ = "Production"

# Dependencies
import logging
import datetime
from requests import Session
import sys
import os
import time
from Save_GDrive import Create_Upload_Files
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from LRUS_SignIn import LRUS_upload
#from slack import sendmsg

# Directory Init
DIRNAME = os.path.dirname(__file__)
MODULES_DIR = os.path.join(DIRNAME,"..","Modules")  

#Desktop Path
try:
    DESKTOP_PATH = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') 
except:
    DESKTOP_PATH = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')  #for mac users

#Variable Init
error = 0
success = 0
SESSION_ID = "Result Upload_" + datetime.datetime.now().strftime("%m%d%Y_%H%M")
GDRIVE_FOLDER_NAME=datetime.datetime.now().strftime("%Y-%m-%d")+"_TBOT"
SLACK_URL = "https://hooks.slack.com/services/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" #Automation Channel
ROOMC_URL = "https://hooks.slack.com/services/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" #labreporting-roomc-rooml Channel
#SLACK_URL = "https://hooks.slack.com/services/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" #drt-testing


#Init Download folder
DPATH = os.path.join(DESKTOP_PATH,"TGTS Result",SESSION_ID)
if not os.path.exists(DPATH):
    os.makedirs(DPATH)
print("DPATH: " + DPATH)

#Init Log folder
LOG_DIR = os.path.join(DESKTOP_PATH, "TGTS Result","Log")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
print("LOGPATH: " + LOG_DIR)
print("Writing to log now...")

#import modules
sys.path.append(MODULES_DIR)
from send_slack import sendmsg
import Google_Credentials_ALL 

#import PP Export script 
from PP_TBOT_Export import ExportResults

#Configure log
Log_Format = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(filename = LOG_DIR + "/" + SESSION_ID + ".log", 
                    filemode = "w", 
                    format = Log_Format, 
                    level = logging.DEBUG)


# Create Session Log
# to be changed to a setup.py function
logger = logging.getLogger()
logger.info("Initializaing Logger...")
logger.info("Session ID: " + SESSION_ID + "\n"
            "Creator: " + __creator__ + "\n"
            "Reviewer: " + __reviewer__ + "\n"
            "Version: " + __version__ + "\n"
            "Status: " + __status__ + "\n"
            "Run Time: "+  datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + "\n\n")
print = logging.info

#Pre Export Message
PRE_EXPORT_MSG = "*Result Upload BOT (TBOT):* \n *Session ID:* " + SESSION_ID + "\n" + "TBOT scheduled to commence in a few minutes. \n If there are any urgent issues requiring us to halt export, please *MANUAL OVER-RIDE* the provider on PP Result Upload. \n> https://docs.google.com/spreadsheets/d/1PC6hyI71DJBMB9uB59E4RDoW_V6dU4pS7iJy7SvXgsg/edit#gid=1963486809"  
PRE_EXPORT_WAIT_TIME = 5 #minutes

# Send PRE_EXPORT_MSG
sendmsg(PRE_EXPORT_MSG,SLACK_URL)

# Countdown export timer - in minutes
for i in range(PRE_EXPORT_WAIT_TIME):
    
    # if within 5 minutes
    if (PRE_EXPORT_WAIT_TIME - i) <= 5:
        #print countdown time
        print("Countdown to export time: " + str(PRE_EXPORT_WAIT_TIME-i) + " minutes")
        time.sleep(30)

        #sleep 30 seconds
        print("Countdown to export time: " + str(PRE_EXPORT_WAIT_TIME-i-0.5) + " minutes")
        time.sleep(30)
    else:
        time.sleep(60)
        print("Countdown to export time: " + str(PRE_EXPORT_WAIT_TIME-i) + " minutes")
print("Countdown complete.")


# Export CSV from PP and save to Local SESSION_ID folder
print("Starting Export from PP...")
logger.info("Running Export CSV from PP Module...")
export_success = True
try:
    export_summary, export_error = ExportResults(SESSION_ID,DPATH)
except Exception as e:
    export_success = False
    error_message = str(e)

#format send string
if export_success == True:
    export_msg = "*Result Upload BOT (TBOT):* \n *Session ID:* " + SESSION_ID + "\n" + "[Export from PP Module] Please see summary below. \n" 
    for key in export_summary:
        #format key-value pair
        string = "> " + str(key) + ": " + str(export_summary[key])
        #add key-pair value
        export_msg = export_msg + string + "\n"
    # Add CC if error
    if len(export_error) >= 1:
        export_msg = export_msg + "\n cc: <!here>"
elif export_success == False:
    export_msg = "*ERROR: Result Upload BOT (TBOT):* \n *Session ID:* " + SESSION_ID + "\n" + "[Export from PP Module] An issue occured with Export to PP. ... \n cc: <!channel>" 
    export_msg = export_msg + "\n ERROR MESSAGE: \n " + error_message


# Send slack msg
sendmsg(export_msg,SLACK_URL)


#[INSERT CODE BLOCK HERE]
logger.info("Uploading results onto LRUS portal...")

#Upload the result to LRUS portal
upload_success = True
try:
    upload_log, upload_dict = LRUS_upload (DPATH)
except Exception as e:
    upload_success = False
    error_message = str(e)

#Format msg
if upload_success == True:
    upload_msg = "*Result Upload BOT (TBOT):* \n *Session ID:* " + SESSION_ID + "\n" + "[Result Upload to LRUS] Files are uploaded to LRUS. \n" 
    for key in upload_log:
        #format key-value pair
        string = "> " + str(key) + ": " + str(upload_log[key])
        #add key-pair value
        upload_msg = upload_msg + string + "\n"
    # Add CC
    if len(upload_log) >=1:
        upload_msg = upload_msg + "\n cc: <!here>" 
elif upload_success == False:
    upload_msg = "*ERROR: Result Upload BOT (TBOT):* \n *Session ID:* " + SESSION_ID + "\n" + "[Result Upload to LRUS] An issue occured with LRUS result upload. Continuing to save to Gdrive... \n cc: <!channel>" 
    upload_msg = upload_msg + "\n ERROR MESSAGE: \n " + error_message

#slack save_msg 
sendmsg(upload_msg,SLACK_URL)

"""
Upload results to LRUS portal
# try - catch
#   find supporting element
#   if cannot error - retry function again, error_count++
#   if cannot relogin

"""



# Upload file to Google drive
'''
Save_GDrive.FileSave_GDrive(SESSION_ID,DPATH)

logger.info("Filing onto Google Drive...")'''

#Inital set up for creating Google Drive Credentials 
API_NAME = 'drive'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/drive']
#creds = Google_Credentials_ALL.google_credentials()
#service = build(API_NAME,API_VERSION,credentials=creds)

#Define the Parent Folder ID in Google Drive --> TGTS Result Upload- Automation
MAIN_FOLDER_ID = '1w-NFCIXWw6Ynk4CjdMioC-errhc-R2Na'

#Upload Files to Google Drive
save_success = True

try:
    upload_log, upload_dict = Create_Upload_Files(GDRIVE_FOLDER_NAME,SESSION_ID,DPATH,MAIN_FOLDER_ID)
except Exception as e:
    save_success = False
    error_message = str(e)

#Format msg
if save_success == True:
    save_msg = "*Result Upload BOT (TBOT):* \n *Session ID:* " + SESSION_ID + "\n" + "[Save Files to GDrive] Files are added to GDrive. \n" 
    for key in upload_log:
        #format key-value pair
        string = "> " + str(key) + ": " + str(upload_log[key])
        #add key-pair value
        save_msg = save_msg + string + "\n"
    # Add CC
    if len(upload_log) >=1:
        save_msg = save_msg + "\n cc: <!here>" 
    # add link
    save_msg = save_msg + "\n https://drive.google.com/drive/folders/1w-NFCIXWw6Ynk4CjdMioC-errhc-R2Na"
elif save_success == False:
    save_msg = "*ERROR: Result Upload BOT (TBOT):* \n *Session ID:* " + SESSION_ID + "\n" + "[Save Files to GDrive] An issue occured with Gdrive saving. Continuing to save to Gdrive... \n cc: <!channel>" 
    save_msg = save_msg + "\n ERROR MESSAGE: \n " + error_message
    

#slack save_msg 
sendmsg(save_msg,SLACK_URL)


# Save & close log

logger.info("Script Complete. " + "\n\n"
            "Completion Time: " + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + "\n"
            "Number of Errors: " + str(error) + "\n"
            "Number of Success: " + str(success))
logging.shutdown()




"""
WORKING INFO - TO BE DELETED AFTERWARDS


 Alerts & Log


Exceptions:
- Failed results uploads


System Errors:
- Cannot Login/Timeout to PP
- Cannot Login/Timeout to Gov Portal
- Cannot Find File
- No result from Export
- Cannot upload file


def ExportCSVFromPP(provider) :

def Gdrive(folder_name,location) return success:

def UploadToLRUS(filepath) return success:


"""
"""
I change everything.
"""
