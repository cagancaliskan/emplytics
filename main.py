import sys
from PyQt5 import QtWidgets
from backend import RecruitmentSystemBackend  # Backend'deki temel iş mantığı ve veritabanı işlemlerini yöneten sınıf
import ui_candidate  # Aday ile ilgili arayüz modülü
import ui_hr       # HR ile ilgili arayüz modülü
import ui_admin    # Admin ile ilgili arayüz modülü
import ui_main     # Ana menü ve genel arayüz modülü

def main():
    """
    Uygulamanın başlangıç fonksiyonu.
    PyQt uygulaması başlatılır, backend örneği oluşturulur,
    ve ana pencere (MainWindow) oluşturularak uygulama döngüsü başlatılır.
    """
    # PyQt uygulaması oluşturuluyor
    app = QtWidgets.QApplication(sys.argv)
    
    # Backend nesnesi oluşturuluyor; veritabanı bağlantısı ve demo veriler burada ayarlanıyor
    backend = RecruitmentSystemBackend()
    
    # Ana pencere oluşturuluyor; ilgili tüm UI modülleri ana pencereye aktarılıyor
    window = ui_main.MainWindow(backend, ui_candidate, ui_hr, ui_admin, ui_main)
    window.show()  # Ana pencere ekranda gösteriliyor
    
    # Uygulama döngüsü başlatılıyor; uygulama kapatılana kadar çalışır
    sys.exit(app.exec_())

if __name__ == "__main__":
    # Bu dosya doğrudan çalıştırıldığında main() fonksiyonu çağrılır
    main()
