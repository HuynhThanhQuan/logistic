from collections import deque
first = deque([])
last = deque([])
nom = 0
import tkinter as tk
from tkinter import *


class Application(tk.Frame):
    def __init__(self, master=None, nom=0, priono=1, prio=1):
        super().__init__(master)

        self.pack()
        self.create_widgets()
        self.nom= nom
        self.priono= priono
        self.prio=prio

    def create_widgets(self):
        self.add = tk.Button(self, bg ="black", fg="pink")
        self.add["text"] =   "-----Add to queue-----\n(click me)"
        self.add["command"] = self.create_window
        self.add.pack(side="top", pady = 10, padx = 20)
        self.add["font"] = "Times 16 bold"

        self.remov = tk.Button(self, bg ="black", fg="pink")
        self.remov["text"]= "---Remove in queue---\n(click me)"
        self.remov["command"] = self.remov_
        self.remov.pack(side="top", pady = 10, padx = 20)
        self.remov["font"] = "Times 16 bold"

        self.quit = tk.Button(self, text="QUIT", fg="white", bg = "red",
        command=root.destroy)
        self.quit.pack(side="bottom")

    def create_window(self):
        def inputer(self):
            self.L1 = tk.Label(self, text = "Name")
            self.L1.pack( side = LEFT)
            self.E1 = tk.Entry(self, bd =5)
            self.E1.pack(side = RIGHT)
        win2 = Toplevel(self)
        win2.button = Button(self, text='Ready?\nClick Here', command=inputer)

    def say_hi(self):
        print("hi there, everyone!")

    def add_1(self):
        name=input("What is your name? ")
        first.append(name)
        print("Good Day!",first[self.nom])
        print("Your priority number is:","%03d" % (self.priono))
        self.priono+=1
        self.nom+= 1

    def remov_(self):
        if (len(first)) >= 1:
            first.popleft()
        else:
            print("No one left in queue")


root = tk.Tk()
root.config(background="black")

app = Application(master=root)
app.master.title("ID QUEUEING SYSTEM beta")
app.master.minsize(540, 360)
app.master.maxsize(600, 500)
app.mainloop()
