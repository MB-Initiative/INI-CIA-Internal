import API_Office

id_path = 'API_Office_id.json'
token_path = 'API_Office_token.json'

scopes = [
    'offline_access',
    'Mail.Read', 
    'Mail.Read.Shared', 
    'Mail.ReadBasic', 
    'Mail.ReadWrite', 
    'Mail.ReadWrite.Shared', 
    'Mail.Send', 
    'Mail.Send.Shared',
    'Files.Read', 
    'Files.ReadWrite', 
    'Files.Read.All', 
    'Files.ReadWrite.All', 
    'Sites.Read.All', 
    'Sites.ReadWrite.All'
]

API_Office.API(id_path, token_path, scopes)