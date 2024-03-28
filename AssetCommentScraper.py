# Roblox Asset Comment Scraper -- created by Lanausse and DreamFreeze
# Version 2.1.6 03/27/2024 (MM/DD/YYYY) 23:28 EST

from fileinput import filename
import requests
import datetime
import argparse
import json
import time
import sys
import csv
import os

timeouttime = 30
separatortime = 2
servererrortime = 5

mid_comments = False

### ARGUMENTS ###
parser = argparse.ArgumentParser(description="A Roblox asset comment scraper", epilog="These are optional and are not required",formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-s", "--startingid", type=int, help="Asset ID from which to start scraping comments")
parser.add_argument("-l", "--list", type=str, help="Path to a text file that contains a list of Asset IDs")
args = parser.parse_args()


### CODE ###

## Functions

# This function fetches comments on a Roblox asset
#
# asset_id: The asset id of the asset
# comment_index: The comment index/page
# 
# Return: an array of comments
#
def get_comments(asset_id, comment_index = 0):
    status_code = 0
    comments = None

    while status_code != 200 and status_code != 400:
        response = requests.get(f'https://www.roblox.com/comments/get-json?assetId={asset_id}&startindex={comment_index}&thumbnailWidth=100&thumbnailHeight=100&thumbnailFormat=PNG')
        status_code = response.status_code
        if status_code == 200:
            comments = response.json()['Comments']
        elif status_code == 429:
            print(f'\tWe hit a rate limit! Waiting {timeouttime} seconds before retrying...')
            time.sleep(timeouttime)
        elif status_code == 500 or status_code == 503:
            print(f'\tA server error occurred! Waiting {servererrortime} seconds before retrying...')
            time.sleep(servererrortime)
        
        if status_code == 400:
            log_message(f'{asset_id} doesn\'t exist!')

    
    response.close()
    return comments

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

def scrape_comments(asset_id):
    print(asset_id)
    comment_index = 0
    comments = get_comments(asset_id, comment_index)

    #Create CSV
    if not (comments is None): # Initialise blank CSV, only if any comment section actually returns (this includes places at the moment, although their comment sections are always blank)
        comments_csv = open(f'RBX_ASSET_COMMENTS/{asset_id}.csv', 'w+', encoding='utf-8')
        comments_csv_writer = csv.writer(comments_csv)
        comments_csv_writer.writerow(['Comment ID', 'Post Date (GMT)',  'Author Username',  'Author ID',  'Comment',  'Is Comment Asset Owner?',  'Author Thumbnail URL', 'Is Author Verified?'])
        
        comments_csv.close()
        while len(comments) > 0:
            comments_csv = open(f'RBX_ASSET_COMMENTS/{asset_id}.csv', 'a+', encoding='utf-8')
            for comment in comments:
                print(f'\t({comment["PostedDate"]}) {comment["AuthorName"]}: {comment["Text"]}')
                #Write to CSV
                comments_csv_writer = csv.writer(comments_csv)
                comments_csv_writer.writerow([comment['Id'], comment['PostedDate'],  comment['AuthorName'],  comment['AuthorId'],  comment['Text'],  comment['ShowAuthorOwnsAsset'],  comment['AuthorThumbnail']['Url'], comment['HasVerifiedBadge']])
            comments_csv.close()
            time.sleep(separatortime)
            comment_index += 10
            comments = get_comments(asset_id, comment_index)

        log_message(f'Finished scraping {asset_id}')
        print("") # Spaces the scrape of each asset ID
    else:
        log_message(f'{asset_id} has no comments!')

## Main

# Earliest Existing Asset is 770
asset_id = 770
if args.startingid == None and args.list == None:
    asset_id = int(input("ID from which to start: "))
else:
    asset_id = args.startingid

#Create Folder
if not os.path.exists('RBX_ASSET_COMMENTS'):
    os.makedirs('RBX_ASSET_COMMENTS')


try:
    if args.list != None:
        if not os.path.exists(args.list):
            print(F'{args.list} is an invalid path!')
        else:
            asset_list = open(args.list, 'r+', encoding='utf-8').readlines()

            for id in asset_list:
                mid_comments = True
                scrape_comments(id.strip())
                mid_comments = False

                time.sleep(separatortime)

    else: #Default
        while True:
            mid_comments = True
            scrape_comments(asset_id)
            mid_comments = False

            asset_id += 1
            time.sleep(separatortime)
        
except KeyboardInterrupt as e:
    if mid_comments:
        log_message(f'Attempt to scrape asset {asset_id} was interrupted! (KeyInterrupt)', True)
    print(e, file=sys.stderr)
    print('Comment archival terminated by KeyboardInterrupt.')