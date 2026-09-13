class CurrentUser:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CurrentUser, cls).__new__(cls)
            cls._instance.user_id = None
            cls._instance.name = None
            cls._instance.role = None
            cls._instance.token = None
        return cls._instance
    
    def get_auth_header(self):
        return {"Authorization": f"Bearer {self.token}"}

    def set_user_data(self, user_id, name, role, token):
        """Встановлюємо дані користувача"""
        self.user_id = user_id
        self.name = name
        self.role=role
        self.token = token
    
    def get_user_data(self):
        return {
            'user_id': self.user_id,
            'name': self.name,
            'role': self.role,
            'token': self.token
        }
    
    def get_user_id(self):
        """Отримуємо ID користувача"""
        return self.user_id

    def get_role(self): 
        """Отримуємо роль користувача"""
        return self.role
    
    def get_name(self):
        """Отримуємо ім'я користувача"""
        return self.name
    
    def get_token(self):
        """Отримуємо токен користувача"""
        return self.token
    
    def set_token(self, token): 
        """Встановлюємо токен користувача"""
        self.token = token

    def is_librarian(self):
        """Перевіряємо, чи користувач є бібліотекарем"""
        return self.role == "librarian"
    def is_guest(self):
        """Перевіряємо, чи користувач є гостем"""
        return self.role == "guest"
    
    def clear_user_data(self):
        """Очищаємо дані користувача після виходу"""
        self.user_id = None
        self.name = None
        self.token = None
        self.role = None
