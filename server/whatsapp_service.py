# -*- coding: utf-8 -*-
"""
Bhoomi-Raksha: WhatsApp Cloud API Dispatcher & Webhook Service
Sends real-time hyper-localized dialect emergency alerts to citizen mobile numbers.
"""

import os
import requests

class WhatsAppService:
    def __init__(self):
        self.token = os.environ.get("WHATSAPP_TOKEN", "")
        self.phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "1364841016701806")
        self.api_version = "v21.0"
        self.api_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"

    def send_evacuation_alert(self, recipient_phone, alert_message, safe_route=""):
        """Sends live text evacuation notification to recipient WhatsApp."""
        if not self.token or not self.phone_number_id:
            return {"success": False, "simulated": True, "message": "WhatsApp credentials not configured, falling back to simulated dispatch."}

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        body_text = f"🚨 *BHOOMI-RAKSHA EMERGENCY DISASTER ALERT* 🚨\n\n{alert_message}\n\n🏔️ *Designated Safe Corridor:* {safe_route}\n\n_Automated Early Warning by Ministry of Earth Sciences / SIH_"

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_phone,
            "type": "text",
            "text": {
                "preview_url": True,
                "body": body_text
            }
        }

        try:
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=8)
            res_data = resp.json()
            if resp.status_code in [200, 201]:
                return {"success": True, "data": res_data, "message": f"Live WhatsApp SOS alert delivered to {recipient_phone}"}
            else:
                return {"success": False, "error": res_data, "message": f"WhatsApp API Error: {res_data.get('error', {}).get('message', 'Unknown')}"}
        except Exception as e:
            return {"success": False, "error": str(e), "message": f"Network error sending WhatsApp message: {str(e)}"}

whatsapp_service = WhatsAppService()
