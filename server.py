from fastapi import FastAPI, APIRouter, BackgroundTasks, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from email_service import send_contact_email


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str


# Contact Form Model
class ContactRequest(BaseModel):
    name: str
    phone: str
    email: EmailStr
    service: str
    message: str


class ContactResponse(BaseModel):
    status: str
    message: str


# Services data with images and reviews
SERVICES_DATA = {
    "elektrik-ariza": {
        "id": "elektrik-ariza",
        "title": "Elektrik Arıza Tamiri",
        "icon": "⚡",
        "short_desc": "7/24 acil müdahale ile tüm elektrik arızalarınıza hızlı çözüm",
        "full_desc": "Elektrik kesintileri, sigorta atmaları, kısa devre sorunları gibi tüm elektrik arızalarınıza 7/24 profesyonel hizmet sunuyoruz. Deneyimli ekibimiz, güvenli ve uygun fiyatlı çözümler için hemen arayın!",
        "images": [
            "https://images.unsplash.com/photo-1660330589693-99889d60181e",
            "https://images.pexels.com/photos/8853500/pexels-photo-8853500.jpeg",
            "https://images.pexels.com/photos/8853472/pexels-photo-8853472.jpeg"
        ],
        "reviews": [
            {"name": "Ahmet Yılmaz", "rating": 5, "comment": "Gece yarısı elektrik kesintisi oldu, hemen geldiler ve sorunu çözdüler. Çok teşekkürler!"},
            {"name": "Ayşe Demir", "rating": 5, "comment": "Profesyonel ve güvenilir hizmet. Fiyatlar çok uygun, kesinlikle tavsiye ederim."},
            {"name": "Mehmet Kaya", "rating": 5, "comment": "Sigorta sürekli atıyordu, sorunu kökten çözdüler. İşlerinde çok başarılılar."}
        ]
    },
    "ev-elektrik": {
        "id": "ev-elektrik",
        "title": "Ev Elektrik Tesisatı",
        "icon": "🏠",
        "short_desc": "Profesyonel elektrik tesisat kurulumu ve yenileme hizmetleri",
        "full_desc": "Yeni inşaat veya tadilat projeleriniz için tam tesisat hizmetleri sunuyoruz. Güvenli, standartlara uygun ve uzun ömürlü elektrik tesisatı için bize ulaşın.",
        "images": [
            "https://images.unsplash.com/photo-1615774925655-a0e97fc85c14",
            "https://images.pexels.com/photos/34404168/pexels-photo-34404168.jpeg",
            "https://images.pexels.com/photos/9242885/pexels-photo-9242885.jpeg"
        ],
        "reviews": [
            {"name": "Fatma Arslan", "rating": 5, "comment": "Ev yenilemesinde elektrik işlerini yaptırdık, mükemmel işçilik!"},
            {"name": "Ali Özkan", "rating": 5, "comment": "Temiz ve düzenli çalışıyorlar, işlerini hakkıyla yapıyorlar."},
            {"name": "Zeynep Çelik", "rating": 5, "comment": "Yeni evimizin tüm elektrik tesisatını yaptılar, çok memnun kaldık."}
        ]
    },
    "tadilat": {
        "id": "tadilat",
        "title": "Tadilat İşleri",
        "icon": "🔧",
        "short_desc": "Elektrik panosu değişimi, kablo çekimi ve tadilat işleri",
        "full_desc": "Eski elektrik tesisatınızı yenilemek, ek priz-anahtar takmak veya elektrik panosunu değiştirmek için profesyonel tadilat hizmetlerimizden yararlanın.",
        "images": [
            "https://images.unsplash.com/photo-1595856619767-ab739fa7daae",
            "https://images.pexels.com/photos/8853472/pexels-photo-8853472.jpeg",
            "https://images.pexels.com/photos/5691608/pexels-photo-5691608.jpeg"
        ],
        "reviews": [
            {"name": "Hakan Aydın", "rating": 5, "comment": "Eski elektrik panomuz çok eskiydi, yenilediler. Hem güvenli hem modern oldu."},
            {"name": "Elif Yıldız", "rating": 5, "comment": "Her odaya ek prizler taktırdık, çok pratik oldu. İşçilik çok iyiydi."},
            {"name": "Mustafa Kara", "rating": 5, "comment": "Tadilat sırasında elektrik işlerini yaptılar, zamanında ve temiz bitirdiler."}
        ]
    },
    "klima": {
        "id": "klima",
        "title": "Klima Montaj, Bakım ve Onarım",
        "icon": "❄️",
        "short_desc": "Klima montajı, bakımı, gaz dolumu ve tüm klima hizmetleri",
        "full_desc": "Tüm marka klima montajı, periyodik bakım, gaz dolumu, arıza onarımı ve temizlik hizmetleri. Uzman kadromuzla klimanızın verimliliğini artırıyoruz.",
        "images": [
            "https://images.unsplash.com/photo-1631545954854-576ffe7f2e6a",
            "https://images.pexels.com/photos/6069108/pexels-photo-6069108.jpeg",
            "https://images.pexels.com/photos/8092509/pexels-photo-8092509.jpeg"
        ],
        "reviews": [
            {"name": "Selin Öztürk", "rating": 5, "comment": "2 klima monte ettirdik, çok temiz ve özenli çalıştılar. Fiyat da uygundu."},
            {"name": "Burak Şahin", "rating": 5, "comment": "Klimam soğutmuyordu, gaz doldurdular ve bakımını yaptılar. Şimdi harika çalışıyor!"},
            {"name": "Deniz Koç", "rating": 5, "comment": "Her yıl klima bakımı yaptırıyorum, çok profesyoneller. Kesinlikle tavsiye ederim."}
        ]
    },
    "guvenlik-kamera": {
        "id": "guvenlik-kamera",
        "title": "Güvenlik Kamerası Sistemleri",
        "icon": "📷",
        "short_desc": "Güvenlik kamerası kurulumu, montajı ve teknik destek",
        "full_desc": "İşyeri ve ev güvenliğiniz için IP kamera, analog kamera ve kayıt sistemleri kurulumu. Uzaktan erişim ve 7/24 izleme imkanı.",
        "images": [
            "https://images.unsplash.com/photo-1557597774-9d273605dfa9",
            "https://images.pexels.com/photos/430208/pexels-photo-430208.jpeg",
            "https://images.pexels.com/photos/96612/pexels-photo-96612.jpeg"
        ],
        "reviews": [
            {"name": "Can Yılmaz", "rating": 5, "comment": "Dükkanıma 4 kamera taktırdım, telefondan canlı izleyebiliyorum. Çok memnunum."},
            {"name": "Ece Demir", "rating": 5, "comment": "Evimizin güvenliği için kamera sistemi kurdular, kurulum ve ayarlar mükemmeldi."},
            {"name": "Oğuz Arslan", "rating": 5, "comment": "Fabrikamıza kamera sistemi kurdular, gece görüşü de çok net çalışıyor."}
        ]
    },
    "boyler": {
        "id": "boyler",
        "title": "Sıcak Su Boyler Bakım Onarım ve Anot Değişimi",
        "icon": "🔥",
        "short_desc": "Boyler montajı, bakımı, onarımı ve anot değişimi hizmetleri",
        "full_desc": "Elektrikli su ısıtıcılarınızın (termosifon) montajı, bakımı, anot değişimi ve arıza onarımı. Uzun ömürlü kullanım için profesyonel hizmet.",
        "images": [
            "https://images.unsplash.com/photo-1585128792336-fb45eecad5cd",
            "https://images.pexels.com/photos/3964736/pexels-photo-3964736.jpeg",
            "https://images.pexels.com/photos/8853500/pexels-photo-8853500.jpeg"
        ],
        "reviews": [
            {"name": "Leyla Aydın", "rating": 5, "comment": "Boylerimin anotunu değiştirdiler, su ısınma problemi çözüldü. Teşekkürler!"},
            {"name": "Serkan Kaya", "rating": 5, "comment": "Yeni boyler taktırdım, montaj çok hızlı ve temiz oldu."},
            {"name": "Gizem Çelik", "rating": 5, "comment": "Boyler periyodik bakımını yaptırıyorum, uzun ömürlü olması için şart."}
        ]
    },
    "aydinlatma": {
        "id": "aydinlatma",
        "title": "Aydınlatma Sistemleri",
        "icon": "💡",
        "short_desc": "LED aydınlatma, spot montajı ve dekoratif aydınlatma çözümleri",
        "full_desc": "Modern LED sistemler, spot aydınlatma, şerit LED montajı ve tüm aydınlatma ihtiyaçlarınız için profesyonel çözümler sunuyoruz.",
        "images": [
            "https://images.unsplash.com/photo-1565814636199-ae8133055c1c",
            "https://images.pexels.com/photos/1112598/pexels-photo-1112598.jpeg",
            "https://images.pexels.com/photos/2251247/pexels-photo-2251247.jpeg"
        ],
        "reviews": [
            {"name": "Emre Özkan", "rating": 5, "comment": "Salon aydınlatması için spot sistemler taktırdık, harika görünüyor!"},
            {"name": "Nazlı Demir", "rating": 5, "comment": "Mutfakta şerit LED monte ettiler, hem fonksiyonel hem estetik."},
            {"name": "Tolga Şahin", "rating": 5, "comment": "Bahçe aydınlatması yaptırdık, gece çok güzel görünüyor."}
        ]
    },
    "audio": {
        "id": "audio",
        "title": "Audio Sistemleri",
        "icon": "🔊",
        "short_desc": "Ses sistemleri kurulumu, hoparlör montajı ve akustik çözümler",
        "full_desc": "Ev sinema sistemleri, çok kanallı ses sistemleri, hoparlör kurulumu ve profesyonel ses yalıtımı hizmetleri.",
        "images": [
            "https://images.unsplash.com/photo-1545259741-2ea3ebf61fa3",
            "https://images.pexels.com/photos/744318/pexels-photo-744318.jpeg",
            "https://images.pexels.com/photos/325682/pexels-photo-325682.jpeg"
        ],
        "reviews": [
            {"name": "Kaan Yıldız", "rating": 5, "comment": "Ev sinema sistemi kurdular, ses kalitesi muhteşem oldu!"},
            {"name": "Aylin Koç", "rating": 5, "comment": "Salona 5.1 ses sistemi taktırdık, montaj ve kablolama çok özenli yapıldı."},
            {"name": "Cem Arslan", "rating": 5, "comment": "Ofisimize anons sistemi kurdular, ses kalitesi çok net."}
        ]
    },
    "isyeri-elektrik": {
        "id": "isyeri-elektrik",
        "title": "İş Yeri Elektrik İşleri",
        "icon": "🏢",
        "short_desc": "Fabrika, ofis ve mağaza elektrik tesisatı ve otomasyon sistemleri",
        "full_desc": "Endüstriyel ve ticari elektrik tesisatı, üç fazlı sistem kurulumu, otomasyon ve tüm iş yeri elektrik ihtiyaçlarınız için çözümler.",
        "images": [
            "https://images.unsplash.com/photo-1581092921461-eab62e97a780",
            "https://images.pexels.com/photos/159775/construction-site-build-construction-work-159775.jpeg",
            "https://images.pexels.com/photos/585419/pexels-photo-585419.jpeg"
        ],
        "reviews": [
            {"name": "Mehmet Aydın", "rating": 5, "comment": "Fabrikamızın elektrik tesisatını yaptılar, hem güvenli hem verimli çalışıyor."},
            {"name": "Sibel Kaya", "rating": 5, "comment": "Mağazamızın tüm elektrik işlerini yaptılar, vitrin aydınlatması çok şık oldu."},
            {"name": "Hasan Çelik", "rating": 5, "comment": "Ofis elektrik tesisatını yenilediler, artık hiç sorun yaşamıyoruz."}
        ]
    }
}


# Routes using the router
@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}


@api_router.post("/statuscheck", response_model=StatusCheck)
async def create_status_check(status_check: StatusCheckCreate):
    status_check_dict = status_check.model_dump()
    status_check_dict["id"] = str(uuid.uuid4())
    status_check_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.status_checks.insert_one(status_check_dict)
    created_check = await db.status_checks.find_one({"id": status_check_dict["id"]})
    
    return StatusCheck(**created_check)


@api_router.get("/statuscheck", response_model=List[StatusCheck])
async def get_status_checks():
    checks = await db.status_checks.find().to_list(length=None)
    return [StatusCheck(**check) for check in checks]


# Services endpoints
@api_router.get("/services")
async def get_services():
    """Get all services with basic info"""
    services_list = [
        {
            "id": service["id"],
            "title": service["title"],
            "icon": service["icon"],
            "short_desc": service["short_desc"]
        }
        for service in SERVICES_DATA.values()
    ]
    return {"services": services_list}


@api_router.get("/services/{service_id}")
async def get_service_detail(service_id: str):
    """Get detailed service information including images and reviews"""
    if service_id not in SERVICES_DATA:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return {"service": SERVICES_DATA[service_id]}


# Contact form endpoint
@api_router.post("/contact", response_model=ContactResponse)
async def submit_contact_form(contact: ContactRequest, background_tasks: BackgroundTasks):
    """
    Handle contact form submission and send email
    """
    try:
        # Send email in background
        background_tasks.add_task(
            send_contact_email,
            contact.name,
            contact.phone,
            contact.email,
            contact.service,
            contact.message
        )
        
        return ContactResponse(
            status="success",
            message="Mesajınız başarıyla alındı. En kısa sürede size dönüş yapacağız."
        )
    except Exception as e:
        logging.error(f"Contact form error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Mesaj gönderilemedi. Lütfen daha sonra tekrar deneyin."
        )


# Mount the router to the app
app.include_router(api_router)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()