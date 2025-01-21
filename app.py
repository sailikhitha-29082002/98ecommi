from flask import Flask,request,render_template,redirect,url_for,flash,session
from otp import genotp
from cmail import sendmail
from stoken import encode,decode
import os
#import razorpay
import re
from mysql.connector import (connection)  #database and flask connection
import mysql.connector
#mydb=connection.MySQLConnection(user='root',host='localhost',password='admin',db ='ecommi')
user=os.environ.get('RDS_USERNAME')
db=os,environ.get('RDS_DB_NAME')
password=os.environ.get('RDS_PASSWORD')
host=os.environ.get('RDS_HOSTNAME')
port=os.environ,get('RDS_PORT')
with mysql.connector.connect(host=host,port=port,db=db,password=password,user=user) as conn:
    cursor=conn.cursor()
    cursor.execute("CREATE TABLE if not exists usercreate (username varchar(50) NOT NULL,user_email varchar(100) NOT NULL,address text NOT NULL,password varbinary(20) NOT NULL,gender enum('Male','Female') DEFAULT NULL,PRIMARY KEY (user_email),UNIQUE KEY username (username)) ")
    cursor.execute("CREATE TABLE if not exists admincreate (email varchar(50) NOT NULL,username varchar(100) NOT NULL,password varbinary(10) NOT NULL,address text NOT NULL,accept enum('on','off') DEFAULT NULL,dp_image varchar(50) DEFAULT NULL,PRIMARY KEY (email)) ")
    cursor.execute("CREATE TABLE if not exists items (item_id binary(16) NOT NULL,item_name varchar(255) NOT NULL,quantity int unsigned DEFAULT NULL,price decimal(14,4) NOT NULL,category enum('Home_appliances','Electronics','Fashion','Grocery') DEFAULT NULL,image_name varchar(255) NOT NULL,added_by varchar(50) DEFAULT NULL,description longtext,PRIMARY KEY (item_id),KEY added_by (added_by),CONSTRAINT items_ibfk_1 FOREIGN KEY (added_by) REFERENCES admincreate (email) ON DELETE CASCADE ON UPDATE CASCADE) ")
    cursor.execute("CREATE TABLE if not exists  orders (orderid bigint NOT NULL AUTO_INCREMENT,itemid binary(16) DEFAULT NULL,item_name longtext,qty` int DEFAULT NULL,total_price bigint DEFAULT NULL,user varchar(100) DEFAULT NULL,PRIMARY KEY (orderid),KEY user (user),KEY itemid (itemid),CONSTRAINT orders_ibfk_1 FOREIGN KEY (user) REFERENCES usercreate (user_email),CONSTRAINT orders_ibfk_2 FOREIGN KEY (itemid) REFERENCES items (item_id))")
    cursor.execute("CREATE TABLE if not exists reviews (username varchar(30) NOT NULL,itemid binary(16) NOT NULL,title tinytext,review text,rating int DEFAULT NULL,date datetime DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY (itemid,username),KEY username (username),CONSTRAINT reviews_ibfk_1 FOREIGN KEY (itemid) REFERENCES items (item_id) ON DELETE CASCADE ON UPDATE CASCADE,CONSTRAINT reviews_ibfk_2 FOREIGN KEY (username) REFERENCES usercreate (user_email) ON DELETE CASCADE ON UPDATE CASCADE) ")
    cursor.execute("CREATE TABLE if not exists contactus (name varchar(100) DEFAULT NULL,email varchar(100) DEFAULT NULL,message text") 
mydb=mysql.connector.connect(host=host,user=user,port=port,db=db,password=password)
app=Flask(__name__)  #object creation
app.config['SESSION_TYPE']='filesystem' #to store session data
app.secret_key='likhitha@123' #secret key to activate flash messages
RAZORPAY_KEY_ID='rzp_test_BdYxoi5GaEITjc'
RAZORPAY_KEY_SECRET='H0FUH2n4747ZSYBRyCn2D6rc'
#client=razorpay.Client(auth=(RAZORPAY_KEY_ID,RAZORPAY_KEY_SECRET))
@app.route('/')   #by default read method
def home():
    return render_template('welcome.html')  #It will load the template and show in the front-end

@app.route('/index')  #index route creation
def index():
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select bin_to_uuid(item_id),item_name,quantity,price,category,image_name from items')
        items_data=cursor.fetchall() #retrieving all the items from items table
    except Exception as e:
        print(e)
        flash('Could not fetch Items')
        return redirect(url_for('home'))
    else:
        return render_template('index.html',items_data=items_data)
    return render_template('index.html')  #This will show the respective html page.

@app.route('/admincreate', methods=['GET','POST'])  #admin registration GET->Load the page , POST->To accept the data from the user Method not allowed error
def admincreate():
    if request.method == 'POST':
        print (request.form)
        #BAD REQUEST KEY ERROR (if name attribute doesnot match)
        aname=request.form['username'] #mounika [names in brackets are name attribute vales given in admincreate html page]
        aemail=request.form['email'] #bindumounikakanneganti@gmail.com
        apassword=request.form['password'] #123
        address=request.form['address'] #Guntur, AP
        status_accept=request.form['agree'] #agreed to the terms (ON/OFF)
        cursor=mydb.cursor(buffered=True) #open cursor to check if the mailid already exists or not
        cursor.execute('select count(email) from admincreate where email=%s',[aemail]) 
        email_count=cursor.fetchone() #operation is done on aggregate column which gives only one record so we use fetchone().
        if email_count[0]==0: #if the given mail id is not in the database [0 stands for email is not stored in database]
            otp=genotp()  #generating OTP
            admindata={'aname':aname,'aemail':aemail,'password':apassword,'address':address,'accept':status_accept,'aotp':otp} #creating a dictionary to store the data
            subject='BuyRoute Verification Mail'
            body=f'BuyRoute Verification OTP for admin registration {otp}'
            sendmail(to=aemail,subject=subject,body=body)  #Sending mail to the user
            flash('OTP has sent to the given mail')
            return redirect(url_for('otp',padata=encode(data=admindata))) #encoded otp is passed
        elif email_count[0]==1:
            flash('Email already exists')
            return redirect(url_for('adminlogin'))   
    return render_template('admincreate.html')  #This will show the respective html page

@app.route('/otp/<padata>',methods=['GET','POST'])
def otp(padata):
    if request.method == 'POST':
        fotp=request.form['otp'] #user given otp
        try:
            d_data=decode(data=padata) #decoding the tokenised data
            #admindata={'aname':aname,'aemail':aemail,'password':'password','address':address,
            #           'accept':status_accept,'aotp':otp} #creating a dictionary to store
        except Exception as e:
            print(e)
            flash('Something Went Wrong')
            return redirect(url_for('admincreate'))
        else:
            if d_data['aotp']==fotp: #comparing the fotp with generated otp.
                cursor=mydb.cursor(buffered=True)
                cursor.execute('insert into admincreate(email,username,password,address,accept) values(%s,%s,%s,%s,%s)',[d_data['aemail'],d_data['aname'],d_data['password'],d_data['address'],d_data['accept']])
                #fetching the data and storing it in database
                mydb.commit()
                cursor.close()
                flash('Registration Successfull')
                return redirect(url_for('adminlogin')) #it will be redirected to login page on giving the right otp.
            else:
                flash('Otp given is wrong Please Try Again.....') #This message will be displayed if the entered otp is wrong to the users.
                return redirect(url._for('admincreate')) #It will be redirected to admincreate page if the given otp is wrong.
    return render_template('adminotp.html')

@app.route('/adminlogin',methods=['GET','POST']) #route for adminlogin page 
def adminlogin():
    if not session.get('admin'): #creating session
        if request.method=='POST':
            login_email=request.form['email'] #storing the email given
            login_password=request.form['password'] #storing the password given
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select count(email) from admincreate where email=%s',[login_email]) #checking for the email in the database.
                stored_emailcount=cursor.fetchone()
            except Exception as e:
                print(e)
                flash('Connection Error') #if not found display the flash message 
                return redirect(url_for('adminlogin')) #if not matched redirect to the adminlogin page.
            else:
                if stored_emailcount[0]==1:
                    cursor.execute('select password from admincreate where email=%s',[login_email]) #checking for the email in the database
                    stored_password=cursor.fetchone()
                    print(stored_password)
                    if login_password==stored_password[0].decode('utf-8'): # checking if the given password and stored password matches or not
                        print(session) #Before session is created
                        session['admin']=login_email
                        if not session.get(login_email):
                            session[login_email] = {} #creating an empty dictionary with an email in the session
                        print(session)  #After session is created
                        return redirect(url_for('adminpanel')) #if credentials are matched redirect to adminpanel route.
                    else:
                        flash('Password is wrong')
                        return redirect(url_for('adminlogin')) #if credentials don't match redirect to adminlogin route.
                else:
                    flash('Email is wrong')
                    return redirect(url_for('adminlogin'))
        return render_template('adminlogin.html') #loads the adminlogin page when the route is called.
    else:
        return redirect(url_for('adminpanel'))

@app.route('/adminpanel')
def adminpanel():
    if session.get('admin'):
        return render_template('adminpanel.html') #returns the adminpanel when called
    else:
        return redirect(url_for('adminlogin'))

@app.route('/adminforgot',methods=['GET','POST'])
def adminforgot():
    if request.method=='POST':
        forgot_email=request.form['email'] #storing the email given
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(email) from admincreate where email=%s',[forgot_email]) #checking if the email is in the database or not
        stored_email=cursor.fetchone() 
        if stored_email[0]==1: #condition to find if the email is there are not
            subject='Admin reset link for Byroute'
            body=f"Click on the Link for resetting the password: {url_for('ad_password_uodate',token=encode(data=forgot_email),_external=True)}"
            sendmail(to=forgot_email,subject=subject,body=body)
            flash(f'Reset Link has sent to the given {forgot_email}')
            return redirect(url_for('adminforgot'))
        elif stored_email[0]==0:#condition to find if the email is not there are not
            flash('Email is not registered')
            return redirect(url_for('adminlogin'))
    return render_template('forgot.html')

@app.route('/ad_password_update/<token>',methods=['GET','POST'])
def ad_password_uodate(token):
    if request.method=='POST':
        try:
            npassword=request.form['npassword']
            cpassword=request.form['cpassword']
            dtoken=decode(data=token) #detoken the encrypted email
        except Exception as e:
            print(e)
            flash('Something Went Wrong')
            return redirect(url_for('adminlogin'))
        else:
            if npassword==cpassword: #condition to check if the password and confirm password are same
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update admincreate set password=%s where email=%s',[npassword,dtoken]) #password gets updated
                mydb.commit() #after dml command we use commit command to save the changes
                flash('password updated successfully')
                return redirect(url_for('adminlogin'))
            else:
                flash('password mismatch')
                return redirect(url_for('ad_password_update',token=token))
    return render_template('newpassword.html')

@app.route('/additem',methods=['GET','POST'])
def additem():
    if session.get('admin'):
        if request.method=='POST':
            title=request.form['title']
            desc=request.form['Discription']
            price=request.form['price']
            category=request.form['category']
            quantity=request.form['quantity']
            img_file=request.files['file']
            print(img_file.filename.split('.')) 
            img_name=genotp()+'.'+img_file.filename.split('.')[-1] #create filename using user given extension
            '''to store the img in static folder i need to get the path without system varies'''
            drname=os.path.dirname(os.path.abspath(__file__)) # C:\Users\bindu\OneDrive\Desktop\Flask98\Ecommerce
            static_path=os.path.join(drname,'static') # C:\Users\bindu\OneDrive\Desktop\Flask98\Ecommerce\static
            img_file.save(os.path.join(static_path,img_name)) 
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('insert into items(item_id,item_name,description,price,quantity,category,image_name,added_by) values(uuid_to_bin(uuid()),%s,%s,%s,%s,%s,%s,%s)',[title,desc,price,quantity,category,img_name,session.get('admin')])
                mydb.commit()
                cursor.close()
            except Exception as e:
                print(e)
                flah('Connection Error')
                return redirect(url_for('additem'))
            else:
                flash(f'{title[:10]}.. added successfully')
                return redirect(url_for('additem'))
        return render_template('additem.html') #if logged in additem html page will be rendered
    else:
        return redirect(url_for('adminlogin')) #else will redirect to adminlogin route
    
@app.route('/viewallitems')
def viewallitems():
    if session.get('admin'): #if present in the session render to viewall_items page else redirect to adminlogin page.
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select bin_to_uuid(item_id),item_name,image_name from items where added_by=%s',[session.get('admin')]) 
            stored_items=cursor.fetchall() #to look multiple items
        except Exception as e:
            print(e)
            flash('Connection Error')
            return redirect(url_for('adminpanel'))
        else:
            return render_template('viewall_items.html',stored_items=stored_items)
    else:
        return redirect(url_for('adminlogin'))

@app.route('/deleteitem/<item_id>')
def deleteitem(item_id):
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select image_name from items where item_id=uuid_to_bin(%s)',[item_id])
        stored_image=cursor.fetchone()
        drname=os.path.dirname(os.path.abspath(__file__)) # C:\Users\bindu\OneDrive\Desktop\Flask98\Ecommerce
        static_path=os.path.join(drname,'static') # C:\Users\bindu\OneDrive\Desktop\Flask98\Ecommerce\static
        if stored_image in os.listdir(static_path):
            os.remove(os.path.join(static_path,stored_image[0]))
        cursor.execute('delete from items where item_id = uuid_to_bin(%s)',[item_id])
        mydb.commit()
        cursor.close()
    except Exception as e:
        print(e)
        flash('Could not delete item')
        return redirect(url_for('viewallitems'))
    else:
        flash('Item deleted Successfully')
        return redirect(url_for('viewallitems'))

@app.route('/viewitem/<item_id>') #url id passing
def viewitem(item_id): #catch
    if session.get('admin'):
        try:
            cursor=mydb.cursor(buffered=-True)
            cursor.execute('select bin_to_uuid(item_id),item_name,description,price,quantity,category,image_name from items where item_id=uuid_to_bin(%s)',[item_id])
            item_data=cursor.fetchone()
        except Exception as e:
            print(e)
            flash('Connection Error')
            return redirect(url_for('viewallitems'))
        else:
            return render_template('view_item.html',item_data=item_data)
    else:
        return redirect(url_for('adminlogin'))

@app.route('/updateitem/<item_id>',methods=['GET','POST'])
def updateitem(item_id):
    if session.get('admin'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select bin_to_uuid(item_id),item_name,description,price,quantity,category,image_name from items where item_id=uuid_to_bin(%s)',[item_id])
            item_data=cursor.fetchone() #(item_id,item_name)
        except Exception as e:
            print(e)
            flash('Connection Error')
            return redirect(url_for('viewallitems'))
        else:
            if request.method=='POST':
                title=request.form['title']  #Fetching the details
                desc=request.form['Discription']
                price=request.form['price']
                category=request.form['category']
                quantity=request.form['quantity']
                img_file=request.files['file'] #if new file is not uploaded then ''
                filename=img_file.filename #fetch the filename
                print(filename,11)
                if filename == '':
                    img_name=item_data[6] #updating with old name
                else:
                    img_name=genotp()+'.'+filename.split('.')[-1] #creating new filename if new image is uploaded
                    drname=os.path.dirname(os.path.abspath(__file__)) # C:\Users\bindu\OneDrive\Desktop\Flask98\Ecommerce
                    static_path=os.path.join(drname,'static') # C:\Users\bindu\OneDrive\Desktop\Flask98\Ecommerce\static
                    if item_data[6] in os.listdir(static_path):
                        os.remove(os.path.join(static_path,item_data[6]))
                    img_file.save(os.path.join(static_path,img_name))
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update items set item_name=%s,description=%s,price=%s,quantity=%s,category=%s,image_name=%s where item_id=uuid_to_bin(%s)',[title,desc,price,quantity,category,img_name,item_id])
                mydb.commit()
                cursor.close()
                flash('Item Updated Successfully')
                return redirect(url_for('viewitem',item_id=item_id))
            return render_template('update_item.html',data=item_data)                
    else:
        return redirect(url_for('adminlogin'))

@app.route('/adminupdateprofile',methods=['GET','POST'])
def adminupdateprofile():
    if session.get('admin'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select username,address,dp_image from admincreate where email=%s',[session.get('admin')])
            admin_data=cursor.fetchone()
        except Exception as e:
            print(e)
            flash('Something Went Wrong')
            return redirect(url_for('adminpanel'))
        else:
            if request.method=='POST':
                username=request.form['adminname']
                address=request.form['address']
                image_data=request.files['file']
                filename=image_data.filename #method to fetch filename from the data
                print(filename,234)
                if filename == '':
                    image_name=admin_data[2] #if no new image is uploaded then use old image name
                else:
                    image_name=genotp()+'.'+filename.split('.')[-1] #creating new filename
                    drname=os.path.dirname(os.path.abspath(__file__)) # C:\Users\bindu\
                    static_path=os.path.join(drname,'static') # C:\Users\bindu\OneDrive\Desktop\Flask98\Ecommerce\static
                    if admin_data[2] in os.listdir(static_path): #if old image exists in static folder
                        os.remove(os.path.join(static_path,admin_data[2]))
                    else:
                        image_data.save(os.path.join(static_path,image_name)) #saving new file in static
                cursor.execute('update admincreate set username=%s,address=%s,dp_image=%s where email=%s',[username,address,image_name,session.get('admin')])
                mydb.commit()
                cursor.close()
                flash('Profile Updated Successfully')
                return redirect(url_for('adminupdateprofile'))
            return render_template('adminupdate.html',admin_data='admin_data')        
    else:
        return redirect(url_for('adminlogin'))
        
@app.route('/adminlogout')
def adminlogout():
    if session.get('admin'):
        session.pop('admin')
        print('pop',session.get('admin'))
        return redirect(url_for('adminlogin'))
    else:
        return redirect(url_for('adminlogin'))

@app.route('/usercreate',methods=['GET','POST'])
def usercreate():
    if request.method=='POST':
        uname=request.form['name']
        uemail=request.form['email']
        uaddress=request.form['address']
        upassword=request.form['password']
        usergender=request.form['usergender']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(user_email) from usercreate where user_email=%s',[uemail])
        uemail_count=cursor.fetchone()
        if uemail_count[0]==0:
            uotp=genotp()
            userdata={'uname':uname,'uemail':uemail,'upassword':upassword,'uaddress':uaddress,'usergender':usergender,'uotp':uotp}
            subject='TQ for registering in taneemkart'
            body=f'Ecommers verification otp for user regrestation {uotp}'
            sendmail(to=uemail,subject=subject,body=body)
            flash('OTP has sent to given mail')
            return redirect(url_for('uotp',pudata=encode(data=userdata)))
        elif uemail_count[0]==1:
            flash('email already exist please login')
            return redirect(url_for('userlogin'))
    return render_template('usersignup.html')

@app.route('/uotp/<pudata>',methods=['GET','POST'])
def uotp(pudata):
    if request.method=='POST':
        fuotp=request.form['otp']
        try:
            d_udata=decode(data=pudata)
        except Exception as e:
            print(e)
            flash('something went wrong')
            return redirect(url_for('usercreate'))
        else:
            if fuotp==d_udata['uotp']:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('insert into usercreate(user_email,username,password,address,gender) values(%s,%s,%s,%s,%s)',[d_udata['uemail'],d_udata['uname'],d_udata['upassword'],d_udata['uaddress'],d_udata['usergender']])
                mydb.commit()
                cursor.close()
                flash('reg success')
                return redirect(url_for('userlogin'))
            else:
                flash('otp is wrong')
                return redirect(url_for('usercreate'))
    return render_template('userotp.html')

@app.route('/userlogin',methods=['GET','POST'])
def userlogin():
    if not session.get('user'):
        if request.method=='POST':
                log_uemail=request.form['email']
                log_upassword=request.form['password']
                try:
                    cursor=mydb.cursor(buffered=True)
                    cursor.execute('select count(user_email) from usercreate where user_email=%s',[log_uemail])
                    stored_emailcount=cursor.fetchone()
                except Exception as e:
                    print(e)
                    flash('something went wrong connection error')
                    return redirect(url_for('userlogin'))
                else:
                    if stored_emailcount[0]==1:
                        cursor.execute('select password from usercreate where user_email=%s',[log_uemail])
                        stored_password=cursor.fetchone()
                        print(stored_password)
                        if log_upassword==stored_password[0].decode('utf-8'):
                            print(session)
                            session['user']=log_uemail
                            if not session.get(log_uemail):
                                session[log_uemail]={}
                            print(session)
                            return redirect(url_for('index')) # ya asal readreview page aanaaa
                        else:
                            flash('wrong pass')
                            return redirect(url_for('userlogin'))
                    else:
                        flash('wrong email')
                        return redirect(url_for('userlogin'))
        return render_template('userlogin.html')
    else:
        return redirect(url_for('index'))

@app.route('/category/<type>')
def category(type):
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select bin_to_uuid(item_id),item_name,quantity,price,category,image_name from items where category=%s',[type])
        items_data=cursor.fetchall() #retrieving all the items from items table
    except Exception as e:
        print(e)
        flash('Could not fetch Items')
        return redirect(url_for('index'))
    else:
        return render_template('dashboard.html',items_data=items_data)
    return render_template('dashboard')

@app.route('/addcart/<itemid>/<name>/<price>/<qyt>/<image>/<category>')
def addcart(itemid,name,price,qyt,image,category):
    if not session.get('user'):
        return redirect(url_for('userlogin'))
    else:
        print(session) #{}
        if itemid not in session['user']:
            session[session.get('user')][itemid]=[name,price,1,image,category,qyt]
            session.modified=True
            print(session)
            flash(f'{name} added to cart')
            return redirect(url_for('index'))
        session[session.get('user')][itemid][2]+=1
        flash('item already in cart')
        return redirect(url_for('index'))

@app.route('/viewcart')
def viewcart():
    if not session.get('user'):
        return redirect(url_for('userlogin'))
    else:
        if session.get(session.get('user')):
            items=session[session.get('user')]
            print(items)
        else:
            items='empty'
        if items=='empty':
            flash('No Products added to cart')
            return redirect(url_for('index'))
        return render_template('cart.html',items=items)

@app.route('/removecart_item/<itemid>')
def removecart_item(itemid):
    if not session.get('user'):
        return redirect(url_for('userlogin'))
    else:
        session.get(session.get('user')).pop(itemid)
        session.modified=True
        flash('Item removed from the cart')
        return redirect(url_for('viewcart'))

@app.route('/description/<itemid>')
def description(itemid):
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select bin_to_uuid(item_id),item_name,description,quantity,price,category,image_name from items where item_id=uuid_to_bin(%s)',[itemid])
        item_data=cursor.fetchone() #retrieving all the items from items table
    except Exception as e:
        print(e)
        flash('Could not fetch Items')
        return redirect(url_for('index'))
    return render_template('description.html',item_data=item_data)


@app.route('/userlogout')
def userlogout():
    if session.get('user'):
        session.pop('user')
        print('pop',session.get('user'))
        return redirect(url_for('userlogin'))
    return redirect(url_for('userlogin'))

'''@app.route('/pay/<itemid>/<name>/<float:price>',methods=['GET','POST'])
def pay(itemid,name,price):
    try:
        qyt=int(request.form['qyt'])
        amount=price*100
        total_price=qyt*amount
        print(amount,qyt,total_price)
        print(f'creating payment for item:{itemid},name:{name},price:{total_price}')
        #create Razor order
        order=client.order.create({'amount':total_price,'currency':'INR','payment_capture':'1'})
        print(f"order created:{order}")
        return render_template('pay.html',order=order,itemid=itemid,name=name,price=total_price,qyt=qyt)
    except Exception as e:
        #log the error and return a 400 response
        print(f'Error creating order:{str(e)}')
        flash('Error in payment')
        return redirect(url_for('index'))

@app.route('/success',methods=['POST'])
def success():
    #extract payment details from the form
    payment_id=request.form.get('razorpay_payment_id')
    order_id=request.form.get('razorpay_order_id')
    signature=request.form.get('razorpay_signature')
    name=request.form.get('name')
    itemid=request.form.get('itemid')
    price=request.form.get('total_price')
    qyt=request.form.get('qyt')
    print('qyt in success:',qyt)
    #verification process
    params_dict={'razorpay_order_id':order_id,'razorpay_payment_id':payment_id,'razorpay_signature':signature}
    try:
        client.utility.verify_payment_signature( params_dict)
        cursor=mydb.cursor(buffered=True)
        cursor.execute('insert into orders(itemid,item_name,total_price,user,qty) values(uuid_to_bin(%s),%s,%s,%s,%s)',[itemid,name,price,session.get('user'),qyt])
        mydb.commit()
        cursor.close()
        flash('order placed successfully')
        return redirect(url_for('orders'))
    except razorpay.errors.SignatureVerificationError:
        #if the signature verification fails ,you should redirect to the user to a error page
        return 'pay Verification Failed',400
    else:
        flash('order placed successfully')
        return good placed order'''
@app.route('/orders')
def orders():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select orderid,bin_to_uuid(itemid),item_name,total_price,user,qty from orders where user=%s',[session.get('user')])
            ordlist=cursor.fetchall()
        except Exception as e:
            print('Error in fetching orders')
            flash("could n't fetch orders")
        else:
            return render_template('orders.html',ordlist=ordlist)
    return redirect(url_for('userlogin'))
@app.route('/search',methods=['GET','POST'])
def search():
    if request.method=='POST':
        search=request.form['search']
        strg=['A-Za-z0-9']
        pattern=re.compile(f'{strg}',re.IGNORECASE)
        if (pattern.match(search)):
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select bin_to_uuid(item_id),item_name,quantity,price category,image_name from items where item_name like%s or price like %s or category like %s or description like %s',['%'+search+'%','%'+search+'%','%'+search+'%','%'+search+'%'])
                searcheddata=cursor.fetchall()
            except Exception as e:
                print(f'error to fetch searchdata:{e}')
                flash('couldnot fetch data')
                return redirect(url_for('index'))
            else:
                return render_template('dashboard.html',items_data=searcheddata)
        else:
            flash('No data given invallide search')
            return redirect(url_for('index'))
    return render_template('index.html')
@app.route('/addreview/<itemid>',methods=['GET','POST'])
def addreview(itemid):
    if session.get('user'):
        if request.method=='POST':
            title=request.form['title']
            reviewtext=request.form['review']
            rating=request.form['rate']
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('insert into reviews(username,itemid,title,review,rating) values(%s,uuid_to_bin(%s),%s,%s,%s)',[session.get('user'),itemid,title,reviewtext,rating])
                mydb.commit()
            except Exception as e:
                print(f'Error in inserting review:{e}')
                flash("can't add a review")
                return redirect(url_for('description',itemid=itemid))
            else:
                cursor.close()
                flash('review has given')
                return redirect(url_for('description',itemid=itemid))
        return render_template('review.html')  
    else:
        return redirect(url_for('userlogin'))
@app.route('/readreview/<itemid>')
def readreview(itemid):
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select bin_to_uuid(item_id),item_name,description,quantity,price,category,image_name from items where item_id=uuid_to_bin(%s)',[itemid])
        item_data=cursor.fetchone()
        cursor.execute('select *from reviews where itemid =uuid_to_bin(%s)',[itemid])
        data=cursor.fetchall()
        mydb.commit()
    except Exception as e:
        print(f'error in reading the review')
        flash(' can not read the review')
        return redirect(url_for('description',itemid=itemid))
    else:
        cursor.close()
        flash('read the review')
        return render_template('readreview.html',item_data=item_data,data=data)
if __name__='__main__':
    app.run()