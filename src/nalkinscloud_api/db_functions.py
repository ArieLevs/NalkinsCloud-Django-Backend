
'''# Insert new customer into customers table in mosquitto
def insert_new_customer_to_mosquitto(user_id, email):
    db = MosquittoDB()
    sql = 'INSERT INTO customers ' \
          '(user_id, email, is_active, country_id, registration_ip, ' \
          'date_created, last_update_date, last_login, last_login_ip) ' \
          'VALUES (%s, %s, 0, null, null, null, null, null, null)'
    params = [user_id, email]
    db.query(sql, params)
    db.commit()


def get_client_secret_web_db2(client_secret):
    OAuthApp.object.filter(client_secret=client_secret)


def get_client_secret_web_db(client_secret):
    db = DjangoDB()
    sql = 'SELECT client_secret FROM oauth2_provider_application WHERE client_secret=%s'
    params = [client_secret]
    result = db.query(sql, params)
    if result:
        return True
    else:
        return False


# Update device password on mosquitto DB
def update_device_pass_mosquitto_db(device_id, password):
    db = MosquittoDB()
    sql = 'UPDATE mosquitto.devices ' \
          'SET password=%s ' \
          'WHERE device_id=%s'
    params = [password, device_id]
    db.query(sql, params)
    db.commit()


def insert_into_acls_mosquitto_db(device_id, topic):
    db = MosquittoDB()
    sql = 'INSERT INTO acls (device_id, topic, rw, date_created)' \
          'VALUES (%s, %s, 2, null) ' \
          'ON DUPLICATE KEY UPDATE device_id=%s, topic=%s'
    params = [device_id, topic, device_id, topic]
    db.query(sql, params)
    db.commit()


# Get client ID from mosquitto if exists
def is_device_id_exists(device_id):
    db = MosquittoDB()
    sql = 'SELECT device_id ' \
          'FROM devices ' \
          'WHERE device_id=%s'
    params = [device_id]
    result = db.query(sql, params)
    if result:
        return True
    else:
        return False


# Get current owner id of the device
def get_device_owner(device_id, logged_in_user_id):
    db = MosquittoDB()
    sql = 'SELECT user_id ' \
          'FROM customer_devices ' \
          'WHERE device_id =%s'
    params = [device_id]
    result = db.query(sql, params)
    if result:
        # If the user currently logged in (has the current token) is also the owner of the device
        if logged_in_user_id == result[0][0]:
            return True
        else:
            return False
    # If result is empty, this means the device never activated
    else:
        return True


def insert_into_customer_devices(user_id, device_id, device_name):
    db = MosquittoDB()  # Create new DB handler object
    sql = 'INSERT INTO customer_devices (user_id, device_id, device_name) ' \
          'VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE' \
          ' user_id=%s, device_id=%s, device_name=%s'
    params = [user_id, device_id, device_name, user_id, device_id, device_name]
    db.query(sql, params)  # Execute the query
    db.commit()  # Commit the changes
    # db.__del__()  # Close the connection


def remove_from_customer_devices(user_id, device_id):
    db = MosquittoDB()  # Create new DB handler object
    sql = 'DELETE FROM customer_devices WHERE user_id=%s AND device_id=%s;'
    params = [user_id, device_id]
    db.query(sql, params)  # Execute the query
    db.commit()  # Commit the changes


def remove_from_acls(device_id, topic):
    db = MosquittoDB()  # Create new DB handler object
    sql = 'DELETE FROM acls WHERE device_id=%s AND topic LIKE %s;'
    params = [device_id, topic]
    db.query(sql, params)  # Execute the query
    db.commit()  # Commit the changes


# Get customers devices by using user id
def get_customers_devices(user_id):
    db = MosquittoDB()
    sql = 'SELECT c.device_id, c.device_name, d.type ' \
          'FROM customer_devices as c, devices as d ' \
          'WHERE c.device_id = d.device_id ' \
          'AND user_id=%s'
    params = [user_id]
    result = db.query(sql, params)
    if result:
        return result
    else:
        return None


# Add new device to the devices table
def insert_new_client_to_devices(email, password, ip):
    db = MosquittoDB()
    sql = "INSERT INTO devices " \
          "(device_id, password, is_enabled, model, type, date_created, " \
          "last_update_date, last_connection, last_connection_ip) " \
          "VALUES (%s, %s, '1', 'application', 'user', null, null, null, %s)"
    params = [email, password, ip]
    db.query(sql, params)
    db.commit()


def get_device_name_by_id(device_id):
    db = MosquittoDB()
    sql = 'SELECT device_name ' \
          'FROM customer_devices ' \
          'WHERE device_id=%s'
    params = [device_id]
    return db.query(sql, params)'''
