import tkinter as tk
from tkinter import ttk
from tkinter import *
import sqlite3
import smtplib, ssl
from datetime import datetime
import pickle

def fSendEmail(nOrder,aProduct):
    #Function sends order email. Needs order amount and product.

    conn = sqlite3.connect("Stock_management.db")

    #When selecting with conditions variable must be a string.

    cursor=conn.execute("SELECT EMAIL_ADDRESS FROM SUPPLIERS where SUPPLIER_ID=?",str((aProduct[2])))

    for row in cursor:
        sEmail=row

    conn.close()

    EmailPass=open('EmailPass','rb')
    aEmailPass=pickle.load(EmailPass)
    EmailPass.close()

    #Defining variables needed to send email
    port = 587
    smtp_server = "smtp.gmail.com"
    sSender = aEmailPass[0]
    sRecipient = sEmail
    password = aEmailPass[1]
    message = """\
    Subject: Automatic reorder

    This is an automated request from warehouse to order {number} units of {name}""".format(number=nOrder,name=aProduct[0])

    #Sends an email with selected variables
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sSender, password)
        server.sendmail(sSender, sRecipient, message)        

    OrderHistory=open('OrderHistory','rb')
    aOrderHistory=pickle.load(OrderHistory)
    OrderHistory.close()

    #Selects current time
    dNow=datetime.now()
    dString = dNow.strftime("%d/%m/%Y %H:%M")

    aOrder=[]
    nCost='%.2f' % (aProduct[4]*nOrder)

    NextOrder=open('NextOrder','rb')
    nOrderNumber=pickle.load(NextOrder)
    NextOrder.close()

    nNextOrder=nOrderNumber+1

    NextOrder=open('NextOrder','wb')
    pickle.dump(nNextOrder,NextOrder)
    NextOrder.close()                    

    aOrder.append(dString)
    aOrder.append(aProduct[0])
    aOrder.append(nOrder)
    aOrder.append(nCost)
    aOrder.append(nOrderNumber)
    aOrder.append(True)

    aOrderHistory.append(aOrder)

    OrderHistory=open('OrderHistory','wb')
    pickle.dump(aOrderHistory,OrderHistory)
    OrderHistory.close()

    return nOrderNumber

def fLevelChange():
    #Allows to decrease stock levels
    def fDecrease():
        tAlerts.delete(1.0,"end")

        tStockLeft.delete(1.0,"end")

        nOrder=int(eOrder.get())

        if nOrder<0:
            tAlerts.insert(tk.END,"Can't enter a minus")

        else:

            aStocks=[]

            conn = sqlite3.connect("Stock_management.db")

            cursor=conn.execute("SELECT PRODUCT_NAME, CURRENT_STOCK, SUPPLIER_ID, CRITICAL_STOCK, UNIT_COST, PRODUCT_ACTIVE, PRODUCT_REORDER FROM PRODUCTS")
            for row in cursor:
                aProduct=[]
                aProduct.append(row[0])
                aProduct.append(row[1])
                aProduct.append(row[2])
                aProduct.append(row[3])
                aProduct.append(row[4])
                aProduct.append(row[5])
                aProduct.append(row[6])
                aStocks.append(aProduct)

            conn.close()
            
            sChoice=(cProduct.get())
            for i in range(0,len(aStocks)):
                if sChoice==aStocks[i][0]:
                    nChoice=i

            if aStocks[nChoice][1]-nOrder<0:
                    tStockLeft.insert(tk.END,"Stock cannot be"+" below 0")

            else:
                aStocks[nChoice][1]=aStocks[nChoice][1]-nOrder

                tStockLeft.insert(tk.END,"Stock of "+aStocks[nChoice][0]+" remaining:"+str(aStocks[nChoice][1]))

                eOrder.delete(0,"end")

                conn = sqlite3.connect('Stock_management.db')

                conn.execute("UPDATE PRODUCTS set CURRENT_STOCK = ? where PRODUCT_NAME = ?",(aStocks[nChoice][1],aStocks[nChoice][0]))
                conn.commit()
                conn.close()

                #Checks product and product reorder are active(Product reorder is redunant currently)
                if aStocks[nChoice][5]==1 and aStocks[nChoice][6]==1:

                    OrderHistory=open('OrderHistory','rb')
                    aOrderHistory=pickle.load(OrderHistory)
                    OrderHistory.close()

                    aDelivery=[]

                    for i in range(0,len(aOrderHistory)):
                        if aStocks[nChoice][0]==aOrderHistory[i][1]:
                            aDelivery=aOrderHistory[i]

                    bValid=False

                    AutoReorder=open('AutoReorder','rb')
                    nAutoReorder=pickle.load(AutoReorder)
                    AutoReorder.close()

                    #If and elif statements perfrom error checking.
                    #Checks system autoreorder is on. If it isnt Valid is False
                    if nAutoReorder==0:
                        bValid=False

                    #Verifies there are no orders. If there are none Valid is True
                    elif aDelivery==[]:
                        bValid=True

                    #Verifies if there have been orders if they are still be delivered. If they aren't being delivered Valid is True
                    elif aDelivery[5]==False:
                        bValid=True

                    #If there are active deliveries for the product the user gets informed of this.
                    elif aDelivery[5]==True:
                        tAlerts.insert(tk.END,"There is currently an order active for "+str(aDelivery[2])+" units of "+str(aDelivery[1]+". To place an additional order use the manual order option availible on the home screen."))

                    #If the stock is below the crit stock and Valid is True then the email function is run
                    if aStocks[nChoice][1]<=aStocks[nChoice][3] and bValid==True:

                        conn.close()

                        nOrder=(aStocks[nChoice][3]*4)-aStocks[nChoice][1]

                        fSendEmail(nOrder,aStocks[nChoice])

                        tAlerts.insert(tk.END,"Automatically ordered "+str(nOrder)+" units of "+aStocks[nChoice][0]+".")
                        
                            
                            
                        
    #Allows to increase the level of stock
    def fIncrease():

        tAlerts.delete(1.0,"end")

        tStockLeft.delete(1.0,"end")

        nSupply=int(eSupply.get())

        OrderHistory=open('OrderHistory','rb')
        aOrderHistory=pickle.load(OrderHistory)
        OrderHistory.close()

        for i in range(0,len(aOrderHistory)):
            if aOrderHistory[i][4]==nSupply:
                aDelivery=aOrderHistory[i]
        
        #Checks order hasn't already been entered
        if aDelivery[5]==False:
            tAlerts.insert(tk.END,"Order already registered")

        else:
            #Registers delivery arrival time
            dNow=datetime.now()
            dString = dNow.strftime("%d/%m/%Y %H:%M")

            aDelivery.append(dString)

            #Sets the delivery active to False
            aDelivery[5]=False

            #Writes new info to external file
            for i in range(0,len(aOrderHistory)):
                if aOrderHistory[i][4]==nSupply:
                    aOrderHistory[i]=aDelivery

            OrderHistory=open('OrderHistory','wb')
            pickle.dump(aOrderHistory,OrderHistory)
            OrderHistory.close()

            conn = sqlite3.connect("Stock_management.db")

            cursor=conn.execute("SELECT CURRENT_STOCK from PRODUCTS where PRODUCT_NAME=?",(aDelivery[1],))

            for row in cursor:
                nStock=row[0]

            nStock=nStock+aDelivery[2]

            conn = sqlite3.connect("Stock_management.db")

            conn.execute("UPDATE PRODUCTS set CURRENT_STOCK = ? where PRODUCT_NAME = ?",(nStock,aDelivery[1]))
            conn.commit()
            conn.close()

            tStockLeft.insert(tk.END,"Stock of "+aDelivery[1]+" remaining:"+str(nStock))
            tAlerts.insert(tk.END,"Succesfully registered "+str(aDelivery[2])+" additional units of "+aDelivery[1])

        
    wStock=tk.Toplevel(wMenu)
    wStock.geometry("1100x125")
    wStock.title("Stock level management")

    tAlerts=tk.Text(master=wStock,height=3,width=60,wrap="word")
    tAlerts.place(x=550,y=0)

    tStockLeft=tk.Text(master=wStock,height=1,width=60)
    tStockLeft.place(x=550,y=60)

    #Entry and buttons for stock level changes
    lOrder=tk.Label(wStock,text="""Enter the number of
    stock leaving warehouse""")
    lOrder.grid(column=0,row=1)

    eOrder=tk.Entry(wStock)
    eOrder.grid(column=1,row=1)

    bOrder=tk.Button(wStock,text="Confirm",command=fDecrease,bg='grey')
    bOrder.grid(column=2,row=1,padx=(0,50))

    lOrder=tk.Label(wStock,text="""Enter the order number of incoming delivery""")
    lOrder.grid(column=0,row=2)

    eSupply=tk.Entry(wStock)
    eSupply.grid(column=1,row=2)

    bSupply=tk.Button(wStock,text="Confirm",command=fIncrease,bg='grey')
    bSupply.grid(column=2,row=2,padx=(0,50))

    aProducts=[]

    conn = sqlite3.connect("Stock_management.db")

    cursor=conn.execute("SELECT PRODUCT_NAME, CURRENT_STOCK, PRODUCT_ACTIVE FROM PRODUCTS")

    aProducts=[] 
    for row in cursor:
        aProduct=[]
        aProduct.append(row[0])
        aProduct.append(row[1])
        aProduct.append(row[2])
        aProducts.append(aProduct)

    aProductNames=[]

    for i in range(0,len(aProducts)):
        if aProducts[i][2]!=0:
            aProductNames.append(aProducts[i][0])

        elif aProducts[i][2]==0 and aProducts[i][1]>0:
            aProductNames.append(aProducts[i][0])

    aProductNames.sort()   

    conn.close()
        
    #Drop down list to select products
    cProduct=ttk.Combobox(wStock,width=35,height=1,values=aProductNames)
    cProduct.grid(column=1,row=0)

    lProduct=tk.Label(wStock,text="Select the outgoing product")
    lProduct.grid(column=0,row=0)

    wStock.mainloop()


def fDataViewer():

    def fSSearch():

        tData.delete(1.0,"end")
        
        sSupplier=(cSupplier.get())
        
        conn=sqlite3.connect("Stock_management.db")

        cursor=conn.execute("SELECT * FROM SUPPLIERS where SUPPLIER_NAME = ?",(sSupplier,))

        aInfo=[["Supplier ID: "],["Supplier Name: "],["Address: "],["Email: "]]

        for row in cursor:
            aInfo[0].append(row[0])
            aInfo[1].append(row[1])
            aInfo[2].append(row[2])
            aInfo[3].append(row[3])
      
        conn.close()
        #Array looks like [["Supplier ID: ",5],["Supplier Name: ","A Name"],["Address: ","46 Street"],["Email: ","Address@email.com].
        #Array is the same format for products but just with product info.
        
        #Outputs the requested info line by line by cycling through array
        for i in range(0,len(aInfo)):
            tData.insert(tk.END,str(aInfo[i][0])+str(aInfo[i][1])+"\n")
        

    def fPSearch():

        tData.delete(1.0,"end")
        
        product=(cProduct.get())
        
        conn=sqlite3.connect("Stock_management.db")

        cursor=conn.execute("SELECT * FROM PRODUCTS where PRODUCT_NAME = ?",(product,))

        aInfo=[["Product ID: "],["Product Name: "],["Supplier ID: "],["Current Stock: "],["Product Life(Days): "],["Storage Location: "],["Sale Price: "],["Unit cost: "],["Critical stock level: "]]

        for row in cursor:
            aInfo[0].append(row[0])
            aInfo[1].append(row[1])
            aInfo[2].append(row[2])
            aInfo[3].append(row[3])
            aInfo[4].append(row[4])
            aInfo[5].append(row[5])
            aInfo[6].append(row[6])
            aInfo[7].append(row[7])
            aInfo[8].append(row[8])

            aInfo[7][1]='%.2f' % (aInfo[7][1])
            aInfo[6][1]='%.2f' % (aInfo[6][1])

        
        conn.close()

        #Outputs the requested info line by line by cycling through array
        for i in range(0,len(aInfo)):
            tData.insert(tk.END,str(aInfo[i][0])+str(aInfo[i][1])+"\n")

        
        
    wPData=tk.Toplevel(wMenu)
    wPData.geometry("700x300")
    wPData.title("Database viewer")

    aProducts=[]
    aSuppliers=[]

    conn = sqlite3.connect("Stock_management.db")

    #Only allows non deleted products/suppliers to be selected.
    cursor=conn.execute("SELECT PRODUCT_NAME FROM PRODUCTS where PRODUCT_ACTIVE=1")

    for row in cursor:
        aProducts.append(row[0])

    cursor=conn.execute("SELECT SUPPLIER_NAME FROM SUPPLIERS where SUPPLIER_ACTIVE=1")

    for row in cursor:
        aSuppliers.append(row[0]) 

    conn.close()

    aSuppliers.sort()
    aProducts.sort()

    lProduct=tk.Label(wPData,text="Products:")
    lProduct.grid(column=0,row=2)

    cProduct=ttk.Combobox(wPData,width=35,height=1,values=aProducts)
    cProduct.grid(column=1,row=2,padx=(0,50))

    bPSearch=tk.Button(wPData,text="Search",command=fPSearch,bg='grey')
    bPSearch.grid(column=1,row=3,padx=(0,50))

    lSupplier=tk.Label(wPData,text="Suppliers:")
    lSupplier.grid(column=2,row=2)

    cSupplier=ttk.Combobox(wPData,width=35,height=1,values=aSuppliers)
    cSupplier.grid(column=3,row=2)

    bSSearch=tk.Button(wPData,text="Search",command=fSSearch,bg='grey')
    bSSearch.grid(column=3,row=3)

    tData=tk.Text(master=wPData,height=9,width=50,wrap="word")
    tData.place(x=140,y=75)

    wPData.mainloop()

def fOrderHistory():
    wOrderHistory=tk.Tk()
    wOrderHistory.geometry("825x300")
    wOrderHistory.title("Order History")

    lOrder=tk.Label(wOrderHistory,text="Order Time",font='bold')
    lOrder.grid(column=0,row=0,padx=10)

    lProduct=tk.Label(wOrderHistory,text="Product Ordered",font='bold')
    lProduct.grid(column=1,row=0,padx=10)

    lUnits=tk.Label(wOrderHistory,text="Quantity",font='bold')
    lUnits.grid(column=2,row=0,padx=10)

    lCost=tk.Label(wOrderHistory,text="Cost",font='bold')
    lCost.grid(column=3,row=0,padx=10)

    lNumber=tk.Label(wOrderHistory,text="Order Number",font='bold')
    lNumber.grid(column=4,row=0,padx=10)

    lOut=tk.Label(wOrderHistory,text="Waiting For Delivery",font='bold')
    lOut.grid(column=5,row=0,padx=10)

    lArrive=tk.Label(wOrderHistory,text="Arrival Time",font='bold')
    lArrive.grid(column=6,row=0,padx=10)

    OrderHistory=open('OrderHistory','rb')
    aOrderHistory=pickle.load(OrderHistory)
    OrderHistory.close()

    #Array is reversed so most recent orders appear at the top
    aReverse=[]
    for i in range(0,len(aOrderHistory)):
        aReverse.append(aOrderHistory[len(aOrderHistory)-1-i])

    aOrderHistory=aReverse

    for i in range(0,len(aOrderHistory)):
        for j in range(0,len(aOrderHistory[i])):
            if j==2:
                sText=str(aOrderHistory[i][j])+" units"

            elif j==3:
                sText="£"+str(aOrderHistory[i][j])

            else:
                sText=str(aOrderHistory[i][j])

            label=tk.Label(master=wOrderHistory,text=sText)
            label.grid(column=j,row=i+1)

    wOrderHistory.mainloop()

    
def fOrderReset():

    def fReset():

        #Resets order history by dumping a new file with one test order in it.

        dNow=datetime.now()
        dString = dNow.strftime("%d/%m/%Y %H:%M")

        aOrderHistory=[]

        OrderHistory=open('OrderHistory','wb')
        pickle.dump(aOrderHistory,OrderHistory)
        OrderHistory.close()

        nNextOrder=1

        NextOrder=open('NextOrder','wb')
        pickle.dump(nNextOrder,NextOrder)
        NextOrder.close()

        bResetOrders=tk.Button(text="Reset the order history",width=20,height=10,command=fOrderReset,bg='yellow')
        bResetOrders.grid(column=5,row=2,padx=(0,50))

    bSure=tk.Button(master=wMenu,text="Click to confirm",width=20,height=10,command=fReset,bg='grey')
    bSure.grid(column=5,row=2,padx=(0,50))

def fAddProduct():

    def fAdd():
        aID=[]

        conn = sqlite3.connect("Stock_management.db")

        #Find the largest current product ID and uses the next number up for the new product
        cursor=conn.execute("SELECT PRODUCT_ID FROM PRODUCTS")

        for row in cursor:
            aID.append(row[0])

        conn.close()

        aID.sort()

        nProdID=aID[-1]+1

        aSuppliers=[]

        conn = sqlite3.connect("Stock_management.db")

        cursor=conn.execute("SELECT SUPPLIER_NAME, SUPPLIER_ID FROM SUPPLIERS")

        for row in cursor:
            aSupplier=[]
            aSupplier.append(row[0])
            aSupplier.append(row[1])
            aSuppliers.append(aSupplier)

        conn.close()

        sSupplier=(cSupplier.get())

        for i in range(0,len(aSuppliers)):
            if sSupplier==aSuppliers[i][0]:
                nSupID=aSuppliers[i][1]
                break

        #Fetching entered info
        sName=str((eName.get()))
        nStock=int((eStock.get()))
        nLife=int((eLife.get()))
        sStorage=str((eStorage.get()))
        nSale=(eSale.get())
        nUnit=(eUnit.get())
        nCritical=int((eCritical.get()))

        conn = sqlite3.connect("Stock_management.db")

        conn.execute("INSERT INTO PRODUCTS (PRODUCT_ID,PRODUCT_NAME,SUPPLIER_ID,CURRENT_STOCK,PRODUCT_LIFE,STORAGE_LOCATION,SALE_PRICE,UNIT_COST,CRITICAL_STOCK,PRODUCT_ACTIVE,PRODUCT_REORDER)\
        VALUES(?,?,?,?,?,?,?,?,?,1,1)",(nProdID,sName,nSupID,nStock,nLife,sStorage,nSale,nUnit,nCritical));

        conn.commit()
        conn.close()

        tAlerts.delete(1.0,"end")
        tAlerts.insert(tk.END,"Succesfully added record")

    def fRestore():
        #Just takes selected record and sets its active column back to 1
        sRestore=(cRestore.get())

        conn = sqlite3.connect('Stock_management.db')
        conn.execute("UPDATE PRODUCTS set PRODUCT_ACTIVE = 1 where PRODUCT_NAME = ?",(sRestore,))
        conn.commit()
        conn.close()

        tAlerts.delete(1.0,"end")
        tAlerts.insert(tk.END,"Succesfully restored "+sRestore)

    wAddProduct=tk.Tk()
    wAddProduct.geometry("500x300")
    wAddProduct.title("Add a product")

    lRestore=tk.Label(wAddProduct,text="Restore a deleted product:")
    lRestore.grid(column=3,row=1)

    conn = sqlite3.connect("Stock_management.db")

    cursor=conn.execute("SELECT PRODUCT_NAME FROM PRODUCTS where PRODUCT_ACTIVE=0")

    #Array of deleted products that can be restored
    aDeletedProd=[]
    for row in cursor:
        aDeletedProd.append(row[0])

    conn.close()

    cRestore=ttk.Combobox(wAddProduct,width=17,height=1,values=aDeletedProd)
    cRestore.grid(column=3,row=2)

    bRestore=tk.Button(wAddProduct,width=17,height=1,text="Restore",command=fRestore,bg='grey')
    bRestore.grid(column=3,row=3)

    tAlerts=tk.Text(wAddProduct,height=2,width=30,wrap="word")
    tAlerts.place(x=237,y=70)

    lName=tk.Label(wAddProduct,text="Product Name:")
    lName.grid(column=0,row=1)
    eName=tk.Entry(wAddProduct)
    eName.grid(column=1,row=1)

    lSupplier=tk.Label(wAddProduct,text="Supplier:")
    lSupplier.grid(column=0,row=2)

    aSuppliers=[]

    conn = sqlite3.connect("Stock_management.db")

    cursor=conn.execute("SELECT SUPPLIER_NAME FROM SUPPLIERS")

    for row in cursor:
        aSuppliers.append(row[0])

    conn.close()

    aSuppliers.sort()

    cSupplier=ttk.Combobox(wAddProduct,width=17,height=1,values=aSuppliers)
    cSupplier.grid(column=1,row=2)

    lStock=tk.Label(wAddProduct,text="Current Stock:")
    lStock.grid(column=0,row=3)
    eStock=tk.Entry(wAddProduct)
    eStock.grid(column=1,row=3)

    lLife=tk.Label(wAddProduct,text="Product Life:")
    lLife.grid(column=0,row=4)
    eLife=tk.Entry(wAddProduct)
    eLife.grid(column=1,row=4)

    lStorage=tk.Label(wAddProduct,text="Storage Location:")
    lStorage.grid(column=0,row=5)
    eStorage=tk.Entry(wAddProduct)
    eStorage.grid(column=1,row=5) 

    lSale=tk.Label(wAddProduct,text="Sale Price:")
    lSale.grid(column=0,row=6)
    eSale=tk.Entry(wAddProduct)
    eSale.grid(column=1,row=6)    

    lUnit=tk.Label(wAddProduct,text="Unit Price:")
    lUnit.grid(column=0,row=7)
    eUnit=tk.Entry(wAddProduct)
    eUnit.grid(column=1,row=7)

    lCritical=tk.Label(wAddProduct,text="Critical Stock:")
    lCritical.grid(column=0,row=8)
    eCritical=tk.Entry(wAddProduct)
    eCritical.grid(column=1,row=8)

    bAdd=tk.Button(wAddProduct,text="Add new product",width=17,height=1,command=fAdd,bg='grey')
    bAdd.grid(column=1,row=9)

def fDelProduct():

    def fDelete():
        #Just takes selected record and sets its active to 0
        sProduct=(cProducts.get())
        
        conn = sqlite3.connect('Stock_management.db')
        conn.execute("UPDATE PRODUCTS set PRODUCT_ACTIVE = 0 where PRODUCT_NAME = ?",(sProduct,))
        conn.commit()
        conn.close()

        tAlerts.delete(1.0,"end")
        tAlerts.insert(tk.END,"Succesfully deleted "+sProduct+". If this was a mistake go to add a product then restore a product.")

    wDelProduct=tk.Tk()
    wDelProduct.geometry("175x175")
    wDelProduct.title("Delete a product")
    
    conn = sqlite3.connect("Stock_management.db")

    cursor=conn.execute("SELECT PRODUCT_NAME FROM PRODUCTS where PRODUCT_ACTIVE=1")

    aProducts=[]
    for row in cursor:
        aProducts.append(row[0])

    aProducts.sort()
        
    lDelete=tk.Label(wDelProduct,text="Select a product to delete:")
    lDelete.grid(column=0,row=0)

    cProducts=ttk.Combobox(wDelProduct,width=20,height=1,values=aProducts)
    cProducts.grid(column=0,row=1)

    bDelete=tk.Button(wDelProduct,width=8,height=1,command=fDelete,text="Confirm",bg='grey')
    bDelete.grid(column=0,row=2)

    tAlerts=tk.Text(wDelProduct,height=6,width=20,wrap="word")
    tAlerts.grid(column=0,row=3)
        
def fPlaceOrder():

    def fOrder():

        nOrder=int(eAmount.get())
        sProduct=(cProducts.get())

        aStocks=[]

        conn = sqlite3.connect("Stock_management.db")

        cursor=conn.execute("SELECT PRODUCT_NAME, CURRENT_STOCK, SUPPLIER_ID, CRITICAL_STOCK, UNIT_COST, PRODUCT_ACTIVE, PRODUCT_REORDER from PRODUCTS where PRODUCT_NAME=?",(sProduct,))
        aProduct=[]
        for row in cursor:
            aProduct.append(row[0])
            aProduct.append(row[1])
            aProduct.append(row[2])
            aProduct.append(row[3])
            aProduct.append(row[4])
            aProduct.append(row[5])
            aProduct.append(row[6])

        conn.close()

        #If the product is active the order process will begin
        if aProduct[5]==1:

            bValid=True

            OrderHistory=open('OrderHistory','rb')
            aOrderHistory=pickle.load(OrderHistory)
            OrderHistory.close()

            aCurrentOrders=[]

            #Finds any currently active orders for the selected product
            for i in range(0,len(aOrderHistory)):
                if aOrderHistory[i][5]==True and aOrderHistory[i][1]==sProduct:
                    aCurrentOrders.append(aOrderHistory[i])

            if aCurrentOrders!=[]:
                #If there is already an active order the user is informed and given an option to make a second order
                def fSecondOrder():
                    bSecondConfirm.destroy()
                    conn = sqlite3.connect("Stock_management.db")

                    fSendEmail(nOrder,aProduct)

                    tAlerts.delete(1.0,"end")
                    tAlerts.insert(tk.END,"Automatically ordered "+str(nOrder)+" units of "+sProduct+".")
                    
                    
                bSecondConfirm=tk.Button(wPlaceOrder,text="Confirm Second Order",command=fSecondOrder)
                bSecondConfirm.grid(column=2,row=4)
                nTotOrder=0
                for i in range(0,len(aCurrentOrders)):
                    nTotOrder=nTotOrder+aCurrentOrders[i][2]

                tAlerts.delete(1.0,"end")
                tAlerts.insert(tk.END,"There is already "+str(len(aCurrentOrders))+" order(s) of this product totalling "+str(nTotOrder)+" units. To proceed with another order press the button below")

            elif bValid==True:

                fSendEmail(nOrder,aProduct)

                tAlerts.delete(1.0,"end")
                tAlerts.insert(tk.END,"Ordered "+str(nOrder)+" units of "+sProduct+".")

        else:
            tAlerts.delete(1.0,"end")
            tAlerts.insert(tk.END,"Product is not active. Go to add a product option to restore an old product.")


                            
    wPlaceOrder=tk.Tk()
    wPlaceOrder.geometry("900x100")
    wPlaceOrder.title("Place Manual Order")
    
    conn = sqlite3.connect("Stock_management.db")

    cursor=conn.execute("SELECT PRODUCT_NAME FROM PRODUCTS where PRODUCT_ACTIVE=1")

    aProducts=[]
    for row in cursor:
        aProducts.append(row[0])

    aProducts.sort()
    
    cProducts=ttk.Combobox(wPlaceOrder,width=36,height=1,values=aProducts)
    cProducts.grid(column=1,row=0)

    lProduct=tk.Label(wPlaceOrder,text="Select product to order:")
    lProduct.grid(column=0,row=0)

    lAmount=tk.Label(wPlaceOrder,text="Select amount to order:")
    lAmount.grid(column=0,row=1)

    eAmount=tk.Entry(wPlaceOrder)
    eAmount.grid(column=1,row=1)

    tAlerts=tk.Text(master=wPlaceOrder,height=4,width=60,wrap="word")
    tAlerts.place(x=375,y=0)

    bConfirm=tk.Button(wPlaceOrder,text="Place Order",command=fOrder,bg='grey',fg='black')
    bConfirm.grid(column=1,row=2)

def fAddSupplier():

    def fAdd():
        aID=[]

        conn = sqlite3.connect("Stock_management.db")

        #Takes highest supplier ID and adds 1 for new supplier ID
        cursor=conn.execute("SELECT SUPPLIER_ID FROM SUPPLIERS")

        for row in cursor:
            aID.append(row[0])

        conn.close()

        aID.sort()

        nSupID=aID[-1]+1

        sName=str((eName.get()))
        sAddress=str(eAddress.get())
        sEmail=str(eEmail.get())

        conn = sqlite3.connect("Stock_management.db")

        conn.execute("INSERT INTO SUPPLIERS (SUPPLIER_ID,SUPPLIER_NAME,ADDRESS,EMAIL_ADDRESS,SUPPLIER_ACTIVE)\
        VALUES(?,?,?,?,1)",(nSupID,sName,sAddress,sEmail));

        conn.commit()
        conn.close()

        tAlerts.delete(1.0,"end")
        tAlerts.insert(tk.END,"Succesfully added record")

    def fRestore():
        #Just takes selected record and sets its active column back to 1
        sRestore=(cRestore.get())

        conn = sqlite3.connect('Stock_management.db')
        conn.execute("UPDATE SUPPLIERS set SUPPLIER_ACTIVE = 1 where SUPPLIER_NAME = ?",(sRestore,))
        conn.commit()
        conn.close()

        tAlerts.delete(1.0,"end")
        tAlerts.insert(tk.END,"Succesfully restored "+sRestore)

    wAddSupplier=tk.Tk()
    wAddSupplier.geometry("400x150")
    wAddSupplier.title("Add a supplier")

    lRestore=tk.Label(wAddSupplier,text="Restore a deleted supplier:")
    lRestore.grid(column=3,row=1)

    conn = sqlite3.connect("Stock_management.db")

    cursor=conn.execute("SELECT SUPPLIER_NAME FROM SUPPLIERS where SUPPLIER_ACTIVE=0")

    aDeletedSup=[]
    for row in cursor:
        aDeletedSup.append(row[0])

    conn.close()

    cRestore=ttk.Combobox(wAddSupplier,width=17,height=1,values=aDeletedSup)
    cRestore.grid(column=3,row=2)

    bRestore=tk.Button(wAddSupplier,width=17,height=1,text="Restore",command=fRestore,bg='grey')
    bRestore.grid(column=3,row=3)

    tAlerts=tk.Text(wAddSupplier,height=2,width=30,wrap="word")
    tAlerts.place(x=0,y=100)

    lName=tk.Label(wAddSupplier,text="Supplier Name:")
    lName.grid(column=0,row=1)
    eName=tk.Entry(wAddSupplier)
    eName.grid(column=1,row=1)

    lAddress=tk.Label(wAddSupplier,text="Address:")
    lAddress.grid(column=0,row=2)
    eAddress=tk.Entry(wAddSupplier)
    eAddress.grid(column=1,row=2)

    lEmail=tk.Label(wAddSupplier,text="Email Address:")
    lEmail.grid(column=0,row=3)
    eEmail=tk.Entry(wAddSupplier)
    eEmail.grid(column=1,row=3)

    bAdd=tk.Button(wAddSupplier,text="Add new supplier",width=17,height=1,command=fAdd,bg='grey')
    bAdd.grid(column=1,row=4)


def fDelSupplier():
        #Just takes selected record and sets its active column to 0

    def fDeleteSupplier():
        sSupplier=(cSuppliers.get())
        
        conn = sqlite3.connect('Stock_management.db')
        conn.execute("UPDATE SUPPLIERS set SUPPLIER_ACTIVE = 0 where SUPPLIER_NAME = ?",(sSupplier,))
        conn.commit()
        conn.close()

        tAlerts.delete(1.0,"end")
        tAlerts.insert(tk.END,"Succesfully deleted "+sSupplier+". If this was a mistake go to add a supplier then restore a supplier")

    wDelSupplier=tk.Tk()
    wDelSupplier.geometry("175x175")
    wDelSupplier.title("Delete a supplier")
    
    conn = sqlite3.connect("Stock_management.db")

    cursor=conn.execute("SELECT SUPPLIER_NAME FROM SUPPLIERS where SUPPLIER_ACTIVE=1")

    aSuppliers=[]
    for row in cursor:
        aSuppliers.append(row[0])

    aSuppliers.sort()

    lDelete=tk.Label(wDelSupplier,text="Select a supplier to delete:")
    lDelete.grid(column=0,row=0)

    cSuppliers=ttk.Combobox(wDelSupplier,width=20,height=1,values=aSuppliers)
    cSuppliers.grid(column=0,row=1)

    bDelete=tk.Button(wDelSupplier,width=8,height=1,command=fDeleteSupplier,text="Confirm",bg='grey')
    bDelete.grid(column=0,row=2)

    tAlerts=tk.Text(wDelSupplier,height=6,width=20,wrap="word")
    tAlerts.grid(column=0,row=3)

def fEmailSetup():

    def fChangeEmail():
        #Checks the entered emails and passwords match up. If they do the pickle file is updated
        sEmail1=(eEmail1.get())
        sEmail2=(eEmail2.get())

        sPassword1=(ePassword1.get())
        sPassword2=(ePassword2.get())

        if sEmail1==sEmail2 and sPassword1==sPassword2:
            aEmailSetup=[sEmail1,sPassword1]

            EmailPass=open('EmailPass','wb')
            pickle.dump(aEmailSetup,EmailPass)
            EmailPass.close()

            tAlerts.delete(1.0,"end")
            tAlerts.insert(tk.END,("Succesfully setup new password"))

        else:
            tAlerts.delete(1.0,"end")
            tAlerts.insert(tk.END,("Emails or Passwords did not match"))
            

    wEmailSetup=tk.Tk()
    wEmailSetup.geometry("600x150")
    wEmailSetup.title("EmailSetup")
    
    lEmail1=tk.Label(wEmailSetup,text="Enter New Email Address:")
    lEmail1.grid(column=0,row=0)
    eEmail1=tk.Entry(wEmailSetup)
    eEmail1.grid(column=1,row=0)

    lEmail2=tk.Label(wEmailSetup,text="Enter Email Address Again:")
    lEmail2.grid(column=0,row=1)
    eEmail2=tk.Entry(wEmailSetup)
    eEmail2.grid(column=1,row=1)

    lPassword1=tk.Label(wEmailSetup,text="Enter Password For Email Account:")
    lPassword1.grid(column=0,row=2)
    ePassword1=tk.Entry(wEmailSetup)
    ePassword1.grid(column=1,row=2)

    lPassword2=tk.Label(wEmailSetup,text="Enter Password Again:")
    lPassword2.grid(column=0,row=3)
    ePassword2=tk.Entry(wEmailSetup)
    ePassword2.grid(column=1,row=3)

    bAdd=tk.Button(wEmailSetup,text="Confirm Setup of Email",width=17,height=1,command=fChangeEmail,bg='grey')
    bAdd.grid(column=1,row=4)

    tAlerts=tk.Text(master=wEmailSetup,height=5,width=30,wrap="word")
    tAlerts.place(x=350,y=0)

def fAutoReorder():

        #When the button is pressed the value in the pickle file changes and the colour and text of the button changes.
        AutoReorder=open('AutoReorder','rb')
        nAutoReorder=pickle.load(AutoReorder)
        AutoReorder.close()

        if nAutoReorder==1:
            nAutoReorder=0
            bAutoReorder['text']="Turn auto reorder on"
            bAutoReorder.configure(bg = 'red')
            bAutoReorder.configure(fg = 'white')

        else:
            nAutoReorder=1
            bAutoReorder['text']="Turn auto reorder off"
            bAutoReorder.configure(bg = 'dark green')
            bAutoReorder.configure(fg = 'white')

        AutoReorder=open('AutoReorder','wb')
        pickle.dump(nAutoReorder,AutoReorder)
        AutoReorder.close()

def fProdEdit():
    
    def fPSearch():

        tData.delete(1.0,"end")
        
        product=(cProduct.get())
        
        conn=sqlite3.connect("Stock_management.db")

        cursor=conn.execute("SELECT * FROM PRODUCTS where PRODUCT_NAME = ?",(product,))

        aInfo=[["Product ID: "],["Product Name: "],["Supplier ID: "],["Current Stock: "],["Product Life(Days): "],["Storage Location: "],["Sale Price: "],["Unit cost: "],["Critical stock level: "]]

        for row in cursor:
            aInfo[0].append(row[0])
            aInfo[1].append(row[1])
            aInfo[2].append(row[2])
            aInfo[3].append(row[3])
            aInfo[4].append(row[4])
            aInfo[5].append(row[5])
            aInfo[6].append(row[6])
            aInfo[7].append(row[7])
            aInfo[8].append(row[8])

            aInfo[7][1]='%.2f' % (aInfo[7][1])
            aInfo[6][1]='%.2f' % (aInfo[6][1])

        
        conn.close()

        for i in range(0,len(aInfo)):
            tData.insert(tk.END,str(aInfo[i][0])+str(aInfo[i][1])+"\n")

    #Each function corresponds to a different window in which a different value can be edited.
    def fEditName():
        def fChangeName():
            sName=(eName.get())
            sProduct=(cProduct.get())

            conn = sqlite3.connect('Stock_management.db')
            conn.execute("UPDATE PRODUCTS set PRODUCT_NAME = ? where PRODUCT_NAME = ?",(sName,sProduct))
            conn.commit()
            conn.close()
            #Windows need to be force closed to prevent errors with newly changed data
            wEditPName.destroy()
            wEditPData.destroy()

        wEditPName=tk.Toplevel(wEditPData)
        wEditPName.geometry("200x100")
        wEditPName.title("Edit product name")

        lName=tk.Label(wEditPName,text="Enter new product name:")
        lName.place(x=0,y=0)

        eName=tk.Entry(wEditPName)
        eName.place(x=0,y=20)

        bName=tk.Button(wEditPName,text="Confirm name change",command=fChangeName,bg='grey')
        bName.place(x=0,y=40)

    def fEditLife():
        def fChangeLife():
            nLife=int((eLife.get()))
            sProduct=(cProduct.get())

            conn = sqlite3.connect('Stock_management.db')
            conn.execute("UPDATE PRODUCTS set PRODUCT_LIFE = ? where PRODUCT_NAME = ?",(nLife,sProduct))
            conn.commit()
            conn.close()
            wEditLife.destroy()
            wEditPData.destroy()

        wEditLife=tk.Toplevel(wEditPData)
        wEditLife.geometry("200x100")
        wEditLife.title("Edit product life")

        lLife=tk.Label(wEditLife,text="Enter new product life:")
        lLife.place(x=0,y=0)

        eLife=tk.Entry(wEditLife)
        eLife.place(x=0,y=20)

        bLife=tk.Button(wEditLife,text="Confirm product life change",command=fChangeLife,bg='grey')
        bLife.place(x=0,y=40)

    def fEditLocation():
        def fChangeLocation():
            sLocation=eLocation.get()
            sProduct=cProduct.get()

            conn = sqlite3.connect('Stock_management.db')
            conn.execute("UPDATE PRODUCTS set STORAGE_LOCATION = ? where PRODUCT_NAME = ?",(sLocation,sProduct))
            conn.commit()
            conn.close()
            wEditLocation.destroy()
            wEditPData.destroy()

        wEditLocation=tk.Toplevel(wEditPData)
        wEditLocation.geometry("200x100")
        wEditLocation.title("Edit storage location")

        lLocation=tk.Label(wEditLocation,text="Enter new storage location:")
        lLocation.place(x=0,y=0)

        eLocation=tk.Entry(wEditLocation)
        eLocation.place(x=0,y=20)

        bLocation=tk.Button(wEditLocation,text="Confirm location change",command=fChangeLocation,bg='grey')
        bLocation.place(x=0,y=40)

    def fEditSale():
        def fChangeSale():
            sSale=eSale.get()
            sProduct=cProduct.get()

            conn = sqlite3.connect('Stock_management.db')
            conn.execute("UPDATE PRODUCTS set SALE_PRICE = ? where PRODUCT_NAME = ?",(sSale,sProduct))
            conn.commit()
            conn.close()
            wEditSale.destroy()
            wEditPData.destroy()

        wEditSale=tk.Toplevel(wEditPData)
        wEditSale.geometry("200x100")
        wEditSale.title("Edit sale price")

        lSale=tk.Label(wEditSale,text="Enter new sale price:")
        lSale.place(x=0,y=0)

        eSale=tk.Entry(wEditSale)
        eSale.place(x=0,y=20)

        bSale=tk.Button(wEditSale,text="Confirm price change",command=fChangeSale,bg='grey')
        bSale.place(x=0,y=40)

    def fEditUnit():
        def fChangeUnit():
            sUnit=eUnit.get()
            sProduct=cProduct.get()

            conn = sqlite3.connect('Stock_management.db')
            conn.execute("UPDATE PRODUCTS set UNIT_COST = ? where PRODUCT_NAME = ?",(sUnit,sProduct))
            conn.commit()
            conn.close()
            wEditUnit.destroy()
            wEditPData.destroy()

        wEditUnit=tk.Toplevel(wEditPData)
        wEditUnit.geometry("200x100")
        wEditUnit.title("Edit unit cost")

        lUnit=tk.Label(wEditUnit,text="Enter new unit cost:")
        lUnit.place(x=0,y=0)

        eUnit=tk.Entry(wEditUnit)
        eUnit.place(x=0,y=20)

        bUnit=tk.Button(wEditUnit,text="Confirm unit cost change",command=fChangeUnit,bg='grey')
        bUnit.place(x=0,y=40)

    def fEditCritical():
        def fChangeCritical():
            nCritical=int(eCritical.get())
            sProduct=cProduct.get()

            conn = sqlite3.connect('Stock_management.db')
            conn.execute("UPDATE PRODUCTS set CRITICAL_STOCK = ? where PRODUCT_NAME = ?",(nCritical,sProduct))
            conn.commit()
            conn.close()
            wEditCritical.destroy()
            wEditPData.destroy()

        wEditCritical=tk.Toplevel(wEditPData)
        wEditCritical.geometry("200x100")
        wEditCritical.title("Edit critical stock")

        lCritical=tk.Label(wEditCritical,text="Enter new critical stock:")
        lCritical.place(x=0,y=0)

        eCritical=tk.Entry(wEditCritical)
        eCritical.place(x=0,y=20)

        bCritical=tk.Button(wEditCritical,text="Confirm critical stock change",command=fChangeCritical,bg='grey')
        bCritical.place(x=0,y=40)

        
    wEditPData=tk.Toplevel(wMenu)
    wEditPData.geometry("560x300")
    wEditPData.title("Database viewer")

    aProducts=[]
    aSuppliers=[]

    conn = sqlite3.connect("Stock_management.db")

    cursor=conn.execute("SELECT PRODUCT_NAME FROM PRODUCTS where PRODUCT_ACTIVE=1")

    for row in cursor:
        aProducts.append(row[0])

    conn.close()

    aProducts.sort()

    lProduct=tk.Label(wEditPData,text="Products:")
    lProduct.place(x=25,y=0)

    cProduct=ttk.Combobox(wEditPData,width=35,height=1,values=aProducts)
    cProduct.grid(column=1,row=1)

    bPSearch=tk.Button(wEditPData,text="Search",command=fPSearch,bg='grey')
    bPSearch.grid(column=1,row=2)

    tData=tk.Text(master=wEditPData,height=9,width=50,wrap="word")
    tData.grid(column=1,row=3)

    bName=tk.Button(wEditPData,text="Edit Name",width=20,height=1,command=fEditName)
    bName.place(x=404,y=47)

    bLife=tk.Button(wEditPData,text="Edit Product Life",width=20,height=1,command=fEditLife)
    bLife.place(x=404,y=72)

    bLocation=tk.Button(wEditPData,text="Edit Storage Location",width=20,height=1,command=fEditLocation)
    bLocation.place(x=404,y=97)

    bSale=tk.Button(wEditPData,text="Edit Sale Price",width=20,height=1,command=fEditSale)
    bSale.place(x=404,y=122)

    bUnit=tk.Button(wEditPData,text="Edit Unit Cost",width=20,height=1,command=fEditUnit)
    bUnit.place(x=404,y=147)

    bCritical=tk.Button(wEditPData,text="Edit Critical Stock",width=20,height=1,command=fEditCritical)
    bCritical.place(x=404,y=172)

    wEditPData.mainloop()

def fSupEdit():
#Supplier edits follow exactly same format as product edits
    def fSSearch():
        tData.delete(1.0,"end")
            
        sSupplier=(cSupplier.get())
            
        conn=sqlite3.connect("Stock_management.db")

        cursor=conn.execute("SELECT * FROM SUPPLIERS where SUPPLIER_NAME = ?",(sSupplier,))

        aInfo=[["Supplier ID: "],["Supplier Name: "],["Address: "],["Email: "]]

        for row in cursor:
            aInfo[0].append(row[0])
            aInfo[1].append(row[1])
            aInfo[2].append(row[2])
            aInfo[3].append(row[3])
          
        conn.close()

        for i in range(0,len(aInfo)):
                tData.insert(tk.END,str(aInfo[i][0])+str(aInfo[i][1])+"\n")

    def fEditName():
        def fChangeName():
            sName=(eName.get())
            sSupplier=(cSupplier.get())

            conn = sqlite3.connect('Stock_management.db')
            conn.execute("UPDATE SUPPLIERS set SUPPLIER_NAME = ? where SUPPLIER_NAME = ?",(sName,sSupplier))
            conn.commit()
            conn.close()
            wEditSName.destroy()
            wEditSData.destroy()

        wEditSName=tk.Toplevel(wEditSData)
        wEditSName.geometry("200x100")
        wEditSName.title("Edit Supplier name")

        lName=tk.Label(wEditSName,text="Enter new supplier name:")
        lName.place(x=0,y=0)

        eName=tk.Entry(wEditSName)
        eName.place(x=0,y=20)

        bName=tk.Button(wEditSName,text="Confirm name change",command=fChangeName,bg='grey')
        bName.place(x=0,y=40)

    def fEditAddress():
        def fChangeAddress():
            sAddress=(eAddress.get())
            sSupplier=(cSupplier.get())

            conn = sqlite3.connect('Stock_management.db')
            conn.execute("UPDATE SUPPLIERS set ADDRESS = ? where SUPPLIER_NAME = ?",(sAddress,sSupplier))
            conn.commit()
            conn.close()
            wEditSAddress.destroy()
            wEditSData.destroy()

        wEditSAddress=tk.Toplevel(wEditSData)
        wEditSAddress.geometry("200x100")
        wEditSAddress.title("Edit Supplier Address")

        lAddress=tk.Label(wEditSAddress,text="Enter new supplier address:")
        lAddress.place(x=0,y=0)

        eAddress=tk.Entry(wEditSAddress)
        eAddress.place(x=0,y=20)

        bAddress=tk.Button(wEditSAddress,text="Confirm address change",command=fChangeAddress,bg='grey')
        bAddress.place(x=0,y=40)

    def fEditEmail():
        def fChangeEmail():
            sEmail=(eEmail.get())
            sSupplier=(cSupplier.get())

            conn = sqlite3.connect('Stock_management.db')
            conn.execute("UPDATE SUPPLIERS set EMAIL_ADDRESS = ? where SUPPLIER_NAME = ?",(sEmail,sSupplier))
            conn.commit()
            conn.close()
            wEditSEmail.destroy()
            wEditSData.destroy()
            
        wEditSEmail=tk.Toplevel(wEditSData)
        wEditSEmail.geometry("200x100")
        wEditSEmail.title("Edit Supplier Email")

        lEmail=tk.Label(wEditSEmail,text="Enter new supplier email:")
        lEmail.place(x=0,y=0)

        eEmail=tk.Entry(wEditSEmail)
        eEmail.place(x=0,y=20)

        bEmail=tk.Button(wEditSEmail,text="Confirm email change",command=fChangeEmail,bg='grey')
        bEmail.place(x=0,y=40)


    wEditSData=tk.Toplevel(wMenu)
    wEditSData.geometry("575x300")
    wEditSData.title("Database viewer")

    aSuppliers=[]

    conn = sqlite3.connect("Stock_management.db")

    cursor=conn.execute("SELECT SUPPLIER_NAME FROM SUPPLIERS where SUPPLIER_ACTIVE=1")

    for row in cursor:
        aSuppliers.append(row[0])

    conn.close()

    aSuppliers.sort()

    lSupplier=tk.Label(wEditSData,text="Suppliers:")
    lSupplier.place(x=25,y=0)

    cSupplier=ttk.Combobox(wEditSData,width=35,height=1,values=aSuppliers)
    cSupplier.grid(column=1,row=1)

    bSSearch=tk.Button(wEditSData,text="Search",command=fSSearch,bg='grey')
    bSSearch.grid(column=1,row=2)

    tData=tk.Text(master=wEditSData,height=9,width=50,wrap="word")
    tData.grid(column=1,row=3)

    bName=tk.Button(wEditSData,text="Edit Name",width=20,height=1,command=fEditName)
    bName.place(x=404,y=47)

    bAddress=tk.Button(wEditSData,text="Edit Address",width=20,height=1,command=fEditAddress)
    bAddress.place(x=404,y=72)

    bEmail=tk.Button(wEditSData,text="Edit Email",width=20,height=1,command=fEditEmail)
    bEmail.place(x=404,y=97)


wMenu=tk.Tk()
wMenu.geometry("1250x300")
wMenu.title("Menu")

bLevelChange=tk.Button(text="Change the stock levels",width=20,height=10,command=fLevelChange,bg='light blue')
bLevelChange.grid(column=0,row=1,padx=(0,50))

bDataViewer=tk.Button(text="View the database records",width=20,height=10,command=fDataViewer,bg='turquoise')
bDataViewer.grid(column=1,row=1,padx=(0,50))

bOrderHistory=tk.Button(text="View the order history",width=20,height=10,command=fOrderHistory,bg='turquoise')
bOrderHistory.grid(column=1,row=2,padx=(0,50))

bResetOrders=tk.Button(text="Reset the order history",width=20,height=10,command=fOrderReset,bg='yellow')
bResetOrders.grid(column=5,row=2,padx=(0,50))

bAddProduct=tk.Button(text="Add a new product",width=20,height=10,command=fAddProduct,bg='dark orange')
bAddProduct.grid(column=2,row=1)

bDelProduct=tk.Button(text="Delete a product",width=20,height=10,command=fDelProduct,bg='dark orange')
bDelProduct.grid(column=3,row=1)

bPlaceOrder=tk.Button(text="Manually place an order",width=20,height=10,command=fPlaceOrder,bg='light blue')
bPlaceOrder.grid(column=0,row=2,padx=(0,50))

bAddSup=tk.Button(text="Add a supplier",width=20,height=10,command=fAddSupplier,bg='dark orange')
bAddSup.grid(column=2,row=2)

bDelSupplier=tk.Button(text="Delete a supplier",width=20,height=10,command=fDelSupplier,bg='dark orange')
bDelSupplier.grid(column=3,row=2)

bEmailSetup=tk.Button(text="Setup or change the email",width=20,height=10,command=fEmailSetup,bg='yellow')
bEmailSetup.grid(column=5,row=1,padx=(0,50))

bAutoReorder=tk.Button(text="Turn auto-reorder on/off",width=20,height=10,command=fAutoReorder)
bAutoReorder.grid(column=6,row=1)

AutoReorder=open('AutoReorder','rb')
nAutoReorder=pickle.load(AutoReorder)
AutoReorder.close()

#Ensures auto reorder button is the right colour on startup.
if nAutoReorder==1:
    bAutoReorder['text']="Turn auto reorder off"
    bAutoReorder.configure(bg = 'dark green')
    bAutoReorder.configure(fg = 'white')

else:
    bAutoReorder['text']="Turn auto reorder on"
    bAutoReorder.configure(bg = 'red')
    bAutoReorder.configure(fg = 'white')


bProdEdit=tk.Button(text="Edit product data",width=20,height=10,command=fProdEdit,bg='dark orange')
bProdEdit.grid(column=4,row=1,padx=(0,50))

bSupEdit=tk.Button(text="Edit supplier data",width=20,height=10,command=fSupEdit,bg='dark orange')
bSupEdit.grid(column=4,row=2,padx=(0,50))

wMenu.mainloop()




#DATABASE USED IF NEEDED TO RECREATE OR REFERENCE
#NOTE: Insert command for products is missing column names referenced for active and reorder. Supplier phone numbers need to be emails.

#conn= sqlite3.connect("Stock_management.db")

#conn.execute('''CREATE TABLE SUPPLIERS
         #(SUPPLIER_ID   INT   PRIMARY KEY   NOT NULL,
         #SUPPLIER_NAME   TEXT   NOT NULL,
         #ADDRESS   TEXT   NOT NULL,
         #EMAIL_ADDRESS   TEXT   NOT NULL,
         #SUPPLIER_ACTIVE   INT   NOT NULL);''')

#conn.execute('''CREATE TABLE PRODUCTS
            #(PRODUCT_ID   INT   PRIMARY KEY   NOT NULL,
            #PRODUCT_NAME   TEXT   NOT NULL,
            #SUPPLIER_ID   INT   NOT NULL,
            #CURRENT_STOCK   INT   NOT NULL,
            #PRODUCT_LIFE   INT,
            #STORAGE_LOCATION   TEXT   NOT NULL,
            #SALE_PRICE   REAL   NOT NULL,
            #UNIT_COST   REAL   NOT NULL,
            #CRITICAL_STOCK   INT   NOT NULL,
            #PRODUCT_ACTIVE   INT   NOT NULL,
            #PRODUCT_REORDER   INT   NOT NULL,
            #FOREIGN KEY(SUPPLIER_ID) REFERENCES SUPPLIERS(SUPPLIER_ID)
            #);''')

#conn.close()



#INSERT COMMANDS

#conn = sqlite3.connect("Stock_management.db")

#conn.execute("INSERT INTO SUPPLIERS (SUPPLIER_ID,SUPPLIER_NAME,ADDRESS,EMAIL_ADDRESS,SUPPLIER_ACTIVE)\
    #VALUES(1,'Walkers','4 Leycroft Road, Leicester','ukproductorders@gmail.com',1)");

#conn.execute("INSERT INTO SUPPLIERS (SUPPLIER_ID,SUPPLIER_NAME,ADDRESS,EMAIL_ADDRESS,SUPPLIER_ACTIVE)\
    #VALUES(2,'Kettle','12 Harling Road, Norwich','ukproductorders@gmail.com',1)");

#conn.execute("INSERT INTO SUPPLIERS (SUPPLIER_ID,SUPPLIER_NAME,ADDRESS,EMAIL_ADDRESS,SUPPLIER_ACTIVE)\
    #VALUES(3,'Pringles','52 Gambrel Road, Northampton','ukproductorders@gmail.com',1)");

#conn.execute("INSERT INTO PRODUCTS (PRODUCT_ID,PRODUCT_NAME,SUPPLIER_ID,CURRENT_STOCK,PRODUCT_LIFE,STORAGE_LOCATION,SALE_PRICE,UNIT_COST,CRITICAL_STOCK,PRODUCT_ACTIVE,PRODUCT_REORDER)\
    #VALUES(1,'Walkers Ready Salted Crisps',1,200,100,'C1',0.8,0.2,70,1,1)");

#conn.execute("INSERT INTO PRODUCTS (PRODUCT_ID,PRODUCT_NAME,SUPPLIER_ID,CURRENT_STOCK,PRODUCT_LIFE,STORAGE_LOCATION,SALE_PRICE,UNIT_COST,CRITICAL_STOCK,PRODUCT_ACTIVE,PRODUCT_REORDER)\
    #VALUES(2,'Walkers Salt and Vinegar Crisps',1,150,110,'C1',0.8,0.23,60,1,1)");

#conn.execute("INSERT INTO PRODUCTS (PRODUCT_ID,PRODUCT_NAME,SUPPLIER_ID,CURRENT_STOCK,PRODUCT_LIFE,STORAGE_LOCATION,SALE_PRICE,UNIT_COST,CRITICAL_STOCK,PRODUCT_ACTIVE,PRODUCT_REORDER)\
    #VALUES(3,'Walkers Cheese and Onion Crisps',1,230,100,'C1',0.8,0.25,60,1,1)");

#conn.execute("INSERT INTO PRODUCTS (PRODUCT_ID,PRODUCT_NAME,SUPPLIER_ID,CURRENT_STOCK,PRODUCT_LIFE,STORAGE_LOCATION,SALE_PRICE,UNIT_COST,CRITICAL_STOCK,PRODUCT_ACTIVE,PRODUCT_REORDER)\
    #VALUES(4,'Kettle Lightly Salted',2,62,90,'C2',1,0.42,35,1,1)");

#conn.execute("INSERT INTO PRODUCTS (PRODUCT_ID,PRODUCT_NAME,SUPPLIER_ID,CURRENT_STOCK,PRODUCT_LIFE,STORAGE_LOCATION,SALE_PRICE,UNIT_COST,CRITICAL_STOCK,PRODUCT_ACTIVE,PRODUCT_REORDER)\
    #VALUES(5,'Kettle Sea Salt and Balsamic Vinegar',2,32,95,'C2',1.1,0.46,30,1,1)");

#conn.execute("INSERT INTO PRODUCTS (PRODUCT_ID,PRODUCT_NAME,SUPPLIER_ID,CURRENT_STOCK,PRODUCT_LIFE,STORAGE_LOCATION,SALE_PRICE,UNIT_COST,CRITICAL_STOCK,PRODUCT_ACTIVE,PRODUCT_REORDER)\
    #VALUES(6,'Kettle Mature Cheddar and Onion',2,34,80,'C2',1.1,0.41,30,1,1)");

#conn.execute("INSERT INTO PRODUCTS (PRODUCT_ID,PRODUCT_NAME,SUPPLIER_ID,CURRENT_STOCK,PRODUCT_LIFE,STORAGE_LOCATION,SALE_PRICE,UNIT_COST,CRITICAL_STOCK,PRODUCT_ACTIVE,PRODUCT_REORDER)\
    #VALUES(7,'Pringles Original',3,78,120,'C3',1.5,0.62,50,1,1)");

#conn.execute("INSERT INTO PRODUCTS (PRODUCT_ID,PRODUCT_NAME,SUPPLIER_ID,CURRENT_STOCK,PRODUCT_LIFE,STORAGE_LOCATION,SALE_PRICE,UNIT_COST,CRITICAL_STOCK,PRODUCT_ACTIVE,PRODUCT_REORDER)\
    #VALUES(8,'Pringles Salt and Vinegar',3,62,120,'C3',1.5,0.68,40,1,1)");

#conn.execute("INSERT INTO PRODUCTS (PRODUCT_ID,PRODUCT_NAME,SUPPLIER_ID,CURRENT_STOCK,PRODUCT_LIFE,STORAGE_LOCATION,SALE_PRICE,UNIT_COST,CRITICAL_STOCK,PRODUCT_ACTIVE,PRODUCT_REORDER)\
    #VALUES(9,'Pringles Cheese and Onion',3,72,120,'C3',1.5,0.67,40,1,1)");

#conn.commit()
#conn.close()
    
    




