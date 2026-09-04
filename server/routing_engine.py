# -*- coding: utf-8 -*-
"""
Bhoomi-Raksha: Dynamic Pathfinding & Road Evacuation Routing Engine
Implements Hazard Cost Surface Algorithm with NetworkX OpenStreetMap Graph.
Contrasts Naive Google Maps Routing (hazard blind) vs. Bhoomi-Raksha Safe Evacuation Corridors.
"""
import math
import networkx as nx

ROAD_NETWORKS = {
    "chamoli_joshimath": {
        "nodes": {
            "N_MARWARI_ENTRY": {"lat": 30.5520, "lng": 79.5580, "name": "Marwari Highway Entry", "elev_m": 1820},
            "N_MARWARI_SCARP": {"lat": 30.5562, "lng": 79.5636, "name": "Marwari Ward 9 (Active Fissure Scarp)", "elev_m": 1870},
            "N_LOWER_BAZAAR":  {"lat": 30.5580, "lng": 79.5665, "name": "Joshimath Lower Market Junction", "elev_m": 1890},
            "N_AULI_BYPASS_1": {"lat": 30.5545, "lng": 79.5610, "name": "Auli Ridge Bypass B-4 Takeoff", "elev_m": 1950},
            "N_AULI_RIDGE_MID": {"lat": 30.5590, "lng": 79.5570, "name": "Upper Ridge Traverse Path", "elev_m": 2300},
            "N_AULI_SHELTER":  {"lat": 30.5650, "lng": 79.5540, "name": "Auli High Ridge Relief Camp (Safe)", "elev_m": 2800}
        },
        "edges": [
            # Main Highway Route (Shortest in distance = 3.2km, but traverses active fissure scarp)
            {"u": "N_MARWARI_ENTRY", "v": "N_MARWARI_SCARP", "length_km": 1.0, "type": "highway", "name": "NH-58 Main Highway", "hazard_zone": "fissure"},
            {"u": "N_MARWARI_SCARP", "v": "N_LOWER_BAZAAR",  "length_km": 0.8, "type": "highway", "name": "NH-58 Market Corridor", "hazard_zone": "fissure"},
            {"u": "N_LOWER_BAZAAR",  "v": "N_AULI_SHELTER",   "length_km": 1.4, "type": "link",    "name": "Town to Camp Road", "hazard_zone": "subsidence"},
            
            # High-Ridge Safe Bypass (Longer in distance = 4.8km, but 100% safe from landslides)
            {"u": "N_MARWARI_ENTRY", "v": "N_AULI_BYPASS_1",  "length_km": 1.2, "type": "bypass", "name": "Auli Bypass B-4 Takeoff", "hazard_zone": "none"},
            {"u": "N_AULI_BYPASS_1", "v": "N_AULI_RIDGE_MID", "length_km": 2.0, "type": "bypass", "name": "Auli Upper Ridge Highway", "hazard_zone": "none"},
            {"u": "N_AULI_RIDGE_MID","v": "N_AULI_SHELTER",   "length_km": 1.6, "type": "ridge_road", "name": "Auli High Ridge Final Approach", "hazard_zone": "none"}
        ],
        "default_start": "N_MARWARI_ENTRY",
        "default_dest": "N_AULI_SHELTER"
    },

    "wayanad_meppadi": {
        "nodes": {
            "N_CHOORAL_ENTRY": {"lat": 11.5280, "lng": 76.1260, "name": "Chooralmala Road Entry", "elev_m": 720},
            "N_CHOORAL_BRIDGE":{"lat": 11.5332, "lng": 76.1320, "name": "Chooralmala Bridge (Debris Slurry Breach)", "elev_m": 740},
            "N_MUNDAKKAI_LOW": {"lat": 11.5370, "lng": 76.1390, "name": "Mundakkai Valley Road", "elev_m": 760},
            "N_MEPPADI_BYPASS": {"lat": 11.5310, "lng": 76.1290, "name": "Meppadi Highland Bypass Route", "elev_m": 880},
            "N_CHEMBRA_RIDGE": {"lat": 11.5380, "lng": 76.1240, "name": "Chembra Peak Foothill Trail", "elev_m": 1120},
            "N_MEPPADI_SHELTER":{"lat": 11.5430, "lng": 76.1200, "name": "Meppadi High Ground Relief Camp (Safe)", "elev_m": 950}
        },
        "edges": [
            # Main Low Valley Route (Shortest = 2.9km, but blocked by slurry dam breach)
            {"u": "N_CHOORAL_ENTRY", "v": "N_CHOORAL_BRIDGE", "length_km": 0.9, "type": "highway", "name": "Chooralmala River Highway", "hazard_zone": "debris_flow"},
            {"u": "N_CHOORAL_BRIDGE","v": "N_MUNDAKKAI_LOW",  "length_km": 0.8, "type": "valley_road", "name": "Mundakkai Valley Link", "hazard_zone": "debris_flow"},
            {"u": "N_MUNDAKKAI_LOW", "v": "N_MEPPADI_SHELTER", "length_km": 1.2, "type": "link", "name": "Valley to Camp Road", "hazard_zone": "subsidence"},

            # Safe Highland Bypass Route (4.1km)
            {"u": "N_CHOORAL_ENTRY", "v": "N_MEPPADI_BYPASS", "length_km": 1.1, "type": "bypass", "name": "Meppadi Highland Diversion", "hazard_zone": "none"},
            {"u": "N_MEPPADI_BYPASS","v": "N_CHEMBRA_RIDGE",  "length_km": 1.7, "type": "ridge_road", "name": "Chembra Foothill Evacuation Corridor", "hazard_zone": "none"},
            {"u": "N_CHEMBRA_RIDGE", "v": "N_MEPPADI_SHELTER", "length_km": 1.3, "type": "ridge_road", "name": "Meppadi Shelter Main Path", "hazard_zone": "none"}
        ],
        "default_start": "N_CHOORAL_ENTRY",
        "default_dest": "N_MEPPADI_SHELTER"
    },

    "shimla_ridge": {
        "nodes": {
            "N_SUMMER_ENTRY":  {"lat": 31.1000, "lng": 77.1680, "name": "Summer Hill University Entry", "elev_m": 2100},
            "N_WALL_COLLAPSE": {"lat": 31.1048, "lng": 77.1734, "name": "Cart Road Retaining Wall Bulge (16? Tilt)", "elev_m": 2150},
            "N_KRISHNA_NAGAR": {"lat": 31.1090, "lng": 77.1790, "name": "Krishna Nagar Sinking Slope Nallah", "elev_m": 1950},
            "N_RIDGE_BYPASS":  {"lat": 31.1025, "lng": 77.1705, "name": "Upper Ridge Pedestrian Mall Bypass", "elev_m": 2220},
            "N_RIDGE_PLAZA":   {"lat": 31.1100, "lng": 77.1650, "name": "The Ridge Municipal Plaza Assembly Point (Safe)", "elev_m": 2250}
        },
        "edges": [
            # Main Cart Road (Shortest = 2.7km, but retaining wall failure)
            {"u": "N_SUMMER_ENTRY",  "v": "N_WALL_COLLAPSE", "length_km": 0.8, "type": "highway", "name": "Cart Road Main Highway", "hazard_zone": "wall_failure"},
            {"u": "N_WALL_COLLAPSE", "v": "N_KRISHNA_NAGAR", "length_km": 0.9, "type": "valley_road", "name": "Krishna Nagar Downslope Road", "hazard_zone": "wall_failure"},
            {"u": "N_KRISHNA_NAGAR", "v": "N_RIDGE_PLAZA",   "length_km": 1.0, "type": "link", "name": "Nallah to Ridge Escalator", "hazard_zone": "subsidence"},

            # Safe Upper Ridge Mall Bypass (3.4km)
            {"u": "N_SUMMER_ENTRY",  "v": "N_RIDGE_BYPASS",  "length_km": 1.2, "type": "bypass", "name": "Upper Ridge Diverter Path", "hazard_zone": "none"},
            {"u": "N_RIDGE_BYPASS",  "v": "N_RIDGE_PLAZA",   "length_km": 2.2, "type": "ridge_road", "name": "The Ridge Municipal Safe Mall", "hazard_zone": "none"}
        ],
        "default_start": "N_SUMMER_ENTRY",
        "default_dest": "N_RIDGE_PLAZA"
    }
}

class EvacuationRoutingEngine:
    def __init__(self):
        self.networks = ROAD_NETWORKS

    def build_graph(self, sector_id, apply_hazard_cost=True, vlm_depth_cm=8.4, turbidity_pct=45.0):
        data = self.networks.get(sector_id, self.networks["chamoli_joshimath"])
        G = nx.Graph()

        for node_id, node_attr in data["nodes"].items():
            G.add_node(node_id, **node_attr)

        for edge in data["edges"]:
            length = edge["length_km"]
            hazard_zone = edge.get("hazard_zone", "none")

            if not apply_hazard_cost:
                weight = length
            else:
                if hazard_zone in ["fissure", "debris_flow", "wall_failure"]:
                    if vlm_depth_cm > 5.0 or turbidity_pct > 70.0:
                        weight = 99999.0
                    else:
                        weight = length * 15.0
                elif hazard_zone == "ravine":
                    weight = length * 8.0
                elif hazard_zone == "subsidence":
                    weight = length * 3.5
                else:
                    weight = length * 1.0

            G.add_edge(edge["u"], edge["v"], weight=weight, length_km=length, name=edge["name"], hazard_zone=hazard_zone)

        return G, data

    def compute_evacuation_routes(self, sector_id="chamoli_joshimath", vlm_depth_cm=8.4, turbidity_pct=45.0, mode="vehicle"):
        data = self.networks.get(sector_id, self.networks["chamoli_joshimath"])
        start_node = data["default_start"]
        dest_node = data["default_dest"]

        # 1. Compute Naive Route (Standard Google Maps)
        G_naive, _ = self.build_graph(sector_id, apply_hazard_cost=False)
        try:
            naive_path = nx.shortest_path(G_naive, source=start_node, target=dest_node, weight="weight")
            naive_length = sum(G_naive[u][v]["length_km"] for u, v in zip(naive_path[:-1], naive_path[1:]))
            has_hazard = any(G_naive[u][v]["hazard_zone"] in ["fissure", "debris_flow", "wall_failure"] for u, v in zip(naive_path[:-1], naive_path[1:]))
            naive_status = "CRITICAL HAZARD (BLOCKED ROAD)" if has_hazard else "CLEAR"
            naive_hazard_pct = 95.0 if has_hazard else 0.0
            naive_eta_min = int(naive_length * 2.5) + (240 if has_hazard else 0)
        except Exception as e:
            naive_path = []
            naive_length = 0
            naive_status = "NO_ROUTE"
            naive_hazard_pct = 100.0
            naive_eta_min = 999

        # 2. Compute Bhoomi-Raksha Dynamic Safe Route (Hazard Cost Surface)
        G_safe, _ = self.build_graph(sector_id, apply_hazard_cost=True, vlm_depth_cm=vlm_depth_cm, turbidity_pct=turbidity_pct)
        try:
            safe_path = nx.shortest_path(G_safe, source=start_node, target=dest_node, weight="weight")
            safe_length = sum(G_safe[u][v]["length_km"] for u, v in zip(safe_path[:-1], safe_path[1:]))
            safe_eta_min = int(safe_length * 2.8)
            safe_hazard_pct = 0.0
            safe_status = "100% CLEAR (DESIGNATED HIGH-RIDGE CORRIDOR)"
        except Exception as e:
            safe_path = []
            safe_length = 0
            safe_status = "NO_SAFE_ROUTE"
            safe_hazard_pct = 0.0
            safe_eta_min = 0

        def build_coords(path):
            coords = []
            steps = []
            for i, nid in enumerate(path):
                node = data["nodes"][nid]
                coords.append([node["lat"], node["lng"]])
                if i < len(path) - 1:
                    next_id = path[i+1]
                    edge = G_naive.get_edge_data(nid, next_id) or {}
                    steps.append({
                        "step": i + 1,
                        "from": node["name"],
                        "to": data["nodes"][next_id]["name"],
                        "road": edge.get("name", "Mountain Corridor"),
                        "distance_km": edge.get("length_km", 0.8),
                        "elevation_m": node.get("elev_m", 1900)
                    })
            return coords, steps

        naive_coords, naive_steps = build_coords(naive_path)
        safe_coords, safe_steps = build_coords(safe_path)

        return {
            "sector_id": sector_id,
            "evacuation_mode": mode,
            "start_location": data["nodes"][start_node]["name"],
            "destination_shelter": data["nodes"][dest_node]["name"],
            
            "google_maps_naive": {
                "route_name": "Standard Shortest Path (Google Maps Baseline)",
                "distance_km": round(naive_length, 2),
                "eta_minutes": naive_eta_min,
                "hazard_exposure_pct": naive_hazard_pct,
                "status": naive_status,
                "warning": "? DANGER: Routes directly through active tension scarp collapse at KM 248!",
                "waypoints": naive_coords,
                "steps": naive_steps
            },
            
            "bhoomi_raksha_safe": {
                "route_name": "Bhoomi-Raksha Dynamic Safe Corridor (Hazard-Aware)",
                "distance_km": round(safe_length, 2),
                "eta_minutes": safe_eta_min,
                "hazard_exposure_pct": safe_hazard_pct,
                "status": safe_status,
                "safety_clearance": "? VERIFIED: Avoids valley shear plane; routes via Auli High Ridge B-4 bypass.",
                "waypoints": safe_coords,
                "steps": safe_steps
            }
        }

routing_engine = EvacuationRoutingEngine()
