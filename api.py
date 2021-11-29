import logging
from flask import Flask
from account.api import account_app
from identify.api import identify_app
from login.api import login_app
from record.api import record_app
from user.api import user_app

app = Flask(__name__)
app.register_blueprint(account_app, url_prefix='/account')
app.register_blueprint(identify_app, url_prefix='/identify')
app.register_blueprint(login_app, url_prefix='/login')
app.register_blueprint(record_app, url_prefix='/record')
app.register_blueprint(user_app, url_prefix='/user')
logging.basicConfig(filename='run.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s : %(message)s')

if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=8085, debug=True)
    app.run(host='0.0.0.0', port=8080, debug=True, ssl_context=(
        '../../license/cert.pem', '../../license/key.pem'))
