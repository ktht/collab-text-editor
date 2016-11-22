import Tkinter as tk
import sys, tkFileDialog, os, Queue, threading, time, random, socket

import backend.common
from backend.client_backend import client
from tkSimpleDialog import askstring
from tkFileDialog   import asksaveasfilename

from tkMessageBox import askokcancel

queue_send2srvr = Queue.Queue()

class TextEdGUI(tk.Tk):

    def __init__(self, queue_recv_srvr, endCommand, *args, **kwargs):
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

        self.queue_recv_srvr = queue_recv_srvr

        for F in (ConnectPage, SelectorPage, EditorPage):
            frame = F(container, self)
            self.frames[F] = frame
            page_name = F.__name__
            self.frames[page_name] = frame

            frame.grid(row=0, column=0, sticky="nsew")

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
        self.status = tk.Label(container, text="Client ID: ", bd=1,
                          relief=tk.SUNKEN, anchor=tk.W)
        self.status.grid(row=3, column=0, sticky="sw")


    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

    def get_page(self, page_name):
        return self.frames[page_name]

    def processIncoming(self):
        self.get_page("EditorPage").updateQueue()
        while self.queue_recv_srvr.qsize():
            try:
                msg = self.queue_recv_srvr.get(0)
                #print(self.get_page("ConnectPage").entryText.get())
                #self.get_page("EditorPage").text.insert("1.0", str(msg)+'\n')
                #print msg
            except Queue.Empty:
                pass



class ConnectPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        label = tk.Label(self, text="Connect Page", font=("Verdana", 12))
        label.grid(pady = 10, padx = 10,row=0, column=0, sticky="new")

        self.label3 = tk.Label(self, text="", font=("Verdana", 12))
        self.label3.grid(pady=10, padx=10, row=5, column=1, sticky="ew")

        #button1 = tk.Button(self, text="Connect",
        #                    command=lambda: controller.show_frame(SelectorPage))
        button1 = tk.Button(self, text="Connect",
                            command=lambda: self.funcs(self.controller))
        button1.grid(row=3, column=3, padx=15)

        label6 = tk.Label(self, text="User ID").grid(row=1, column=0, pady=5)
        label4 = tk.Label(self, text="Server IP").grid(row=2,column=0)
        label5 = tk.Label(self, text="Server Port").grid(row=3, column=0)

        self.entryText = tk.StringVar()
        entry = tk.Entry(self, textvariable=self.entryText).grid(row=1, column=1)

        self.entryText2 = tk.StringVar()
        entry2 = tk.Entry(self, textvariable=self.entryText2).grid(row=2, column=1)
        self.entryText2.set(backend.common.SERVER_INET_ADDR_DEFAULT)

        self.entryText3 = tk.StringVar()
        entry3 = tk.Entry(self, textvariable=self.entryText3).grid(row=3, column=1)
        self.entryText3.set(backend.common.SERVER_PORT_DEFAULT)

    def funcs(self, contr):
        try:
            if self.entryText.get() == "Creating new ID!":
                pass
            else:
                if not self.entryText.get().isdigit():
                    popupmsg("ID needs to be an integer!")
                    return None
                if len(self.entryText.get()) > 4:
                    popupmsg("Max length is 4 digits!")
                    return None
        except Exception as err:
            print(err)

        try:
            socket.inet_aton(self.entryText2.get())
        except socket.error:
            popupmsg("Not IPv4 address!")

        try:
            port_nr = self.entryText3.get()
            if not port_nr.isdigit():
                popupmsg("Port number needs to be an integer!")
                return None
            port_range = (2 ** 10, 2 ** 16 - 1)
            if not (port_range[0] <= int(port_nr) <= port_range[1]):
                popupmsg("Port number out of range!")
        except Exception as err:
            print(err)

        contr.show_frame(SelectorPage)
        client1.e.set()

class SelectorPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.controller = controller
        label = tk.Label(self, text="Select file to modify", font=("Verdana", 12))
        label.grid(pady = 10, padx = 10,row=0, column=0, sticky="new")

        label7 = tk.Label(self, text="ID").grid(row=1, column=0, pady=5)
        label8 = tk.Label(self, text="File").grid(row=2, column=0, pady=5)
        label8 = tk.Label(self, text="Files").grid(row=3, column=0, pady=5)

        tk.Button(self, text='Select', command=lambda: controller.show_frame(EditorPage)
                  ).grid(row=2, column=2, padx=15, pady=5)

        #button3 = tk.Button(self, text="Disconnect",
        #                    command=lambda: controller.show_frame(ConnectPage))
        #button3.grid(row=4, column=1)

        button4 = tk.Button(self, text="Select from list",
                            command= self.select_Listelem)
        button4.grid(row=3, column=2, padx=10)

        self.entryText4 = tk.StringVar()
        entry4 = tk.Entry(self, textvariable=self.entryText4).grid(row=1, column=1)
        self.entryText4.set("Files user ID")

        self.entryText5 = tk.StringVar()
        entry4 = tk.Entry(self, textvariable=self.entryText5).grid(row=2, column=1)
        self.entryText5.set("File ID")

        self.listBox = tk.Listbox(self)
        self.listBox.grid(row=3, column=1, pady=10, padx=10)

        self.var = tk.IntVar()
        checkBox = tk.Checkbutton(self, text="Public", variable=self.var, command=self.checkingBox)
        checkBox.grid(row = 1, column = 2)

    def checkingBox(self):
        print(self.var.get())

    def select_Listelem(self):
        try:
            print(self.listBox.get(self.listBox.curselection()))
            self.controller.show_frame(EditorPage)
        except Exception:
            print('Nothing has been selected from the list!')
            #assert type(exception).__name__ == 'NameError'


class EditorPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.controller = controller
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
                    queue_send2srvr.put(str(str(rida) + ":" + self.text.get(str(rida) + ".0", str(
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
        self.queue_recv_srvr = Queue.Queue()

        self.gui = TextEdGUI(self.queue_recv_srvr, self.endApplication)
        #self.gui.get_page("EditorPage").text.insert("1.0","Hello, world!")

        self.running = 1
        self.e = threading.Event()
        self.thread1 = threading.Thread(target=self.recv_srvr_Thread)
        self.thread2 = threading.Thread(target=self.send2srvr_Thread)
        self.thread3 = threading.Thread(target = self.clientThread)
        self.thread3.setDaemon(True)
        #self.thread2.setDaemon(True)
        self.create_new_ID = False
        self.thread1.start()
        self.thread2.start()
        self.thread3.start()

        self.periodicCall() # Periodic call to check if the queue contains something



        if not os.path.exists(backend.common.TMP_DIR_CLIENT):
            os.makedirs(backend.common.TMP_DIR_CLIENT)

        try:
            with open(os.path.join(backend.common.TMP_DIR_CLIENT, 'Usr_ID'), 'r+') as f:
                self.ID_from_file = f.readline()
                self.gui.get_page("ConnectPage").entryText.set(str(self.ID_from_file).rstrip())
                if os.stat(str(os.path.join(backend.common.TMP_DIR_CLIENT, 'Usr_ID'))).st_size == 0:
                    self.create_new_ID = True
                    self.gui.get_page("ConnectPage").label3.config(
                        text='Hello new user, we will create a new ID for you '
                                                            '\n when you connect!')
                    self.gui.get_page("ConnectPage").entryText.set("Creating new ID!")
                else:
                    self.gui.get_page("ConnectPage").label3.config(
                        text='Hello existing user!')
        except IOError:
            self.gui.get_page("ConnectPage").entryText.set("Creating new ID!")
            self.create_new_ID = True
            self.gui.get_page("ConnectPage").label3.config(text='Hello new user, we will create a new ID for you '
                                                                '\n when you connect!')
            print("File for user ID was not found!")

    def periodicCall(self):
        self.gui.processIncoming()
        if not self.running:
            sys.exit(1)
        self.gui.after(200, self.periodicCall) # Check every 200 ms if there is something new in the queue.

    def recv_srvr_Thread(self):
        while self.running:
            time.sleep(random.random() * 1.5)
            msg = random.random()
            self.queue_recv_srvr.put(msg)

    def send2srvr_Thread(self):
        """Handle all messages currently in the queue, if any."""
        while self.running:
            time.sleep(0.2)
            while queue_send2srvr.qsize():
                try:
                    msg = queue_send2srvr.get(0)
                    print msg
                except Queue.Empty:
                    pass


    def clientThread(self):
        self.e.wait()
        usr_ID = self.gui.get_page("ConnectPage").entryText.get()
        server_IP  = self.gui.get_page("ConnectPage").entryText2.get()
        server_PORT = int(self.gui.get_page("ConnectPage").entryText3.get())

        if not usr_ID.isdigit():
            usr_ID = 1

        with client(server_IP, server_PORT, backend.common.TMP_DIR_SERVER, int(usr_ID)) as c:
            print("Server connected")
            if self.create_new_ID:
                client_id = c.req_id()
                try:
                    with open(os.path.join(backend.common.TMP_DIR_CLIENT, 'Usr_ID'), 'w+') as f:
                        print(client_id)
                        f.write(str(client_id))
                except IOError:
                    print("File IOError!")
            else:
                client_id = usr_ID

            self.gui.status.config(text='Client ID: '+str(client_id))

            client_files = c.req_session()
            self.gui.get_page("SelectorPage").listBox.delete(0, tk.END)
            if client_files:
                print(client_files)
                for i in client_files:
                    self.gui.get_page("SelectorPage").listBox.insert(tk.END, i)
                file_contents = c.req_file('%d:test.txt' % 4)
            #print(client_files)

            while(self.running):
                time.sleep(0.2)


    def endApplication(self):
        self.running = 0

if __name__ == '__main__':
    client1 = ThreadedClient()
    client1.gui.mainloop()


# GUI insert keskele
# Cliendi ja GUI suhtlus yle Queue
# Req file tests


# Klient yritab yhenduda serveriga vaartuste abil, mis on kuvatud Connect Page lehel
# Default ID loetakse sisse .tmp_collab/client olevast failist
# Kui seal ID puudub, tuleb pop up, mis kysib ka olete uus kasutaja ning kas soovite luua uue ID?
#


