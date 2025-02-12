from PyQt5 import QtCore, QtWidgets
from backend import parse_resume, JobModel, InterviewModel, generate_dynamic_question, compute_matching_percentage

# ---------------------------
# ADAY İŞLEMLERİ İÇİN ARAYÜZ
# ---------------------------

class CandidateLoginWidget(QtWidgets.QWidget):
    """
    Aday giriş ekranını temsil eden widget.
    Kullanıcı adı ve şifre bilgilerini alır, adayın sisteme giriş yapmasını sağlar.
    """
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  
        layout = QtWidgets.QVBoxLayout()
        
        # Başlık etiketi: "Candidate Login"
        title = QtWidgets.QLabel("Candidate Login")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Form alanı: Kullanıcı adı ve şifre girişi
        form_layout = QtWidgets.QFormLayout()
        self.username_edit = QtWidgets.QLineEdit()
        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        form_layout.addRow("Username:", self.username_edit)
        form_layout.addRow("Password:", self.password_edit)
        layout.addLayout(form_layout)
        
        # Buton düzeni: Login ve Back butonları
        btn_layout = QtWidgets.QHBoxLayout()
        btn_login = QtWidgets.QPushButton("Login")
        btn_back = QtWidgets.QPushButton("Back")
        btn_login.clicked.connect(self.login)
        btn_back.clicked.connect(lambda: self.main_window.switch_page(self.main_window.main_menu))
        btn_layout.addWidget(btn_login)
        btn_layout.addWidget(btn_back)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)

    def login(self):
        """
        Adayın giriş bilgilerini kontrol eder, doğruysa dashboard'a yönlendirir.
        """
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        success, result = self.main_window.backend.candidate_login(username, password)
        if success:
            # Dashboard sayfasına aday bilgileri aktarılır ve ekran yenilenir.
            self.main_window.candidate_dashboard_page.set_candidate(result)
            self.main_window.candidate_dashboard_page.refresh()
            self.main_window.switch_page(self.main_window.candidate_dashboard_page)
        else:
            QtWidgets.QMessageBox.warning(self, "Login Failed", result)


class CandidateRegistrationWidget(QtWidgets.QWidget):
    """
    Aday kayıt ekranını temsil eden widget.
    Kayıt için gerekli bilgilerin (kullanıcı adı, şifre, tam ad, beceriler, CV) girilmesini sağlar.
    """
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  
        self.resume_text = ""
        layout = QtWidgets.QVBoxLayout()
        
        # Başlık etiketi: "Candidate Registration"
        title = QtWidgets.QLabel("Candidate Registration")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Form alanları: Kayıt için gerekli bilgilerin girilmesi
        form_layout = QtWidgets.QFormLayout()
        self.username_edit = QtWidgets.QLineEdit()
        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.name_edit = QtWidgets.QLineEdit()
        self.key_skills_edit = QtWidgets.QLineEdit()
        self.resume_edit = QtWidgets.QTextEdit()
        self.resume_edit.setPlaceholderText("Paste your resume here or use the Browse button to load a file (PDF/PNG)")
        
        form_layout.addRow("Username:", self.username_edit)
        form_layout.addRow("Password:", self.password_edit)
        form_layout.addRow("Full Name:", self.name_edit)
        form_layout.addRow("Key Skills (comma-separated):", self.key_skills_edit)
        form_layout.addRow("Resume:", self.resume_edit)
        layout.addLayout(form_layout)
        
        # Buton düzeni: Dosya tarama (Browse), kayıt ve geri butonları
        btn_layout = QtWidgets.QHBoxLayout()
        btn_browse = QtWidgets.QPushButton("Browse for CV File")
        btn_browse.clicked.connect(self.browse_file)
        btn_register = QtWidgets.QPushButton("Register")
        btn_register.clicked.connect(self.register)
        btn_back = QtWidgets.QPushButton("Back")
        btn_back.clicked.connect(lambda: self.main_window.switch_page(self.main_window.main_menu))
        btn_layout.addWidget(btn_browse)
        btn_layout.addWidget(btn_register)
        btn_layout.addWidget(btn_back)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)

    def browse_file(self):
        """
        Dosya seçme penceresini açar ve seçilen PDF/PNG dosyasını parse ederek CV metnini alır.
        """
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select CV File", "", "PDF Files (*.pdf);;PNG Files (*.png)"
        )
        if file_path:
            self.resume_text = parse_resume(file_path)
            if self.resume_text:
                self.resume_edit.setText(self.resume_text)
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to parse the selected file.")

    def register(self):
        """
        Kayıt formunda girilen bilgileri backend üzerinden kaydeder.
        Tüm alanların doldurulmuş olduğundan emin olur, eksik bilgi varsa hata mesajı gösterir.
        """
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        name = self.name_edit.text().strip()
        key_skills = self.key_skills_edit.text().strip()
        resume = self.resume_edit.toPlainText().strip()
        if not all([username, password, name, key_skills, resume]):
            QtWidgets.QMessageBox.warning(self, "Input Error", "All fields are required.")
            return
        success, msg = self.main_window.backend.register_candidate(username, password, name, resume, key_skills)
        if success:
            QtWidgets.QMessageBox.information(self, "Success", msg)
            self.main_window.switch_page(self.main_window.main_menu)
        else:
            QtWidgets.QMessageBox.warning(self, "Registration Failed", msg)


# ---------------------------
# ADAY DASHBOARD & AI MÜLAKAT DİYALOĞU
# ---------------------------

class CandidateAIInterviewDialog(QtWidgets.QDialog):
    """
    Adayların AI destekli mülakat oturumuna katılmalarını sağlayan diyalog penceresi.
    Mülakat boyunca adayın yanıtları, AI tarafından oluşturulan takip soruları ve toplam puan hesaplanır.
    """
    def __init__(self, interview, session, parent=None):
        super().__init__(parent)
        self.interview = interview
        self.session = session
        self.candidate_response_count = 0  # Adayın verebileceği maksimum yanıt sayısı (örneğin: 5)
        self.setWindowTitle(f"AI Interview Session - {interview.interview_id}")
        self.resize(600, 400)
        layout = QtWidgets.QVBoxLayout(self)
        # Mülakat sırasında oluşan konuşma metnini gösteren okuma alanı
        self.conversation_display = QtWidgets.QTextEdit()
        self.conversation_display.setReadOnly(True)
        layout.addWidget(self.conversation_display)
        # Adayın mesaj girebilmesi için giriş alanı
        self.input_line = QtWidgets.QLineEdit()
        layout.addWidget(self.input_line)
        # Mesaj gönderme butonu
        self.send_button = QtWidgets.QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        layout.addWidget(self.send_button)
        # Mülakatı bitirme butonu
        self.finish_button = QtWidgets.QPushButton("Finish Interview")
        self.finish_button.clicked.connect(self.finish_interview)
        layout.addWidget(self.finish_button)
        self.conversation = ""
        # Başlangıç olarak HR tarafından sorulan sorular eklenir
        initial_text = f"HR Questions:\n{self.interview.hr_questions}\n"
        self.append_conversation(initial_text)
    
    def append_conversation(self, text):
        """
        Konuşma metnine yeni bir satır ekler ve ekranda günceller.
        
        :param text: Eklenmek istenen metin.
        """
        self.conversation += text + "\n"
        self.conversation_display.setText(self.conversation)
    
    def send_message(self):
        """
        Adayın mesajını alır, konuşmaya ekler ve gerekli sayıda yanıt alınmamışsa AI tarafından yeni bir soru ekler.
        """
        candidate_msg = self.input_line.text().strip()
        if not candidate_msg:
            return
        self.append_conversation(f"Candidate: {candidate_msg}")
        self.input_line.clear()
        self.candidate_response_count += 1
        if self.candidate_response_count < 5:
            # Backend'den seçili iş ilanının required_skills'i kullanılarak dinamik takip sorusu üretilir
            job = self.session.query(JobModel).filter_by(job_id=self.interview.job_id).first()
            if job:
                followup = generate_dynamic_question(job.required_skills, self.conversation)
            else:
                followup = "Could you please elaborate?"
            self.append_conversation(f"AI Recruiter: {followup}")
        else:
            self.append_conversation("AI Recruiter: That is all for this interview. Thank you.")
            self.finish_interview()
    
    def finish_interview(self):
        """
        Mülakatı sonlandırır; adayın yanıtları üzerinden toplam puan hesaplanır,
        mülakatın durumunu "Completed" olarak günceller ve backend'e kaydeder.
        """
        candidate_lines = [line for line in self.conversation.splitlines() if line.startswith("Candidate:")]
        total_words = sum(len(line.split()) for line in candidate_lines)
        # Basit bir puanlama algoritması: Toplam kelime sayısı * 2, maksimum 100 puan.
        score = min(100, total_words * 2)
        self.interview.candidate_responses = self.conversation
        self.interview.score = score
        self.interview.status = "Completed"
        self.session.commit()
        QtWidgets.QMessageBox.information(self, "Interview Completed", f"Your interview is complete. Score: {score}")
        self.accept()


class CandidateDashboardWidget(QtWidgets.QWidget):
    """
    Aday dashboard'ını temsil eden widget.
    Adayın bilgilerini, başvurabileceği iş ilanlarını listeler ve mülakat oturumuna katılım sağlar.
    """
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  
        self.candidate = None  # Giriş yapan adayın bilgileri burada saklanır
        layout = QtWidgets.QVBoxLayout()
        
        # Dashboard başlığı
        self.title_label = QtWidgets.QLabel("Candidate Dashboard")
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; margin-bottom: 10px;")
        layout.addWidget(self.title_label)
        
        # Aday bilgilerini gösteren etiket
        self.info_label = QtWidgets.QLabel("")
        layout.addWidget(self.info_label)
        
        # İş ilanlarını listeleyen liste widget'ı
        self.job_list = QtWidgets.QListWidget()
        layout.addWidget(self.job_list)
        
        # Buton düzeni: İş başvurusu yapma ve mülakat oturumuna katılma
        btn_layout = QtWidgets.QHBoxLayout()
        btn_apply = QtWidgets.QPushButton("Apply for Selected Job")
        btn_apply.clicked.connect(self.apply_job)
        btn_layout.addWidget(btn_apply)
        self.join_interview_btn = QtWidgets.QPushButton("Join Interview Session")
        self.join_interview_btn.clicked.connect(self.join_interview)
        btn_layout.addWidget(self.join_interview_btn)
        layout.addLayout(btn_layout)
        
        # Çıkış (Logout) butonu
        btn_logout = QtWidgets.QPushButton("Logout")
        btn_logout.clicked.connect(lambda: self.main_window.switch_page(self.main_window.main_menu))
        layout.addWidget(btn_logout)
        
        self.setLayout(layout)
    
    def set_candidate(self, candidate):
        """
        Giriş yapan adayın bilgisini ayarlar.
        
        :param candidate: Backend'den alınan aday nesnesi.
        """
        self.candidate = candidate
    
    def refresh(self):
        """
        Dashboard verilerini günceller; adayın bilgileri ve iş ilanları listesi yenilenir.
        """
        if not self.candidate:
            return
        applied_jobs = [app.job.job_id for app in self.candidate.applications if app.job]
        info = (f"Name: {self.candidate.name}\n"
                f"Username: {self.candidate.username}\n"
                f"Status: {self.candidate.status}\n"
                f"Applied Jobs: {', '.join(applied_jobs) if applied_jobs else 'None'}")
        self.info_label.setText(info)
        self.job_list.clear()
        for job in self.main_window.backend.get_candidate_jobs():
            item_text = (f"{job.job_id}: {job.job_title} at {job.company_name}\n"
                         f"Description: {job.job_description}\n"
                         f"Required Skills: {job.required_skills}")
            item = QtWidgets.QListWidgetItem(item_text)
            item.setData(QtCore.Qt.UserRole, job.job_id)
            self.job_list.addItem(item)
    
    def apply_job(self):
        """
        Seçili iş ilanına adayın başvurusunu gerçekleştirir.
        """
        selected = self.job_list.currentItem()
        if not selected:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a job to apply for.")
            return
        job_id = selected.data(QtCore.Qt.UserRole)
        success, msg = self.main_window.backend.apply_for_job(self.candidate.username, job_id)
        if success:
            QtWidgets.QMessageBox.information(self, "Success", msg)
            self.refresh()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", msg)
    
    def join_interview(self):
        """
        Adayın planlanmış mülakat oturumuna katılmasını sağlar.
        Backend üzerinden adayın mülakatları çekilir, gerekirse seçim diyalogu açılır.
        """
        session = self.main_window.backend.session
        interviews = session.query(InterviewModel).filter_by(candidate_username=self.candidate.username, status="Scheduled").all()
        if not interviews:
            QtWidgets.QMessageBox.information(self, "No Interview", "You have no scheduled interviews.")
            return
        if len(interviews) == 1:
            chosen = interviews[0]
        else:
            choices = [f"{i.interview_id} (Job: {i.job_id})" for i in interviews]
            item, ok = QtWidgets.QInputDialog.getItem(self, "Select Interview", "Choose an interview session:", choices, 0, False)
            if not ok:
                return
            chosen = interviews[choices.index(item)]
        # Mülakat diyalog penceresi açılır
        dialog = CandidateAIInterviewDialog(chosen, session, self)
        dialog.exec_()
        self.refresh()
