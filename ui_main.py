from PyQt5 import QtCore, QtWidgets

# ---------------------------
# ANA MENÜ VE ANA PENCERE
# ---------------------------

class MainMenuWidget(QtWidgets.QWidget):
    """
    Sistemin giriş ekranı; aday, admin, HR giriş ve kayıt işlemleri için yönlendirme sağlar.
    """
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignCenter)
        
        # Ana başlık
        title = QtWidgets.QLabel("Welcome to the Open Source Resume System")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Menü butonları: Aday Giriş, Aday Kayıt, Admin Giriş, HR Giriş ve Çıkış
        btn_candidate_login = QtWidgets.QPushButton("Candidate Login")
        btn_candidate_reg = QtWidgets.QPushButton("Candidate Registration")
        btn_admin_login = QtWidgets.QPushButton("Admin Login")
        btn_hr_login = QtWidgets.QPushButton("HR Login")
        btn_exit = QtWidgets.QPushButton("Exit")
        btn_candidate_login.clicked.connect(lambda: self.main_window.switch_page(self.main_window.candidate_login_page))
        btn_candidate_reg.clicked.connect(lambda: self.main_window.switch_page(self.main_window.candidate_registration_page))
        btn_admin_login.clicked.connect(lambda: self.main_window.switch_page(self.main_window.admin_login_page))
        btn_hr_login.clicked.connect(lambda: self.main_window.switch_page(self.main_window.hr_login_page))
        btn_exit.clicked.connect(QtWidgets.qApp.quit)
        for btn in [btn_candidate_login, btn_candidate_reg, btn_admin_login, btn_hr_login, btn_exit]:
            btn.setMinimumWidth(200)
            layout.addWidget(btn)
        self.setLayout(layout)


class MainWindow(QtWidgets.QMainWindow):
    """
    Uygulamanın ana penceresi; tüm sayfalar arasında geçiş yapmayı sağlayan merkezi widget (StackedWidget) içerir.
    Ayrıca genel stil ve sayfa yapılandırması burada yapılır.
    """
    def __init__(self, backend, ui_candidate, ui_hr, ui_admin, ui_main):
        """
        :param backend: Uygulamanın backend nesnesi (veritabanı ve iş mantığı işlemleri için)
        :param ui_candidate: Aday ile ilgili arayüz modülü
        :param ui_hr: HR ile ilgili arayüz modülü
        :param ui_admin: Admin ile ilgili arayüz modülü
        :param ui_main: Ana menü modülü
        """
        super().__init__()
        self.backend = backend
        self.setWindowTitle("Open Source Resume System")
        self.resize(900, 600)
        # Merkezi widget olarak QStackedWidget kullanılarak sayfalar arasında geçiş sağlanır.
        self.central_widget = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.central_widget)
        
        # UI modüllerinden sayfaların örnekleri oluşturulur.
        self.main_menu = ui_main.MainMenuWidget(self)
        self.candidate_login_page = ui_candidate.CandidateLoginWidget(self)
        self.candidate_registration_page = ui_candidate.CandidateRegistrationWidget(self)
        self.candidate_dashboard_page = ui_candidate.CandidateDashboardWidget(self)
        self.admin_login_page = ui_admin.AdminLoginWidget(self)
        self.admin_dashboard_page = ui_admin.AdminDashboardWidget(self)
        self.hr_login_page = ui_hr.HRLoginWidget(self)
        self.hr_dashboard_page = ui_hr.HRDashboardWidget(self)
        
        # Tüm sayfalar merkezi widget'a eklenir.
        self.central_widget.addWidget(self.main_menu)
        self.central_widget.addWidget(self.candidate_login_page)
        self.central_widget.addWidget(self.candidate_registration_page)
        self.central_widget.addWidget(self.candidate_dashboard_page)
        self.central_widget.addWidget(self.admin_login_page)
        self.central_widget.addWidget(self.admin_dashboard_page)
        self.central_widget.addWidget(self.hr_login_page)
        self.central_widget.addWidget(self.hr_dashboard_page)
        
        # Uygulama açıldığında ana menü sayfası görüntülenir.
        self.central_widget.setCurrentWidget(self.main_menu)
        self.setStyleSheet(self.load_stylesheet())
    
    def load_stylesheet(self):
        """
        Uygulamanın genel görünümünü belirleyen stil dosyasını yükler.
        Burada koyu, geleceğe yönelik (futuristic) bir stil kullanılmıştır.
        """
        return """
        QWidget {
            background-color: #121212;
            color: #e0e0e0;
            font-family: 'Roboto', sans-serif;
        }
        QMainWindow {
            background-color: #121212;
        }
        QPushButton {
            background-color: #1f1f1f;
            color: #e0e0e0;
            border: 1px solid #333;
            border-radius: 4px;
            padding: 8px 16px;
        }
        QPushButton:hover {
            background-color: #272727;
        }
        QLineEdit, QTextEdit, QComboBox {
            background-color: #1e1e1e;
            color: #e0e0e0;
            border: 1px solid #333;
            border-radius: 4px;
            padding: 6px;
        }
        QLabel {
            font-weight: bold;
        }
        QListWidget {
            background-color: #1e1e1e;
            color: #e0e0e0;
            border: 1px solid #333;
            border-radius: 4px;
        }
        QTableWidget {
            background-color: #1e1e1e;
            color: #e0e0e0;
            border: 1px solid #333;
        }
        QHeaderView::section {
            background-color: #333;
            color: #e0e0e0;
            padding: 4px;
            border: none;
        }
        """
    
    def setup_ui(self):
        """
        Ek UI ayarları veya yapılandırmaları gerekiyorsa burada yapılabilir.
        """
        pass
    
    def switch_page(self, widget):
        """
        Merkezi widget içinde geçiş yapmak için sayfa değiştirir.
        
        :param widget: Görüntülenmek istenen widget nesnesi.
        """
        self.central_widget.setCurrentWidget(widget)
