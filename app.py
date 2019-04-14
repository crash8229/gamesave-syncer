# from paramiko import SSHClient
import paramiko
import tkinter as tk
from functools import partial
from threading import Thread
from time import time
import json
import lzma


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
        self.grab_set()

        # Creating the fields for entering SSH information needed
        tk.Label(self, text="Address: ").grid(row=0, column=0)
        self.host = tk.Entry(self)
        self.host.grid(row=0, column=1)

        tk.Label(self, text="Port: ").grid(row=0, column=4)
        self.port = tk.Entry(self)
        self.port.grid(row=0, column=5)

        tk.Label(self, text="Username: ").grid(row=1, column=0)
        self.user = tk.Entry(self)
        self.user.grid(row=1, column=1)

        tk.Label(self, text="Key: ").grid(row=2, column=0)
        self.key = tk.Entry(self)
        self.key.grid(row=2, column=1)
        tk.Button(self, text="...", command=self.getFile).grid(row=2, column=2)

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
        self.destroy()

    def getFile(self):
        print("Get File")


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.option_add('*tearOff', tk.FALSE)

        self.clientInfo = dict()

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
        helpMenu.add_command(label="About...", command=self.callback)

        self.status = StatusBar(self.root)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        main_frame = tk.Frame(self.root)
        main_frame.pack()

        self.text = tk.Text(main_frame)
        self.text.pack()

        self.client = None

        self.root.after(1000, self.update)
        self.root.mainloop()

    def update(self):
        startTime = time()

        print(self.clientInfo)
        if "status" in self.clientInfo and self.clientInfo["status"] == "Log In":
            client_info = dict(self.clientInfo)
            client_info.pop("status")
            client_info.pop("type")
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
        try:
            self.client.connect(**info)
        except:
            self.clientInfo["status"] = "Error"
            self.status.set(self.clientInfo["status"])
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



