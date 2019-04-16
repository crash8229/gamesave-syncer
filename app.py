import paramiko
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from functools import partial
from threading import Thread
from time import time
import json
import lzma
from socket import error as socketError


# TODO: use timestamp to determine if to upload
class StatusBar(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.label = tk.Label(self, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.label.pack(fill=tk.X)

    def set(self, text):
        self.label.config(text=text)
        self.label.update_idletasks()

    def clear(self):
        self.label.config(text="")
        self.label.update_idletasks()


class SSHWindow(tk.Toplevel):
    def __init__(self, info):
        tk.Toplevel.__init__(self)
        self.resizable(0, 0)
        self.title("SSH Login")
        self.grab_set()

        # Creating the fields for entering SSH information needed
        tk.Label(self, text="Address: ").grid(row=0, column=0)
        self.host = tk.Entry(self)
        self.host.grid(row=0, column=1)
        if "hostname" in info:
            self.host.delete(0, tk.END)
            self.host.insert(0, info["hostname"])

        tk.Label(self, text="Port: ").grid(row=0, column=4)
        self.port = tk.Entry(self)
        self.port.grid(row=0, column=5)
        if "port" in info:
            self.port.delete(0, tk.END)
            self.port.insert(0, info["port"])

        tk.Label(self, text="Username: ").grid(row=1, column=0)
        self.user = tk.Entry(self)
        self.user.grid(row=1, column=1)
        if "username" in info:
            self.user.delete(0, tk.END)
            self.user.insert(0, info["username"])

        self.auto = tk.BooleanVar(False)
        if "auto" in info:
            self.auto.set(info["auto"])
        tk.Checkbutton(self, variable=self.auto).grid(row=1, column=4, sticky="E")
        tk.Label(self, text="Auto Login at Start").grid(sticky="W", row=1, column=5)

        tk.Label(self, text="Key: ").grid(row=2, column=0)
        self.key = tk.Entry(self)
        self.key.grid(row=2, column=1, columnspan=5, sticky="WE")
        tk.Button(self, text="...", command=self.getFile).grid(row=2, column=6)
        if "key_filename" in info:
            self.key.delete(0, tk.END)
            self.key.insert(0, info["key_filename"])

        # Making the Ok and Cancel buttons
        tk.Button(self, text="Ok", command=partial(self.ok, info)).grid(row=4, column=2)
        tk.Button(self, text="Cancel", command=self.destroy).grid(row=4, column=3)
        tk.Button(self, text="Apply", command=partial(self.apply, info)).grid(row=4, column=4)

    def updateInfo(self, info):
        info.clear()
        info["hostname"] = self.host.get()
        info["port"] = int(self.port.get())
        info["username"] = self.user.get()
        info["key_filename"] = self.key.get()
        info["type"] = "SSH"
        info["auto"] = self.auto.get()
        save = dict(info)
        config = open("config", "w")
        config.write(json.dumps(save, sort_keys=False, indent=4, separators=(',', ': ')))
        config.close()

    def ok(self, info):
        self.updateInfo(info)
        info["status"] = "Log In"
        self.destroy()

    def apply(self, info):
        self.updateInfo(info)
        info["status"] = "Idle"

    def getFile(self):
        filename = filedialog.askopenfilename(initialdir="", title="Select private key")
        if filedialog != "":
            self.key.delete(0, tk.END)
            self.key.insert(0, filename)


class Dropdown(ttk.Combobox):
    def __init__(self, master):
        self.master = master
        self.options = [""]
        ttk.Combobox.__init__(self, master, values=self.options)
        self.update_option_menu()

    def update_option_menu(self):
        self["values"] = self.options
        self.current(0)


class App:
    def __init__(self):
        self.firstTime = True
        self.root = tk.Tk()
        self.root.title("Game Save Syncer")
        self.root.option_add('*tearOff', tk.FALSE)
        self.root.geometry("640x360")
        self.root.minsize(640, 360)
        self.root.resizable(1, 1)

        self.clientInfo = dict()
        try:
            config = open("config", "r")
            self.clientInfo = json.load(config)
            if self.clientInfo["auto"]:
                self.clientInfo["status"] = "Log In"
                self.firstTime = False
            else:
                self.clientInfo["status"] = "Idle"
            config.close()
        except IOError:
            self.clientInfo.clear()

        # create a menu
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        fileMenu = tk.Menu(menu)
        menu.add_cascade(label="File", menu=fileMenu)
        connectionMenu = tk.Menu(menu)
        fileMenu.add_cascade(label="Conections", menu=connectionMenu)
        connectionMenu.add_command(label="SSH", command=partial(SSHWindow, self.clientInfo))
        fileMenu.add_separator()
        fileMenu.add_command(label="Exit", command=self.close)

        helpMenu = tk.Menu(menu)
        menu.add_cascade(label="Help", menu=helpMenu)
        helpMenu.add_command(label="About", command=self.callback)

        mainFrame = tk.Frame(self.root)
        mainFrame.grid(row=0, column=0, sticky="nesw")
        mainFrame.rowconfigure(2, weight=2)
        mainFrame.columnconfigure(0, weight=1)

        labelFrame = tk.LabelFrame(mainFrame, text="Connection Information")
        labelFrame.grid(row=0, column=0, sticky="nswe")
        labelFrame.columnconfigure(0, weight=1)
        self.connectionInfo = tk.Label(labelFrame, text="Not Connected")
        self.connectionInfo.grid(row=0, column=0, sticky="nswe")

        # create dropdown menu
        gameDropdownLabel= tk.LabelFrame(mainFrame, text="Game:")
        gameDropdownLabel.grid(row=1, column=0, sticky="nsew")
        gameDropdownLabel.columnconfigure(0, weight=1)
        self.gameDropdown = Dropdown(gameDropdownLabel)
        self.gameDropdown.grid(row=0, column=0, sticky="nsew")

        # create treeview
        self.saveList = ttk.Treeview(mainFrame)
        self.saveList["columns"] = ("1", "2")
        self.saveList.column("#0", width=270, minwidth=270)
        self.saveList.column("1", width=150, minwidth=150)
        self.saveList.column("2", width=80, minwidth=50)
        self.saveList.heading("#0", text="Name", anchor="w")
        self.saveList.heading("1", text="Date Modified", anchor="w")
        self.saveList.heading("2", text="Size", anchor="w")
        self.saveList.grid(row=2, column=0, columnspan=2, sticky="nwes")

        self.status = StatusBar(self.root)
        self.status.grid(row=1, column=0, sticky="we")

        self.client = None
        self.fileList = dict()

        self.root.after(0, self.update)
        self.root.mainloop()

    def update(self):
        startTime = time()
        # print(self.clientInfo)
        if "status" in self.clientInfo and self.clientInfo["status"] == "Log In":
            client_info = dict(self.clientInfo)
            client_info.pop("status")
            client_info.pop("type")
            client_info.pop("auto")
            client_info["timeout"] = 1
            client_info["look_for_keys"] = False
            client_info["allow_agent"] = False
            self.clientInfo["status"] = "Logging In"
            self.status.set(self.clientInfo["status"])
            self.connectionSSH(client_info)

            # Do not add a print statement in this block it will cause the second attempt to fail
            if self.firstTime:
                self.clientInfo["status"] = "Logging In"
                self.status.set(self.clientInfo["status"])
                self.firstTime = False
                self.clientInfo["status"] = "Log In"
                self.root.after(1500, self.update)
                return

        dt = int(1000 - (time() - startTime) * 1000)
        if dt < 0:
            self.root.after(0, self.update)
        else:
            self.root.after(dt, self.update)

    def callback(self):
        print("called the callback!")

    def openSSH(self, info):
        try:
            self.client.connect(**info)
            return True
        except paramiko.BadHostKeyException:
            self.clientInfo["status"] = "Error: Bad Host Key"
            self.status.set(self.clientInfo["status"])
            self.client.close()
        except paramiko.AuthenticationException:
            self.clientInfo["status"] = "Error: Authentication Error"
            self.status.set(self.clientInfo["status"])
            self.client.close()
        except (paramiko.SSHException, paramiko.ssh_exception.SSHException, socketError) as e:
            self.clientInfo["status"] = "Error: Connection Error"
            self.status.set(self.clientInfo["status"])
            self.client.close()
        return False

    def connectionSSH(self, info):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        tries = 0
        while not self.openSSH(info) and tries < 3 and not self.firstTime:
            tries += 1
            self.status.set("Retrying ... {0}".format(tries))
        if tries == 3 or self.firstTime:
            return
        self.clientInfo["status"] = "Connected"
        self.status.set(self.clientInfo["status"])
        self.getSaveConfig()
        # stdin, stdout, stderr = self.client.exec_command('ls -l')
        # out = stdout.read().decode("UTF-8")
        # print(out)
        #
        # self.client.close()
        # self.clientInfo["status"] = "Disconnected"
        # self.status.set(self.clientInfo["status"])

    def getSaveConfig(self):
        stdin, stdout, stderr = self.client.exec_command("test  -d \"./.gamesaver\" && echo \"yes\"")
        out = stdout.read().decode("UTF-8")
        out = out.strip()
        if out == "":
            self.client.exec_command("mkdir \"./.gamesaver\"")
            stdin, stdout, stderr = self.client.exec_command("test  -d \"./.gamesaver\" && echo \"yes\"")
            out = stdout.read().decode("UTF-8")
            out = out.strip()
            if out == "":
                print("Could not create directory")  # Need to display error in status bar about not being able to create directory and return

        # sftp = paramiko.SFTP()
        sftp = self.client.open_sftp()
        sftp.chdir("./.gamesaver/")
        # print(sftp.getcwd())
        stdin, stdout, stderr = self.client.exec_command("test  -f \"./.gamesaver/save.conf\" && echo \"yes\"")
        out = stdout.read().decode("UTF-8")
        out = out.strip()
        if out == "":
            self.client.exec_command("touch \"./.gamesaver/save.conf\"")
            stdin, stdout, stderr = self.client.exec_command("test  -f \"./.gamesaver/save.conf\" && echo \"yes\"")
            out = stdout.read().decode("UTF-8")
            out = out.strip()
            if out == "":
                print("Could not create config.")  # Need to display error in status bar about not being able to create file and return

            try:
                file = sftp.open("save.conf", "w")
                file.write(json.dumps({}, sort_keys=False, indent=4, separators=(',', ': ')))
                file.close()
            except IOError:
                print("Could not open config")

        file = sftp.open("save.conf", "r")
        self.fileList = json.load(file)
        file.close()

        self.client.close()
        self.clientInfo["status"] = "Disconnected"
        self.status.set(self.clientInfo["status"])

    def close(self):
        self.root.destroy()


App()
