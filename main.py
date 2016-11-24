import Tkinter as tk
import sys, tkFileDialog, os, Queue, threading, time, random, socket, logging

import backend.common
from backend.client_backend import client

logging.basicConfig(
    level  = logging.DEBUG,
    format = '[%(asctime)s] [%(threadName)s] [%(module)s:%(funcName)s:%(lineno)d] [%(levelname)s] -- %(message)s',
    stream = sys.stdout
  )

cv = threading.Condition()
queue_send2srvr = Queue.Queue()
useListElem = True
lineCount = 0

class TextEdGUI(tk.Tk):

    def __init__(self, endCommand, *args, **kwargs):
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
        self.status2 = tk.Label(container, text="Last edit done by ID: ", bd=1,
                               relief=tk.SUNKEN, anchor=tk.W)
        self.status2.grid(row=3, column=0, sticky="se")


    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

    def get_page(self, page_name):
        return self.frames[page_name]

    def processIncoming(self):
        while client.queue_incoming.qsize():
            self.get_page("EditorPage").unBindCallback()
            try:
                if client1.useMarshalling:
                    line_no, action, payload, id_c = client.queue_incoming.get(0)
                    self.status2.config(text='Last edit done by ID: ' + str(id_c))
                    if int(action) == backend.common.EDIT_REPLACE:
                        self.get_page("EditorPage").text.delete(str(line_no+1)+".0", str(line_no+2)+".0")
                        self.get_page("EditorPage").text.insert(str(line_no+1)+".0", str(payload)+'\n')
                    elif int(action) == backend.common.EDIT_INSERT:
                        self.get_page("EditorPage").text.delete(str(line_no + 1) + ".0", str(line_no + 2) + ".0")
                        self.get_page("EditorPage").text.insert(str(line_no + 1) + ".0", str(payload) + '\n')

                    elif int(action) == backend.common.EDIT_DELETE:
                        tekst = str(self.get_page("EditorPage").text.get(str(line_no+1)+".0", str(line_no+2)+".0")).rstrip()
                        tekst2 = str(self.get_page("EditorPage").text.get(str(line_no+2) + ".0",
                                                                         str(line_no+3) + ".0")).rstrip()
                        self.get_page("EditorPage").text.delete(str(line_no+1) + ".0", str(line_no+3) + ".0")
                        self.get_page("EditorPage").text.insert(str(line_no+1)+".0",tekst+tekst2+'\n')
                else:
                    self.get_page("EditorPage").text.insert("1.0", str(client.queue_incoming.get(0)))
                    global lineCount
                    lineCount = int(self.get_page("EditorPage").text.index('end-1c').split('.')[0])
            except Queue.Empty:
                pass
        self.get_page("EditorPage").bindCallback()


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

        #label6 = tk.Label(self, text="User ID").grid(row=1, column=0, pady=5)
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
        client1.e.clear()

class SelectorPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.controller = controller
        label = tk.Label(self, text="Select file to modify", font=("Verdana", 12))
        label.grid(pady = 10, padx = 10,row=0, column=0, sticky="new")

        label7 = tk.Label(self, text="ID").grid(row=1, column=0, pady=5)
        label8 = tk.Label(self, text="File").grid(row=2, column=0, pady=5)
        label8 = tk.Label(self, text="Files").grid(row=3, column=0, pady=5)

        tk.Button(self, text='Select', command=lambda: self.funcs3(self.controller)
                  ).grid(row=2, column=2, padx=15, pady=5)

        #button3 = tk.Button(self, text="Disconnect",
        #                    command=lambda: controller.show_frame(ConnectPage))
        #button3.grid(row=4, column=1)

        button4 = tk.Button(self, text="Select from list",
                            command=lambda: self.funcs2(self.controller))
        button4.grid(row=3, column=2, padx=10)

        self.entryText4 = tk.StringVar()
        entry4 = tk.Entry(self, textvariable=self.entryText4).grid(row=1, column=1)
        #self.entryText4.set("Files user ID")

        self.entryText5 = tk.StringVar()
        entry4 = tk.Entry(self, textvariable=self.entryText5).grid(row=2, column=1)
        #self.entryText5.set("File ID")

        self.listBox = tk.Listbox(self)
        self.listBox.grid(row=3, column=1, pady=10, padx=10)

        self.var = tk.IntVar()
        checkBox = tk.Checkbutton(self, text="Private", variable=self.var)
        checkBox.grid(row = 1, column = 2)


    def select_Listelem(self):
        try:
            print(self.listBox.get(self.listBox.curselection()))
            self.controller.show_frame(EditorPage)
        except Exception:
            print('Nothing has been selected from the list!')

    def funcs2(self, contr):
        contr.show_frame(EditorPage)
        client1.e.set()
        client1.e.clear()

    def funcs3(self, contr):
        contr.show_frame(EditorPage)
        global useListElem
        useListElem = False
        client1.e.set()
        client1.e.clear()


class EditorPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.controller = controller
        self.text = CustomText(self, height=25, width=80)
        self.text.grid(column=0, row=0, sticky="nw")
        self.text.grid(column=0, row=0, sticky="nw")
        self.text.bind('<Control-v>', lambda e: 'break')  # Disable paste option

        scroll = tk.Scrollbar(self)
        self.text.configure(yscrollcommand=scroll.set)
        scroll.grid(column=1, row=0, sticky="ne", ipady=163)
        self.rowChange = 0 # rowChange = 0 means no change, rowChange = 1 means enter, rowChange = 2 means delete line

        #button5 = tk.Button(self, text="Back",
        #                    command=lambda: controller.show_frame(SelectorPage))
        #button5.grid(column=0,row=1, sticky="sw", padx=5)

    def bindCallback(self):
        self.text.bind("<<TextModified>>", self.onModification)

    def unBindCallback(self):
        self.text.bind("<<TextModified>>", self.emptyFunc)

    def emptyFunc(self, event):
        pass

    def onModification(self, event):
        client1.gui.status2.config(text='Last edit done by Me!')
        global lineCount
        var = lineCount
        lineCount =  int(self.text.index('end-1c').split('.')[0])
        rida = int(self.text.index('insert').partition(".")[0])

        if var == lineCount:
            self.rowChange = 0
        elif var < lineCount:
            self.rowChange = 1
        else:
            self.rowChange = 2

        try:
            if self.rowChange == 1:
                for i in range(2):
                    if i == 0:
                        cv.acquire()
                        queue_send2srvr.put(str(str(rida-2) + backend.common.DELIM + str(self.rowChange) + backend.common.DELIM
                                                + self.text.get(str(rida-1) + ".0", str(rida) + ".0").rstrip())+'\n')
                        if queue_send2srvr.qsize() == 1:
                            cv.notify_all()
                        cv.release()
                    else:
                        time.sleep(0.02)
                        cv.acquire()
                        queue_send2srvr.put(
                            str(str(rida - 1) + backend.common.DELIM + str(self.rowChange) + backend.common.DELIM
                                + self.text.get(str(rida) + ".0", str(rida + 1) + ".0").rstrip()))
                        if queue_send2srvr.qsize() == 1:
                            cv.notify_all()
                        cv.release()
            else:
                cv.acquire()
                queue_send2srvr.put(str(str(rida - 1) + backend.common.DELIM + str(self.rowChange) + backend.common.DELIM
                                        + self.text.get(str(rida) + ".0", str(rida + 1) + ".0").rstrip()))
                time.sleep(0.02)
                if queue_send2srvr.qsize() == 1:
                    cv.notify_all()
                cv.release()
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

def popupmsg_close(argument):
    popup = tk.Tk()
    popup.title("Pop up")
    label=tk.Label(popup, text = argument)
    label.pack(side="top", fill="x", pady=10)
    B1 = tk.Button(popup, text="Ok", command=client1.endApplication)
    B1.pack()
    popup.mainloop()


class ThreadedClient(threading.Thread):

    def __init__(self):
        self.gui = TextEdGUI( self.endApplication)

        self.useMarshalling = False
        self.running = 1
        self.e = threading.Event()
        self.thread3 = threading.Thread(target = self.clientThread, name="clientThread")
        self.thread3.setDaemon(True)
        self.create_new_ID = False
        self.thread3.start()

        self.periodicCall() # Periodic call to check if the queue contains something

        if not os.path.exists(backend.common.TMP_DIR_CLIENT):
            os.makedirs(backend.common.TMP_DIR_CLIENT)

        try:
            with open(os.path.join(backend.common.TMP_DIR_CLIENT, 'Usr_ID'), 'r+') as f:
                self.ID_from_file = f.readline()
                self.gui.get_page("ConnectPage").entryText.set(str(self.ID_from_file))
                logging.debug('Read client ID from file %s' %self.ID_from_file)
                if os.stat(str(os.path.join(backend.common.TMP_DIR_CLIENT, 'Usr_ID'))).st_size == 0:
                    self.create_new_ID = True
                    logging.debug('Creating new ID for the user')
                    self.gui.get_page("ConnectPage").label3.config(
                        text='Hello new user, we will create a new ID for you '
                                                            '\n when you connect!')
                    self.gui.get_page("ConnectPage").entryText.set("Creating new ID!")
                else:
                    logging.debug('Read client ID from file %s' % self.ID_from_file)
                    self.gui.get_page("ConnectPage").label3.config(
                        text='Hello existing user!')
        except IOError:
            self.gui.get_page("ConnectPage").entryText.set("Creating new ID!")
            self.create_new_ID = True
            logging.debug('Creating new ID for the user')
            self.gui.get_page("ConnectPage").label3.config(text='Hello new user, we will create a new ID for you '
                                                                '\n when you connect!')
            print("File for user ID was not found!")

    def periodicCall(self):
        self.gui.processIncoming()
        if not self.running:
            sys.exit(1)
        self.gui.after(200, self.periodicCall) # Check every 200 ms if there is something new in the queue.


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
                        f.write(str(client_id))
                except IOError:
                    print("File IOError!")
            else:
                client_id = usr_ID

            self.gui.status.config(text='Client ID: '+str(client_id))

            client_files = c.req_session()
            self.gui.get_page("SelectorPage").listBox.delete(0, tk.END)
            if client_files:
                for i in client_files:
                    self.gui.get_page("SelectorPage").listBox.insert(tk.END, i)

            self.e.wait()

            if useListElem:
                try:
                    print("Using list!")
                    fname = self.gui.get_page("SelectorPage").listBox.get(
                        self.gui.get_page("SelectorPage").listBox.curselection())
                    file_contents = c.req_file(backend.common.DELIM_ID_FILE.join([str(client_id), fname.split(':')[1]]))
                    client.queue_incoming.put(file_contents)
                except Exception:
                    print('Nothing has been selected from the list!')
            else:
                fname = self.gui.get_page("SelectorPage").entryText4.get()
                cl_ID = self.gui.get_page("SelectorPage").entryText5.get()

                if self.gui.get_page("SelectorPage").var.get():
                    file_contents = c.req_file(backend.common.DELIM_ID_FILE.join([str(fname), str(cl_ID)]), backend.common.FILEMODE_PRIVATE)
                else:
                    file_contents = c.req_file(backend.common.DELIM_ID_FILE.join([str(fname), str(cl_ID)]))

                if file_contents == None:
                    popupmsg_close("This file does not exist, closing program.")
                client.queue_incoming.put(file_contents)

            time.sleep(1)
            self.useMarshalling = True
            self.gui.get_page("EditorPage").bindCallback()

            while(self.running):
                cv.acquire()
                if queue_send2srvr.qsize() == 0:
                    cv.wait()
                try:
                    msg = queue_send2srvr.get(0)
                    msg = msg.split(backend.common.DELIM)
                    if int(msg[1]) == 0:
                        c.send_changes(int(msg[0]), backend.common.EDIT_REPLACE, str(msg[2]))
                    elif int(msg[1]) == 1:
                        c.send_changes(int(msg[0]), backend.common.EDIT_INSERT, str(msg[2]))
                    elif int(msg[1]) == 2:
                        c.send_changes(int(msg[0]), backend.common.EDIT_DELETE, str(msg[2]))
                except Queue.Empty:
                    pass
                cv.release()


    def endApplication(self):
        self.running = 0

if __name__ == '__main__':
    client1 = ThreadedClient()
    client1.gui.mainloop()

