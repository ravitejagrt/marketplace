import configparser, json, base64
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText              
from io import BytesIO
from flask import Flask, jsonify, request, send_file
from flask_mysqldb import MySQL
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

config = configparser.RawConfigParser()
config.read('environment/pmp-properties.properties')

# MySQL configurations
app.config['MYSQL_HOST'] = config['mysql']['host']
app.config['MYSQL_USER'] = config['mysql']['user']
app.config['MYSQL_PASSWORD'] = config['mysql']['password']
app.config['MYSQL_DB'] = config['mysql']['db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)
# mysql.init_app(app)

@app.route('/', methods = ['GET'])
def index():
    try:
        cursor = mysql.connection.cursor()
        # cur.execute('SELECT * FROM products')
        # results = cur.fetchall()
        return jsonify('Database connection worked!')
    except Exception as e:
        print(e)
    finally:
        cursor.close()

context = ssl.create_default_context()
@app.route('/email', methods=['POST'])
def sendEmail():
    try:
        data = json.loads(request.data)
        port = config['smtp']['port']
        smtp_server = config['smtp']['server']
        sender_email = config['smtp']['username']
        receiver_email = data['recipients']
        print(type(receiver_email[0]))
        password = config['smtp']['password']

        message = MIMEMultipart("alternative")
        message["Subject"] = data['subject']
        message["From"] = sender_email
        message["To"] = receiver_email[0]
        html_msg = "<html><body>" + data['body'] + "</body></html>"
        text = MIMEText(data['text'], "plain")
        html = MIMEText(html_msg, "html")
        message.attach(text)
        message.attach(html)

        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
          server.login(sender_email, password)
          server.sendmail(sender_email, receiver_email[0], message.as_string().encode('utf-8'))

        return jsonify({
          "status": "success",
          "message": "Mail sent"
        })
    except smtplib.SMTPException as smtpex:
        print(smtpex)
    except smtplib.SMTPAuthenticationError as auterr:
        print(auterr)
    except Exception as e:
        print("exception: ", e)
    finally:
        print("end finally")

@app.route('/categories', methods=['GET'])
def getCategories():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, name, img FROM category")
        cat = cursor.fetchall()
        
        categories = []
        for i in cat:
            temp = {
                "id": i["id"],
                "name": i["name"],
                "img": i["img"].decode('utf-8')
            }
            categories.append(temp)
        resp = jsonify(categories)
        print(resp)
        return resp
    except Exception as e:
        print(e)
    finally:
        cursor.close()
    
@app.route('/categories/<int:categoryId>', methods=['GET'])
def getCategoryById(categoryId):
    try:
        cursor = mysql.connection.cursor()
        select_stmt = "SELECT id, name, img FROM category where  id = %(catId)s"
        cursor.execute(select_stmt, {'catId': categoryId})
        cat = cursor.fetchone()
        categories = {
            "id": cat["id"],
            "name": cat["name"],
            "img": cat["img"].decode('utf-8')
        }
        resp = jsonify(categories)
        return resp
    except Exception as e:
        print(e)
    finally:
        cursor.close()

@app.route('/products', methods=['GET'])
def getProducts():
    try:
        # conn = mysql.connect()
        # cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor = mysql.connection.cursor()
        cursor.execute("select id, name, categoryId, userId, description, price, datediff(current_date(), createdDate) as days  from products order by modifiedDate desc")
        rows = cursor.fetchall()
        products = []
        i=0
        for row in rows:
            products.append(row)
            i+=1
        #print(products)
        resp = {'products': products}
        return jsonify(resp)
    except Exception as e:
        print(e)
    finally:
        cursor.close()

@app.route('/products', methods=['POST'])     
def setProducts():   
    try:
        data = json.loads(request.data)
        cursor = mysql.connection.cursor()

        insert_stmt = (
            "INSERT INTO products (name, categoryId, userId, description, price) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        insertData = (data['prodName'], data['categoryId'], data['userId'], data['prodDesc'], data['prodPrice'])
        resp = cursor.execute(insert_stmt, insertData)
        id = cursor.lastrowid
        mysql.connection.commit()

        resp=jsonify({'prodId':id})
        return resp

    except Exception as e:
            print(e)

@app.route('/product/<int:productId>', methods=['GET', 'PUT', 'DELETE'])
def getProductById(productId):
    if (request.method == 'GET'):
        try:
            cursor = mysql.connection.cursor()
            select_stmt = "SELECT id, name, categoryId, userId, description, price, datediff(current_date(), createdDate) as days FROM products WHERE id = %(prodId)s"
            cursor.execute(select_stmt, {'prodId': productId})
            product = cursor.fetchone()
            categories = json.loads(getCategoryById(product['categoryId']).data)
            product['categoryName'] = categories['name']
            resp = jsonify(product)
            return resp
        except Exception as e:
            print('exception: ', e)
        finally:
            cursor.close()       
    elif (request.method == 'PUT'):
        return "TO BE IMPLEMENTED"
    elif (request.method == 'DELETE'):
        try:
            cursor = mysql.connection.cursor()
            select_stmt = "DELETE FROM products WHERE id = %(prodId)s"
            cursor.execute(select_stmt, {'prodId': productId})
            mysql.connection.commit()
            resp = jsonify({'msg': 'Success'})
            return resp
        except Exception as e:
            print('exception: ', e)
        finally:
            cursor.close()   
    else:
        return 'NOT IMPLEMENTED'

@app.route('/user/<int:userId>', methods=['GET', 'PUT', 'DELETE'])
def user(userId):
    if (request.method == 'GET'):
        try:
            cursor = mysql.connection.cursor()
            select_stmt = "SELECT id, firstName, lastName, email FROM users WHERE id = %(userId)s"
            cursor.execute(select_stmt, {'userId': userId})

            user = cursor.fetchone()
            resp = jsonify(user)
            return resp
        except Exception as e:
            print(e)
        finally:
            cursor.close()
    elif (request.method == 'PUT'):
        try:
            userData = json.loads(request.data)
            cursor = mysql.connection.cursor()
            if 'firstName' in userData:
                update_stmt = "UPDATE users SET firstName = %(fName)s WHERE id = %(uId)s"
                # print("user details: ", ('userId': userId, 'firstName': userData['firstName']))
                updateData = {'fName': userData['firstName'], 'uId': userId}
            elif 'lastName' in userData:
                update_stmt = "UPDATE users SET lastName = %(lName)s WHERE id = %(uId)s"
                # print("user details: ", ('userId': userId, 'lastName': userData['lastName']))
                updateData = {'lName': userData['lastName'], 'uId': userId}
            elif 'phone' in userData:
                update_stmt = "UPDATE users SET phone = %(ph)s WHERE id = %(uId)s"
                # print("user details: ", ('userId': userId, 'phone': userDate['phone']))
                updateData = {'ph': userData['phone'], 'uId': userId}
            else:
                return "No firstName or lastName or phone in request"
            cursor.execute(update_stmt, updateData)
            mysql.connection.commit()
            resp = cursor._fetch_type
            return str(resp)
        except Exception as e:
            print(e)
        finally:
            cursor.close()
    elif (request.method == 'DELETE'):
        return 'TO BE IMPLEMETED'
    else:
        return 'NOT IMPLEMETED'  

@app.route('/user/<int:userId>/favProducts', methods=['GET'])
def userFavProducts(userId):
    if (request.method == 'GET'):
        try:
            cursor = mysql.connection.cursor()
            select_stmt = "SELECT product_id, created_date FROM fav_products WHERE user_id = %(userId)s"
            cursor.execute(select_stmt, {'userId': userId})

            user = cursor.fetchall()
            resp = jsonify(user)
            return resp
        except Exception as e:
            print(e)
        finally:
            cursor.close()
    else:
        return 'NOT IMPLEMETED'

@app.route('/user/<int:userId>/favProduct/<int:productId>', methods=['GET', 'POST', 'DELETE'])
def favProduct(userId, productId):
    if (request.method == 'GET'):

    elif (request.method == 'POST'):
        try:
            cursor = mysql.connection.cursor()
            create_stmt = "INSERT INTO fav_products (user_id, product_id) VALUES (%(userId)s, %(productId)s)"
            cursor.execute(create_stmt, {'userId': userId, 'productId': productId})

            mysql.connection.commit()

            select_stmt = "SELECT product_id, created_date FROM fav_products WHERE user_id = %(userId)s AND product_id = %(productId)s"
            cursor.execute(select_stmt, {'userId': userId, 'productId': productId})

            favProduct = cursor.fetchone()
            resp = jsonify(favProduct)
            return resp
        except Exception as e:
            print(e)
        finally:
            cursor.close()
    elif (request.method == 'DELETE'):
        try:
            cursor = mysql.connection.cursor()
            delete_stmt = "DELETE FROM fav_products WHERE user_id = %(userId)s AND product_id = %(productId)s"
            cursor.execute(delete_stmt, {'userId': userId, 'productId': productId})

            mysql.connection.commit()
            resp = jsonify({'msg': 'Success'})
            return resp
        except Exception as e:
            print(e)
        finally:
            cursor.close()
    else:
        return 'NOT IMPLEMETED'

@app.route('/user', methods=['POST'])
def signup():
    try:
        data = json.loads(request.data)
        count=0
        for item in data:
            count+=1
        cursor = mysql.connection.cursor()

        # sql = "INSERT INTO users (firstName, lastName, email, phone) VALUES (%s, %s, %s, %s)"
        # userData = (data.firstName, data.lastName, data.email, data.phone)
        # cursor.execute(sql, userData)
        if(count!=1):
            insert_stmt = (
                "INSERT INTO users (firstName, lastName, email, phone) "
                "VALUES(%s, %s, %s, %s)"
            )
            insertData = (data['firstName'], data['lastName'], data['email'], data['phone'])
            resp = cursor.execute(insert_stmt, insertData)
            mysql.connection.commit()

        select_stmt = """SELECT email, firstName, lastName, phone, id from users WHERE email = %(emailId)s"""
        cursor.execute(select_stmt, {'emailId': data['email']})
        user = cursor.fetchall()
        resp = jsonify(user)
        return resp
    except Exception as e:
        print(e)
    finally:
     cursor.close()

@app.route('/product/<int:productId>/image', methods=['POST', 'GET'])
def productImages(productId):
    if (request.method == 'POST'):
        try:
            cursor = mysql.connection.cursor()
            r = request
            image = r.files['file']
            if (str(image.filename).split('.')[-1] == "jpeg" or str(image.filename).split('.')[-1] == "jpg"):

                insert_stmt = (
                    "INSERT INTO product_image (productId, productImage) "
                    "VALUES (%s, %s)"
                )
                # insertData = (productId, MySQLdb.escape_string(image.read()))
                insertData = (productId, image.read())
                resp = cursor.execute(insert_stmt, insertData)
                id = cursor.lastrowid
                mysql.connection.commit()
                resp = {'message': 'Success', 'imageId': id}
            else:
                resp = {'message': 'Correct file not received.'}
            return jsonify(resp)
        except Exception as e:
            print(e)
        finally:
            cursor.close()
    if (request.method == 'GET'):
        try:
            cursor = mysql.connection.cursor()
            sql_fetch_blob_query = """SELECT * FROM product_image WHERE productId = %(prodId)s"""
            cursor.execute(sql_fetch_blob_query, {'prodId': productId})
            records = cursor.fetchall()
            # print("records : ", records)
            resp = []
            images  = []
            for row in records:
                images.add(row['productImage'])
                resp.append([{ 'imageId': row['imageId'], 'productId': row['productId'], 'image': str(base64.encodebytes(row['productImage'])) }])
                # i = row['product_image']
                # write_file(i, "D:\PycharmWork\space1\pmp-api\image.jpeg")

            # print("resp : ", resp)
            return send_file(BytesIO(image), attachment_filename='image.jpeg', as_attachment=False)
            # return jsonify(resp)
        except Exception as e:
            print(e)
        finally:
            cursor.close()


@app.route('/product/<int:productId>/allImages', methods=[ 'GET'])
def getAllProductImageIds(productId):
    try:
        cursor = mysql.connection.cursor()
        sql_fetch_blob_query = """SELECT productId, imageId FROM product_image WHERE productId = %(prodId)s"""
        cursor.execute(sql_fetch_blob_query, {'prodId': productId})
        records = cursor.fetchall()
        imageIds = []
        for row in records:
            imageIds.append(row['imageId'])
        
        images =  {'productId': productId,
                'imageIds': imageIds}
        resp = {'images': images}
        return jsonify(resp)
    except Exception as e:
        print(e)
    finally:
        cursor.close()

@app.route('/image/<int:imageId>', methods=['GET'])
def getImageById(imageId):
    try:
        cursor = mysql.connection.cursor()
        sql_fetch_blob_query = """SELECT * FROM product_image WHERE imageId = %(imgId)s"""
        cursor.execute(sql_fetch_blob_query, {'imgId': imageId})
        record = cursor.fetchone()
        # print("records : ", records)
        # resp = []
        # images = []
        # for row in records:
        #     images.add(row['productImage'])
        #     resp.append([{'imageId': row['imageId'], 'productId': row['productId'],
        #                   'image': str(base64.encodebytes(row['productImage']))}])
        #     # i = row['product_image']
        #     # write_file(i, "D:\PycharmWork\space1\pmp-api\image.jpeg")

        # print("resp : ", resp)
        image = record['productImage']
        return send_file(BytesIO(image), attachment_filename='image.jpeg', as_attachment=False)
        # return jsonify(resp)
    except Exception as e:
        print(e)
    finally:
        cursor.close()

def write_file(data, filename):
    # Convert binary data to proper format and write it on Hard Disk
    with open(filename, 'wb') as file:
        file.write(data)

if __name__ == '__main__':
	 app.run()