from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt
from components.MenuButton import MenuButton
from components.UserCard import UserCard
from database.repositories.userRepository import createUser, getAllUsers

class UsersView(QWidget):
    def __init__(self, parent=None):
        super(UsersView, self).__init__(parent)

        layout = QVBoxLayout()
        layout.addWidget(MenuButton('Crear usuario', self.create_user))

        users = getAllUsers()
        if not users:
            layout.addWidget(UserCard('There are no users'))
        for user in users:
            layout.addWidget(UserCard(f'User {user.id}: {user.name}'))
        
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

    def create_user(self):
        createUser("Leandro Bertoluzzi", "leajb10@gmail.com", "Magno066", "admin")