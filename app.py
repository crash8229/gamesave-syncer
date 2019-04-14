import paramiko
import tkinter as tk
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

    def ok(self, info):
        info.clear()
        info["hostname"] = self.host.get()
        info["port"] = int(self.port.get())
        info["username"] = self.user.get()
        info["key_filename"] = self.key.get()
        info["status"] = "Log In"
        info["type"] = "SSH"
        info["auto"] = self.auto.get()
        save = dict(info)
        save.pop("status")
        config = open("config", "w")
        config.write(json.dumps(save, sort_keys=False, indent=4, separators=(',', ': ')))
        config.close()
        self.destroy()

    def getFile(self):
        print("Get File")


class Dropdown(tk.OptionMenu):

    def __init__(self, master):
        self.master = master
        self.var = tk.StringVar()
        self.var.set("")
        self.options = [""]
        tk.OptionMenu.__init__(self, master, self.var, *self.options)

    def update_option_menu(self):
        menu = self["menu"]
        menu.delete(0, "end")
        for string in self.options:
            menu.add_command(label=string, command=lambda value=string: self.var.set(value))
        self.var.set(self.options[0])



class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Game Save Syncer")
        self.root.option_add('*tearOff', tk.FALSE)

        self.clientInfo = dict()
        try:
            config = open("config", "r")
            self.clientInfo = json.load(config)
            config.close()
        except IOError:
            self.clientInfo.clear()

        # create a menu
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)

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

        self.status = StatusBar(self.root)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        main_frame = tk.Frame(self.root)
        main_frame.pack()

        # create dropdown menu
        tk.Label(main_frame, text="Game:").grid(row=1, column=0, sticky="e")
        self.gameDropdown = Dropdown(main_frame)
        self.gameDropdown.grid(row=1, column=1, sticky="w")

        self.text = tk.Text(main_frame)
        self.text.grid(row=2, column=0, columnspan=2)

        self.client = None

        self.root.after(1000, self.update)
        self.root.mainloop()

    def update(self):
        startTime = time()
        print(self.gameDropdown.var.get())
        print(self.clientInfo)
        if "status" in self.clientInfo and self.clientInfo["status"] == "Log In":
            client_info = dict(self.clientInfo)
            client_info.pop("status")
            client_info.pop("type")
            client_info.pop("auto")
            client_info["timeout"] = 1
            self.clientInfo["status"] = "Logging In"
            self.status.set(self.clientInfo["status"])
            self.connectionSSH(client_info)

        dt = int(1000 - (time() - startTime) * 1000)
        if dt < 0:
            self.root.after(0, self.update)
        else:
            self.root.after(dt, self.update)
        pass

    def callback(self):
        print("called the callback!")

    def connectionSSH(self, info):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        tries = 2
        while tries > 0:
            try:
                self.client.connect(**info)
                tries = 0
            except paramiko.BadHostKeyException:
                self.clientInfo["status"] = "Error: Bad Host Key"
                self.status.set(self.clientInfo["status"])
                self.client.close()
                return
            except paramiko.AuthenticationException:
                self.clientInfo["status"] = "Error: Authentication Error"
                self.status.set(self.clientInfo["status"])
                self.client.close()
                return
            except (paramiko.SSHException, paramiko.ssh_exception.SSHException, socketError):
                if tries > 0:
                    tries -= 1
                    self.client.close()
                    self.client = paramiko.SSHClient()
                    self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    continue
                self.clientInfo["status"] = "Error: Connection Error"
                self.status.set(self.clientInfo["status"])
                self.client.close()
                return
        try:
            self.client.exec_command("ls")
        except AttributeError:
            self.clientInfo["status"] = "Error: Connection Error (maybe due to bad private key)"
            self.status.set(self.clientInfo["status"])
            self.client.close()
            return
        self.clientInfo["status"] = "Connected"
        self.status.set(self.clientInfo["status"])
        stdin, stdout, stderr = self.client.exec_command('ls -l')
        out = stdout.read().decode("UTF-8")
        self.text.delete(1.0, tk.END)
        self.text.insert(1.0, out)

        self.client.close()
        self.clientInfo["status"] = "Disconnected"
        self.status.set(self.clientInfo["status"])

    def close(self):
        self.root.destroy()


App()
