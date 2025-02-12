import os
import datetime
# SQLAlchemy ile veritabanı işlemleri için gerekli modüllerin import edilmesi
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
# PDF dosyalarını okumak için PyPDF2 kütüphanesi
from PyPDF2 import PdfReader
# Görüntü işleme için PIL (Python Imaging Library)
from PIL import Image
# Görüntülerdeki metni tespit etmek için pytesseract (OCR)
import pytesseract
# Metin gömme (embedding) ve benzerlik hesaplamaları için SentenceTransformer ve yardımcı fonksiyonlar
from sentence_transformers import SentenceTransformer, util
import torch  # PyTorch, embedding hesaplamalarında kullanılabilir
import openai  # OpenAI API'si ile etkileşim kurmak için

# OpenAI API anahtarı (Not: Gerçek projelerde bu anahtarın güvenliğini sağlamak için çevre değişkenleri veya güvenli yöntemler kullanın.)
openAPIkey = "YOUR_KEY_HERE"

# OpenAI API anahtarını ayarla
openai.api_key = openAPIkey

# SentenceTransformer modelini yükle; bu model, metinleri vektörlere çevirerek benzerlik hesaplamalarında kullanılacaktır.
model = SentenceTransformer('all-MiniLM-L6-v2')

# SQLAlchemy için ortak temel sınıf; tüm model sınıfları bu sınıftan türeyecektir.
Base = declarative_base()

# -----------------------------------------------------
# MODELLER: Veritabanı tablolarını temsil eden sınıflar
# -----------------------------------------------------

class CandidateModel(Base):
    """
    Adayların bilgilerini saklayan model.
    """
    __tablename__ = 'candidates'
    id = Column(Integer, primary_key=True)  # Her aday için benzersiz kimlik
    username = Column(String, unique=True, nullable=False)  # Benzersiz kullanıcı adı
    password = Column(String, nullable=False)  # Şifre (not: gerçek uygulamalarda şifrelerin hashlenmesi önerilir)
    name = Column(String, nullable=False)  # Adayın tam adı
    resume = Column(Text)  # Özgeçmiş metni
    key_skills = Column(Text)  # Adayın anahtar becerileri
    status = Column(String, default="Pending")  # Başvuru durumu, varsayılan "Pending" (beklemede)
    # Adayın yaptığı başvuruları temsil eden ilişki (ApplicationModel ile)
    applications = relationship("ApplicationModel", back_populates="candidate")


class AdminModel(Base):
    """
    Sistem yöneticilerinin bilgilerini saklayan model.
    """
    __tablename__ = 'admins'
    id = Column(Integer, primary_key=True)  # Benzersiz yönetici kimliği
    username = Column(String, unique=True, nullable=False)  # Benzersiz kullanıcı adı
    password = Column(String, nullable=False)  # Şifre
    name = Column(String, nullable=False)  # Yönetici adı


class HRModel(Base):
    """
    İnsan Kaynakları (HR) çalışanlarının bilgilerini saklayan model.
    """
    __tablename__ = 'hrs'
    id = Column(Integer, primary_key=True)  # Benzersiz HR kimliği
    username = Column(String, unique=True, nullable=False)  # Benzersiz kullanıcı adı
    password = Column(String, nullable=False)  # Şifre
    name = Column(String, nullable=False)  # HR çalışanının adı


class JobModel(Base):
    """
    İş ilanlarının bilgilerini saklayan model.
    """
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)  # Veritabanı içindeki benzersiz kimlik
    job_id = Column(String, unique=True, nullable=False)  # İş ilanı için benzersiz ID
    company_name = Column(String, nullable=False)  # Şirket adı
    job_title = Column(String, nullable=False)  # İş başlığı
    job_description = Column(Text)  # İş tanımı
    required_skills = Column(Text)  # İş için gerekli beceriler
    # İşe yapılan başvuruları temsil eden ilişki (ApplicationModel ile)
    applications = relationship("ApplicationModel", back_populates="job")


class InterviewModel(Base):
    """
    Mülakat (interview) bilgilerini saklayan model.
    """
    __tablename__ = 'interviews'
    id = Column(Integer, primary_key=True)  # Benzersiz mülakat kimliği
    interview_id = Column(String, unique=True, nullable=False)  # Mülakat için benzersiz ID
    candidate_username = Column(String, nullable=False)  # Adayın kullanıcı adı (mülakat yapan aday)
    job_id = Column(String, nullable=False)  # İlgili iş ilanının ID'si
    scheduled_time = Column(DateTime)  # Mülakatın planlanan tarihi ve saati
    status = Column(String, default="Scheduled")  # Mülakat durumu, varsayılan "Scheduled" (planlanmış)
    hr_questions = Column(Text)  # HR tarafından sorulan sorular
    candidate_responses = Column(Text, default="")  # Adayın yanıtları
    score = Column(Float, default=0.0)  # Adayın mülakattaki puanı


class ApplicationModel(Base):
    """
    Adayların iş başvurularını temsil eden model.
    """
    __tablename__ = 'applications'
    id = Column(Integer, primary_key=True)  # Benzersiz başvuru kimliği
    candidate_id = Column(Integer, ForeignKey('candidates.id'))  # Adayın ID'si (yabancı anahtar)
    job_id = Column(Integer, ForeignKey('jobs.id'))  # İş ilanının ID'si (yabancı anahtar)
    # Aday modeli ile çift yönlü ilişki kurulması
    candidate = relationship("CandidateModel", back_populates="applications")
    # İş ilanı modeli ile çift yönlü ilişki kurulması
    job = relationship("JobModel", back_populates="applications")


# -----------------------------------------------------
# YARDIMCI FONKSİYONLAR (UTILITY FUNCTIONS)
# -----------------------------------------------------

def parse_resume(file_path: str) -> str:
    """
    Verilen dosya yolundaki özgeçmiş dosyasını (PDF veya PNG) metin olarak çıkartır.
    
    :param file_path: Özgeçmiş dosyasının yolu.
    :return: Çıkartılan metin; hata durumunda boş string döner.
    """
    # Dosya mevcut değilse, boş string döndür
    if not os.path.isfile(file_path):
        return ""
    # Dosya uzantısını al ve küçük harfe çevir
    ext = os.path.splitext(file_path)[1].lower()
    extracted_text = ""
    try:
        if ext == ".pdf":
            # PDF dosyası ise, sayfa sayfa metin çıkar
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"
        elif ext == ".png":
            # PNG dosyası ise, OCR (Optik Karakter Tanıma) kullanarak metni çıkar
            image = Image.open(file_path)
            extracted_text = pytesseract.image_to_string(image)
    except Exception as e:
        # Hata durumunda, hatayı konsola yazdır
        print(f"Error parsing resume: {e}")
    # Gereksiz boşlukları kaldırarak metni döndür
    return extracted_text.strip()


def generate_dynamic_question(job_requirements, conversation_context):
    """
    İş gereksinimleri ve mevcut konuşma geçmişine dayanarak adayın deneyimini değerlendirmek amacıyla 
    dinamik bir takip sorusu oluşturur. OpenAI Chat API'si kullanılır.
    
    :param job_requirements: İş ilanının gereksinimleri (örneğin, aranan beceriler).
    :param conversation_context: Aday ile daha önce yapılan konuşmanın metni.
    :return: Oluşturulan takip sorusu.
    """
    # Konuşma geçmişinin uzunluğunu 1000 karakter ile sınırla; uzun ise son 1000 karakter kullanılır.
    truncated_context = conversation_context[-1000:] if len(conversation_context) > 1000 else conversation_context
    # OpenAI API'sine gönderilecek mesaj dizisi
    messages = [
        {"role": "system", "content": "You are a professional recruiter."},
        {"role": "user", "content": (
            f"Based on the job requirements: '{job_requirements}', and the conversation so far: '{truncated_context}', "
            "ask a follow-up question to evaluate the candidate's experience and knowledge."
        )}
    ]
    try:
        # OpenAI Chat API'si ile dinamik soru üretimi
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=60,         # Üretilen cevabın maksimum token sayısı
            temperature=0.7,       # Rastlantısallık ve yaratıcılık derecesi
        )
        # API yanıtından üretilen soruyu al
        question = response.choices[0].message["content"].strip()
    except Exception as e:
        # Hata durumunda, hatayı yazdır ve varsayılan bir soru döndür
        print(f"Error generating question: {e}")
        question = "Could you please provide more details about your experience?"
    return question


def compute_matching_percentage(candidate, job):
    # "MiniLM-L6-v2" modelinin kullanıldığı kısım
    """
    Adayın becerileri ile iş ilanının gereksinimleri arasındaki uyum oranını yüzde olarak hesaplar.
    Bunun için SentenceTransformer kullanılarak metin embedding'leri oluşturulur ve cosine similarity hesaplanır.
    
    :param candidate: CandidateModel örneği (aday)
    :param job: JobModel örneği (iş ilanı)
    :return: 0 ile 100 arasında, adayın iş gereksinimlerine ne kadar uyduğunu gösteren yüzdelik oran.
    """
    # Adayın anahtar becerileri için embedding oluştur
    candidate_embedding = model.encode(candidate.key_skills, convert_to_tensor=True)
    # İş ilanının gerektirdiği beceriler için embedding oluştur
    job_embedding = model.encode(job.required_skills, convert_to_tensor=True)
    # Cosine similarity (kosinüs benzerliği) hesaplanır
    similarity = util.cos_sim(candidate_embedding, job_embedding).item()
    return similarity * 100  # Yüzde değerine çevrilir


# -----------------------------------------------------
# İŞE ALIM SİSTEMİ BACKEND SINIFI
# -----------------------------------------------------

class RecruitmentSystemBackend:
    """
    Bu sınıf, işe alım sistemi backend'inde veritabanı işlemlerini ve iş mantığını yönetir.
    SQLAlchemy kullanılarak veritabanı bağlantısı, oturum yönetimi ve CRUD işlemleri gerçekleştirilir.
    """
    def __init__(self, db_url="sqlite:///recruitment.db"):
        """
        Sınıf örneği oluşturulduğunda veritabanı bağlantısı kurulur ve gerekli tablolar oluşturulur.
        
        :param db_url: Kullanılacak veritabanı URL'si (varsayılan olarak SQLite kullanılır).
        """
        # SQLAlchemy engine oluşturulur; echo=False ile SQL sorgularının konsola yazdırılması engellenir.
        self.engine = create_engine(db_url, echo=False)
        # Tabloları oluştur (eğer mevcut değilse)
        Base.metadata.create_all(self.engine)
        # Oturum (session) oluşturmak için sessionmaker kullanılır
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        # Demo verilerini ekle (örnek admin, HR ve iş ilanları)
        self.setup_demo_data()

    def setup_demo_data(self):
        """
        Sistemin temel işlevlerini test etmek amacıyla demo verileri (admin, HR ve örnek iş ilanları) ekler.
        """
        # Eğer "admin" adlı yönetici yoksa, yeni bir yönetici oluştur
        if not self.session.query(AdminModel).filter_by(username="admin").first():
            admin = AdminModel(username="admin", password="adminpass", name="Administrator")
            self.session.add(admin)
        # Eğer "hr" adlı HR çalışanı yoksa, yeni bir HR oluştur
        if not self.session.query(HRModel).filter_by(username="hr").first():
            hr = HRModel(username="hr", password="hrpass", name="HR Manager")
            self.session.add(hr)
        # Eğer henüz herhangi bir iş ilanı yoksa, örnek iş ilanları ekle
        if not self.session.query(JobModel).first():
            job1 = JobModel(job_id="JOB1", company_name="TechCorp", job_title="Software Engineer",
                            job_description="Develop scalable software solutions.",
                            required_skills="Python, Django, REST")
            job2 = JobModel(job_id="JOB2", company_name="DataInc", job_title="Data Scientist",
                            job_description="Analyze data and build models.",
                            required_skills="Python, Machine Learning, Data Analysis")
            self.session.add_all([job1, job2])
        # Yapılan eklemeleri veritabanına kaydet
        self.session.commit()

    def register_candidate(self, username, password, name, resume, key_skills):
        """
        Yeni bir aday kaydı oluşturur.
        
        :param username: Adayın kullanıcı adı
        :param password: Adayın şifresi
        :param name: Adayın adı
        :param resume: Adayın özgeçmiş metni
        :param key_skills: Adayın anahtar becerileri
        :return: (Başarı durumu, mesaj)
        """
        # Aynı kullanıcı adıyla daha önce kayıt yapılmış mı kontrol et
        if self.session.query(CandidateModel).filter_by(username=username).first():
            return False, "Username already exists."
        # Yeni aday nesnesi oluşturuluyor
        candidate = CandidateModel(username=username, password=password, name=name,
                                   resume=resume, key_skills=key_skills, status="Pending")
        self.session.add(candidate)
        self.session.commit()
        return True, "Registration successful."

    def candidate_login(self, username, password):
        """
        Aday giriş işlemini gerçekleştirir.
        
        :param username: Adayın kullanıcı adı
        :param password: Adayın şifresi
        :return: (Başarı durumu, aday nesnesi ya da hata mesajı)
        """
        candidate = self.session.query(CandidateModel).filter_by(username=username).first()
        if candidate and candidate.password == password:
            return True, candidate
        return False, "Invalid credentials."

    def admin_login(self, username, password):
        """
        Yönetici giriş işlemini gerçekleştirir.
        
        :param username: Yönetici kullanıcı adı
        :param password: Yönetici şifresi
        :return: (Başarı durumu, yönetici nesnesi ya da hata mesajı)
        """
        admin = self.session.query(AdminModel).filter_by(username=username).first()
        if admin and admin.password == password:
            return True, admin
        return False, "Invalid credentials."

    def hr_login(self, username, password):
        """
        HR (İnsan Kaynakları) giriş işlemini gerçekleştirir.
        
        :param username: HR kullanıcı adı
        :param password: HR şifresi
        :return: (Başarı durumu, HR nesnesi ya da hata mesajı)
        """
        hr = self.session.query(HRModel).filter_by(username=username).first()
        if hr and hr.password == password:
            return True, hr
        return False, "Invalid credentials."

    def add_job(self, company_name, job_title, job_description, required_skills):
        """
        Yeni bir iş ilanı ekler.
        
        :param company_name: Şirket adı
        :param job_title: İş başlığı
        :param job_description: İş tanımı
        :param required_skills: İş için gerekli beceriler
        """
        # İş ilanı için benzersiz bir job_id oluştur (mevcut iş sayısına göre)
        job_id = f"JOB{self.session.query(JobModel).count() + 1}"
        job = JobModel(job_id=job_id, company_name=company_name, job_title=job_title,
                       job_description=job_description, required_skills=required_skills)
        self.session.add(job)
        self.session.commit()

    def apply_for_job(self, candidate_username, job_id):
        """
        Belirtilen adayın, belirtilen iş ilanına başvurusunu gerçekleştirir.
        
        :param candidate_username: Adayın kullanıcı adı
        :param job_id: İş ilanı ID'si
        :return: (Başarı durumu, mesaj)
        """
        # Aday ve iş ilanı nesneleri veritabanından çekilir
        candidate = self.session.query(CandidateModel).filter_by(username=candidate_username).first()
        job = self.session.query(JobModel).filter_by(job_id=job_id).first()
        if not candidate or not job:
            return False, "Candidate or Job not found."
        # Adayın daha önce aynı işe başvurup başvurmadığı kontrol edilir
        if self.session.query(ApplicationModel).filter_by(candidate_id=candidate.id, job_id=job.id).first():
            return False, "Already applied."
        # Yeni başvuru nesnesi oluşturulur ve adayın durumu "Applied" olarak güncellenir
        application = ApplicationModel(candidate=candidate, job=job)
        candidate.status = "Applied"
        self.session.add(application)
        self.session.commit()
        return True, "Application successful."

    def get_candidate_jobs(self):
        """
        Tüm iş ilanlarını getirir.
        
        :return: İş ilanlarının listesi.
        """
        return self.session.query(JobModel).all()

    def get_all_candidates(self):
        """
        Sistemde kayıtlı tüm adayları getirir.
        
        :return: Aday nesnelerinin listesi.
        """
        return self.session.query(CandidateModel).all()

    def improved_match_candidates_to_job(self, job: JobModel):
        """
        Belirtilen iş ilanına uygun adayları, adayın beceri metni ile iş ilanı gereksinimleri arasındaki 
        cosine similarity (kosinüs benzerliği) baz alınarak sıralar.
        
        :param job: İş ilanı nesnesi.
        :return: (Aday, benzerlik skoru) çiftlerini içeren liste; benzerlik skoruna göre azalan sırada.
        """
        # İş ilanının gerektirdiği becerilerden embedding oluşturulur
        job_embedding = model.encode(job.required_skills, convert_to_tensor=True)
        matches = []
        # Veritabanındaki tüm adaylar üzerinden döngü
        for candidate in self.session.query(CandidateModel).all():
            # Adayın anahtar becerilerinden embedding oluşturulur
            candidate_embedding = model.encode(candidate.key_skills, convert_to_tensor=True)
            # Cosine similarity hesaplanır
            similarity = util.cos_sim(job_embedding, candidate_embedding).item()
            matches.append((candidate, similarity))
        # Adaylar, benzerlik skoruna göre büyükten küçüğe sıralanır
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
