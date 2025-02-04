"""Database Manager GUI - Login Dialog

Building Custom UIs with PyQt with Packt Publishing
Chapter 4 - Handling Data with PyQt
Created by: Joshua Willman
"""

# Import necessary modules
import sys
from PyQt6.QtWidgets import (QApplication, QDialog, QLabel,
    QDialogButtonBox, QLineEdit, QMessageBox, QGridLayout) 
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
# Import relative modules
from .main_window import MainWindow

class LoginWindow(QDialog):

    def __init__(self):
        """ Login Dialog """
        super().__init__()
        self.initializeUI()

    def initializeUI(self):
        self.setWindowTitle("Login Window")
        self.setFixedSize(500, 200) 

        self.setUpWindow()
        # Connect to database after setting up the login dialog
        self.connectToDatabase()
        self.show()

    def setUpWindow(self):
        """Set up the dialog's widgets and layout.""" 
        header_label = QLabel("""<p style='color:#65888C'>
            Welcome to Database Manager</p>""")
        header_label.setFont(QFont("Arial", 24))
        header_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter)

        self.info_label = QLabel(
            """<p style='color:#65888C'>
            Sign into your account.</p>""")
        self.info_label.setAlignment(
            Qt.AlignmentFlag.AlignHCenter)

        username_label = QLabel("Username:")
        self.username_line = QLineEdit()
        self.username_line.textEdited.connect(
            self.replaceText)

        password_label = QLabel("Password:")
        self.password_line = QLineEdit()
        self.password_line.setEchoMode(
            QLineEdit.EchoMode.Password)
        self.password_line.textEdited.connect(
            self.replaceText)

        button_box = QDialogButtonBox()
        button_box.addButton("Log In", 
            QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.accepted.connect(
            self.clickedLogInButton)

        log_in_grid = QGridLayout()
        log_in_grid.addWidget(header_label, 0, 0, 1, 3, Qt.AlignmentFlag.AlignCenter)
        log_in_grid.addWidget(self.info_label, 1, 0, 1, 3, Qt.AlignmentFlag.AlignCenter)
        log_in_grid.addWidget(username_label, 2, 0)
        log_in_grid.addWidget(self.username_line, 2, 1)
        log_in_grid.addWidget(password_label, 3, 0)
        log_in_grid.addWidget(self.password_line, 3, 1)
        log_in_grid.addWidget(button_box, 4, 1)      
        self.setLayout(log_in_grid)

    def connectToDatabase(self):
        """Create a QSqlDatabase object and connect to the database."""
        database = QSqlDatabase.addDatabase("QSQLITE") 
        database.setDatabaseName("data/inventory.db") 
        database.setConnectOptions("QSQLITE_ENABLE_REGEXP")
        if not database.open():
            error = database.lastError().text()
            QMessageBox.critical(QApplication.activeWindow(), 
                "Connection Error",
                f"Something went wrong: {error}")
            sys.exit(1)     

        # Handle if the database is missing and SQLite creates a new,
        # empty database
        tables_needed = {"Staff", "Customers", "Orders", 
            "Products", "Categories"}
        no_tables = tables_needed - set(database.tables())
        if no_tables:
            QMessageBox.critical(QApplication.activeWindow(), 
                "Error", f'{no_tables} missing.')
            sys.exit(1) 

    def replaceText(self, text):
        """Slot for resetting the information label's text."""
        self.info_label.setText(
            "<p style='color:#65888C'>Sign into your account.</p>")          

    def clickedLogInButton(self):
        """Check the user's username and password information from 
        the database to determine if they are able to log in."""
        username = self.username_line.text()
        password = self.password_line.text()

        query = QSqlQuery()
        query.exec("PRAGMA foreign_keys = ON")
        query.prepare(
            "SELECT * FROM Staff WHERE username=:username")
        query.bindValue(":username", username) 
        query.exec()

        # Open the main window or provide feedback 
        if query.first(): # Retrieve the first matching username
            if query.value("password") == password:
                admin_or_not = query.value("is_admin") # Retrieve the value for administrative privileges
                
                # Open the main window and close the login dialog
                self.main_window = MainWindow(admin_or_not)
                self.main_window.showMaximized()
                self.close()
            else: 
                self.info_label.setText(
                    "<p style='color:#F34B2C'>Incorrect password.</p>")
        else: 
            self.info_label.setText(
                "<p style='color:#F34B2C'>Incorrect username.</p>")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    sys.exit(app.exec())