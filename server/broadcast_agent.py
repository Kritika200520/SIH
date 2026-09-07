# -*- coding: utf-8 -*-
"""
Bhoomi-Raksha: Broadcasting LLM Agent & Dialect Voice Synthesizer
Generates hyper-localized evacuation alerts translated into specific regional dialects.
"""
import os, hashlib
from gtts import gTTS

DIALECT_TEMPLATES = {
    "Garhwali": {
        "name": "Garhwali (Chamoli / Uttarakhand)",
        "lang_code": "hi",
        "text": "आपातकालीन चेतावनी! आपके क्षेत्र में भारी भूस्खलन का खतरा है। कृपया तुरंत सुरक्षित और ऊंचे स्थानों की ओर निकल जाएं।",
        "route_instruction": "नदी-नालों से दूर रहें और ऊपरी मार्ग (B-4) का प्रयोग करें।"
    },
    "Malayalam": {
        "name": "Malayalam (Wayanad / Kerala)",
        "lang_code": "ml",
        "text": "അടിയന്തര മുന്നറിയിപ്പ്! നിങ്ങളുടെ പ്രദേശത്ത് കനത്ത ഉരുൾപൊട്ടലിന് സാധ്യതയുണ്ട്. ദയവായി ഉടൻ തന്നെ സുരക്ഷിതമായ ഉയർന്ന സ്ഥലങ്ങളിലേക്ക് മാറുക.",
        "route_instruction": "നദികളിൽ നിന്നും അകന്നു നിൽക്കുക, സുരക്ഷിതമായ ഉയർന്ന വഴികൾ മാത്രം ഉപയോഗിക്കുക."
    },
    "Pahari": {
        "name": "Pahari / Himachali (Shimla)",
        "lang_code": "hi",
        "text": "चेतावनी! जमीन खिसकने का भारी खतरा है। कृपया तुरंत सुरक्षित आश्रयों की ओर प्रस्थान करें।",
        "route_instruction": "खड्डों से दूर रहें और मुख्य सड़क (बाईपास) का उपयोग करें।"
    },
    "Nepali": {
        "name": "Nepali (Darjeeling / Sikkim)",
        "lang_code": "ne",
        "text": "आपत्कालीन चेतावनी! तपाईको क्षेत्रमा गम्भीर पहिरोको जोखिम छ। कृपया तुरुन्तै सुरक्षित र उच्च स्थानहरूमा जानुहोस्।",
        "route_instruction": "खोला र नदीहरूबाट टाढा रहनुहोस् र सुरक्षित उच्च मार्गहरूको प्रयोग गर्नुहोस्।"
    },
    "Hindi": {
        "name": "Hindi (Common North)",
        "lang_code": "hi",
        "text": "गंभीर आपातकालीन चेतावनी: भारी भूस्खलन और मलबे के खतरे की पुष्टि हुई है। तुरंत नामित ऊंचे आश्रयों की ओर जाएं।",
        "route_instruction": "नदियों और खाइयों से बचें। आधिकारिक मंजूरी मिलने तक सुरक्षित ऊपरी बाईपास कॉरिडोर का पालन करें।"
    },
    "English": {
        "name": "English (National Broadcast)",
        "lang_code": "en",
        "text": "CRITICAL EMERGENCY WARNING: Severe landslide and debris torrent risk verified. Evacuate immediately to designated high ridge shelters.",
        "route_instruction": "Avoid river ravines and culverts. Follow high-ridge bypass corridors until official clearance."
    }
}

class BroadcastVoiceAgent:
    def __init__(self):
        self.dialects = DIALECT_TEMPLATES
        self.audio_dir = os.path.join(os.path.dirname(__file__), "static", "audio")
        os.makedirs(self.audio_dir, exist_ok=True)

    def generate_alert(self, dialect_key="Garhwali", sector_name="Chamoli"):
        dialect = self.dialects.get(dialect_key, self.dialects["Garhwali"])
        alert_text = f"[{dialect['name']}]\n\n" + dialect["text"] + "\n\n" + dialect["route_instruction"]
        
        audio_filename = f"alert_{dialect_key.lower()}.mp3"
        audio_path = os.path.join(self.audio_dir, audio_filename)
        
        if not os.path.exists(audio_path):
            try:
                tts = gTTS(text=dialect["text"] + " " + dialect["route_instruction"], lang=dialect["lang_code"], slow=False)
                tts.save(audio_path)
            except Exception as e:
                print(f"[TTS Audio Generation Note]: {e}")

        return {
            "dialect": dialect_key,
            "dialect_name": dialect["name"],
            "broadcast_text": alert_text,
            "speech_script": dialect["text"],
            "evacuation_route": dialect["route_instruction"],
            "audio_url": f"/static/audio/{audio_filename}" if os.path.exists(audio_path) else None,
            "channels": ["WhatsApp Voice Notes (95% Penetration)", "IVR Gram Pradhan Auto-Calls", "Village Loudspeaker Mesh"]
        }

    def list_dialects(self):
        return {k: v["name"] for k, v in self.dialects.items()}

broadcast_agent = BroadcastVoiceAgent()
