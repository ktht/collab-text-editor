import Tkinter as tk
import sys
import Queue
import threading
import time
import random

from tkSimpleDialog import askstring
from tkFileDialog   import asksaveasfilename

from tkMessageBox import askokcancel


class TextEdGUI(tk.Tk):

    def __init__(self, queue, endCommand, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.title(self, "Collab Text Editor")
        tk.Tk.geometry(self, '580x410')
        container = tk.Frame(self)

        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.menubar(container, endCommand)
        self.statusbar(container)

        self.protocol("WM_DELETE_WINDOW", endCommand) # Handles when GUI is closed from X
        self.bind('<Escape>',lambda x: endCommand()) # Make Esc also exit the program

        self.frames = {}

        self.queue = queue

        for F in (ConnectPage, EditorPage):
            frame = F(container, self)
            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        page_name = EditorPage.__name__
        self.frames[page_name] = frame

        self.show_frame(ConnectPage)


    def menubar(self, container, endCommand):  # **** Menubar stuff *****
        menubar = tk.Menu(container)

        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open file",
                                 command=lambda: popupmsg("Not supported yet!"))
        filemenu.add_command(label="Exit", command=endCommand)
        menubar.add_cascade(label="File", menu=filemenu)

        editmenu = tk.Menu(menubar, tearoff=0)
        editmenu.add_command(label="Copy",
                                 command=lambda: popupmsg("Sorry no can do, sir!"))
        menubar.add_cascade(label="Edit", menu=editmenu)

        tk.Tk.config(self, menu=menubar)


    def statusbar(self, container): # **** Status bar stuff ****

        status = tk.Label(container, text="Connected clients:", bd=1,
                          relief=tk.SUNKEN, anchor=tk.W)
        status.grid(row=3, column=0, sticky="sw")


    def show_frame(self, cont):

        frame = self.frames[cont]
        frame.tkraise()

    def get_page(self, page_name):
        return self.frames[page_name]

    def processIncoming(self):
        """Handle all messages currently in the queue, if any."""
        while self.queue.qsize():
            try:
                msg = self.queue.get(0)
                self.get_page("EditorPage").text.insert("1.0", str(msg)+'\n')
                #print msg
            except Queue.Empty:
                pass


class ConnectPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        label = tk.Label(self, text="Connect Page", font=("Verdana", 12))
        label.grid(pady = 10, padx = 10,row=0, column=0, sticky="new")

        button1 = tk.Button(self, text="Connect",
                            command=lambda: controller.show_frame(EditorPage))
        button1.grid(row=2, column=3, padx=15)

        label4 = tk.Label(self, text="Server IP")
        label5 = tk.Label(self, text="Server Port")
        label5.grid(row=1,column=0)
        label4.grid(row=2, column=0)


        entryText = tk.StringVar()
        entry = tk.Entry(self, textvariable=entryText)
        entryText.set("Default server Port")
        entry.grid(row=1, column=1)

        entryText2 = tk.StringVar()
        entry2 = tk.Entry(self, textvariable=entryText2)
        entryText2.set("Default server IP")
        entry2.grid(row=2, column=1)




class EditorPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.text = tk.Text(self, height=25, width=80)

        self.text.grid(column=0, row=0, sticky="nw")
        scroll = tk.Scrollbar(self, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        scroll.grid(column=1, row=0, sticky="ne", ipady=163)

        label = tk.Label(self, text="Editor Page", font=("Verdana", 12))
        label.grid(column=0, row=1, sticky="se")

        label2 = tk.Label(self, text="Editor Page", font=("Verdana", 12))
        label2.grid(column=0, row=1, sticky="s")

        button2 = tk.Button(self, text="Disconnect",
                            command=lambda: controller.show_frame(ConnectPage))
        button2.grid(column=0,row=1, sticky="sw")


def popupmsg(argument):
    popup = tk.Tk()
    popup.title("Pop up")
    label=tk.Label(popup, text = argument)
    label.pack(side="top", fill="x", pady=10)
    B1 = tk.Button(popup, text="Ok", command=popup.destroy)
    B1.pack()
    popup.mainloop()


class ThreadedClient(threading.Thread):

    def __init__(self):

        self.queue = Queue.Queue()

        self.gui = TextEdGUI(self.queue, self.endApplication)
        self.gui.get_page("EditorPage").text.insert("1.0","Hello, world!")

        self.running = 1
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.start()

        self.periodicCall() # Periodic call to check if the queue contains something

    def periodicCall(self):
        self.gui.processIncoming()
        if not self.running:
            sys.exit(1)
        self.gui.after(200, self.periodicCall) # Check every 200 ms if there is something new in the queue.

    def workerThread1(self):

        while self.running:
            time.sleep(random.random() * 1.5)
            msg = random.random()
            self.queue.put(msg)

    def endApplication(self):
        self.running = 0

if __name__ == '__main__':
    client = ThreadedClient()
    client.gui.mainloop()

