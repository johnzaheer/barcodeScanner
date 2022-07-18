from doctest import master
from faulthandler import disable
from glob import glob
from mimetypes import init
from sqlite3 import Row
from sre_parse import State
from tkinter import *
import tkinter
from turtle import position, width
import cv2
from PIL import Image, ImageTk
import barCodeScannerSupport as sup
import warnings
from pyzbar import pyzbar
from tkinter import messagebox

#ascas

warnings.filterwarnings("ignore")

class barCodeScanner(Tk):
    def __init__(self, video_source=0):
        Tk.__init__(self)
        self.winfo_toplevel().title('Bar Code Scanner')
        self.video_source = video_source
        global videoCanvas, totalLabel, freezeFrameState
        freezeFrameState=tkinter.StringVar(master=self,value='Off')
        #on window exit make sure to close connection before destroying
        self.protocol('WM_DELETE_WINDOW', self.on_exit)
        #database code
        self.DBConnection, self.DBCursor=sup.databaseConnect()
        
        self.mainFrame = tkinter.Frame(master=self)
        self.mainFrame.grid(row=0, column=0)
        #initiate frame so it can be destroyed at every call to build (including the first)
        self.barcodeResultFrame = tkinter.Frame(master=self)
        
        self.vid = myVideoCapture(self.video_source)
        
        videoCanvas = tkinter.Canvas(master=self.mainFrame, width=self.vid.width, height=self.vid.height)
        videoCanvas.grid(row=0, column=0, columnspan=2)
        
        totalLabel = tkinter.Label(master=self.mainFrame, text='Total Barcodes Found: ')
        totalLabel.grid(row=1,column=0)

        self.CreateMainButton()

        self.delay = 15
        self.updateFrame()
        print('freezeFrameState turned: ', freezeFrameState.get())

    def CreateMainButton(self):
        if freezeFrameState.get() == 'Off':
            self.mainButton = tkinter.Button(master=self.mainFrame,text='Capture',command=lambda:self.captureCall())
            self.mainButton.grid(row=1,column=1,sticky=N+E+S+W, padx=5, pady=5)
        if freezeFrameState.get() == 'On':
            self.mainButton = tkinter.Button(master=self.mainFrame,text='Restart Capture',command=lambda:self.restartCaptureCall())
            self.mainButton.grid(row=1,column=1,sticky=N+E+S+W, padx=5, pady=5)
        
    def captureCall(self):
        freezeFrameState.set('On')
        print('freezeFrameState turned: ', freezeFrameState.get())
        self.mainButton.destroy
        self.CreateMainButton()
        self.updateFrame()
        self.barcodeDictionary=sup.databaseCheck(self.DBCursor, self.decodedObjects)
        self.barcodesFoundBuild()

    def restartCaptureCall(self):
        freezeFrameState.set('Off')
        print('freezeFrameState turned: ', freezeFrameState.get())
        self.mainButton.destroy()
        self.CreateMainButton()
        self.barcodeResultFrame.destroy()
        self.updateFrame()


    def updateFrame(self):
        if freezeFrameState.get() == 'Off':
            ret, photo, self.totalNumberBarcodes, self.decodedObjects = self.vid.get_frame()
            if ret:
                self.photo = ImageTk.PhotoImage(image=photo) #Image.fromarray(frame))
                videoCanvas.create_image(0,0, image=self.photo, anchor=tkinter.NW)
                totalLabel.config(text='Total Barcodes Found: '+ str(self.totalNumberBarcodes))
            self.after(self.delay, self.updateFrame)

    def barcodesFoundBuild(self):
        self.barcodeResultFrame.destroy()
        self.barcodeResultFrame = tkinter.Frame(master=self)
        self.barcodeResultFrame.grid(row=1, column=0)
        tkinter.Label(master=self.barcodeResultFrame, text='Display Number', justify='right', relief=RIDGE).grid(row=0, column=0, sticky=N+E+S+W)
        tkinter.Label(master=self.barcodeResultFrame, text='Barcode Type', justify='left', relief=RIDGE).grid(row=0, column=1, sticky=N+E+S+W)
        tkinter.Label(master=self.barcodeResultFrame, text='Barcode Data', justify='left', relief=RIDGE).grid(row=0, column=2, sticky=N+E+S+W)
        tkinter.Label(master=self.barcodeResultFrame, text='Description', justify='left', relief=RIDGE).grid(row=0, column=3, sticky=N+E+S+W)
        tkinter.Label(master=self.barcodeResultFrame, text='Date Entered in DB', justify='left', relief=RIDGE).grid(row=0, column=4, sticky=N+E+S+W)
        count=1
        for barcode in self.decodedObjects:
            tkinter.Label(master=self.barcodeResultFrame, text=str(count), justify='right', relief=RIDGE).grid(row=count, column=0, sticky=N+E+S+W)
            tkinter.Label(master=self.barcodeResultFrame, text=barcode.type, justify='left', relief=RIDGE).grid(row=count, column=1, sticky=N+E+S+W)
            tkinter.Label(master=self.barcodeResultFrame, text=barcode.data, justify='left', relief=RIDGE).grid(row=count, column=2, sticky=N+E+S+W)
            if self.barcodeDictionary[count].__contains__('DBDescription'):
                tkinter.Label(master=self.barcodeResultFrame, text=self.barcodeDictionary[count]['DBDescription'], justify='left', relief=RIDGE).grid(row=count, column=3, sticky=N+E+S+W)
                tkinter.Label(master=self.barcodeResultFrame, text=self.barcodeDictionary[count]['DBDate'], justify='left', relief=RIDGE).grid(row=count, column=4, sticky=N+E+S+W)
                updateButton = tkinter.Button(master=self.barcodeResultFrame,text='Update?',command=lambda item=count: self.openUpdateWindow(item, self.barcodeDictionary))
                updateButton.grid(row=count, column=5, sticky=N+E+S+W)
            else:
                tkinter.Label(master=self.barcodeResultFrame, text='Not in database', justify='left', relief=RIDGE).grid(row=count, column=3, sticky=N+E+S+W)
                tkinter.Label(master=self.barcodeResultFrame, text='', justify='left', relief=RIDGE).grid(row=count, column=4, sticky=N+E+S+W)
                insertButton = tkinter.Button(master=self.barcodeResultFrame,text='Insert?',command=lambda item=count: self.openInsertWindow(item, self.barcodeDictionary))
                insertButton.grid(row=count, column=5, sticky=N+E+S+W)
            count+=1

    def openInsertWindow(self, item, barcodeDictionary):
        self.wm_attributes("-disabled", True)
        self.insertWindow = tkinter.Toplevel()
        self.insertWindow.protocol('WM_DELETE_WINDOW', self.on_exit_insert)
        
        tkinter.Label(master=self.insertWindow,text=item).grid(row=0,column=0, pady=5, padx=5)
        tkinter.Label(master=self.insertWindow,text=barcodeDictionary[item]['barcodeData']).grid(row=0,column=1, pady=5, padx=5)
        newEntry = tkinter.Entry(master=self.insertWindow)
        newEntry.grid(row=0, column=2, sticky=N+E+S+W, pady=5, padx=5)

        tkinter.Button(master=self.insertWindow, text='Insert', command=lambda: self.dbInsert(item,barcodeDictionary,newEntry.get())).grid(row=0,column=3, pady=5, padx=5)

        self.insertWindow.grid_columnconfigure(2,weight=1)

    def openUpdateWindow(self, item, barcodeDictionary):
        self.wm_attributes("-disabled", True)
        self.updateWindow = tkinter.Toplevel()
        self.updateWindow.protocol('WM_DELETE_WINDOW', self.on_exit_update)
        
        tkinter.Label(master=self.updateWindow,text=item).grid(row=0,column=0, pady=5, padx=5)
        tkinter.Label(master=self.updateWindow,text=barcodeDictionary[item]['barcodeData']).grid(row=0,column=1, pady=5, padx=5)
        initialText=tkinter.StringVar()
        initialText.set(str(barcodeDictionary[item]['DBDescription']))
        newEntry = tkinter.Entry(master=self.updateWindow, textvariable=initialText)
        newEntry.grid(row=0, column=2, sticky=N+E+S+W, pady=5, padx=5)

        tkinter.Button(master=self.updateWindow, text='Update', command=lambda: self.dbUpdate(item,barcodeDictionary,newEntry.get())).grid(row=0,column=3, pady=5, padx=5)

        self.updateWindow.grid_columnconfigure(2,weight=1)


    def dbUpdate(self, item, barcodeDictionary, newEntry):
        print('inside the dbUpdate')
        try:
            barcodeDictionary[item]['DBDescription'] = newEntry
            sup.databaseUpdate(self.DBConnection, self.DBCursor, item, barcodeDictionary)
        except Exception as e:
            messagebox.showwarning(message='Something went wrong: '+str(e))
        else:
            print('everything went well')
            self.on_exit_update()

    def dbInsert(self, item, barcodeDictionary, newEntry):
        print('inside the dbInsert')
        try:
            barcodeDictionary[item]['DBDescription'] = newEntry
            sup.databaseInsert(self.DBConnection, self.DBCursor, item, barcodeDictionary)
        except Exception as e:
            messagebox.showwarning(message='Something went wrong: '+str(e))
        else:
            print('everything went well')
            self.on_exit_insert()



    def on_exit_insert(self):
        self.insertWindow.destroy()
        self.captureCall()
        self.wm_attributes("-disabled", False)
    
    def on_exit_update(self):
        self.updateWindow.destroy()
        self.captureCall()
        self.wm_attributes("-disabled", False)

    def on_exit(self):
        if messagebox.askyesno("Exit", "Do you want to quit the application?"):
            self.DBCursor.close
            self.destroy()


        


class myVideoCapture:
    def __init__(self, video_source=0):
        #open the video source
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)
        #define height and weight
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def get_frame(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                photo, self.totalNumberBarcodes, self.decodedObjects = sup.detect(frame)
                return(ret, photo, self.totalNumberBarcodes, self.decodedObjects)#cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
            else:
                return(ret, None, self.totalNumberBarcodes)
        else:
            return(ret, None)
    # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()



if __name__ == '__main__':
    app=barCodeScanner()
    app.mainloop()
