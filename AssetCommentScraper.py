# Roblox Asset Comment Scraper -- created by Lanausse and DreamFreeze
# Version 3.1.1 03/29/2024 (MM/DD/YYYY) 06:07 AEST

### IMPORTS ###

import requests # HTTP(S) requests
import datetime # Date-time stamp; used in logs
import argparse # Args
import json # JSON processing; used to process comments API response, which is in JSON
import time # Time-related thingies; used for getting the program to wait for a set number of seconds
import sys # System-related thingies; used for outputting errors
import csv # CSV processing; used for saving comment files
import os # OS-related thingies; used for checking if files and folders exist

### VARIABLES ###

# Wait time variables (in seconds); can change at user's discretion
separatortime = 2
servererrortime = 5

# Pre-set values for utility functions - not for user's modification
mid_comments = False
waiting = False

### ARGUMENTS ###

parser = argparse.ArgumentParser(description="A Roblox asset comment scraper", epilog="These are optional and are not required",formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-s", "--startingid", type=int, help="Asset ID from which to start scraping comments")
parser.add_argument("-l", "--list", type=str, help="Path to a text file that contains a list of Asset IDs")
args = parser.parse_args()


### FUNCTIONS ###

# <Puropse>: fetches a single comment page for a particular ROBLOX asset
#
# <Parameters>
# asset_id: The asset id of the asset
# comment_index: The comment index/page
# 
# <Returns>: an array of comments
#
def get_comments(asset_id, comment_index = 0):
    global waiting
    
    status_code = 0
    comments = None
    waiting = False

    while status_code != 200 and status_code != 400:
        response = requests.get(f'https://www.roblox.com/comments/get-json?assetId={asset_id}&startindex={comment_index}&thumbnailWidth=100&thumbnailHeight=100&thumbnailFormat=PNG')
        status_code = response.status_code
        if waiting and status_code != 429:
            waiting = False
            print('')
        if status_code == 200:
            comments = response.json()['Comments']
            
        elif status_code == 429:
            if waiting:
                print('.', end='')
            else:
                print(f'\tWe hit a rate limit! Waiting for return of access.')
                waiting = True
            time.sleep(separatortime)
            
        elif status_code == 500 or status_code == 503:
            print(f'\tA server error occurred! Waiting {servererrortime} seconds before retrying...')
            time.sleep(servererrortime)
            
        if status_code == 400:
            log_message(f'{asset_id} doesn\'t exist!')

    
    response.close()
    return comments

# <Puropse>: logs a message
#
# <Parameters>
# msg: The message to log
# silent: Determines whether to output the same message in the console log as well (True = no)
# 
# <Returns>: nothing
#
def log_message(msg, silent = False):
    #Create Log
    if not os.path.exists(f'RBX_ASSET_COMMENTS/logs.txt'):
        log = open(f'RBX_ASSET_COMMENTS/logs.txt', 'w+', encoding='utf-8')
        log.write(f'Log created at {datetime.datetime.now()}\n')
        log.close()

    log = open(f'RBX_ASSET_COMMENTS/logs.txt', 'a', encoding='utf-8')
    log.write(f'[{datetime.datetime.now()}] {msg}\n')
    log.close()
    if not silent:
        print(msg)

# <Puropse>: fetches all comments on a particular ROBLOX asset and saves them to a CSV file
#
# <Parameters>
# asset_id: The asset id of the asset
# 
# <Returns>: nothing
#
def scrape_comments(asset_id):
    print(asset_id)
    comment_index = 0
    comments = get_comments(asset_id, comment_index)

    #Create CSV
    if comments is not None: # Initialise blank CSV, only if any comment section actually returns (this includes places at the moment, although their comment sections are always blank)
        comments_csv = open(f'RBX_ASSET_COMMENTS/{asset_id}.csv', 'w+', encoding='utf-8')
        comments_csv_writer = csv.writer(comments_csv)
        comments_csv_writer.writerow(['Comment ID', 'Post Date (GMT)',  'Author Username',  'Author ID',  'Comment',  'Is Comment Asset Owner?',  'Author Thumbnail URL', 'Is Author Verified?'])
        
        comments_csv.close()

        reading_comments = True
        while reading_comments:
            reading_comments = (len(comments) >= 10)
            
            comments_csv = open(f'RBX_ASSET_COMMENTS/{asset_id}.csv', 'a+', encoding='utf-8')
            for comment in comments:
                print(f'\t({comment["PostedDate"]}) {comment["AuthorName"]}: {comment["Text"]}')
                
                #Write to CSV
                comments_csv_writer = csv.writer(comments_csv)
                comments_csv_writer.writerow([comment['Id'], comment['PostedDate'],  comment['AuthorName'],  comment['AuthorId'],  comment['Text'],  comment['ShowAuthorOwnsAsset'],  comment['AuthorThumbnail']['Url'], comment['HasVerifiedBadge']])
            comments_csv.close()
            
            if reading_comments:
                time.sleep(separatortime)
                comment_index += 10
                comments = get_comments(asset_id, comment_index)

        log_message(f'Finished scraping {asset_id}')
        print("") # Spaces the scrape of each asset ID
    else:
        log_message(f'{asset_id} has no comments!')

# <Puropse>: prompts user for starting asset ID until the user inputs either a pure number or nothing
#
# <Parameters>: nothing
# 
# <Returns>: the final input value
#
def getassettidfrominput():
    numbers = ["0",  "1",  "2",  "3",  "4",  "5",  "6",  "7",  "8",  "9"]
    temp_asset_input = input("ID from which to start (or nothing to input asset list): ")
    isnumber = all([char in numbers for char in temp_asset_input])
    while temp_asset_input is not None and temp_asset_input != "" and not isnumber:
        temp_asset_input = input("ID from which to start (or nothing to input asset list) [Input must be number or empty]: ")
        isnumber = all([char in numbers for char in temp_asset_input])
    if isnumber:
        temp_asset_input = int(temp_asset_input)
    return temp_asset_input

### MAIN CODE ###

# Receive parameters
asset_id = 770 # Earliest Existing Asset is 770
if args.startingid is None and args.list is None:
    asset_id = getassettidfrominput()
    if asset_id is None or asset_id == "":
        asset_list_path = input("Path of asset list file: ")
    else:
        asset_list_path = input("Path of file with list of assets to exclude (or nothing if you don't want to exclude assets): ")
else:
    asset_id = args.startingid
    asset_list_path = args.list

# Create Folder
if not os.path.exists('RBX_ASSET_COMMENTS'):
    os.makedirs('RBX_ASSET_COMMENTS')

# Process asset comments
try:
    if (asset_list_path is not None) and (asset_list_path != ""): # There is an asset list to process
        if not os.path.exists(asset_list_path):
            print(F'{asset_list} is an invalid path!')
        else:
            asset_list = [int(item.strip()) for item in open(asset_list_path, 'r+', encoding='utf-8').readlines()]
        
        if (asset_id is None) and (asset_id == ""):
            for asset_id in asset_list:
                mid_comments = True
                scrape_comments(asset_id)
                mid_comments = False

                time.sleep(separatortime)
        else:
            while True:
                mid_comments = True
                if asset_id not in asset_list:
                    scrape_comments(asset_id)
                else:
                    log_message(f"{asset_id} skipped - it's in the exclusion list.")
                    print('')
                mid_comments = False

                asset_id += 1
                time.sleep(separatortime)

    else: # There is no asset list to process
        while True:
            mid_comments = True
            scrape_comments(asset_id)
            mid_comments = False

            asset_id += 1
            time.sleep(separatortime)
            
except KeyboardInterrupt as e: # Manages exiting the program
    if waiting:
        print('')
    if mid_comments:
        log_message(f'Attempt to scrape asset {asset_id} was interrupted! (KeyInterrupt)', True)
    print(e, file=sys.stderr)
    print('Comment archival terminated by KeyboardInterrupt.')