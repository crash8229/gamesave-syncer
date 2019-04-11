# from paramiko import SSHClient
import paramiko
import tkinter as tk
from threading import Thread


class app:
    def __init__(self):
        root = tk.Tk()
        main_frame = tk.Frame(root)
        main_frame.pack()
        text = tk.Text(main_frame)
        text.pack()

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname='mikeuserver.zapto.org', port=5555,
                       username='crash8229', key_filename='private')
        stdin, stdout, stderr = client.exec_command('ls -l')
        out = stdout.read().decode("UTF-8")

        client.close()

        text.insert(tk.END, out)
        root.mainloop()

app()
