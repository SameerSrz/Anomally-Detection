from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.uic import loadUi
from settings_window import SettingsWindow
import webbrowser
import requests
import json

class LoginWindow(QMainWindow):
    def __init__(self):
        super(LoginWindow,self).__init__()
        loadUi('UI/login_window.ui',self)

        self.register_button.clicked.connect(self.go_to_register_page)
        self.login_button.clicked.connect(self.login)

        self.popup = QMessageBox()
        self.popup.setWindowTitle("Failed")


        self.show()
    
    def go_to_register_page(self):
        webbrowser.open('http://127.0.0.1:8000/register/')

    def login(self):
        try:
            url = 'http://127.0.0.1:8000/api/get_auth_token/'
            response = requests.post(url, data={'username': self.Username_input.text(), 'password': self.password_input.text()})

            # Check if the response status code is 200 (OK)
            if response.status_code == 200:
                json_response = json.loads(response.text)
                # Open settings window
                self.open_settings_window(json_response['token'])
            else:
                # Show error based on response status code
                if response.status_code == 400:
                    self.popup.setText("Username or Password is not correct")
                elif response.status_code == 500:
                    self.popup.setText("Internal Server Error")
                else:
                    self.popup.setText("Error: {}".format(response.status_code))
                self.popup.exec_()
        except Exception as e:
            # Unable to access server or other exceptions
            self.popup.setText("Unable to access server: {}".format(str(e)))
            self.popup.exec_()


    def open_settings_window(self, token):
        self.settings_window = SettingsWindow(token)
        self.settings_window.displayInfo()
        self.close()

