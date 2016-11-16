import Tkinter as tk
import sys, tkFileDialog, os, Queue, threading, time, random

import backend.common
from tkSimpleDialog import askstring
from tkFileDialog   import asksaveasfilename

from tkMessageBox import askokcancel

queue_recv = Queue.Queue()

class TextEdGUI(tk.Tk):

    def __init__(self, queue_send, endCommand, *args, **kwargs):
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

        self.queue_send = queue_send

        for F in (ConnectPage, SelectorPage, EditorPage):
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
        self.get_page("EditorPage").updateQueue()
        while self.queue_send.qsize():
            try:
                msg = self.queue_send.get(0)
                #self.get_page("EditorPage").text.insert("1.0", str(msg)+'\n')
                #print msg
            except Queue.Empty:
                pass



class ConnectPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        label = tk.Label(self, text="Connect Page", font=("Verdana", 12))
        label.grid(pady = 10, padx = 10,row=0, column=0, sticky="new")

        button1 = tk.Button(self, text="Connect",
                            command=lambda: controller.show_frame(SelectorPage))
        button1.grid(row=3, column=3, padx=15)

        label6 = tk.Label(self, text="User ID").grid(row=1, column=0, pady=5)
        label4 = tk.Label(self, text="Server IP").grid(row=2,column=0)
        label5 = tk.Label(self, text="Server Port").grid(row=3, column=0)

        entryText = tk.StringVar()
        entry = tk.Entry(self, textvariable=entryText).grid(row=1, column=1)
        entryText.set("Default user ID")

        entryText2 = tk.StringVar()
        entry2 = tk.Entry(self, textvariable=entryText2).grid(row=2, column=1)
        entryText2.set(backend.common.SERVER_INET_ADDR_DEFAULT)

        entryText3 = tk.StringVar()
        entry3 = tk.Entry(self, textvariable=entryText3).grid(row=3, column=1)
        entryText3.set(backend.common.SERVER_PORT_DEFAULT)




class SelectorPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.controller = controller
        label = tk.Label(self, text="Select file to modify", font=("Verdana", 12))
        label.grid(pady = 10, padx = 10,row=0, column=0, sticky="new")

        label7 = tk.Label(self, text="File directory").grid(row=1, column=0, pady=5)
        label8 = tk.Label(self, text="Files").grid(row=2, column=0, pady=5)

        button3 = tk.Button(self, text="Disconnect",
                            command=lambda: controller.show_frame(ConnectPage))
        button3.grid(row=3, column=1)

        button4 = tk.Button(self, text="Select",
                            command= self.select_Listelem)
        button4.grid(row=2, column=3, padx=10)

        self.entryText4 = tk.StringVar()
        entry4 = tk.Entry(self, textvariable=self.entryText4).grid(row=1, column=1)
        self.entryText4.set("Default directory")

        self.listBox = tk.Listbox(self)
        self.listBox.grid(row=2, column=1, pady=10, padx=10)
        self.listBox.insert(tk.END, "a list entry")

        tk.Button(self, text='Choose dir', command=self.askdirectory).grid(row=1, column=3, padx=15, pady=10)

        # defining options for opening a directory
        self.dir_opt = options = {}
        options['initialdir'] = '/home'
        options['mustexist'] = False
        options['parent'] = parent
        options['title'] = 'Choose directory..'

    def select_Listelem(self):
        try:
            print(os.path.expanduser("~"))
            print(self.listBox.get(self.listBox.curselection()))
            self.controller.show_frame(EditorPage)
            print(os.path.dirname(os.path.realpath(__file__)))
        except Exception:
            print('Nothing has been selected from the list!')
            #assert type(exception).__name__ == 'NameError'

    def askdirectory(self):
        dirname = tkFileDialog.askdirectory(**self.dir_opt)
        if dirname:
            self.entryText4.set(dirname)
            print(os.path.isdir(self.entryText4.get()))
            print(os.listdir(self.entryText4.get()))
            self.populateListbox()

    def populateListbox(self):
        self.listBox.delete(0, tk.END)
        for i in os.listdir(self.entryText4.get()):
            self.listBox.insert(tk.END, i)




class EditorPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.text = CustomText(self, height=25, width=80)
        self.text.grid(column=0, row=0, sticky="nw")
        self.text.grid(column=0, row=0, sticky="nw")
        self.text.bind("<<TextModified>>", self.onModification)
        self.text.bind('<Control-v>', lambda e: 'break')  # Disable paste option

        scroll = tk.Scrollbar(self)
        self.text.configure(yscrollcommand=scroll.set)
        scroll.grid(column=1, row=0, sticky="ne", ipady=163)

        label = tk.Label(self, text="Editor Page", font=("Verdana", 12))
        label.grid(column=0, row=1, sticky="se")

        label2 = tk.Label(self, text="Editor Page", font=("Verdana", 12))
        label2.grid(column=0, row=1, sticky="s")

        button5 = tk.Button(self, text="Back",
                            command=lambda: controller.show_frame(SelectorPage))
        button5.grid(column=0,row=1, sticky="sw", padx=5)

        self.text_muudatused = []
        self.counter = 0


    def onModification(self, event):
        self.text_muudatused.append((self.text.index('insert').partition(".")[0]))
        self.counter = 0

    def updateQueue(self):
        self.counter += 1

        if self.counter >= 5 and self.text_muudatused:
            self.text_muudatused = set(self.text_muudatused)
            self.text_muudatused = [int(x) for x in self.text_muudatused]
            self.text_muudatused.sort(reverse=True)

            while len(self.text_muudatused) > 0:
                try:
                    rida = self.text_muudatused.pop()
                    queue_recv.put(str(str(rida) + ":" + self.text.get(str(rida) + ".0", str(
                        rida + 1) + ".0").rstrip()))
                except UnicodeEncodeError:
                    print("Sisestatud char ei sobi (pole ascii koodis olemas)!")


class CustomText(tk.Text):
    def __init__(self, *args, **kwargs):
        """A text widget that report on internal widget commands"""
        tk.Text.__init__(self, *args, **kwargs)

        # create a proxy for the underlying widget
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, command, *args):
        cmd = (self._orig, command) + args
        result = self.tk.call(cmd)

        if command in ("insert", "delete", "replace"):
            self.event_generate("<<TextModified>>")

        return result

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

        self.queue_send = Queue.Queue()

        self.gui = TextEdGUI(self.queue_send, self.endApplication)
        self.gui.get_page("EditorPage").text.insert("1.0","Hello, world!")

        self.running = 1
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread2 = threading.Thread(target=self.workerThread2)
        self.thread1.start()
        self.thread2.start()

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
            self.queue_send.put(msg)

    def workerThread2(self):
        """Handle all messages currently in the queue, if any."""
        while self.running:
            time.sleep(0.2)
            while queue_recv.qsize():
                try:
                    msg = queue_recv.get(0)
                    #self.get_page("EditorPage").text.insert("1.0", str(msg)+'\n')
                    print msg
                except Queue.Empty:
                    pass

    def endApplication(self):
        self.running = 0

if __name__ == '__main__':
    client = ThreadedClient()
    client.gui.mainloop()



