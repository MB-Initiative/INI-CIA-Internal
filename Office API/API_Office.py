from Log import Log

import json
import requests
import os
import pandas as pd
from io import StringIO
from Date import DefaultDates
from datetime import datetime, timedelta
import base64
import numpy as np


class API(Log):
    
    url_redirect = 'https://login.microsoftonline.com/common/oauth2/nativeclient'
    url_start_oauth2 = 'https://login.microsoftonline.com/common/oauth2/v2.0/'
    url_start = 'https://graph.microsoft.com/v1.0/'
    
    def __init__(
        self, id_path, token_path, scopes = set(),
        log_file_name = None, log_append = True
    ):
        
        Log.__init__(self, log_file_name, log_append)
        
        f = open(id_path)
        self._id_data = json.load(f)
        f.close()
        
        self.logger.info('ID file found at ' + id_path)
        
        
        self._token_path = token_path
        
        if not os.path.exists(self._token_path):
            self.logger.info('No existing token, getting initial token')
            self.post_initial_token(scopes, self._token_path)
            
        else:
            f = open(self._token_path)
            self._token_data = json.load(f)
            f.close()
            
            exist_scopes = set(self._token_data['scope_list'])
            
            self.logger.info('Token found at ' + token_path)
            
            if not all([s in exist_scopes for s in scopes]):
                self.logger.info('New scopes, getting new initial token')
                scopes.union(exist_scopes) 
                self.post_initial_token(scopes, self._token_path)
 
    def post_initial_token(self, scopes, token_path = None):
        '''POST: get initial access token'''
        if not token_path:
            token_path = self._token_path
        
        if 'offline_access' not in scopes:
            scopes.update({'offline_access'})    
        
        url = self.url_start_oauth2 + 'authorize?client_id=%s&response_type=code&redirect_uri=%s&response_mode=query&scope=%s&state=12345'%(
            self._id_data['client_id'], 
            self.url_redirect,
            '%20'.join(scopes)
        )
        self.logger.info('Paste the url to browser, and login')
        self.logger.info(url)
        
        print(url)
        url_output = input('Paste the resulted url here: ')
        
        url_output_list = (url_output.split('?')[-1]).split('&')
        self._initial_token_data = {s.split('=')[0]: s.split('=')[1] for s in url_output_list}
        
        data = {
            'client_id': self._id_data['client_id'],
            'client_secret': self._id_data['client_secret'],
            'code': self._initial_token_data['code'],
            'scope': ' '.join(scopes),
            'redirect_uri': self.url_redirect,
            'grant_type': 'authorization_code',
        }
        
        response = requests.post(self.url_start_oauth2 + 'token', data=data)
        
        if response.status_code == 200:
            self._token_data = response.json()
            self._token_data['scope_list'] = list(scopes)
            
            f = open(token_path, 'w')
            json.dump(self._token_data, f)
            f.close()
            self.logger.info('New initial token saved at ' + token_path)
            
        else:
            self.logger.info('Failed to get initial token, status code %s'%(response.status_code))
            self.logger.info(response.json())
            
        return response
        
    def post_refresh_token(self, token_path = None):
        '''POST: refresh using refresh token saved in token_path'''
        if not token_path:
            token_path = self._token_path
            
        data = {
            'client_id': self._id_data['client_id'],
            'client_secret': self._id_data['client_secret'],
            'refresh_token': self._token_data['refresh_token'],
            'scope': self._token_data['scope'],
            'grant_type': 'refresh_token',
        }

        response = requests.post(self.url_start_oauth2 + 'token', data=data)
        
        if response.status_code == 200:
            self._token_data = {
                **response.json(), 
                **{'scope_list': self._token_data['scope_list']}
            }
            
            f = open(token_path, 'w')
            json.dump(self._token_data, f)
            f.close()
            self.logger.info('Refreshed token saved at ' + token_path)
            
        else:
            self.logger.info('Failed to refresh token, status code %s'%(response.status_code))
            self.logger.info(response.json())
        
        return response    
    
    def get_raw(self, url):
        '''run GET given a url (do not include url_start)'''
        response = requests.get(
            self.url_start+url, headers={'Authorization': 'Bearer ' + self._token_data['access_token']})
        
        if response.status_code == 401:
            self.logger.info('API fail: Token expired, refreshing')
            
            self.post_refresh_token()
            response = requests.get(
                self.url_start+url, headers={'Authorization': 'Bearer ' + self._token_data['access_token']})
        
        elif response.status_code == 200:
            self.logger.info('API succeed')
        else:
            self.logger.info('API fail: status code %s'%(response.status_code))
            self.logger.info(response.json())

        return response
    
    def get(self, url):
        '''return the result of GET in dictionary'''
        return self.get_raw(url).json()
    
    def post_raw(self, url, data = ''):
        '''run POST given a url (do not include url_start) data in dictionary'''
        response = requests.post(
            self.url_start+url, headers={
                'Authorization': 'Bearer ' + self._token_data['access_token'],
                'Content-type': 'application/json'
            }
            , data = data
        )
        
        if response.status_code == 401:
            self.logger.info('API fail: Token expired, refreshing')
            
            self.post_refresh_token()
            response = requests.post(
                self.url_start+url, headers={
                    'Authorization': 'Bearer ' + self._token_data['access_token'],
                'Content-type': 'application/json'
                }
                , data = data
            )
        
        elif response.status_code in [200,201,202]:
            self.logger.info('API succeed')
        else:
            self.logger.info('API fail: status code %d'%(response.status_code))
            
        return response
    
    def delete_raw(self, url, data = ''):
        '''run DELETE given a url (do not include url_start) data in dictionary'''
        response = requests.delete(
            self.url_start+url, headers={
                'Authorization': 'Bearer ' + self._token_data['access_token'],
                'Content-type': 'application/json'
            }
            , data = data
        )
        
        if response.status_code == 401:
            self.logger.info('API fail: Token expired, refreshing')
            
            self.post_refresh_token()
            response = requests.delete(
                self.url_start+url, headers={
                    'Authorization': 'Bearer ' + self._token_data['access_token'],
                'Content-type': 'application/json'
                }
                , data = data
            )
        
        elif response.status_code in [200,204]:
            self.logger.info('API succeed')
        else:
            self.logger.info('API fail: status code %d'%(response.status_code))
            
        return response
    
    def EditNestDict_step(self, Dict, prefix_list = []):
        '''given a dictionary with multiple nested dictionaries, return a flat disctionary. The new keys will be all the nested keys joined by _'''
        Dict_new = {}

        for k,v in Dict.items():

            if isinstance(v, dict):
                Dict_sub, prefix_list = self.EditNestDict_step(v, prefix_list+[str(k)])
                Dict_new = {**Dict_new , **Dict_sub}
                prefix_list = prefix_list[:-1]

            else:
                Dict_new['_'.join(prefix_list+[str(k)])] = str(v)

        return Dict_new, prefix_list  
    
    def EditNestDict(self, Dict):
        '''only take the dictionary output, prefix_list is not needed'''
        return self.EditNestDict_step(Dict, prefix_list = [])[0]
    
    def ToTable(
        self, rawres, nested = False,
        file_sep = '\t', return_str = False, keep_head = True):
        '''change teh raw output into a table (not used atm)'''
        cols = []
        res = ''
            
        for line in rawres:
            
            if nested:
                line,_ = self.EditNestDict(line)

            current_cols = list(line.keys())
            new_cols = [c for c in current_cols if c not in cols]
            
            if len(new_cols) > 0:
                
                empty_values = ['' for i in range(len(new_cols))]
                res.replace('\n', file_sep.join(empty_values) + '\n')
                cols += new_cols

            values = [line[c] if c in current_cols else '' for c in cols]
            res += file_sep.join([
                '"'+str(s)+'"' if (file_sep in str(s) or '\n' in str(s)) else str(s)
                for s in values]) + '\n'
        
        if keep_head:
            res = file_sep.join([
                '"'+str(s)+'"' if (file_sep in str(s) or '\n' in str(s)) else str(s)
                for s in cols]) + '\n' + res
            
        
        if return_str:    
            return res
        else:
            return pd.read_csv(StringIO(res), sep = file_sep, quotechar = '"')
        
    
class Mail(API):    
    
    def __init__(self, id_path, token_path):
        
        scopes = {
            'Mail.Read', 
            'Mail.Read.Shared', 
            'Mail.ReadBasic', 
            'Mail.ReadWrite', 
            'Mail.ReadWrite.Shared', 
            'Mail.Send', 
            'Mail.Send.Shared'}
        API.__init__(self, id_path, token_path, scopes)
        
    def get_mail_folders(self, user = 'me', mailFolder = None):
        '''run GET to get info of folder; if mailFolder = None get all folders of the user'''
        ## /me/mailFolders/{optional mailFolder}?includeHiddenFolders=true&top=100
        ## /users/{user}/mailFolders/{optiona lmailFolder}?includeHiddenFolders=true&top=100
        
        if user == 'me':
            url = user
        else:
            url = 'users/'+user   
        url += '/mailfolders'
        if mailFolder:
            url += '/'+mailFolder
        url += '?includeHiddenFolders=true&top=1000'
        
        return self.get(url)
    
    
    def get_children_folder(
        self, user = 'me', mailFolder = 'Inbox'):
        '''run GET to get all children folders'''
        ## /me/mailFolders/{mailFolder}/childFolders?includeHiddenFolders=true
        ## /users/{user}/...
        
        if user == 'me':
            url = user
        else:
            url = 'users/'+user   
        
        url += '/mailFolders/%s/childFolders?includeHiddenFolders=true'%(mailFolder)
        
        return self.get(url)
    
    def get_children_folder_all(
        self, user = 'me', mailFolder = 'Inbox'):
        '''run get_children_folder to get all layers of folders'''
        response = self.get_mail_folders(user, mailFolder)
            
        if mailFolder:
            folders_check = [response]
        else:
            folders_check = response['value'].copy() ## if mailFolder = None, will have a value list
        
        ## check if have children folder
    
        folders_collect = [r for r in folders_check if r['totalItemCount'] != 0] ## folders has emails
        
        while folders_check != []:
            folders_check_step = []
            
            for f in folders_check:
                
                response = self.get_children_folder(user, f['id'])['value']
                for r in response:
                   
                    if r['childFolderCount'] != 0:
                        folders_check_step += [r]
                    if r['totalItemCount'] != 0:
                        folders_collect += [r]
                        
            folders_check = folders_check_step.copy()

        return folders_collect
    
    def get_message_list(
        self, user = 'me', mailFolder = 'Inbox', 
        select = ['hasAttachments', 'receivedDateTime', 'sender', 'subject', 'body'],
        messageID = None,
        top = 100, skip = 0
    ):
        '''run GET to get a certain number of messages given user and mailFolder, use skip to keep checking more messages (e.g. top 200 skip 100 is 101 to 200)'''
# @odata.etag (default)
# id (default)
# createdDateTime
# lastModifiedDateTime
# changeKey
# categories
# receivedDateTime
# sentDateTime
# hasAttachments
# internetMessageId
# subject
# bodyPreview
# importance
# parentFolderId
# conversationId
# conversationIndex
# isDeliveryReceiptRequested
# isReadReceiptRequested
# isRead
# isDraft
# webLink
# inferenceClassification
# body
# sender
# from
# toRecipients
# ccRecipients
# bccRecipients
# replyTo
# flag
        ## me/mailFolders/{mailFolder}/messages/{optional messageID}?$top={x}&skip={x}&select={col,col,...}
        ## users/{user}/...
        
        if user == 'me':
            url = user
        else:
            url = 'users/'+user
            
        
        url += '''/mailFolders/%s/messages'''%(mailFolder)

        if messageID:
            url += '/%s'%(messageID)

        url += '''?$top=%d'''%(top)

        if skip:
            url += '&skip=%d'%(skip)

        if select != []:
            url += '&select=' + ','.join(select)

        self.logger.info('Get messages, Account: %s; Folder: %s; Message ID: %s; Top: %d; Skip top: %d'%(
                user, mailFolder, messageID, top, skip
            ))
        return self.get(url) 


    def filter_message_single(
        self, message_response_value,
        attachment = None, 
        sender_list = [], subject_list = [], body_list = [], 
        min_date = None, max_date = None, date_format = '%Y-%m-%d'
    ):
        '''filter the list from ['value'] of the dictionary output of get_message_list'''
        dates = []
        filtered = []
        
        if min_date:
            min_date = datetime.strptime(min_date, date_format)
        if max_date:
            max_date = datetime.strptime(max_date, date_format)
         
        message_response_flat = [self.EditNestDict(line) for line in message_response_value]
        
        for message in message_response_flat:
            keep = True
            
            if attachment:
                if (message['hasAttachments'] != str(attachment)):
                    keep = False
                
            for col, List in zip(
                ['sender_emailAddress_address', 'subject', 'body_content'], 
                [sender_list, subject_list, body_list]):

                if not all([k.lower() in message[col].lower() for k in List]):
                    keep = False

            receivedDateTime = datetime.strptime(message['receivedDateTime'], '%Y-%m-%dT%H:%M:%SZ')
            if min_date:
                if receivedDateTime < min_date:
                    keep = False
            if max_date:
                if receivedDateTime > max_date:
                    keep = False
                    
            if keep:
                dates.append(receivedDateTime)
                filtered.append(message)
            
        ## reverse order by date
        sort_index = np.argsort(np.array(dates))
        dates = [dates[sort_index[-i]] for i in range(1, len(sort_index)+1)]
        filtered = [filtered[sort_index[-i]] for i in range(1, len(sort_index)+1)]

        return filtered
    
    def get_message_filtered(
        self, user = 'me', mailFolder = 'Inbox', 
        select = ['hasAttachments', 'receivedDateTime', 'sender', 'subject', 'body'],
        step = 100, count = 1, 
        attachment = None, 
        sender_list = [], subject_list = [], body_list = [], 
        min_date = None, max_date = None, date_format = '%Y-%m-%d'
    ):
        '''run get_message_list and filter_message_single until finds the required number of messages'''
        
        self.logger.info('Account: %s; Folder: %s; Count: %s'%(user, mailFolder, count) )
        self.logger.info(
                'Has attachement: %s; Sender: %s; Subject keyword: %s; Body keyword: %s'%(
                    attachment, '|'.join(sender_list), '|'.join(subject_list), '|'.join(body_list)
                ))
        self.logger.info('Date range: %s to %s'%(min_date, max_date))
        
        
        folders = self.get_children_folder_all(user, mailFolder)
        if len(folders) > 1:
            self.logger.info('! Have children folders')
        
        check = True
        current_skip = 0
        current_count = count
        folders_id_finished = []
        response_final = []
        
        while check:
            
            self.logger.info('Searching top %d to %d'%(
                current_skip+1, current_skip+step
            ))
            
            response_value = []
            
            for f in folders:
                if f['id'] not in folders_id_finished:
                    self.logger.info('Search folder %s'%(f['displayName']))
                    response = self.get_message_list(
                        user = user, mailFolder = f['id'], 
                        select = select,
                        top = step, skip = current_skip
                    )
                    if not '@odata.nextLink' in response.keys():
                        folders_id_finished.append(f['id'])
                        self.logger.info('Reached the end of the folder %s'%(f['displayName']))
                    response_value += response['value']
 
            response_filtered = self.filter_message_single(
                response_value,
                attachment = attachment, 
                sender_list = sender_list, subject_list = subject_list, body_list = body_list, 
                min_date = min_date, max_date = max_date, date_format = date_format
            )
            
            current_skip += step
            
            if current_count: ## reverse ordered by date, take up to the required count
                response_final += response_filtered[:min(current_count, len(response_filtered))]
                current_count = count-len(response_final)
                self.logger.info('Found %d/%d'%(len(response_final), count))
                
                if current_count == 0:
                    check = False
                    self.logger.info('Reached target count')
            else: ## count = None, take all
                response_final += response_filtered
                self.logger.info('Found %d'%(len(response_final)))
                    
            if len(folders_id_finished) == len(folders):
                check = False
                self.logger.info('Reached the end of all the folders')

        self.logger.info('Search finished')
        
        if response_final != []:
            self.logger.info('Found:')
            for i in range(len(response_final)):
                self.logger.info(
                    '%d. %s; %s; %s'%(
                    i+1, response_final[i]['receivedDateTime'], response_final[i]['subject'], response_final[i]['sender_emailAddress_address']))
 
        return response_final
    
    def get_attachment_list(
        self, messageID, user = 'me'):
        '''run GET to get the attachment info of a message'''
        ## me/messages/{messageID}/attachments
        ## users/{user}/...
        
        if user == 'me':
            url = user
        else:
            url = 'users/'+user   
        url += '''/messages/%s/attachments'''%(messageID)
        
        self.logger.info('Get attachments, Account: %s; Message ID: %s'%(
                user, messageID
            ))
        
        return self.get(url)
    
    def save_attachment_single(
        self, attachment_response, attachment_keyword = [], save_path = ''):
        '''filter the result of get_attachment_list and save the file to the save_path'''
        ## by attachmentID & io
        # if user == 'me':
        #     url = user
        # else:
        #     url = 'users/'+user   
        # url += '''/messages/%s/attachments/%s/$value'''%(messageID, attachmentID)
        # raw = self.get_raw(url)
        # toread = io.BytesIO()
        # toread.write(raw.content)
        # toread.seek(0)
        # if file_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        #     df = pd.read_excel(toread)
        
        self.logger.info('---- Save attachments by keyword: %s ----'%(' | '.join(attachment_keyword)))      
        
        all_file_names = []
        
        for line in attachment_response['value']:
            file_name = line['name']
            self.logger.info('File: ' + file_name)
            
            if all([k in file_name for k in attachment_keyword]):
                file_content = line['contentBytes']
                
                final_file_name = save_path + file_name
                if final_file_name in all_file_names:
                    final_file_name = final_file_name.split('.')[0] + '_1' + final_file_name.split('.')[1]
                    
                f = open(final_file_name, 'w+b')
                f.write(base64.b64decode(file_content))
                f.close()
                all_file_names.append(final_file_name)
            
                self.logger.info('Saved: ' + final_file_name)
            else:
                self.logger.info('Not saved, keyword unmatch')
        
        return all_file_names
    
    def save_attachment_filtered(
        self, user = 'me', mailFolder = 'Inbox', 
        step = 100, count = 1, 
        sender_list = [], subject_list = [], body_list = [], 
        min_date = None, max_date = None, date_format = '%Y-%m-%d',
        attachment_keyword = [], save_path = ''
    ):
        '''run get_message_filtered, get_attachment_list, save_attachment_single to find and save attachments'''
        self.logger.info('---- Save attachments from filtered messages ----')
        
        select = ['hasAttachments', 'receivedDateTime', 'sender', 'subject']
        if body_list != []:
            select.append('body')

        messages_filtered = self.get_message_filtered(
            user = user, mailFolder = mailFolder, 
            select = select,
            step = step, count = count, 
            attachment = True, 
            sender_list = sender_list, subject_list = subject_list, body_list = body_list, 
            min_date = min_date, max_date = max_date, date_format = date_format
        )
        all_file_names = []
        for message in messages_filtered:
            attachment_response = self.get_attachment_list(message['id'], user = user)
            file_names = self.save_attachment_single(
                attachment_response, attachment_keyword = attachment_keyword, save_path = save_path)
            all_file_names += file_names
        return all_file_names
    
    def post_send_message(self, to, subject, content = '', cc = [], user = 'me'):
        '''run POST to send out an email'''
        ## me/sendMail
        ## users/{user}/...
        
#         {
#           "message": {
#             "subject": "Meet for lunch?",
#             "body": {
#               "contentType": "Text",
#               "content": "The new cafeteria is open."
#             },
#             "toRecipients": [
#               {
#                 "emailAddress": {
#                   "address": "meganb@contoso.onmicrosoft.com"
#                 }
#               }
#             ]
#             ,"ccRecipients": [
#               {
#                 "emailAddress": {
#                   "address": "danas@contoso.onmicrosoft.com"
#                 }
#               }
#             ]

#             ,"attachments": [
#               {
#                 "@odata.type": "#microsoft.graph.fileAttachment",
#                 "name": "attachment.txt",
#                 "contentType": "text/plain",
#                 "contentBytes": "SGVsbG8gV29ybGQh"
#               }
#             ]
#           }
#         }

        if user == 'me':
            url = user
        else:
            url = 'users/'+user
        
        url += '/sendMail'
        
        if cc != []:
            data_cc = ''',"ccRecipients": [%s]'''%(
                ','.join(['''{"emailAddress": {"address": "%s"}}'''%(c) for c in cc])
            )
        else:
            data_cc = ''
        
        data = '''{
            "message": {
                "subject": "%s",
                "body": {
                    "contentType": "Text",
                    "content": "%s"
                },
                "toRecipients": [%s]
                %s
          }
        }'''%(
            subject, 
            content,
            ','.join(['''{"emailAddress": {"address": "%s"}}'''%(t) for t in to]),
            data_cc
        )
        
        self.logger.info('Send message to: %s, cc: %s'%(','.join(to), ','.join(cc)))
        print(url, data)
        return self.post_raw(url, data)
        
    def post_move_message(self, messageID, folderID, user = 'me'):
        '''run POST to move a message to a folder'''
        if user == 'me':
            url = user
        else:
            url = 'users/'+user
            
        url += '/messages/%s/move/'%(messageID)
        data = '{ "destinationId": "%s" }'%(folderID)
        
        self.logger.info('Move message %s to folder %s'%(messageID, folderID))
        
        return self.post_raw(url, data)
    
    def post_move_message_filtered(
        self, mailFolder_to, user = 'me', mailFolder = 'Inbox', 
        step = 100, count = None, 
        attachment = None,
        sender_list = [], subject_list = [], body_list = [], 
        min_date = None, max_date = None, date_format = '%Y-%m-%d'
    ):
        '''run get_message_filtered and then post_move_message'''
        self.logger.info('---- Filter and move messages ----')
        
        select = ['hasAttachments', 'receivedDateTime', 'sender', 'subject']
        if body_list != []:
            select.append('body')
            
        messages_filtered = self.get_message_filtered(
            user = user, mailFolder = mailFolder, 
            select = select,
            step = step, count = count, 
            attachment = attachment, 
            sender_list = sender_list, subject_list = subject_list, body_list = body_list, 
            min_date = min_date, max_date = max_date, date_format = date_format
        )
        
        for m in messages_filtered:
            self.post_move_message(m['id'], mailFolder_to, user = user)
            
        return messages_filtered
    
    
    def delete_message(self, messageID, user = 'me'):
        '''run DELETE to delete a message'''
        if user == 'me':
            url = user
        else:
            url = 'users/'+user
            
        url += '/messages/%s'%(messageID)
        
        self.logger.info('Delete message %s'%(messageID))
        
        return self.delete_raw(url)
    
    def delete_message_filtered(
        self, user = 'me', mailFolder = 'Inbox', 
        step = 100, count = None, 
        attachment = None,
        sender_list = [], subject_list = [], body_list = [], 
        min_date = None, max_date = None, date_format = '%Y-%m-%d'
    ):
        '''run get_message_filtered and then delete_message'''
        self.logger.info('---- Filter and delete messages ----')
        
        select = ['hasAttachments', 'receivedDateTime', 'sender', 'subject']
        if body_list != []:
            select.append('body')
            
        messages_filtered = self.get_message_filtered(
            user = user, mailFolder = mailFolder, 
            select = select,
            step = step, count = count, 
            attachment = attachment, 
            sender_list = sender_list, subject_list = subject_list, body_list = body_list, 
            min_date = min_date, max_date = max_date, date_format = date_format
        )
        
        for m in messages_filtered:
            self.delete_message(m['id'], user = user)
            
        return messages_filtered
        
class File(API):
            
    def __init__(self, id_path, token_path):
        
        scopes = {
            'Files.Read', 
            'Files.ReadWrite', 
            'Files.Read.All', 
            'Files.ReadWrite.All', 
            'Sites.Read.All', 
            'Sites.ReadWrite.All'}
        
        API.__init__(self, id_path, token_path, scopes)
     
    def url_encode(self, url):
        '''required to process shared onedrive links'''
        message_bytes = url.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode('ascii')

        base64_message_edit = "u!" + base64_message.split('=')[0].replace('/','_').replace('+','-')

        return base64_message_edit
    
    def get_shared_bylink(self, url):
        '''run GET to get info of a file from onedrive shared link'''
        url_encode = self.url_encode(url)
        url_api = '/shares/%s/driveItem'%(url_encode)
        
        self.logger.info('Get file from shared link: %s'%(url))
        return self.get(url_api)

    
    def save_shared_bylink(
        self, url, save = True, file_path = '', file_name_custom = None, file_name_timestamp = True,
        save_cols = ['@microsoft.graph.downloadUrl', 'name', 'lastModifiedDateTime', 'lastModifiedBy_user_email']):
        '''run get_shared_bylink, return selected info and save the file if file_path is not empty'''
    # '@odata.context', 
    # '@microsoft.graph.downloadUrl', 
    # 'createdDateTime',
    # 'eTag', 
    # 'id', 
    # 'lastModifiedDateTime', 
    # 'name', 
    # 'webUrl', 
    # 'cTag', 
    # 'size',
    # 'createdBy_user_email', 
    # 'createdBy_user_displayName',
    # 'lastModifiedBy_user_email', 
    # 'lastModifiedBy_user_displayName',
    # 'parentReference_driveType', 
    # 'parentReference_driveId',
    # 'parentReference_id', 
    # 'parentReference_path', 
    # 'file_mimeType',
    # 'file_hashes_quickXorHash', 
    # 'fileSystemInfo_createdDateTime',
    # 'fileSystemInfo_lastModifiedDateTime', 
    # 'shared_scope'        
            
        response = self.get_shared_bylink(url)
        response_flat = self.EditNestDict(response)
        url_download = response_flat['@microsoft.graph.downloadUrl']
        if save_cols != []:
            save_info = {k:response_flat[k] for k in save_cols if k in response_flat.keys()}
        else:
            save_info = response_flat
        if save:
            if not file_name_custom:
                file_name = file_path + response_flat['name']
            else:
                file_name = file_path + file_name_custom
            
            if file_name_timestamp:
                file_name = file_name.split('.')[0] + '_' + response_flat['lastModifiedDateTime'].replace(':', '') + '.' + file_name.split('.')[1]
            
            r = requests.get(url_download, allow_redirects=True)
            open(file_name, 'wb').write(r.content)
            
            self.logger.info('Saved to ' + file_name)
            self.logger.info(save_info)
                                
            return file_name, save_info
        
        else:
            self.logger.info('Download link ' + url_download)
            self.logger.info(save_info)
            print(url_download)
            return url_download, save_info
    
    def get_drives(self, user = 'me', id = None):
        '''run GET to get onedrive info given a user or a drive id'''
        ## /me/drives
        ## /users/{id}/drives
        ## /groups/{groupId}/drives
        ## /sites/{siteId}/drives
        ## /drives/{driveId}
        
        if id:
            url = 'drives/'+id 
        elif user == 'me':
            url = user+'/drives'
        else:
            url = 'users/'+user+'/drives' 
        
        return self.get(url)
    
    def show_get_drives(
            self, user = 'me', id = None,
            select = ['driveType', 'id', 'owner_user_displayName', 'owner_user_id']    
        ):
        '''process output of get_drives'''
        # 'driveType'
        # 'id'
        # 'owner_user_displayName'
        # 'owner_user_id'
        # 'quota_deleted'
        # 'quota_remaining'
        # 'quota_state'
        # 'quota_total'
        # 'quota_used'
        # 'quota_storagePlanInformation_upgradeAvailable'

        raw = self.get_drives(user = 'me', id = None)
        edit = []
        if 'value' in raw.keys():
            edit = [self.EditNestDict(v) for v in raw['value']]
        else:
            edit = [self.EditNestDict(raw)]
        
        if select != []:
            edit = [{k:v for k,v in i.items() if k in select} for i in edit]
        return edit

    def get_drive_children(
        self, link = None, user = 'me', id_drive = None, id_item = None
    ):
        '''run GET to get children folders of a folder'''
        ## me/drive
        ## drives/{id_drive}
        ## shares/{url encoded}
        ## + /root/children
        ## + /items/id_item

        ## https://onedrive.live.com/?id=D898DCBA467A2F70%212796&cid=D898DCBA467A2F70&...

        if link:
            if 'onedrive.live.com' in link:
                id_drive = link.split('&')[1].split('=')[-1]
                id_item = link.split('&')[0].split('=')[-1]
                url = 'drives/'+ id_drive + '/items/' + id_item + '/children'
        
            else:
                url = '/shares/' + self.url_encode(link) + '/root/children'
        
        else:
            if id_drive:
                url = 'drives/'+ id_drive
            elif user == 'me':
                url = user +'/drive'
            else:
                url = 'users/' + user + '/drives' 
            
            if id_item:
                url += '/items/' + id_item + '/children'
            else:
                url += '/root/children'
        return self.get(url)

    def show_get_drive_children(
            self, link = None, user = 'me', id_drive = None, id_item = None,
            split_folder = True,
            select = [
                '@microsoft.graph.downloadUrl', 'name', 'lastModifiedDateTime', 'lastModifiedBy_user_displayName', 'createdBy_user_displayName',
                'parentReference_driveId', 
                'id', 
                'webUrl', 
                'size', 
                'folder_childCount'
                ],
            select_combine_remote = [
                'remoteItem_parentReference_driveId', 
                'remoteItem_id', 
                'remoteItem_webUrl', 
                'remoteItem_size', 
                'remoteItem_folder_childCount'
            ]
        ):
        '''process output of get_drive_children'''
    # '@microsoft.graph.downloadUrl' #### only files ####
    # 'createdDateTime'
    # 'cTag'
    # 'eTag'
    # 'id'
    # 'lastModifiedDateTime'
    # 'name'
    # 'size'
    # 'webUrl'
    # 'reactions_commentCount'
    # 'createdBy_application_displayName'
    # 'createdBy_application_id'
    # 'createdBy_user_displayName'
    # 'createdBy_user_id'
    # 'lastModifiedBy_application_displayName'
    # 'lastModifiedBy_application_id'
    # 'lastModifiedBy_user_displayName'
    # 'lastModifiedBy_user_email' ## not always have
    # 'lastModifiedBy_user_id'
    # 'parentReference_driveId'
    # 'parentReference_driveType'
    # 'parentReference_id'
    # 'parentReference_path'
    # 'file_mimeType' ## not always have
    # 'file_hashes_quickXorHash' ## not always have
    # 'fileSystemInfo_createdDateTime'
    # 'fileSystemInfo_lastModifiedDateTime'
    # 'folder_childCount' #### only folders ####
    # 'folder_view_viewType'
    # 'folder_view_sortBy'
    # 'folder_view_sortOrder'
        

    ## shared
    # 'createdDateTime'
    # 'cTag'
    # 'eTag'
    # 'id'
    # 'lastModifiedDateTime'
    # 'name'
    # 'webUrl'
    # 'createdBy_application_displayName'
    # 'createdBy_application_id'
    # 'createdBy_user_displayName'
    # 'createdBy_user_id'
    # 'lastModifiedBy_user_displayName'
    # 'lastModifiedBy_user_id'
    # 'parentReference_driveId'
    # 'parentReference_driveType'
    # 'parentReference_id'
    # 'parentReference_path'
    # 'remoteItem_id'
    # 'remoteItem_size'
    # 'remoteItem_webUrl'
    # 'remoteItem_fileSystemInfo_createdDateTime'
    # 'remoteItem_fileSystemInfo_lastModifiedDateTime'
    # 'remoteItem_folder_childCount'
    # 'remoteItem_folder_view_viewType'
    # 'remoteItem_folder_view_sortBy'
    # 'remoteItem_folder_view_sortOrder'
    # 'remoteItem_parentReference_driveId'
    # 'remoteItem_parentReference_driveType'
    # 'remoteItem_shared_sharedDateTime'

        raw = self.get_drive_children(link, user, id_drive, id_item)
        edit = []
        if 'value' in raw.keys():
            edit = [self.EditNestDict(v) for v in raw['value']]
        else:
            edit = [self.EditNestDict(raw)]
        
        if select != []:
            if select_combine_remote != []:
                select_combine_remote = [
                    'remoteItem_' + i if 'remoteItem_' + i in select_combine_remote
                    else i
                    for i in select
                ]

            for i in range(len(edit)):
                if 'remoteItem_id'in edit[i].keys():
                    edit[i] = {k:v for k,v in edit[i].items() if k in select_combine_remote}
                else:
                    edit[i] = {k:v for k,v in edit[i].items() if k in select}

        if ('@microsoft.graph.downloadUrl' in select or select == []) and split_folder:
            return {'file': [i for i in edit if '@microsoft.graph.downloadUrl' in i.keys()],
            'folder': [i for i in edit if '@microsoft.graph.downloadUrl' not in i.keys()]}

        else:
            return edit

    def show_drive_children_files(
            self, link = None, user = 'me', id_drive = None, id_item = None,
            select = [
                '@microsoft.graph.downloadUrl', 'name', 'lastModifiedDateTime', 'lastModifiedBy_user_displayName', 'createdDateTime', 'createdBy_user_displayName',
                'parentReference_driveId', 
                'id', 
                'webUrl', 
                'size', 
                'folder_childCount'
                ],
            select_combine_remote = [
                'remoteItem_parentReference_driveId', 
                'remoteItem_id', 
                'remoteItem_webUrl', 
                'remoteItem_size', 
                'remoteItem_folder_childCount'
            ]
        ):
            '''repeats show_get_drive_children until all folders are checked, return the files with their folder paths'''
            res = self.show_get_drive_children(link, user, id_drive, id_item, True, select, select_combine_remote)
            for k in res.keys():
                for i in range(len(res[k])):
                    res[k][i]['path'] = ''
            folder_list = res['folder'].copy()
            file_list = res['file'].copy()
            
            while folder_list != []:
                folder_list_temp = []
                for f in folder_list:
                    res = self.show_get_drive_children(
                        id_drive = f['parentReference_driveId'], id_item = f['id'], split_folder = True, 
                        select = select, select_combine_remote = select_combine_remote
                        )
                    for k in res.keys():
                        for i in range(len(res[k])):
                            res[k][i]['path'] = '/'.join([f['path'], f['name']]).strip('/')
                            
                    folder_list_temp += res['folder'].copy()
                    file_list += res['file'].copy()

                folder_list = folder_list_temp.copy()

            return file_list
    
    def get_files(
            self, link = None, user = 'me', id_drive = None, id_item = None
        ):
        ## me/drive/items/{item-id}
        ## drives/{id_drive}/items/{item-id}
        ## shares/{url encoded}

        ## https://onedrive.live.com/?id=D898DCBA467A2F70%212796&cid=D898DCBA467A2F70&...
        '''run GET to get info of a file (download link will expire, if so rerun the function using the item id and drive id)'''
        if link:
            if 'onedrive.live.com' in link:
                id_drive = link.split('&')[1].split('=')[-1]
                id_item = link.split('&')[0].split('=')[-1]
                url = 'drives/'+ id_drive + '/items/' + id_item
        
            else:
                url = '/shares/' + self.url_encode(link) + '/driveItem'

        elif id_item:
            if id_drive:
                url = 'drives/'+ id_drive + '/items/' + id_item
            elif user == 'me':
                url = user +'/drive' + '/items/' + id_item
            else:
                url = 'users/' + user + '/drives' + '/items/' + id_item

        return self.get(url)
    
    def show_get_files(
            self, link = None, user = 'me', id_drive = None, id_item = None,
            select = [
                '@microsoft.graph.downloadUrl', 'name', 'lastModifiedDateTime', 'lastModifiedBy_user_displayName', 'createdDateTime', 'createdBy_user_displayName',
                'parentReference_driveId', 
                'id', 
                'webUrl', 
                'size', 
                ],
            select_combine_remote = [
                'remoteItem_parentReference_driveId', 
                'remoteItem_id', 
                'remoteItem_webUrl', 
                'remoteItem_size', 
            ]
        ):
            '''process output of get_files'''
            raw = self.get_files(link, user, id_drive, id_item)
            edit = [self.EditNestDict(raw)]
            
            if select != []:
                if select_combine_remote != []:
                    select_combine_remote = [
                        'remoteItem_' + i if 'remoteItem_' + i in select_combine_remote
                        else i
                        for i in select
                    ]

                for i in range(len(edit)):
                    if 'remoteItem_id'in edit[i].keys():
                        edit[i] = {k:v for k,v in edit[i].items() if k in select_combine_remote}
                    else:
                        edit[i] = {k:v for k,v in edit[i].items() if k in select}

            return edit