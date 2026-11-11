import urllib.request
import json
import os
import datetime
import math
import sys

# ==============================================================================
# BALKAN RESEARCH METEOROLOGICAL NETWORK (209 SENSORS)
# Covering:
# 1. North Macedonia (85 nodes: all municipalities, mountains, lakes, ski resorts)
# 2. Northern & Central Greece (74 nodes: Aegean coast, Olympus, Pindus, Chalkidiki)
# 3. Albania (50 nodes: Adriatic & Ionian coasts, Ohrid/Prespa, Alps, Korab)
# ==============================================================================

STATIONS = [
    # --- NORTH MACEDONIA (85 stations) ---
    {"id": "mk_gev_home", "name": "Gevgelija Bulevar 18", "country": "MK", "region": "Gevgelija", "lat": 41.1465, "lon": 22.5042},
    {"id": "mk_gev_center", "name": "Gevgelija Center", "country": "MK", "region": "Gevgelija", "lat": 41.1417, "lon": 22.5083},
    {"id": "mk_gev_mrzen", "name": "Mrzenci", "country": "MK", "region": "Gevgelija", "lat": 41.1681, "lon": 22.5019},
    {"id": "mk_bogdanci", "name": "Bogdanci", "country": "MK", "region": "Gevgelija", "lat": 41.2031, "lon": 22.5786},
    {"id": "mk_dojran_st", "name": "Star Dojran", "country": "MK", "region": "Dojran", "lat": 41.1783, "lon": 22.7203},
    {"id": "mk_dojran_nv", "name": "Nov Dojran", "country": "MK", "region": "Dojran", "lat": 41.2225, "lon": 22.7056},
    {"id": "mk_valandovo", "name": "Valandovo", "country": "MK", "region": "Valandovo", "lat": 41.3169, "lon": 22.5614},
    {"id": "mk_val_pirava", "name": "Pirava", "country": "MK", "region": "Valandovo", "lat": 41.3211, "lon": 22.5317},
    {"id": "mk_udovo", "name": "Udovo", "country": "MK", "region": "Valandovo", "lat": 41.3439, "lon": 22.4411},
    {"id": "mk_demir_kapija", "name": "Demir Kapija Gorge", "country": "MK", "region": "Demir Kapija", "lat": 41.4111, "lon": 22.2422},
    {"id": "mk_kavadarci", "name": "Kavadarci", "country": "MK", "region": "Tikvesh", "lat": 41.4331, "lon": 22.0119},
    {"id": "mk_negotino", "name": "Negotino", "country": "MK", "region": "Tikvesh", "lat": 41.4844, "lon": 22.0911},
    {"id": "mk_rosoman", "name": "Rosoman", "country": "MK", "region": "Tikvesh", "lat": 41.5167, "lon": 21.9472},
    {"id": "mk_tikves_lake", "name": "Tikvesh Lake", "country": "MK", "region": "Tikvesh", "lat": 41.3789, "lon": 21.9436},
    {"id": "mk_veles_c", "name": "Veles Center", "country": "MK", "region": "Veles", "lat": 41.7165, "lon": 21.7723},
    {"id": "mk_veles_lake", "name": "Mladost Lake Veles", "country": "MK", "region": "Veles", "lat": 41.7761, "lon": 21.7583},
    {"id": "mk_gradsko", "name": "Gradsko", "country": "MK", "region": "Veles", "lat": 41.5778, "lon": 21.9428},
    {"id": "mk_strumica_c", "name": "Strumica Center", "country": "MK", "region": "Strumica", "lat": 41.4378, "lon": 22.6433},
    {"id": "mk_str_bansko", "name": "Bansko Spa Strumica", "country": "MK", "region": "Strumica", "lat": 41.3839, "lon": 22.7444},
    {"id": "mk_str_novoselo", "name": "Novo Selo", "country": "MK", "region": "Strumica", "lat": 41.4139, "lon": 22.8814},
    {"id": "mk_radovis", "name": "Radovis", "country": "MK", "region": "Radovis", "lat": 41.6383, "lon": 22.4644},
    {"id": "mk_stip_c", "name": "Stip Center", "country": "MK", "region": "Stip", "lat": 41.7458, "lon": 22.1958},
    {"id": "mk_stip_kril", "name": "Stip Airport", "country": "MK", "region": "Stip", "lat": 41.7708, "lon": 22.1486},
    {"id": "mk_sveti_nikole", "name": "Sveti Nikole", "country": "MK", "region": "Ovce Pole", "lat": 41.8650, "lon": 21.9428},
    {"id": "mk_probistip", "name": "Probistip", "country": "MK", "region": "Probistip", "lat": 41.9961, "lon": 22.1811},
    {"id": "mk_kocani", "name": "Kocani", "country": "MK", "region": "Kocani", "lat": 41.9167, "lon": 22.4128},
    {"id": "mk_vinica", "name": "Vinica", "country": "MK", "region": "Vinica", "lat": 41.8828, "lon": 22.5092},
    {"id": "mk_delcevo", "name": "Delcevo", "country": "MK", "region": "Pijanec", "lat": 41.9667, "lon": 22.7667},
    {"id": "mk_pehcevo", "name": "Pehcevo", "country": "MK", "region": "Maleshevo", "lat": 41.7622, "lon": 22.8889},
    {"id": "mk_berovo", "name": "Berovo", "country": "MK", "region": "Maleshevo", "lat": 41.7056, "lon": 22.8578},
    {"id": "mk_berovo_lake", "name": "Berovo Lake", "country": "MK", "region": "Maleshevo", "lat": 41.6917, "lon": 22.9233},
    {"id": "mk_kriva_palanka", "name": "Kriva Palanka", "country": "MK", "region": "Northeast", "lat": 42.2017, "lon": 22.3319},
    {"id": "mk_kratovo", "name": "Kratovo", "country": "MK", "region": "Northeast", "lat": 42.0783, "lon": 22.1806},
    {"id": "mk_kumanovo_c", "name": "Kumanovo Center", "country": "MK", "region": "Kumanovo", "lat": 42.1322, "lon": 21.7144},
    {"id": "mk_kumanovo_n", "name": "Lipkovo Lake", "country": "MK", "region": "Kumanovo", "lat": 42.1561, "lon": 21.5889},
    {"id": "mk_skopje_c", "name": "Skopje Center", "country": "MK", "region": "Skopje", "lat": 41.9981, "lon": 21.4254},
    {"id": "mk_skopje_karpos", "name": "Skopje Karposh", "country": "MK", "region": "Skopje", "lat": 42.0050, "lon": 21.3917},
    {"id": "mk_skopje_aerodrom", "name": "Skopje Aerodrom", "country": "MK", "region": "Skopje", "lat": 41.9856, "lon": 21.4647},
    {"id": "mk_skopje_gazi_baba", "name": "Skopje Gazi Baba", "country": "MK", "region": "Skopje", "lat": 42.0089, "lon": 21.4550},
    {"id": "mk_skopje_vodno", "name": "Mount Vodno Millennium Cross", "country": "MK", "region": "Skopje", "lat": 41.9650, "lon": 21.3944},
    {"id": "mk_skopje_airp", "name": "Skopje International Airport", "country": "MK", "region": "Skopje", "lat": 41.9616, "lon": 21.6214},
    {"id": "mk_skopje_matka", "name": "Matka Canyon", "country": "MK", "region": "Skopje", "lat": 41.9547, "lon": 21.2975},
    {"id": "mk_tetovo_c", "name": "Tetovo Center", "country": "MK", "region": "Polog", "lat": 42.0106, "lon": 20.9714},
    {"id": "mk_popova_sapka", "name": "Popova Shapka Ski 1780m", "country": "MK", "region": "Shar Planina", "lat": 42.0150, "lon": 20.8767},
    {"id": "mk_gostivar_c", "name": "Gostivar Center", "country": "MK", "region": "Polog", "lat": 41.7961, "lon": 20.9083},
    {"id": "mk_vrutok", "name": "Vrutok Vardar Spring", "country": "MK", "region": "Polog", "lat": 41.7686, "lon": 20.8389},
    {"id": "mk_mavrovo_ski", "name": "Mavrovo Zare Lazareski 1300m", "country": "MK", "region": "Mavrovo", "lat": 41.7011, "lon": 20.7389},
    {"id": "mk_mavrovo_lake", "name": "Mavrovo Lake", "country": "MK", "region": "Mavrovo", "lat": 41.6889, "lon": 20.7250},
    {"id": "mk_rostusa", "name": "Rostusha Radika River", "country": "MK", "region": "Mavrovo", "lat": 41.6094, "lon": 20.6000},
    {"id": "mk_debar_c", "name": "Debar Center", "country": "MK", "region": "Debar", "lat": 41.5250, "lon": 20.5272},
    {"id": "mk_debar_lake", "name": "Debar Lake Spilje", "country": "MK", "region": "Debar", "lat": 41.5056, "lon": 20.5056},
    {"id": "mk_kicevo_c", "name": "Kicevo Center", "country": "MK", "region": "Kicevo", "lat": 41.5139, "lon": 20.9597},
    {"id": "mk_struga_c", "name": "Struga Lakefront", "country": "MK", "region": "Ohrid-Prespa", "lat": 41.1775, "lon": 20.6789},
    {"id": "mk_struga_drin", "name": "Black Drin Outflow", "country": "MK", "region": "Ohrid-Prespa", "lat": 41.1822, "lon": 20.6756},
    {"id": "mk_ohrid_c", "name": "Ohrid Port", "country": "MK", "region": "Ohrid-Prespa", "lat": 41.1128, "lon": 20.8019},
    {"id": "mk_ohrid_airp", "name": "Ohrid St Paul Airport", "country": "MK", "region": "Ohrid-Prespa", "lat": 41.1800, "lon": 20.7425},
    {"id": "mk_sveti_naum", "name": "Sveti Naum Springs", "country": "MK", "region": "Ohrid-Prespa", "lat": 40.9142, "lon": 20.7431},
    {"id": "mk_galicica_pass", "name": "Galicica Pass 1568m", "country": "MK", "region": "Galicica", "lat": 40.9567, "lon": 20.8350},
    {"id": "mk_resen_c", "name": "Resen Center", "country": "MK", "region": "Ohrid-Prespa", "lat": 41.0889, "lon": 21.0117},
    {"id": "mk_prespa_stenje", "name": "Stenje Lake Prespa", "country": "MK", "region": "Ohrid-Prespa", "lat": 40.9556, "lon": 20.9056},
    {"id": "mk_prespa_pretor", "name": "Pretor Lake Prespa", "country": "MK", "region": "Ohrid-Prespa", "lat": 40.9789, "lon": 21.0617},
    {"id": "mk_bitola_c", "name": "Bitola Center Sirok Sokak", "country": "MK", "region": "Pelagonia", "lat": 41.0319, "lon": 21.3347},
    {"id": "mk_bitola_heraklea", "name": "Heraclea Lyncestis", "country": "MK", "region": "Pelagonia", "lat": 41.0114, "lon": 21.3425},
    {"id": "mk_pelister_magaro", "name": "Pelister Baba Mountain 2400m", "country": "MK", "region": "Pelister", "lat": 41.0028, "lon": 21.1814},
    {"id": "mk_pelister_begova", "name": "Pelister Begova Cesma 1420m", "country": "MK", "region": "Pelister", "lat": 41.0361, "lon": 21.2333},
    {"id": "mk_prilep_c", "name": "Prilep Center", "country": "MK", "region": "Pelagonia", "lat": 41.3464, "lon": 21.5542},
    {"id": "mk_prilep_varos", "name": "Markovi Kuli Prilep", "country": "MK", "region": "Pelagonia", "lat": 41.3589, "lon": 21.5333},
    {"id": "mk_krusevo_c", "name": "Krusevo Meckin Kamen 1250m", "country": "MK", "region": "Pelagonia", "lat": 41.3689, "lon": 21.2489},
    {"id": "mk_demir_hisar", "name": "Demir Hisar", "country": "MK", "region": "Pelagonia", "lat": 41.2211, "lon": 21.2033},
    {"id": "mk_kozuf_smrdliva", "name": "Kozuf Smrdliva Voda 850m", "country": "MK", "region": "Kozuf", "lat": 41.1917, "lon": 22.3167},
    {"id": "mk_kozuf_ski", "name": "Kozuf Ski Center 1650m", "country": "MK", "region": "Kozuf", "lat": 41.1611, "lon": 22.2194},
    {"id": "mk_kozuf_dzena", "name": "Mount Dzena / Kozuf 2160m", "country": "MK", "region": "Kozuf", "lat": 41.1444, "lon": 22.1861},
    {"id": "mk_belasica_kolesino", "name": "Kolesino Waterfall Belasica", "country": "MK", "region": "Belasica", "lat": 41.3811, "lon": 22.8100},
    {"id": "mk_belasica_smolare", "name": "Smolare Waterfall Belasica", "country": "MK", "region": "Belasica", "lat": 41.3667, "lon": 22.8989},
    {"id": "mk_plackovica", "name": "Mount Plackovica 1500m", "country": "MK", "region": "East", "lat": 41.7611, "lon": 22.4861},
    {"id": "mk_osogovo", "name": "Osogovo Mountains 1600m", "country": "MK", "region": "East", "lat": 42.1583, "lon": 22.4283},
    {"id": "mk_brod_makedonski", "name": "Makedonski Brod", "country": "MK", "region": "Porece", "lat": 41.5133, "lon": 21.2150},
    {"id": "mk_kozjak_dam", "name": "Kozjak Reservoir", "country": "MK", "region": "Porece", "lat": 41.8797, "lon": 21.1983},
    {"id": "mk_bogomila", "name": "Bogomila Babuna", "country": "MK", "region": "Babuna", "lat": 41.5939, "lon": 21.4706},
    {"id": "mk_casca", "name": "Casca", "country": "MK", "region": "Babuna", "lat": 41.6517, "lon": 21.6617},
    {"id": "mk_gradsko_stobi", "name": "Stobi Archaeological Site", "country": "MK", "region": "Vardar Valley", "lat": 41.5517, "lon": 21.9750},
    {"id": "mk_miravci", "name": "Miravci Gevgelija Basin", "country": "MK", "region": "Gevgelija", "lat": 41.3075, "lon": 22.4356},
    {"id": "mk_smokvica", "name": "Smokvica Vardar Corridor", "country": "MK", "region": "Gevgelija", "lat": 41.2589, "lon": 22.4689},
    {"id": "mk_gev_konsko", "name": "Konsko Kozuf Foothills", "country": "MK", "region": "Gevgelija", "lat": 41.1594, "lon": 22.3789},
    {"id": "mk_gev_huma", "name": "Huma Mountain Village", "country": "MK", "region": "Gevgelija", "lat": 41.1539, "lon": 22.3106},

    # --- NORTHERN & CENTRAL GREECE (74 stations) ---
    {"id": "gr_evzonoi", "name": "Evzonoi Border Post", "country": "GR", "region": "Central Macedonia", "lat": 41.1067, "lon": 22.5539},
    {"id": "gr_idomeni", "name": "Idomeni Railway Station", "country": "GR", "region": "Central Macedonia", "lat": 41.1114, "lon": 22.5111},
    {"id": "gr_polykastro", "name": "Polykastro Axios Basin", "country": "GR", "region": "Central Macedonia", "lat": 40.9967, "lon": 22.5706},
    {"id": "gr_axioupoli", "name": "Axioupoli", "country": "GR", "region": "Central Macedonia", "lat": 40.9856, "lon": 22.5406},
    {"id": "gr_goumenissa", "name": "Goumenissa Paiko Foot", "country": "GR", "region": "Central Macedonia", "lat": 40.9486, "lon": 22.4494},
    {"id": "gr_paiko_mt", "name": "Mount Paiko 1400m", "country": "GR", "region": "Central Macedonia", "lat": 40.9700, "lon": 22.3200},
    {"id": "gr_kilkis_c", "name": "Kilkis Center", "country": "GR", "region": "Central Macedonia", "lat": 40.9931, "lon": 22.8744},
    {"id": "gr_doirani_gr", "name": "Doirani Lake South Shore", "country": "GR", "region": "Central Macedonia", "lat": 41.1667, "lon": 22.7667},
    {"id": "gr_drosato", "name": "Drosato", "country": "GR", "region": "Central Macedonia", "lat": 41.1711, "lon": 22.8094},
    {"id": "gr_kastanies_k", "name": "Kastanies Kilkis", "country": "GR", "region": "Central Macedonia", "lat": 41.0350, "lon": 22.7567},
    {"id": "gr_giannitsa", "name": "Giannitsa Central Plain", "country": "GR", "region": "Central Macedonia", "lat": 40.7933, "lon": 22.4139},
    {"id": "gr_pella", "name": "Ancient Pella", "country": "GR", "region": "Central Macedonia", "lat": 40.7600, "lon": 22.5200},
    {"id": "gr_edessa", "name": "Edessa Waterfalls", "country": "GR", "region": "Central Macedonia", "lat": 40.8039, "lon": 22.0489},
    {"id": "gr_kassandreia", "name": "Kassandreia Chalkidiki", "country": "GR", "region": "Chalkidiki", "lat": 40.0483, "lon": 23.4144},
    {"id": "gr_naoussa", "name": "Naoussa Vermio Foothills", "country": "GR", "region": "Central Macedonia", "lat": 40.6289, "lon": 22.0667},
    {"id": "gr_vermio_ski", "name": "Vermio Ski Seli 1500m", "country": "GR", "region": "Central Macedonia", "lat": 40.5478, "lon": 21.9167},
    {"id": "gr_veria", "name": "Veria Aliakmon Basin", "country": "GR", "region": "Central Macedonia", "lat": 40.5244, "lon": 22.2028},
    {"id": "gr_alexandreia", "name": "Alexandreia Imathia", "country": "GR", "region": "Central Macedonia", "lat": 40.6278, "lon": 22.4444},
    {"id": "gr_thess_c", "name": "Thessaloniki White Tower", "country": "GR", "region": "Thessaloniki", "lat": 40.6264, "lon": 22.9484},
    {"id": "gr_thess_port", "name": "Thessaloniki Port", "country": "GR", "region": "Thessaloniki", "lat": 40.6350, "lon": 22.9300},
    {"id": "gr_thess_kalam", "name": "Kalamaria Coast", "country": "GR", "region": "Thessaloniki", "lat": 40.5833, "lon": 22.9500},
    {"id": "gr_thess_airp", "name": "Thessaloniki Airport SKG", "country": "GR", "region": "Thessaloniki", "lat": 40.5197, "lon": 22.9708},
    {"id": "gr_thermi", "name": "Thermi", "country": "GR", "region": "Thessaloniki", "lat": 40.5478, "lon": 23.0189},
    {"id": "gr_sindos", "name": "Sindos Axios Delta", "country": "GR", "region": "Thessaloniki", "lat": 40.6706, "lon": 22.8050},
    {"id": "gr_chalastra", "name": "Chalastra Delta Wetland", "country": "GR", "region": "Thessaloniki", "lat": 40.6267, "lon": 22.7300},
    {"id": "gr_epeiro_kor", "name": "Korinos Pieria", "country": "GR", "region": "Pieria", "lat": 40.3150, "lon": 22.5850},
    {"id": "gr_katerini_c", "name": "Katerini Center", "country": "GR", "region": "Pieria", "lat": 40.2697, "lon": 22.5061},
    {"id": "gr_litochoro", "name": "Litochoro Olympus Base", "country": "GR", "region": "Pieria", "lat": 40.1044, "lon": 22.5033},
    {"id": "gr_olympus_prion", "name": "Mount Olympus Prionia 1100m", "country": "GR", "region": "Olympus", "lat": 40.0833, "lon": 22.4083},
    {"id": "gr_olympus_peak", "name": "Mount Olympus Mytikas 2917m", "country": "GR", "region": "Olympus", "lat": 40.0883, "lon": 22.3586},
    {"id": "gr_platamonas", "name": "Platamonas Coastal Pass", "country": "GR", "region": "Pieria", "lat": 39.9917, "lon": 22.5931},
    {"id": "gr_tempi_valley", "name": "Tempi Valley Pineios", "country": "GR", "region": "Thessaly", "lat": 39.8767, "lon": 22.5833},
    {"id": "gr_larissa_c", "name": "Larissa Central Plain", "country": "GR", "region": "Thessaly", "lat": 39.6390, "lon": 22.4191},
    {"id": "gr_volos_port", "name": "Volos Port Pagasetic Gulf", "country": "GR", "region": "Thessaly", "lat": 39.3622, "lon": 22.9422},
    {"id": "gr_pelion_ski", "name": "Mount Pelion Ski 1200m", "country": "GR", "region": "Thessaly", "lat": 39.3900, "lon": 23.0767},
    {"id": "gr_kozani_c", "name": "Kozani Plateau", "country": "GR", "region": "Western Macedonia", "lat": 40.3006, "lon": 21.7889},
    {"id": "gr_ptolemaida", "name": "Ptolemaida Basin", "country": "GR", "region": "Western Macedonia", "lat": 40.5122, "lon": 21.6789},
    {"id": "gr_amyntaio", "name": "Amyntaio Vegoritida Lake", "country": "GR", "region": "Western Macedonia", "lat": 40.6900, "lon": 21.6800},
    {"id": "gr_vegoritida", "name": "Lake Vegoritida Shore", "country": "GR", "region": "Western Macedonia", "lat": 40.7500, "lon": 21.7833},
    {"id": "gr_florina_c", "name": "Florina Center", "country": "GR", "region": "Western Macedonia", "lat": 40.7828, "lon": 21.4097},
    {"id": "gr_vigla_ski", "name": "Pisoderi Vigla Ski 1650m", "country": "GR", "region": "Western Macedonia", "lat": 40.7717, "lon": 21.2717},
    {"id": "gr_prespes_gr", "name": "Mikri Prespa Agios Achilleios", "country": "GR", "region": "Western Macedonia", "lat": 40.8167, "lon": 21.0833},
    {"id": "gr_kastoria_c", "name": "Kastoria Lake Orestiada", "country": "GR", "region": "Western Macedonia", "lat": 40.5217, "lon": 21.2633},
    {"id": "gr_nestorio", "name": "Nestorio Aliakmon River", "country": "GR", "region": "Western Macedonia", "lat": 40.4139, "lon": 21.0617},
    {"id": "gr_grevena_c", "name": "Grevena", "country": "GR", "region": "Western Macedonia", "lat": 40.0847, "lon": 21.4278},
    {"id": "gr_vasilitsa_ski", "name": "Vasilitsa Pindus Ski 1800m", "country": "GR", "region": "Western Macedonia", "lat": 40.0389, "lon": 21.0861},
    {"id": "gr_metsovo", "name": "Metsovo Katara Pass 1160m", "country": "GR", "region": "Epirus", "lat": 39.7700, "lon": 21.1833},
    {"id": "gr_ioannina_c", "name": "Ioannina Lake Pamvotis", "country": "GR", "region": "Epirus", "lat": 39.6672, "lon": 20.8519},
    {"id": "gr_ioannina_airp", "name": "Ioannina King Pyrros Airport", "country": "GR", "region": "Epirus", "lat": 39.6964, "lon": 20.8225},
    {"id": "gr_konitsa", "name": "Konitsa Aoos Gorge", "country": "GR", "region": "Epirus", "lat": 40.0461, "lon": 20.7483},
    {"id": "gr_serres_c", "name": "Serres Center", "country": "GR", "region": "Central Macedonia", "lat": 41.0847, "lon": 23.5478},
    {"id": "gr_sidirokastro", "name": "Sidirokastro Struma Pass", "country": "GR", "region": "Central Macedonia", "lat": 41.2350, "lon": 23.3939},
    {"id": "gr_promachonas", "name": "Promachonas Border", "country": "GR", "region": "Central Macedonia", "lat": 41.3650, "lon": 23.3633},
    {"id": "gr_kerkini_lake", "name": "Lake Kerkini Wetland", "country": "GR", "region": "Central Macedonia", "lat": 41.2167, "lon": 23.1500},
    {"id": "gr_nigrita", "name": "Nigrita Strymonic Plain", "country": "GR", "region": "Central Macedonia", "lat": 40.9067, "lon": 23.4989},
    {"id": "gr_amfipoli", "name": "Amfipoli Strymon River Mouth", "country": "GR", "region": "Central Macedonia", "lat": 40.8222, "lon": 23.8472},
    {"id": "gr_asprovalta", "name": "Asprovalta Strymonic Gulf", "country": "GR", "region": "Central Macedonia", "lat": 40.7183, "lon": 23.7056},
    {"id": "gr_stavros", "name": "Stavros Strymonic Bay", "country": "GR", "region": "Central Macedonia", "lat": 40.6650, "lon": 23.6967},
    {"id": "gr_ierissos", "name": "Ierissos Mount Athos Gate", "country": "GR", "region": "Chalkidiki", "lat": 40.3989, "lon": 23.8767},
    {"id": "gr_ouranoupoli", "name": "Ouranoupoli Mount Athos Border", "country": "GR", "region": "Chalkidiki", "lat": 40.3267, "lon": 23.9806},
    {"id": "gr_polygyros", "name": "Polygyros Central Chalkidiki", "country": "GR", "region": "Chalkidiki", "lat": 40.3775, "lon": 23.4422},
    {"id": "gr_neamoudania", "name": "Nea Moudania Thermaic Bay", "country": "GR", "region": "Chalkidiki", "lat": 40.2444, "lon": 23.2844},
    {"id": "gr_sithonia_nik", "name": "Nikiti Sithonia Peninsula", "country": "GR", "region": "Chalkidiki", "lat": 40.2217, "lon": 23.6683},
    {"id": "gr_sithonia_neos", "name": "Neos Marmaras Sithonia", "country": "GR", "region": "Chalkidiki", "lat": 40.0967, "lon": 23.7833},
    {"id": "gr_drama_c", "name": "Drama Center", "country": "GR", "region": "Eastern Macedonia", "lat": 41.1508, "lon": 24.1472},
    {"id": "gr_paranesti", "name": "Paranesti Nestos River", "country": "GR", "region": "Eastern Macedonia", "lat": 41.2667, "lon": 24.5000},
    {"id": "gr_kavala_c", "name": "Kavala Port", "country": "GR", "region": "Eastern Macedonia", "lat": 40.9397, "lon": 24.4128},
    {"id": "gr_kavala_airp", "name": "Kavala Alexander Airport", "country": "GR", "region": "Eastern Macedonia", "lat": 40.9133, "lon": 24.6192},
    {"id": "gr_thasos_limen", "name": "Thasos Town Limenas", "country": "GR", "region": "Eastern Macedonia", "lat": 40.7783, "lon": 24.7094},
    {"id": "gr_falakro_ski", "name": "Falakro Ski Center 1720m", "country": "GR", "region": "Eastern Macedonia", "lat": 41.2989, "lon": 24.0539},
    {"id": "gr_orvilos_mt", "name": "Mount Orvilos Slavianka 1800m", "country": "GR", "region": "Eastern Macedonia", "lat": 41.3667, "lon": 23.6000},
    {"id": "gr_angitis_cave", "name": "Aggitis River Gorge", "country": "GR", "region": "Eastern Macedonia", "lat": 41.2194, "lon": 23.8931},
    {"id": "gr_xanthi_w", "name": "Toxotes Nestos Delta", "country": "GR", "region": "Thrace", "lat": 41.0889, "lon": 24.7917},
    {"id": "gr_alexandroupoli", "name": "Alexandroupoli Thracian Sea", "country": "GR", "region": "Thrace", "lat": 40.8458, "lon": 25.8739},

    # --- ALBANIA (50 stations) ---
    {"id": "al_korce_c", "name": "Korce Plateau", "country": "AL", "region": "Korce", "lat": 40.6186, "lon": 20.7808},
    {"id": "al_korce_mborje", "name": "Mborje Foothills", "country": "AL", "region": "Korce", "lat": 40.5967, "lon": 20.7967},
    {"id": "al_bilisht", "name": "Bilisht Devoll Border", "country": "AL", "region": "Korce", "lat": 40.6275, "lon": 20.9900},
    {"id": "al_kapshtice", "name": "Kapshtice Greece Border", "country": "AL", "region": "Korce", "lat": 40.6133, "lon": 21.0533},
    {"id": "al_pogradec_c", "name": "Pogradec Lake Ohrid South", "country": "AL", "region": "Pogradec", "lat": 40.9025, "lon": 20.6558},
    {"id": "al_lin_lake", "name": "Lin Ohrid Peninsula", "country": "AL", "region": "Pogradec", "lat": 41.0667, "lon": 20.6444},
    {"id": "al_erseke", "name": "Erseke Kolonje 1020m", "country": "AL", "region": "Kolonje", "lat": 40.3378, "lon": 20.6789},
    {"id": "al_leskovik", "name": "Leskovik Pindus Gate", "country": "AL", "region": "Kolonje", "lat": 40.1517, "lon": 20.5983},
    {"id": "al_permet", "name": "Permet Vjosa River Valley", "country": "AL", "region": "Gjirokaster", "lat": 40.2350, "lon": 20.3517},
    {"id": "al_kelcyre", "name": "Kelcyre Gorge Vjosa", "country": "AL", "region": "Gjirokaster", "lat": 40.3128, "lon": 20.1889},
    {"id": "al_tepelene", "name": "Tepelene Ali Pasha Fortress", "country": "AL", "region": "Gjirokaster", "lat": 40.2958, "lon": 20.0189},
    {"id": "al_gjirokaster", "name": "Gjirokaster Stone City", "country": "AL", "region": "Gjirokaster", "lat": 40.0758, "lon": 20.1389},
    {"id": "al_kakavije", "name": "Kakavije Greece Border", "country": "AL", "region": "Gjirokaster", "lat": 39.9117, "lon": 20.3567},
    {"id": "al_sarande_port", "name": "Sarande Ionian Port", "country": "AL", "region": "Vlore", "lat": 39.8756, "lon": 20.0053},
    {"id": "al_ksamil", "name": "Ksamil Ionian Coast", "country": "AL", "region": "Vlore", "lat": 39.7719, "lon": 20.0019},
    {"id": "al_delvine", "name": "Delvine Blue Eye", "country": "AL", "region": "Vlore", "lat": 39.9500, "lon": 20.1000},
    {"id": "al_himare", "name": "Himare Albanian Riviera", "country": "AL", "region": "Vlore", "lat": 40.1017, "lon": 19.7447},
    {"id": "al_dhermi", "name": "Dhermi Llogara Foothills", "country": "AL", "region": "Vlore", "lat": 40.1500, "lon": 19.6417},
    {"id": "al_llogara_pass", "name": "Llogara Pass 1027m", "country": "AL", "region": "Vlore", "lat": 40.1989, "lon": 19.5967},
    {"id": "al_vlore_c", "name": "Vlore Bay of Vlore", "country": "AL", "region": "Vlore", "lat": 40.4667, "lon": 19.4914},
    {"id": "al_fier_c", "name": "Fier Myzeqe Plain", "country": "AL", "region": "Fier", "lat": 40.7258, "lon": 19.5561},
    {"id": "al_apollonia", "name": "Apollonia Archaeo Park", "country": "AL", "region": "Fier", "lat": 40.7267, "lon": 19.4717},
    {"id": "al_lushnje", "name": "Lushnje Agricultural Basin", "country": "AL", "region": "Fier", "lat": 40.9419, "lon": 19.7050},
    {"id": "al_berat_c", "name": "Berat Osum River", "country": "AL", "region": "Berat", "lat": 40.7058, "lon": 19.9522},
    {"id": "al_tomorr_mt", "name": "Mount Tomorr 2416m", "country": "AL", "region": "Berat", "lat": 40.6400, "lon": 20.1400},
    {"id": "al_gramsh", "name": "Gramsh Devolli Cascade", "country": "AL", "region": "Elbasan", "lat": 40.8672, "lon": 20.1850},
    {"id": "al_cerrik", "name": "Cerrik Elbasan Basin", "country": "AL", "region": "Elbasan", "lat": 40.9950, "lon": 19.9817},
    {"id": "al_elbasan_c", "name": "Elbasan Shkumbin River", "country": "AL", "region": "Elbasan", "lat": 41.1125, "lon": 20.0822},
    {"id": "al_librazhd", "name": "Librazhd Upper Shkumbin", "country": "AL", "region": "Elbasan", "lat": 41.1797, "lon": 20.3169},
    {"id": "al_prenjas", "name": "Prrenjas Thanasi Pass", "country": "AL", "region": "Elbasan", "lat": 41.0700, "lon": 20.5500},
    {"id": "al_qafethana", "name": "Qafe Thane MK Border Pass 937m", "country": "AL", "region": "Elbasan", "lat": 41.0833, "lon": 20.6167},
    {"id": "al_durres_port", "name": "Durres Adriatic Port", "country": "AL", "region": "Durres", "lat": 41.3231, "lon": 19.4414},
    {"id": "al_durres_plazh", "name": "Durres Beach Golem", "country": "AL", "region": "Durres", "lat": 41.2500, "lon": 19.5167},
    {"id": "al_tirana_skanderbeg", "name": "Tirana Skanderbeg Square", "country": "AL", "region": "Tirana", "lat": 41.3275, "lon": 19.8189},
    {"id": "al_tirana_airp", "name": "Tirana Mother Teresa Airport", "country": "AL", "region": "Tirana", "lat": 41.4147, "lon": 19.7206},
    {"id": "al_dajti_mt", "name": "Mount Dajti 1613m", "country": "AL", "region": "Tirana", "lat": 41.3667, "lon": 19.9167},
    {"id": "al_kruje", "name": "Kruje Castle Mountain Wall", "country": "AL", "region": "Durres", "lat": 41.5094, "lon": 19.7928},
    {"id": "al_lezhe_c", "name": "Lezhe Drin Plain", "country": "AL", "region": "Lezhe", "lat": 41.7836, "lon": 19.6436},
    {"id": "al_shengjin", "name": "Shengjin Adriatic Bay", "country": "AL", "region": "Lezhe", "lat": 41.8156, "lon": 19.5939},
    {"id": "al_shkoder_c", "name": "Shkoder Lake Skadar", "country": "AL", "region": "Shkoder", "lat": 42.0683, "lon": 19.5125},
    {"id": "al_shkoder_rozafa", "name": "Rozafa Fortress Buna River", "country": "AL", "region": "Shkoder", "lat": 42.0467, "lon": 19.4933},
    {"id": "al_koplik", "name": "Koplik Lake Shore", "country": "AL", "region": "Shkoder", "lat": 42.2133, "lon": 19.4364},
    {"id": "al_puke", "name": "Puke Northern Highlands 830m", "country": "AL", "region": "Shkoder", "lat": 42.0444, "lon": 19.8997},
    {"id": "al_kukes_c", "name": "Kukes Lake Fierza 320m", "country": "AL", "region": "Kukes", "lat": 42.0767, "lon": 20.4219},
    {"id": "al_morine", "name": "Morine Kosovo Border", "country": "AL", "region": "Kukes", "lat": 42.1517, "lon": 20.5483},
    {"id": "al_peshkopi", "name": "Peshkopi Korab Foothills", "country": "AL", "region": "Diber", "lat": 41.6850, "lon": 20.4283},
    {"id": "al_bulqize", "name": "Bulqize Chromium Valley 840m", "country": "AL", "region": "Diber", "lat": 41.4917, "lon": 20.2217},
    {"id": "al_mat_burrel", "name": "Burrel Mat River Basin", "country": "AL", "region": "Diber", "lat": 41.6103, "lon": 20.0108},
    {"id": "al_valbona_pass", "name": "Valbona Valley Alps 1000m", "country": "AL", "region": "Kukes", "lat": 42.4539, "lon": 19.8917},
    {"id": "al_bajram_curri", "name": "Bajram Curri Tropoje", "country": "AL", "region": "Kukes", "lat": 42.3581, "lon": 20.0764}
]

def fetch_grid_data():
    lat_str = ','.join(f"{s['lat']:.4f}" for s in STATIONS)
    lon_str = ','.join(f"{s['lon']:.4f}" for s in STATIONS)
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat_str}&longitude={lon_str}"
        "&current=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,wind_direction_10m,precipitation,weather_code"
        "&timezone=auto"
    )
    req = urllib.request.Request(url, headers={'User-Agent': 'BalkanMeteoResearch/2.0'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode('utf-8'))

def calculate_synoptic_gradients(station_data_map):
    # Calculate physical gradients that steer local weather in Gevgelija
    # 1. Vardar Wind Chute Gradient: dP = P(Skopje) - P(Thessaloniki)
    # Positive dP drives northern cold Vardar wind down the canyon
    p_skopje = station_data_map.get('mk_skopje_c', {}).get('pressure')
    p_thess = station_data_map.get('gr_thess_c', {}).get('pressure')
    p_gev = station_data_map.get('mk_gev_home', {}).get('pressure')

    vardar_dp = round(p_skopje - p_thess, 2) if (p_skopje is not None and p_thess is not None) else None

    # 2. Pindus Mountain Barrier Contrast: dP across Albanian coast vs Greek plateau
    p_vlore = station_data_map.get('al_vlore_c', {}).get('pressure')
    p_kozani = station_data_map.get('gr_kozani_c', {}).get('pressure')
    pindus_dp = round(p_vlore - p_kozani, 2) if (p_vlore is not None and p_kozani is not None) else None

    # 3. Moisture Inflow Index: Relative Humidity at Aegean Coast (Thessaloniki)
    rh_aegean = station_data_map.get('gr_thess_c', {}).get('humidity')
    rh_gev = station_data_map.get('mk_gev_home', {}).get('humidity')

    return {
        "vardar_pressure_gradient_hpa": vardar_dp,
        "pindus_barrier_gradient_hpa": pindus_dp,
        "aegean_rh_pct": rh_aegean,
        "gevgelija_rh_pct": rh_gev
    }

def main():
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_iso = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{now_iso}] Fetching research matrix for {len(STATIONS)} Balkan meteorological nodes...")

    raw_results = fetch_grid_data()
    if len(raw_results) != len(STATIONS):
        raise ValueError(f"Station count mismatch: expected {len(STATIONS)}, got {len(raw_results)}")

    station_records = []
    station_map = {}

    for i, meta in enumerate(STATIONS):
        curr = raw_results[i].get('current', {})
        rec = {
            "id": meta["id"],
            "name": meta["name"],
            "country": meta["country"],
            "region": meta["region"],
            "lat": meta["lat"],
            "lon": meta["lon"],
            "elevation": raw_results[i].get("elevation", 0),
            "temp": curr.get("temperature_2m"),
            "humidity": curr.get("relative_humidity_2m"),
            "pressure": curr.get("surface_pressure"),
            "wind_speed": curr.get("wind_speed_10m"),
            "wind_dir": curr.get("wind_direction_10m"),
            "precip": curr.get("precipitation"),
            "weather_code": curr.get("weather_code")
        }
        station_records.append(rec)
        station_map[meta["id"]] = rec

    gradients = calculate_synoptic_gradients(station_map)

    research_snapshot = {
        "updated_at_utc": now_iso,
        "station_count": len(station_records),
        "synoptic_gradients": gradients,
        "stations": station_records
    }

    # 1. Write research_latest.json
    with open("research_latest.json", "w", encoding="utf-8") as f:
        json.dump(research_snapshot, f, ensure_ascii=False, indent=2)
    print("Saved research_latest.json")

    # 2. Append to research_history.csv (Time series dataset)
    csv_file = "research_history.csv"
    file_exists = os.path.isfile(csv_file)

    with open(csv_file, "a", encoding="utf-8") as f:
        if not file_exists:
            f.write("timestamp,station_id,country,lat,lon,elevation,temp,humidity,pressure,wind_speed,wind_dir,precip,weather_code\n")
        for r in station_records:
            f.write(
                f"{now_iso},{r['id']},{r['country']},{r['lat']},{r['lon']},{r['elevation']},"
                f"{r['temp']},{r['humidity']},{r['pressure']},{r['wind_speed']},{r['wind_dir']},{r['precip']},{r['weather_code']}\n"
            )
    print(f"Appended {len(station_records)} observations to {csv_file}")

if __name__ == "__main__":
    main()
