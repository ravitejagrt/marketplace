import configparser, json, base64
from io import BytesIO
from flask import Flask, jsonify, request, send_file
from flask_mysqldb import MySQL
import MySQLdb
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

config = configparser.RawConfigParser()
config.read('ms3-properties.properties')

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'pace_mp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)
# mysql.init_app(app)

@app.route('/', methods = ['GET'])
def index():
    try:
        cursor = mysql.connection.cursor()
        # cur.execute('SELECT * FROM products')
        # results = cur.fetchall()
        print('cursor created')
        return jsonify('Database connection worked!')
    except Exception as e:
        print(e)
    finally:
        cursor.close()

@app.route('/categories', methods=['GET'])
def getCategories():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, name, img FROM category")
        cat = cursor.fetchall()
        #print('line 43 ', cat)
        print()
        
        categories = []
        for i in cat:
            temp = {
                "id": i["id"],
                "name": i["name"],
                "img": i["img"].decode('utf-8')
            }
            categories.append(temp)
        resp = jsonify(categories)
        resp.status_code = 200
        print("line 56 ", resp)
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
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        resp = jsonify(products)
        resp.status_code = 200
        return resp
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
        mysql.connection.commit()

        resp=jsonify({'msg':'Success'})
        resp.status_code = 200
        return resp

    except Exception as e:
            print(e)

@app.route('/product/<int:productId>', methods=['GET', 'PUT', 'DELETE'])
def getProductById(productId):
    if (request.method == 'GET'):
        try:
            cursor = mysql.connection.cursor()
            select_stmt = "SELECT id, name, categoryId, userId, description, price, datediff(current_date(), createdDate) as days FROM products WHERE id = %(prodId)s"
            print(select_stmt)
            cursor.execute(select_stmt, {'prodId': productId})
            product = cursor.fetchall()
            print('p: ', product)
            resp = jsonify(product)
            resp.status_code = 200
            return resp
        except Exception as e:
            print('exception: ', e)
        finally:
            cursor.close()       
    elif (request.method == 'PUT'):
        return "TO BE IMPLEMENTED"
    elif (request.method == 'DELETE'):
        return "TO BE IMPLEMENTED"
    else:
        return 'NOT IMPLEMENTED'

@app.route('/user/<int:userId>', methods=['GET', 'PUT', 'DELETE'])
def user(userId):
    if (request.method == 'GET'):
        try:
            cursor = mysql.connection.cursor()
            select_stmt = "SELECT id, firstName, lastName, email FROM users WHERE id = %(userId)s"
            print(select_stmt)
            cursor.execute(select_stmt, {'userId': userId})

            user = cursor.fetchall()
            resp = jsonify(user)
            # resp = jsonify({'message': ('Functionality work in progress. Visit back later ' + emailId)})
            resp.status_code = 200
            return resp
        except Exception as e:
            print(e)
        finally:
            cursor.close()
    elif (request.method == 'PUT'):
        return 'TO BE IMPLEMETED'
    elif (request.method == 'DELETE'):
        return 'TO BE IMPLEMETED'
    else:
        return 'NOT IMPLEMETED'  

@app.route('/user', methods=['POST'])
def signup():
    try:
        print('line 121',request.data, ' ', len(request.data))
        data = json.loads(request.data)
        count=0
        for item in data:
            count+=1
        print(count)
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
        print("response : ", resp)
        resp.status_code = 200
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
            if (str(image.filename) == "image.jpeg"):

                insert_stmt = (
                    "INSERT INTO product_image (product_id, product_image) "
                    "VALUES (%s, %s)"
                )
                # insertData = (productId, MySQLdb.escape_string(image.read()))
                insertData = (productId, image.read())
                resp = cursor.execute(insert_stmt, insertData)
                mysql.connection.commit()
                resp = {'message': 'Success'}
                # resp.status_code = 200
                return resp
            else:
                resp = {'message': 'Correct file not received.'}
            return resp
        except Exception as e:
            print(e)
        finally:
            cursor.close()
    if (request.method == 'GET'):
        try:
            cursor = mysql.connection.cursor()
            sql_fetch_blob_query = """SELECT * FROM product_image WHERE product_id = %s"""
            cursor.execute(sql_fetch_blob_query, (productId,))
            records = cursor.fetchall()
            # print("records : ", records)
            resp = []
            for row in records:
                resp.append([{ 'imageId': row['image_id'], 'productId': row['product_id'], 'image': str(base64.encodebytes(row['product_image'])) }])
                # i = row['product_image']
                # write_file(i, "D:\PycharmWork\space1\pmp-api\image.jpeg")

            print("resp : ", resp)
            # return send_file(BytesIO(images[0]), attachment_filename='image.jpeg', as_attachment=True)
            return jsonify(resp)
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