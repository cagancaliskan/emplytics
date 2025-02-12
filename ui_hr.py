from PyQt5 import QtCore, QtWidgets
import datetime
from backend import compute_matching_percentage  # Backend'den hesaplama fonksiyonunu içe aktarıyoruz

# ---------------------------
# ADMIN İŞLEMLERİ İÇİN ARAYÜZ
# ---------------------------

class AdminLoginWidget(QtWidgets.QWidget):
    """
    Yönetici (Admin) giriş ekranını temsil eden widget.
    Kullanıcı adı ve şifre bilgilerini alır, giriş işlemini gerçekleştirir.
    """
    def __init__(self, main_window):
        """
        Widget oluşturulurken ana pencere referansı aktarılır.
        
        :param main_window: Ana pencere nesnesi, sayfa geçişleri ve backend erişimi için kullanılır.
        """
        super().__init__()
        self.main_window = main_window
        layout = QtWidgets.QVBoxLayout()
        
        # Başlık etiketi: "Admin Login"
        title = QtWidgets.QLabel("Admin Login")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Form düzeni: Kullanıcı adı ve şifre girişi
        form_layout = QtWidgets.QFormLayout()
        self.username_edit = QtWidgets.QLineEdit()
        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)  # Şifre gizleme modu
        form_layout.addRow("Username:", self.username_edit)
        form_layout.addRow("Password:", self.password_edit)
        layout.addLayout(form_layout)
        
        # Buton düzeni: Login ve Back butonları
        btn_layout = QtWidgets.QHBoxLayout()
        btn_login = QtWidgets.QPushButton("Login")
        btn_back = QtWidgets.QPushButton("Back")
        btn_login.clicked.connect(self.login)  # Login butonuna tıklandığında login() metodu çalışır
        btn_back.clicked.connect(lambda: self.main_window.switch_page(self.main_window.main_menu))
        btn_layout.addWidget(btn_login)
        btn_layout.addWidget(btn_back)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def login(self):
        """
        Kullanıcının girdiği bilgiler doğrultusunda admin giriş işlemini gerçekleştiren metod.
        Giriş başarılı ise admin dashboard'a geçiş yapar, başarısız ise hata mesajı gösterir.
        """
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        # Backend'den admin giriş kontrolü yapılır
        success, result = self.main_window.backend.admin_login(username, password)
        if success:
            # Giriş başarılı ise dashboard verileri yenilenir ve sayfa değiştirilir.
            self.main_window.admin_dashboard_page.refresh()
            self.main_window.switch_page(self.main_window.admin_dashboard_page)
        else:
            QtWidgets.QMessageBox.warning(self, "Login Failed", result)


class AdminDashboardWidget(QtWidgets.QWidget):
    """
    Yönetici dashboard'ını temsil eden widget.
    Kayıtlı adayların listelenmesi, yenileme ve aday eşleştirme gibi işlemleri içerir.
    """
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QtWidgets.QVBoxLayout()
        
        # Dashboard başlık etiketi
        title = QtWidgets.QLabel("Admin Dashboard")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Adayların bilgilerini gösteren tablo
        self.candidate_table = QtWidgets.QTableWidget()
        self.candidate_table.setColumnCount(4)
        self.candidate_table.setHorizontalHeaderLabels(["Username", "Name", "Status", "Applied Jobs"])
        self.candidate_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.candidate_table)
        
        # Buton düzeni: Yenileme ve aday eşleştirme işlemleri için
        btn_layout = QtWidgets.QHBoxLayout()
        btn_refresh = QtWidgets.QPushButton("Refresh")
        btn_refresh.clicked.connect(self.refresh)  # Tıklandığında tabloyu yeniler
        btn_match = QtWidgets.QPushButton("Match Candidates for a Job")
        btn_match.clicked.connect(self.match_candidates)  # Aday eşleştirme penceresini açar
        btn_layout.addWidget(btn_refresh)
        btn_layout.addWidget(btn_match)
        layout.addLayout(btn_layout)
        
        # Geri butonu
        btn_back = QtWidgets.QPushButton("Back")
        btn_back.clicked.connect(lambda: self.main_window.switch_page(self.main_window.main_menu))
        layout.addWidget(btn_back)
        
        self.setLayout(layout)
    
    def refresh(self):
        """
        Tabloda yer alan aday verilerini backend üzerinden çekip günceller.
        """
        candidates = self.main_window.backend.get_all_candidates()
        self.candidate_table.setRowCount(0)
        for candidate in candidates:
            row = self.candidate_table.rowCount()
            self.candidate_table.insertRow(row)
            self.candidate_table.setItem(row, 0, QtWidgets.QTableWidgetItem(candidate.username))
            self.candidate_table.setItem(row, 1, QtWidgets.QTableWidgetItem(candidate.name))
            self.candidate_table.setItem(row, 2, QtWidgets.QTableWidgetItem(candidate.status))
            # Adayın başvurduğu iş ilanlarının ID'lerini listeler
            applied_jobs = [app.job.job_id for app in candidate.applications if app.job]
            applied = ", ".join(applied_jobs) if applied_jobs else "None"
            self.candidate_table.setItem(row, 3, QtWidgets.QTableWidgetItem(applied))
    
    def match_candidates(self):
        """
        Seçilen iş ilanı için aday eşleştirmesi yapar.
        İş ilanı seçimi sonrasında, backend'deki improved_match_candidates_to_job() fonksiyonu kullanılır.
        Sonuçlar yeni bir diyalog penceresinde tablo halinde gösterilir.
        """
        jobs = self.main_window.backend.get_candidate_jobs()
        job_ids = [job.job_id for job in jobs]
        job_id, ok = QtWidgets.QInputDialog.getItem(self, "Select Job", "Job ID:", job_ids, 0, False)
        if ok and job_id:
            from backend import JobModel
            job = self.main_window.backend.session.query(JobModel).filter_by(job_id=job_id).first()
            if job:
                matches = self.main_window.backend.improved_match_candidates_to_job(job)
                # Eşleşme sonuçları yeni bir diyalog penceresinde listelenir
                dialog = QtWidgets.QDialog(self)
                dialog.setWindowTitle(f"Candidate Matches for {job.job_id}")
                dlg_layout = QtWidgets.QVBoxLayout()
                table = QtWidgets.QTableWidget()
                table.setColumnCount(3)
                table.setHorizontalHeaderLabels(["Username", "Name", "Similarity Score"])
                table.horizontalHeader().setStretchLastSection(True)
                table.setRowCount(0)
                for candidate, score in matches:
                    row = table.rowCount()
                    table.insertRow(row)
                    table.setItem(row, 0, QtWidgets.QTableWidgetItem(candidate.username))
                    table.setItem(row, 1, QtWidgets.QTableWidgetItem(candidate.name))
                    # Benzerlik skorunu yüzde formatında gösterir
                    table.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{score*100:.2f}%"))
                dlg_layout.addWidget(table)
                btn_close = QtWidgets.QPushButton("Close")
                btn_close.clicked.connect(dialog.accept)
                dlg_layout.addWidget(btn_close)
                dialog.setLayout(dlg_layout)
                dialog.exec_()


# ---------------------------
# HR İŞLEMLERİ İÇİN ARAYÜZ
# ---------------------------

class HRLoginWidget(QtWidgets.QWidget):
    """
    HR (İnsan Kaynakları) giriş ekranını temsil eden widget.
    Kullanıcı adı ve şifre ile giriş yapılır.
    """
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QtWidgets.QVBoxLayout()
        
        # Başlık etiketi
        title = QtWidgets.QLabel("HR Login")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Form alanları: Kullanıcı adı ve şifre girişi
        form_layout = QtWidgets.QFormLayout()
        self.username_edit = QtWidgets.QLineEdit()
        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        form_layout.addRow("Username:", self.username_edit)
        form_layout.addRow("Password:", self.password_edit)
        layout.addLayout(form_layout)
        
        # Butonlar: Login ve Back
        btn_layout = QtWidgets.QHBoxLayout()
        btn_login = QtWidgets.QPushButton("Login")
        btn_back = QtWidgets.QPushButton("Back")
        btn_login.clicked.connect(self.login)  # Login işlemi tetiklenir
        btn_back.clicked.connect(lambda: self.main_window.switch_page(self.main_window.main_menu))
        btn_layout.addWidget(btn_login)
        btn_layout.addWidget(btn_back)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def login(self):
        """
        HR giriş bilgilerini kontrol edip, giriş başarılı ise HR dashboard'a geçiş yapar.
        """
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        success, result = self.main_window.backend.hr_login(username, password)
        if success:
            self.main_window.hr_dashboard_page.refresh()
            self.main_window.switch_page(self.main_window.hr_dashboard_page)
        else:
            QtWidgets.QMessageBox.warning(self, "Login Failed", result)


class HRJobManagementWidget(QtWidgets.QWidget):
    """
    HR'nin iş ilanlarını yönetmesi için kullanılan widget.
    İş ilanlarının listelenmesi, eklenmesi ve kaldırılması gibi işlemleri içerir.
    """
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  
        layout = QtWidgets.QVBoxLayout(self)
        
        # Başlık etiketi
        title = QtWidgets.QLabel("Manage Jobs")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px;")
        layout.addWidget(title)
        
        # İş ilanlarının listelendiği tablo
        self.job_table = QtWidgets.QTableWidget()
        self.job_table.setColumnCount(4)
        self.job_table.setHorizontalHeaderLabels(["Job ID", "Company", "Title", "Required Skills"])
        self.job_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.job_table)
        
        # Buton düzeni: İş ilanı ekleme ve kaldırma
        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_add_job = QtWidgets.QPushButton("Add Job")
        self.btn_remove_job = QtWidgets.QPushButton("Remove Selected Job")
        self.btn_add_job.clicked.connect(self.add_job)
        self.btn_remove_job.clicked.connect(self.remove_job)
        btn_layout.addWidget(self.btn_add_job)
        btn_layout.addWidget(self.btn_remove_job)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.refresh()
    
    def refresh(self):
        """
        Backend'den mevcut iş ilanlarını çekip tabloyu günceller.
        """
        jobs = self.main_window.backend.get_candidate_jobs()
        self.job_table.setRowCount(0)
        for job in jobs:
            row = self.job_table.rowCount()
            self.job_table.insertRow(row)
            self.job_table.setItem(row, 0, QtWidgets.QTableWidgetItem(job.job_id))
            self.job_table.setItem(row, 1, QtWidgets.QTableWidgetItem(job.company_name))
            self.job_table.setItem(row, 2, QtWidgets.QTableWidgetItem(job.job_title))
            self.job_table.setItem(row, 3, QtWidgets.QTableWidgetItem(job.required_skills))
    
    def add_job(self):
        """
        Yeni iş ilanı eklemek için bir diyalog penceresi açar.
        Kullanıcıdan gerekli bilgiler alınır, iş ilanı eklenir.
        """
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Add New Job")
        dlg_layout = QtWidgets.QFormLayout(dialog)
        company_edit = QtWidgets.QLineEdit()
        title_edit = QtWidgets.QLineEdit()
        description_edit = QtWidgets.QTextEdit()
        required_skills_edit = QtWidgets.QLineEdit()
        dlg_layout.addRow("Company Name:", company_edit)
        dlg_layout.addRow("Job Title:", title_edit)
        dlg_layout.addRow("Job Description:", description_edit)
        dlg_layout.addRow("Required Skills:", required_skills_edit)
        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        dlg_layout.addWidget(btn_box)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            company = company_edit.text().strip()
            title = title_edit.text().strip()
            description = description_edit.toPlainText().strip()
            required_skills = required_skills_edit.text().strip()
            if company and title and required_skills:
                self.main_window.backend.add_job(company, title, description, required_skills)
                self.refresh()
            else:
                QtWidgets.QMessageBox.warning(self, "Input Error", "Company, Title, and Required Skills are mandatory.")
    
    def remove_job(self):
        """
        Seçili iş ilanını kaldırmak için kullanılır.
        Seçili satırın job_id'si alınarak backend üzerinden silme işlemi yapılır.
        """
        selected = self.job_table.currentRow()
        if selected < 0:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a job to remove.")
            return
        job_id_item = self.job_table.item(selected, 0)
        if job_id_item:
            job_id = job_id_item.text()
            session = self.main_window.backend.session
            from backend import JobModel
            job = session.query(JobModel).filter_by(job_id=job_id).first()
            if job:
                session.delete(job)
                session.commit()
                self.refresh()


class HRInterviewManagementWidget(QtWidgets.QWidget):
    """
    HR'nin mülakatları yönetebilmesi için kullanılan widget.
    Başvuruları yükleme, mülakat planlama ve mülakat transcript'lerini görüntüleme işlevleri sunar.
    """
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  
        layout = QtWidgets.QVBoxLayout(self)
        
        # Başlık etiketi
        title = QtWidgets.QLabel("Interview Management")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px;")
        layout.addWidget(title)
        
        # Uygulanan iş ilanı seçimi ve başvuruların yüklenmesi için form
        form_layout = QtWidgets.QFormLayout()
        self.job_id_combo = QtWidgets.QComboBox()
        form_layout.addRow("Select Job:", self.job_id_combo)
        self.btn_load_applications = QtWidgets.QPushButton("Load Applications")
        self.btn_load_applications.clicked.connect(self.load_applications)
        form_layout.addRow("", self.btn_load_applications)
        layout.addLayout(form_layout)
        
        # Başvuruları listeleyen tablo: Aday kullanıcı adı, adı, ve anahtar beceriler
        self.applications_table = QtWidgets.QTableWidget()
        self.applications_table.setColumnCount(3)
        self.applications_table.setHorizontalHeaderLabels(["Candidate Username", "Candidate Name", "Key Skills"])
        self.applications_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.applications_table)
        
        # Mülakat planlama için ek form: Planlanacak zaman ve HR soruları
        form_layout2 = QtWidgets.QFormLayout()
        self.scheduled_time_edit = QtWidgets.QDateTimeEdit(datetime.datetime.now())
        self.scheduled_time_edit.setCalendarPopup(True)
        self.hr_questions_edit = QtWidgets.QTextEdit()
        self.hr_questions_edit.setPlaceholderText("Enter HR questions/requests for the interview here")
        form_layout2.addRow("Scheduled Time:", self.scheduled_time_edit)
        form_layout2.addRow("HR Questions:", self.hr_questions_edit)
        layout.addLayout(form_layout2)
        
        # Mülakatı planlama butonu
        self.btn_schedule = QtWidgets.QPushButton("Schedule Interview for Selected Candidate")
        self.btn_schedule.clicked.connect(self.schedule_interview)
        layout.addWidget(self.btn_schedule)
        
        # Mülakat transcript'ini görüntüleme butonu
        self.btn_view_transcript = QtWidgets.QPushButton("View Transcript")
        self.btn_view_transcript.clicked.connect(self.view_transcript)
        layout.addWidget(self.btn_view_transcript)
        
        # Tüm mülakatları listeleyen tablo: Mülakat ID, aday, iş ilanı, zaman, durum, puanlar ve transcript özeti
        self.interview_table = QtWidgets.QTableWidget()
        self.interview_table.setColumnCount(9)
        self.interview_table.setHorizontalHeaderLabels([
            "Interview ID", "Candidate", "Job ID", "Scheduled Time", "Status",
            "AI Score", "CV Matching (%)", "Final Matching (%)", "Transcript"
        ])
        self.interview_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.interview_table)
        
        self.setLayout(layout)
        self.refresh()
    
    def refresh(self):
        """
        HR Interview Management sayfasındaki tüm arayüz elemanlarını günceller.
        İş ilanı combobox'ı, uygulama tablosu ve mülakat tablosu backend verilerine göre yenilenir.
        """
        # İş ilanlarını combobox'a ekle
        self.job_id_combo.clear()
        jobs = self.main_window.backend.get_candidate_jobs()
        for job in jobs:
            self.job_id_combo.addItem(job.job_id)
        
        # Mülakat başvurularının ve mülakatların listelenmesi
        self.applications_table.setRowCount(0)
        session = self.main_window.backend.session
        from backend import InterviewModel, JobModel, CandidateModel
        interviews = session.query(InterviewModel).all()
        self.interview_table.setRowCount(0)
        for interview in interviews:
            row = self.interview_table.rowCount()
            self.interview_table.insertRow(row)
            self.interview_table.setItem(row, 0, QtWidgets.QTableWidgetItem(interview.interview_id))
            self.interview_table.setItem(row, 1, QtWidgets.QTableWidgetItem(interview.candidate_username))
            self.interview_table.setItem(row, 2, QtWidgets.QTableWidgetItem(interview.job_id))
            # Tarih ve saati okunabilir formata çevirir
            self.interview_table.setItem(row, 3, QtWidgets.QTableWidgetItem(interview.scheduled_time.strftime("%Y-%m-%d %H:%M")))
            self.interview_table.setItem(row, 4, QtWidgets.QTableWidgetItem(interview.status))
            ai_score_text = f"{interview.score:.2f}" if interview.score and interview.status=="Completed" else "N/A"
            self.interview_table.setItem(row, 5, QtWidgets.QTableWidgetItem(ai_score_text))
            # CV eşleşme oranı hesaplanır
            candidate = session.query(CandidateModel).filter_by(username=interview.candidate_username).first()
            job = session.query(JobModel).filter_by(job_id=interview.job_id).first()
            if candidate and job:
                cv_match = compute_matching_percentage(candidate, job)
                final_matching = (cv_match + interview.score) / 2
                cv_match_text = f"{cv_match:.2f}%"
                final_match_text = f"{final_matching:.2f}%"
            else:
                cv_match_text = "N/A"
                final_match_text = "N/A"
            self.interview_table.setItem(row, 6, QtWidgets.QTableWidgetItem(cv_match_text))
            self.interview_table.setItem(row, 7, QtWidgets.QTableWidgetItem(final_match_text))
            transcript_display = (interview.candidate_responses[:30] + "..." if interview.candidate_responses else "N/A")
            self.interview_table.setItem(row, 8, QtWidgets.QTableWidgetItem(transcript_display))
    
    def load_applications(self):
        """
        Seçilen iş ilanı için aday başvurularını yükler ve uygulama tablosunda listeler.
        """
        selected_job_id = self.job_id_combo.currentText()
        session = self.main_window.backend.session
        from backend import JobModel, ApplicationModel
        job = session.query(JobModel).filter_by(job_id=selected_job_id).first()
        if not job:
            QtWidgets.QMessageBox.warning(self, "Error", "Job not found.")
            return
        applications = session.query(ApplicationModel).filter_by(job_id=job.id).all()
        self.applications_table.setRowCount(0)
        for app in applications:
            candidate = app.candidate
            row = self.applications_table.rowCount()
            self.applications_table.insertRow(row)
            self.applications_table.setItem(row, 0, QtWidgets.QTableWidgetItem(candidate.username))
            self.applications_table.setItem(row, 1, QtWidgets.QTableWidgetItem(candidate.name))
            self.applications_table.setItem(row, 2, QtWidgets.QTableWidgetItem(candidate.key_skills))
    
    def schedule_interview(self):
        """
        Seçili aday için mülakat planlar.
        Adayın kullanıcı adı, seçili iş ilanı, planlanan zaman ve HR soruları kullanılarak yeni bir InterviewModel oluşturulur.
        """
        selected_row = self.applications_table.currentRow()
        if selected_row < 0:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a candidate from the applications list.")
            return
        candidate_username = self.applications_table.item(selected_row, 0).text()
        job_id = self.job_id_combo.currentText()
        scheduled_time = self.scheduled_time_edit.dateTime().toPyDateTime()
        hr_questions = self.hr_questions_edit.toPlainText().strip()
        if not hr_questions:
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please enter HR questions for the interview.")
            return
        session = self.main_window.backend.session
        from backend import InterviewModel
        interview_id = f"INT{session.query(InterviewModel).count() + 1}"
        new_interview = InterviewModel(
            interview_id=interview_id,
            candidate_username=candidate_username,
            job_id=job_id,
            scheduled_time=scheduled_time,
            status="Scheduled",
            hr_questions=hr_questions,
            candidate_responses="",
            score=0.0
        )
        session.add(new_interview)
        session.commit()
        QtWidgets.QMessageBox.information(self, "Success", f"Interview scheduled for candidate {candidate_username}.")
        self.refresh()
    
    def view_transcript(self):
        """
        Seçili mülakatın transcript'ini görüntülemek için diyalog penceresi açar.
        Eğer transcript mevcut değilse bilgilendirme mesajı gösterir.
        """
        selected_row = self.interview_table.currentRow()
        if selected_row < 0:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select an interview to view its transcript.")
            return
        session = self.main_window.backend.session
        from backend import InterviewModel
        interview_id = self.interview_table.item(selected_row, 0).text()
        interview = session.query(InterviewModel).filter_by(interview_id=interview_id).first()
        if interview and interview.candidate_responses:
            dlg = QtWidgets.QDialog(self)
            dlg.setWindowTitle(f"Transcript for {interview.interview_id}")
            dlg_layout = QtWidgets.QVBoxLayout(dlg)
            transcript_text = QtWidgets.QTextEdit()
            transcript_text.setReadOnly(True)
            transcript_text.setText(interview.candidate_responses)
            dlg_layout.addWidget(transcript_text)
            btn_close = QtWidgets.QPushButton("Close")
            btn_close.clicked.connect(dlg.accept)
            dlg_layout.addWidget(btn_close)
            dlg.exec_()
        else:
            QtWidgets.QMessageBox.information(self, "No Transcript", "No transcript is available for the selected interview.")


class HRDashboardWidget(QtWidgets.QWidget):
    """
    HR dashboard'ını temsil eden widget.
    İş ilanı yönetimi ve mülakat yönetimi sekmeleri içerir.
    """
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QtWidgets.QVBoxLayout(self)
        
        # Tab widget içerisinde iş ilanı ve mülakat yönetimi sekmeleri eklenir.
        self.tabs = QtWidgets.QTabWidget()
        self.job_management_tab = HRJobManagementWidget(self.main_window)
        self.interview_management_tab = HRInterviewManagementWidget(self.main_window)
        self.tabs.addTab(self.job_management_tab, "Job Management")
        self.tabs.addTab(self.interview_management_tab, "Interview Management")
        layout.addWidget(self.tabs)
        
        # Geri butonu ile ana menüye dönüş sağlanır.
        btn_back = QtWidgets.QPushButton("Back")
        btn_back.clicked.connect(lambda: self.main_window.switch_page(self.main_window.main_menu))
        layout.addWidget(btn_back)
        
        self.setLayout(layout)
    
    def refresh(self):
        """
        Dashboard'taki tüm alt widget'ların verilerini günceller.
        """
        self.job_management_tab.refresh()
        self.interview_management_tab.refresh()
