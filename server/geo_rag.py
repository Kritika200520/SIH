# -*- coding: utf-8 -*-
"""
Bhoomi-Raksha: Geological Survey of India (GSI) & Geotechnical RAG Engine
Combines Soil Mechanics, InSAR Radar Displacement, and GSI Survey Knowledge Base.
"""
import math

GEOLOGICAL_SURVEY_PROFILES = {
    "chamoli_joshimath": {
        "id": "chamoli_joshimath",
        "region_name": "Chamoli - Joshimath Corridor, Uttarakhand",
        "state": "Uttarakhand",
        "primary_dialect": "Garhwali",
        "fallback_dialect": "Hindi",
        "coordinates": {"lat": 30.5562, "lng": 79.5636},
        "geology": "Main Central Thrust (MCT) shear zone, fractured Gneiss, Quartzite, and moraine overburden",
        "critical_slope_angle_deg": 36.5,
        "cohesion_kpa": 14.2,
        "friction_angle_deg": 28.0,
        "soil_density_kn_m3": 19.5,
        "rainfall_threshold_24h_mm": 65.0,
        "historical_events": [
            "1999 Chamoli M6.8 Earthquake slope destabilization",
            "2021 Rishiganga-Dhauliganga Debris Flow and Rock Avalanche",
            "2023 Joshimath Land Subsidence Crisis (MCT zone reactivation)"
        ],
        "evacuation_routes": {
            "safe_zones": ["Auli High Ridge (Elevation 2800m)", "Panchayat Bhawan Helipad Sector 4"],
            "danger_ravines": ["Alaknanda River Gorge", "Dhauliganga Nallah", "Marwari Downward Scarp"],
            "recommended_action": "Evacuate uphill towards Auli ridge path via B-4 bypass. Strictly avoid riverside ravines and lower market road."
        }
    },
    "wayanad_meppadi": {
        "id": "wayanad_meppadi",
        "region_name": "Meppadi - Chooralmala - Mundakkai, Wayanad",
        "state": "Kerala",
        "primary_dialect": "Malayalam",
        "fallback_dialect": "English",
        "coordinates": {"lat": 11.5332, "lng": 76.1320},
        "geology": "Lateritic soil mantle over Charnockite basement rock, high pore-water pressure vulnerability",
        "critical_slope_angle_deg": 32.0,
        "cohesion_kpa": 11.5,
        "friction_angle_deg": 25.5,
        "soil_density_kn_m3": 18.2,
        "rainfall_threshold_24h_mm": 120.0,
        "historical_events": [
            "2019 Puthumala Debris Flow and Estate Burial",
            "2024 Chooralmala-Mundakkai Catastrophic Landslide and Flash Flood"
        ],
        "evacuation_routes": {
            "safe_zones": ["Meppadi Higher Secondary School Relief Camp", "Chembra Peak High Ridge Shelter"],
            "danger_ravines": ["Iruvaipuzha River Basin", "Chooralmala Bridge Ravine", "Mundakkai Stream Gap"],
            "recommended_action": "Move immediately to Meppadi highland shelters. Keep clear of stream embankments and tea plantation slope gullies."
        }
    },
    "shimla_ridge": {
        "id": "shimla_ridge",
        "region_name": "Shimla Urban Ridge and Tutikandi, Himachal Pradesh",
        "state": "Himachal Pradesh",
        "primary_dialect": "Pahari",
        "fallback_dialect": "Hindi",
        "coordinates": {"lat": 31.1048, "lng": 77.1734},
        "geology": "Jutogh Group Quartzite, Chlorite Schist with heavy uncompacted construction surcharge",
        "critical_slope_angle_deg": 41.0,
        "cohesion_kpa": 16.0,
        "friction_angle_deg": 30.0,
        "soil_density_kn_m3": 20.1,
        "rainfall_threshold_24h_mm": 80.0,
        "historical_events": [
            "2023 Summer Monsoon Catastrophic Slope Failures (Summer Hill and Krishna Nagar)"
        ],
        "evacuation_routes": {
            "safe_zones": ["The Ridge Municipal Plaza", "Annandale Ground"],
            "danger_ravines": ["Krishna Nagar Downslope Nallah", "Summer Hill Ravine"],
            "recommended_action": "Evacuate downhill residences towards the upper Cart Road staging area. Avoid retaining walls showing tensile cracks."
        }
    },
    "darjeeling_tindharia": {
        "id": "darjeeling_tindharia",
        "region_name": "Tindharia - Kurseong Road, Darjeeling",
        "state": "West Bengal",
        "primary_dialect": "Nepali",
        "fallback_dialect": "Bengali",
        "coordinates": {"lat": 26.8580, "lng": 88.3360},
        "geology": "Daling Series Phyllites and Mica Schist, heavily weathered colluvium",
        "critical_slope_angle_deg": 35.0,
        "cohesion_kpa": 12.8,
        "friction_angle_deg": 27.2,
        "soil_density_kn_m3": 18.8,
        "rainfall_threshold_24h_mm": 95.0,
        "historical_events": [
            "2011 Tindharia NH-55 Subsidence",
            "2021 Paglajhora Colluvial Slump"
        ],
        "evacuation_routes": {
            "safe_zones": ["Kurseong Sub-divisional Hospital Ground", "Tindharia Workshop High Ground"],
            "danger_ravines": ["Paglajhora Sinking Zone", "Mahananda Catchment Stream"],
            "recommended_action": "Halt all vehicle movement along Hill Cart Road. Move residents of lower terraces to Tindharia High Ground."
        }
    }
}

SYNTHETIC_SAR_SERIES = {
    "chamoli_joshimath": [
        {"time": "T-60d", "displacement_mm": 1.2, "coherence": 0.89},
        {"time": "T-30d", "displacement_mm": 3.5, "coherence": 0.87},
        {"time": "T-15d", "displacement_mm": 6.8, "coherence": 0.85},
        {"time": "T-7d",  "displacement_mm": 10.4, "coherence": 0.82},
        {"time": "T-24h", "displacement_mm": 14.8, "coherence": 0.78}
    ],
    "wayanad_meppadi": [
        {"time": "T-60d", "displacement_mm": 0.8, "coherence": 0.91},
        {"time": "T-30d", "displacement_mm": 2.1, "coherence": 0.88},
        {"time": "T-15d", "displacement_mm": 5.4, "coherence": 0.84},
        {"time": "T-7d",  "displacement_mm": 9.2, "coherence": 0.80},
        {"time": "T-24h", "displacement_mm": 18.6, "coherence": 0.75}
    ],
    "shimla_ridge": [
        {"time": "T-60d", "displacement_mm": 0.5, "coherence": 0.92},
        {"time": "T-30d", "displacement_mm": 1.9, "coherence": 0.89},
        {"time": "T-15d", "displacement_mm": 4.2, "coherence": 0.86},
        {"time": "T-7d",  "displacement_mm": 7.6, "coherence": 0.81},
        {"time": "T-24h", "displacement_mm": 11.5, "coherence": 0.79}
    ]
}

class GeoRAGEngine:
    def __init__(self):
        self.profiles = GEOLOGICAL_SURVEY_PROFILES
        self.sar_series = SYNTHETIC_SAR_SERIES

    def find_nearest_sector(self, lat, lng):
        best_profile = None
        min_dist = float('inf')
        for key, p in self.profiles.items():
            clat = p["coordinates"]["lat"]
            clng = p["coordinates"]["lng"]
            dist = math.sqrt((lat - clat)**2 + (lng - clng)**2)
            if dist < min_dist:
                min_dist = dist
                best_profile = p
        return best_profile if best_profile else self.profiles["chamoli_joshimath"]

    def get_sar_data(self, sector_id):
        return self.sar_series.get(sector_id, self.sar_series["chamoli_joshimath"])

    def calculate_safety_factor(self, profile, slope_deg, saturation_ratio=0.85, insar_disp_mm=12.0):
        c = profile.get("cohesion_kpa", 14.0)
        phi = math.radians(profile.get("friction_angle_deg", 28.0))
        beta = math.radians(slope_deg)
        gamma = profile.get("soil_density_kn_m3", 19.5)
        gamma_w = 9.81
        z = 3.5
        hw = z * saturation_ratio

        effective_stress = (gamma * z - gamma_w * hw) * (math.cos(beta) ** 2)
        shear_strength = c + max(0.1, effective_stress) * math.tan(phi)
        shear_stress = gamma * z * math.sin(beta) * math.cos(beta)

        fs_raw = shear_strength / max(0.1, shear_stress)

        insar_penalty = 1.0
        if insar_disp_mm > 15.0:
            insar_penalty = 0.72
        elif insar_disp_mm > 8.0:
            insar_penalty = 0.85

        fs_final = round(fs_raw * insar_penalty, 2)
        
        if fs_final < 1.0:
            stability_status = "CRITICAL_FAILURE_IMMINENT"
        elif fs_final <= 1.3:
            stability_status = "UNSTABLE_MARGINAL"
        else:
            stability_status = "STABLE"

        return {
            "safety_factor_fs": fs_final,
            "stability_status": stability_status,
            "shear_strength_kpa": round(shear_strength, 2),
            "shear_stress_kpa": round(shear_stress, 2),
            "insar_penalty_applied": insar_penalty < 1.0,
            "soil_cohesion_kpa": c,
            "critical_slope_deg": profile["critical_slope_angle_deg"]
        }

    def query_rag_context(self, query_text, sector_id=None):
        sector = self.profiles.get(sector_id, self.profiles["chamoli_joshimath"])
        hist = ", ".join(sector["historical_events"])
        excerpts = [
            f"[GSI Hazard Atlas - Sheet {sector['id'].upper()}]: Region categorized under High-to-Very-High Landslide Susceptibility Zone (Zone IV/V).",
            f"[Geological Stratigraphy]: Bedrock consists of {sector['geology']}. Maximum critical equilibrium slope is {sector['critical_slope_angle_deg']} degrees.",
            f"[Hydrological Threshold]: 24-Hour trigger threshold is {sector['rainfall_threshold_24h_mm']} mm precipitation.",
            f"[Historical Baseline]: Previous recorded catastrophic events include {hist}."
        ]
        
        return {
            "matched_sector": sector["region_name"],
            "state": sector["state"],
            "primary_dialect": sector["primary_dialect"],
            "rag_excerpts": excerpts,
            "evacuation_guidance": sector["evacuation_routes"]
        }

geo_rag_engine = GeoRAGEngine()
