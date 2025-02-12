from PyQt5 import QtCore, QtWidgets
import datetime
from backend import compute_matching_percentage  # Backend'den aday ve iş uyum oranı hesaplama fonksiyonu içe aktarılıyor

class AdminLoginWidget(QtWidgets.QWidget):
    """
    Yönetici (Admin) giriş ekranını temsil eden widget.
    Kullanıcı adı ve şifre bilgileri alınır; giriş başarılı ise, admin dashboard sayfasına geçiş yapılır.
    """
    def __init__(self, main_window):
        """
        :param main_window: Uygulamanın ana penceresi; sayfa geçişleri ve backend erişimi için kullanılır.
        """
        super().__init__()
        self.main_window = main_window
        # Ana düzen (vertical layout) oluşturuluyor
        layout = QtWidgets.QVBoxLayout()
        
        # Başlık etiketi oluşturuluyor ve stil veriliyor
        title = QtWidgets.QLabel("Admin Login")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Form düzeni: Kullanıcı adı ve şifre giriş alanları ekleniyor
        form_layout = QtWidgets.QFormLayout()
        self.username_edit = QtWidgets.QLineEdit()
        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)  # Şifrenin gizli olarak girilmesi sağlanır
        form_layout.addRow("Username:", self.username_edit)
        form_layout.addRow("Password:", self.password_edit)
        layout.addLayout(form_layout)
        
        # Buton düzeni: "Login" ve "Back" butonları ekleniyor
        btn_layout = QtWidgets.QHBoxLayout()
        btn_login = QtWidgets.QPushButton("Login")
        btn_back = QtWidgets.QPushButton("Back")
        # Login butonuna tıklandığında login() metodunun çalışması sağlanır
        btn_login.clicked.connect(self.login)
        # Back butonuna tıklandığında ana menüye geçiş yapılır
        btn_back.clicked.connect(lambda: self.main_window.switch_page(self.main_window.main_menu))
        btn_layout.addWidget(btn_login)
        btn_layout.addWidget(btn_back)
        layout.addLayout(btn_layout)
        
        # Oluşturulan düzen widget'ın ana düzeni olarak atanır
        self.setLayout(layout)
    
    def login(self):
        """
        Giriş butonuna tıklanıldığında çağrılır; kullanıcı adı ve şifreyi kontrol edip,
        backend üzerinden admin doğrulaması yapar. Başarılı ise dashboard sayfasına yönlendirir.
        """
        # Kullanıcı adı ve şifre alanlarından veriler alınır ve gereksiz boşluklar temizlenir
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        # Backend üzerinden admin doğrulaması gerçekleştirilir
        success, result = self.main_window.backend.admin_login(username, password)
        if success:
            # Giriş başarılı ise, admin dashboard sayfasındaki veriler yenilenir
            self.main_window.admin_dashboard_page.refresh()
            # Ana pencere, admin dashboard sayfasına geçiş yapar
            self.main_window.switch_page(self.main_window.admin_dashboard_page)
        else:
            # Giriş başarısız ise uyarı mesajı görüntülenir
            QtWidgets.QMessageBox.warning(self, "Login Failed", result)

class AdminDashboardWidget(QtWidgets.QWidget):
    """
    Yönetici dashboard sayfasını temsil eden widget.
    Sistemdeki tüm adaylar tablo şeklinde listelenir ve adayların iş başvuruları gösterilir.
    Ayrıca, belirli bir iş için aday eşleştirmesi yapma işlevi de sunar.
    """
    def __init__(self, main_window):
        """
        :param main_window: Ana pencere nesnesi; sayfa geçişleri ve backend erişimi için kullanılır.
        """
        super().__init__()
        self.main_window = main_window
        layout = QtWidgets.QVBoxLayout()
        
        # Dashboard başlık etiketi oluşturuluyor ve stil veriliyor
        title = QtWidgets.QLabel("Admin Dashboard")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Adayların bilgilerini göstermek için tablo oluşturuluyor
        self.candidate_table = QtWidgets.QTableWidget()
        self.candidate_table.setColumnCount(4)
        self.candidate_table.setHorizontalHeaderLabels(["Username", "Name", "Status", "Applied Jobs"])
        self.candidate_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.candidate_table)
        
        # Buton düzeni: "Refresh" ve "Match Candidates for a Job" butonları ekleniyor
        btn_layout = QtWidgets.QHBoxLayout()
        btn_refresh = QtWidgets.QPushButton("Refresh")
        btn_refresh.clicked.connect(self.refresh)  # Tıklandığında tabloyu yenilemek için refresh() çağrılır
        btn_match = QtWidgets.QPushButton("Match Candidates for a Job")
        btn_match.clicked.connect(self.match_candidates)  # Belirli bir iş için aday eşleştirmesi başlatılır
        btn_layout.addWidget(btn_refresh)
        btn_layout.addWidget(btn_match)
        layout.addLayout(btn_layout)
        
        # Geri butonu: Ana menüye dönüş sağlar
        btn_back = QtWidgets.QPushButton("Back")
        btn_back.clicked.connect(lambda: self.main_window.switch_page(self.main_window.main_menu))
        layout.addWidget(btn_back)
        
        # Oluşturulan düzen widget'ın ana düzeni olarak atanır
        self.setLayout(layout)
    
    def refresh(self):
        """
        Backend'den tüm aday bilgilerini çeker ve tabloyu günceller.
        Her aday için; kullanıcı adı, isim, başvuru durumu ve başvurduğu iş ilanları listelenir.
        """
        # Backend'den tüm adaylar alınır
        candidates = self.main_window.backend.get_all_candidates()
        # Tablo sıfırlanır
        self.candidate_table.setRowCount(0)
        # Her aday için tabloya yeni bir satır eklenir
        for candidate in candidates:
            row = self.candidate_table.rowCount()
            self.candidate_table.insertRow(row)
            self.candidate_table.setItem(row, 0, QtWidgets.QTableWidgetItem(candidate.username))
            self.candidate_table.setItem(row, 1, QtWidgets.QTableWidgetItem(candidate.name))
            self.candidate_table.setItem(row, 2, QtWidgets.QTableWidgetItem(candidate.status))
            # Adayın başvurduğu iş ilanlarının job_id değerleri toplanır
            applied_jobs = [app.job.job_id for app in candidate.applications if app.job]
            applied = ", ".join(applied_jobs) if applied_jobs else "None"
            self.candidate_table.setItem(row, 3, QtWidgets.QTableWidgetItem(applied))
    
    def match_candidates(self):
        """
        Belirli bir iş ilanı için aday eşleştirmesi yapar.
        Önce, backend üzerinden tüm iş ilanları alınır ve kullanıcıdan bir iş seçmesi istenir.
        Seçilen işe göre, adayların uyum skorları hesaplanır ve sonuçlar yeni bir diyalog penceresinde tablo olarak sunulur.
        """
        # Tüm iş ilanları alınır
        jobs = self.main_window.backend.get_candidate_jobs()
        # İş ilanlarının job_id değerleri liste haline getirilir
        job_ids = [job.job_id for job in jobs]
        # Kullanıcıdan hangi iş ilanı için eşleştirme yapılacağı sorulur
        job_id, ok = QtWidgets.QInputDialog.getItem(self, "Select Job", "Job ID:", job_ids, 0, False)
        if ok and job_id:
            # Backend'den ilgili iş ilanı nesnesi çekilir
            from backend import JobModel
            job = self.main_window.backend.session.query(JobModel).filter_by(job_id=job_id).first()
            if job:
                # Belirtilen iş ilanına göre aday eşleştirme işlemi yapılır
                matches = self.main_window.backend.improved_match_candidates_to_job(job)
                # Eşleşme sonuçları için yeni bir diyalog penceresi oluşturulur
                dialog = QtWidgets.QDialog(self)
                dialog.setWindowTitle(f"Candidate Matches for {job.job_id}")
                dlg_layout = QtWidgets.QVBoxLayout()
                table = QtWidgets.QTableWidget()
                table.setColumnCount(3)
                table.setHorizontalHeaderLabels(["Username", "Name", "Similarity Score"])
                table.horizontalHeader().setStretchLastSection(True)
                table.setRowCount(0)
                # Her aday için eşleşme skoru tabloya eklenir
                for candidate, score in matches:
                    row = table.rowCount()
                    table.insertRow(row)
                    table.setItem(row, 0, QtWidgets.QTableWidgetItem(candidate.username))
                    table.setItem(row, 1, QtWidgets.QTableWidgetItem(candidate.name))
                    # Skor yüzde formatında gösterilir
                    table.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{score*100:.2f}%"))
                dlg_layout.addWidget(table)
                # Diyalog penceresini kapatmak için "Close" butonu eklenir
                btn_close = QtWidgets.QPushButton("Close")
                btn_close.clicked.connect(dialog.accept)
                dlg_layout.addWidget(btn_close)
                dialog.setLayout(dlg_layout)
                dialog.exec_()
