# from paramiko import SSHClient
import paramiko
import tkinter as tk
from threading import Thread


# TODO: use timestamp to determine if to upload
class StatusBar(tk.Frame):

    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.label = tk.Label(self, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.label.pack(fill=tk.X)

    def set(self, format, *args):
        self.label.config(text=format % args)
        self.label.update_idletasks()

    def clear(self):
        self.label.config(text="")
        self.label.update_idletasks()


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.option_add('*tearOff', tk.FALSE)

        # create a menu
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)

        filemenu = tk.Menu(menu)
        menu.add_cascade(label="File", menu=filemenu)
        connectionmenu = tk.Menu(menu)
        filemenu.add_cascade(label="Conections", menu=connectionmenu)
        connectionmenu.add_command(label="SSH", command=self.connectionSSH)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.close)

        helpmenu = tk.Menu(menu)
        menu.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="About...", command=self.callback)

        self.status = StatusBar(self.root)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        main_frame = tk.Frame(self.root)
        main_frame.pack()

        text = tk.Text(main_frame)
        text.pack()

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname='mikeuserver.zapto.org', port=5555,
                       username='gamesaver', key_filename='private')
        stdin, stdout, stderr = client.exec_command('ls -l')
        out = stdout.read().decode("UTF-8")

        client.close()

        text.insert(tk.END, out)
        self.root.mainloop()

    def callback(self):
        print("called the callback!")

    def connectionSSH(self):
        # Create the window and focus on it
        sshWindow = tk.Toplevel()
        sshWindow.grab_set()

        # Creating the fields for entering SSH information needed
        tk.Label(sshWindow, text="Address: ").grid(row=0, column=0)
        host = tk.Entry(sshWindow).grid(row=0, column=1)

        tk.Label(sshWindow, text="Port: ").grid(row=0, column=4)
        port = tk.Entry(sshWindow).grid(row=0, column=5)

        tk.Label(sshWindow, text="Username: ").grid(row=1, column=0)
        user = tk.Entry(sshWindow).grid(row=1, column=1)

        tk.Label(sshWindow, text="Password: ").grid(row=2, column=0)
        password = tk.Entry(sshWindow, show="*").grid(row=2, column=1)

        tk.Label(sshWindow, text="Key: ").grid(row=3, column=0)
        key = tk.Entry(sshWindow).grid(row=3, column=1)
        tk.Button(sshWindow, text="...", command=self.callback).grid(row=3, column=2)

        # Making the Ok and Cancel buttons
        tk.Button(sshWindow, text="Ok", command=self.callback)
        tk.Button(sshWindow, text="Cancel", command=self.callback)

    def close(self):
        self.root.destroy()


App()



