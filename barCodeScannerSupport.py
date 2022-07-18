from sqlite3 import connect
from pyzbar import pyzbar
from PIL import Image, ImageDraw, ImageFont
import pyodbc
from datetime import datetime
import configparser
dbconfig=configparser.ConfigParser()
dbconfig.read('db_config.ini')

def detect(frame):
    decodeObjects = pyzbar.decode(frame)
    img=Image.fromarray(frame)
    draw=ImageDraw.Draw(img)
    fontOnBarCode=ImageFont.truetype("impact.ttf", size=18)
    count=1

    for barcode in decodeObjects:
        draw.polygon(barcode.polygon, outline='#e945ff', width=4)
        #location of barcode for number
        x=barcode.rect.left
        y=barcode.rect.top
        #number barcodes
        draw.text((x,y),str(count), font=fontOnBarCode)
        count+=1

    return img, count-1, decodeObjects

def databaseConnect():
    connection = pyodbc.connect('DRIVER={SQL Server};SERVER='+dbconfig['mysqldb']['server']+';DATABASE='+dbconfig['mysqldb']['database']+';UID='+dbconfig['mysqldb']['username']+';PWD='+ dbconfig['mysqldb']['password'])
    cursor=connection.cursor()
    return connection, cursor

    return cursor

def databaseCheck(cursor, barcodeObject):
    barcodeDictionary = {}
    count=1
    for barcode in barcodeObject:
        barcodeDictionary[count] = {'barcodeType':str(barcode.type),'barcodeData': str(barcode.data.decode())}
        count+=1
    
    for i in barcodeDictionary.keys():
        sqlKey=barcodeDictionary[i]['barcodeType'] + barcodeDictionary[i]['barcodeData']
        sql="select bar.description, bar.dateEntered from barcodes bar where CONCAT(bar.type, bar.data) = '" + sqlKey +"';"
        cursor.execute(sql)
        row=cursor.fetchone()
        while row:
            barcodeDictionary[i]['DBDescription'] = row[0]
            barcodeDictionary[i]['DBDate'] = datetime.strftime(row[1], "%m/%d/%Y %I:%M %p")
            row = cursor.fetchone()

    return barcodeDictionary

def databaseUpdate(connection, cursor,item,barcodeDictionary):
    sqlKey=barcodeDictionary[item]['barcodeType'] + barcodeDictionary[item]['barcodeData']
    sql="update barcodes set description = '" + str(barcodeDictionary[item]['DBDescription']) + "' where concat(type,data) = '"+ sqlKey +"';"
    cursor.execute(sql)
    connection.commit()   


def databaseInsert(connection, cursor,item,barcodeDictionary):
    sql="insert into barcodes(type,data,description) select  '" +  str(barcodeDictionary[item]['barcodeType']) + "', '"+ str(barcodeDictionary[item]['barcodeData']) + "', '"+ str(barcodeDictionary[item]['DBDescription']) + "';"
    cursor.execute(sql)
    connection.commit()   
