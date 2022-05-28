class Development(object):
    ENV = 'development'
    DEBUG=True 
    MYSQL_ADDRESS='127.0.0.1'
    MYSQL_USER='root'
    MYSQL_PASSWORD='password'
    MYSQL_PORT=3306
    MYSQL_DATABASE='hogepiyodb'

class Production(Development):
    ENV = 'production'
    DEBUG = False
    MYSQL_ADDRESS='63.31.125.212'
