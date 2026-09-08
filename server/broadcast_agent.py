# -*- coding: utf-8 -*-
"""
Bhoomi-Raksha: Broadcasting LLM Agent & Dialect Voice Synthesizer
Generates hyper-localized evacuation alerts translated into specific regional dialects.
"""
import os, hashlib
from gtts import gTTS

DIALECT_TEMPLATES = {
    "Nepali": {
        "name": "Nepali (Darjeeling / Sikkim)",
        "lang_code": "ne",
        "text": "आपत्कालीन चेतावनी! तपाईंको क्षेत्रमा गम्भीर पहिरोको उच्च जोखिम छ। कृपया तुरुन्त सुरक्षित र अग्लो स्थानतर्फ जानुहोस्।",
        "route_instruction": "खोला र नदीहरूबाट टाढा रहनुहोस् र माथिल्लो बाईपास मार्ग (B-4) प्रयोग गर्नुहोस्।"
    },
    "Garhwali": {
        "name": "Garhwali (Chamoli / Uttarakhand)",
        "lang_code": "hi",
        "text": "सावधान! तुम्हारा इलाका मा भारी भूस्खलन को खतरा च। कृप्या तुरंत सुरक्षित और डांडा (ऊंचे स्थान) की तरफ जावा।",
        "route_instruction": "गाड़-गदेरा (नदी-नालों) से दूर रवां और माथिल्लो बाटो (B-4 बाईपास) को प्रयोग करा।"
    },
    "Pahari": {
        "name": "Pahari / Himachali (Shimla)",
        "lang_code": "hi",
        "text": "चेतावनी! ज़मीन खिसकणे रा भारी ख़तरा ऐ। कृपया सारे तुरंत सुरखित ऊंचे स्थानां जो प्रस्थान करो।",
        "route_instruction": "खड्डों ते दूर रओ ते मथेला रस्ता (B-4 बाईपास) बरतिया।"
    },
    "Hindi": {
        "name": "Hindi (Common North)",
        "lang_code": "hi",
        "text": "आपातकालीन चेतावनी! आपके क्षेत्र में भारी भूस्खलन का खतरा है। कृपया तुरंत सुरक्षित और ऊंचे स्थानों की ओर निकल जाएं।",
        "route_instruction": "नदी-नालों से दूर रहें और ऊपरी सुरक्षित मार्ग (B-4 बाईपास) का प्रयोग करें।"
    },
    "English": {
        "name": "English (National Broadcast)",
        "lang_code": "en",
        "text": "CRITICAL EMERGENCY WARNING: Severe landslide and debris torrent risk verified. Evacuate immediately to designated high ridge shelters.",
        "route_instruction": "Avoid river ravines and culverts. Follow high-ridge bypass corridors (B-4) until official clearance."
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
