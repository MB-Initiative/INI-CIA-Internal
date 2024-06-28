client_list = [
    'RMI', 'WFS'
]

menu = 'Select client:\n\n' + '\n'.join(
    '{index}.\t{client}'.format(index = i+1, client = client_list[i])
    for i in range(len(client_list))
) + '\nEnter:'

run_menu = True
while run_menu:
    client_index = input(menu)
    if client_index in [str(i+1) for i in range(len(client_list))]:
        client_index = int(client_index)
        run_menu = False


client = client_list[client_index-1]
print('Chosen ' + client)

if client == 'RMI':
    from mappings_RMI import *

elif client == 'WFS':
    from mappings_WFS import *
