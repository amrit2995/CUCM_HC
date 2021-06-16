################ Modules ##########################
from tkinter import *
from tkinter import messagebox

import paramiko
import json
from _datetime import datetime as dt
from paramiko import SSHException
###################### UI CLASS ##############################################

class Ui:
    region_options = ["None", "APAC", "EMEA", "NALA"]
    type_options = ["Basic", "Custom"]
    modes_options = ["All", "Selected Only"]

    def __init__(self):
        self.window = Tk()
        self.var = IntVar()
        self.window.minsize(width=200, height=100)
        self.window.title('Test')

        # datatype of menu text
        self.selected_region = StringVar()
        self.selected_type = StringVar()
        self.device_mode = StringVar()
        self.devices = StringVar()

        # initial menu text
        self.selected_region.set("None")
        self.selected_type.set("Basic")
        self.device_mode.set("All")
        self.devices.set("")
        # Create Dropdown menu
        self.label_region = Label(text='Region:')
        self.label_region.grid(row=0, column=0, padx=20, pady=5)

        #Region Bropbox
        self.drop_region = OptionMenu(self.window, self.selected_region, *self.region_options, command=self.disable)
        self.drop_region.grid(row=1, column=0, padx=20, pady=5)

        #Type Label
        self.label_type = Label(text='Type of commands:')
        self.label_type.grid(row=2, column=0, padx=20, pady=5)


        #Type of Commands
        self.drop_type = OptionMenu(self.window, self.selected_type, *self.type_options)
        self.drop_type.grid(row=3, column=0, padx=20, pady=5)

        #mode all or selected
        self.label_mode = Label(text='Mode:')
        self.label_mode.grid(row=4, column=0, padx=20, pady=5)

        #mode devices
        self.devices_mode = OptionMenu(self.window, self.device_mode, *self.modes_options, command=self.disable)
        self.devices_mode.grid(row=5, column=0, padx=20, pady=5)

        #Device input Label
        self.label_type = Label(text='Input the FQDN or the IP:')
        self.label_type.grid(row=6, column=0, padx=20, pady=5, columnspan=2)

        #Input Device names
        self.devices_list = Entry(self.window,textvariable=self.devices)
        self.devices_list.grid(row=7, column=0, padx=20, pady=5, columnspan=2)

        #start the HC
        self.start_button = Button(text='Start', command=self.send_on_click)
        self.start_button.grid(row=8, column=0, padx=20, pady=5, columnspan=2)
        self.window.after(1000, func=self.hp)

        self.disable(0)
        self.window.mainloop()

    def hp(self):
        print('hello')

    def disable(self, option):
        region = self.selected_region.get()
        mode = self.device_mode.get()
        self.devices_list.config(state=DISABLED if (region == 'None' or mode == 'All') else NORMAL)
        self.start_button.config(state=DISABLED if region == 'None' else NORMAL)


    def send_on_click(self):
        if self.confirmation() == 'yes':
            region = self.selected_region.get()
            devices = self.devices.get()
            type = self.selected_type.get()
            mode = self.device_mode.get()
            try:
                self.window.destroy()
            except:
                pass
            return [region, type, mode, devices]

    def confirmation(self):
        return messagebox.askquestion(title='Confirmation ', message='Are you sure you want to continue ? ')

################SSH Class ##########################


class ssh:
    shell = None
    client = None
    log = ''
    output = ''

    def __init__(self,hostname, address, username, password, cshift):
        print("Connecting to server on ip", str(address) + ".")
        self.hostname = hostname
        self.address = address
        self.username = username
        self.password = password
        self.shift = cshift
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
        self.client.connect(address, username=username, password=password, look_for_keys=False)
        self.date = dt.now().strftime('%Y%m%d_%H%M%S')
        self.filename = f'data/output/{self.date}_{cshift}_output.txt'
        self.out_file = open(self.filename, 'a+')
        self.log_file = open(f'data/output/log_file.txt', 'a+')

    def new_server_print(self):
        string = dt.now().strftime('%Y-%m-%d %H:%M:%S')
        server_message = '#'*10 + '\n' + self.hostname + '\n' + '#'*10
        log = f"{string} : Connection successful to the server : {self.address}"
        self.out_file.write(server_message)
        self.log_file.write(log+'\n')

    def close_files(self):
        self.out_file.close()
        self.log_file.close()

    def close_connection(self):
        if(self.client != None):
            self.client.close()

    def open_shell(self):
        self.shell = self.client.invoke_shell()
        print('open_shell')

    def send_shell(self, command):
        string = dt.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log += f"{string} : '{command}' executed successfully"
        self.shell.send(command)

    def process(self):
        output = ''
        while True:
            if self.shell.recv_ready() == True :
                string = self.shell.recv(9999).decode('UTF-8')
                if string == 'admin:':
                    break
                output = output + string
        self.output += output

    def print_lines(self, server,command):
        string = dt.now().strftime('%Y-%m-%d %H:%M:%S')
        log = f"{string} :{server} :'{command.strip()}' executed successfully"
        print(log)
        self.log_file.write(log+'\n')
        self.out_file.write(self.output)

shift = ['APAC','EMEA','NALA']

############################## Main ################################

cshift, commands_type, mode, devices = Ui().send_on_click()
with open('data/input/servers_file.json') as servers_file:
    data = json.load(servers_file)
# getting all the devices into a list
devices = devices.strip().split(',')
if cshift == 'None':
    exit()
servers_list = data[cshift]
if mode == "Selected Only" and len(devices) > 0:
    for device in devices:
        for server in servers_list:
            print(device,server["hostname"],server["ip"])
            if device == server["hostname"] or device == server['ip']:
                if server not in servers_list:
                    servers_list.append(server)

with open(f'data/input/{commands_type}_commands.txt') as commands_file:
    commands = commands_file.readlines()

for server in servers_list:
    ssh_client = ssh(server['hostname'], server['ip'],server['username'],server['password'],cshift)
    ssh_client.new_server_print()
    try:
        ssh_client.open_shell()
    except 	SSHException:
        print("Connection rejected")
    ssh_client.process()
    for command in commands:
        ssh_client.output = ''
        ssh_client.send_shell(command)
        ssh_client.process()
        ssh_client.print_lines(server['hostname'], command)
    ssh_client.close_files()
    ssh_client.close_connection()