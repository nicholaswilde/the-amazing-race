"""Geocoding coordinates and lookup for The Amazing Race destinations."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

CACHE_PATH = Path("data/raw/geocoding_cache.json")

# Curated WGS84 coordinates (latitude, longitude) for all TAR leg destination cities
CITY_COORDINATES: dict[tuple[str, str], tuple[float, float]] = {
    ("Al Ain", "ARE"): (24.2249, 55.7452),
    ("Dubai", "ARE"): (25.0743, 55.1886),
    ("Margham", "ARE"): (24.8995, 55.6255),
    ("Palm Jumeirah", "ARE"): (25.1183, 55.1338),
    ("Yas Island", "ARE"): (24.4864, 54.6091),
    ("Buenos Aires", "ARG"): (-34.6096, -58.3888),
    ("Cafayate", "ARG"): (-26.0729, -65.976),
    ("Córdoba", "ARG"): (-31.4167, -64.1833),
    ("Isla Redonda", "ARG"): (-54.8633, -68.4818),
    ("Las Heras Department", "ARG"): (-32.8486, -68.8317),
    ("Neuquén Province", "ARG"): (-40.7424, -71.6117),
    ("Río Negro", "ARG"): (-40.8, -63),
    ("San Antonio de Areco", "ARG"): (-34.2437, -59.4734),
    ("Vicente Casares", "ARG"): (-34.9623, -58.648),
    ("Garni", "ARM"): (40.1175, 44.7341),
    ("Breakaways National Park", "AUS"): (-28.9667, 134.45),
    ("Broken Hill", "AUS"): (-31.95, 141.4667),
    ("Ellis Beach", "AUS"): (-16.7258, 145.6722),
    ("Fremantle", "AUS"): (-32.0542, 115.7475),
    ("Graham Keating", "AUS"): (-33.8688, 151.2093),
    ("Lake Bennett", "AUS"): (-12.958, 131.1658),
    ("Mooloolaba", "AUS"): (-26.6853, 153.1132),
    ("Sydney", "AUS"): (-33.8688, 151.2093),
    ("Gmunden", "AUT"): (47.9186, 13.8003),
    ("Innsbruck", "AUT"): (47.2683, 11.3933),
    ("Salzburg", "AUT"): (47.8, 13.045),
    ("Vienna", "AUT"): (48.2083, 16.3725),
    ("Baku", "AZE"): (40.3756, 49.8325),
    ("Antwerp", "BEL"): (51.2211, 4.3997),
    ("Brussels", "BEL"): (50.8467, 4.3525),
    ("Bingo", "BFA"): (12.3025, -1.9),
    ("Ouagadougou", "BFA"): (12.3682, -1.5271),
    ("Dhaka", "BGD"): (23.7644, 90.3889),
    ("Sonargaon", "BGD"): (23.7537, 90.3766),
    ("Elin Pelin", "BGR"): (42.6691, 23.6021),
    ("Sofia", "BGR"): (42.7, 23.33),
    ("Sakhir", "BHR"): (26.0311, 50.5144),
    ("La Paz", "BOL"): (-16.4958, -68.1333),
    ("Brotas", "BRA"): (-22.2841, -48.1267),
    ("Fortaleza", "BRA"): (-3.7275, -38.5275),
    ("Iguaçu National Park", "BRA"): (-25.3751, -53.7771),
    ("Niterói", "BRA"): (-22.8833, -43.1036),
    ("Rio Negro", "BRA"): (-0.2932, -65.506),
    ("Rio de Janeiro", "BRA"): (-22.9111, -43.2056),
    ("Salvador", "BRA"): (-12.9822, -38.4813),
    ("São Paulo", "BRA"): (-23.5507, -46.6334),
    ("Christ Church", "BRB"): (13.0826, -59.5374),
    ("Khwai", "BWA"): (-19.1699, 23.7022),
    ("Makgadikgadi Pans National Park", "BWA"): (-20.5108, 24.8106),
    ("Maun", "BWA"): (-19.9861, 23.4224),
    ("Altstätten", "CHE"): (47.3782, 9.5414),
    ("Brienz", "CHE"): (46.756, 8.0303),
    ("Grindelwald", "CHE"): (46.6243, 8.0367),
    ("Lugano", "CHE"): (46.0038, 8.9512),
    ("Meiringen", "CHE"): (46.7286, 8.1871),
    ("Montreux", "CHE"): (46.435, 6.9125),
    ("Stechelberg", "CHE"): (46.545, 7.9022),
    ("Wolfenschiessen", "CHE"): (46.9081, 8.3955),
    ("Zermatt", "CHE"): (46.0212, 7.7493),
    ("Iquique", "CHL"): (-20.2141, -70.1525),
    ("Puerto Varas", "CHL"): (-41.3178, -72.9829),
    ("San José de Maipo", "CHL"): (-33.6404, -70.3528),
    ("San Pedro de Atacama", "CHL"): (-23.3545, -67.9027),
    ("Santiago", "CHL"): (-33.4375, -70.65),
    ("Valparaíso", "CHL"): (-33.0461, -71.6197),
    ("Vicente Pérez Rosales National Park", "CHL"): (-41.0598, -72.169),
    ("Bao Xishun", "CHN"): (31.2304, 121.4737),
    ("Beijing", "CHN"): (39.9057, 116.3913),
    ("Guangzhou", "CHN"): (23.13, 113.26),
    ("Guilin", "CHN"): (25.278, 110.2911),
    ("Kunming", "CHN"): (25.0464, 102.7094),
    ("Lijiang", "CHN"): (26.8596, 100.225),
    ("Shanghai", "CHN"): (31.2304, 121.4737),
    ("Shenzhen", "CHN"): (22.5467, 114.0544),
    ("Xi'an", "CHN"): (34.2611, 108.9422),
    ("Bogotá", "COL"): (4.7111, -74.0722),
    ("Cartagena", "COL"): (10.4, -75.5),
    ("El Peñol", "COL"): (6.2188, -75.2432),
    ("Medellín", "COL"): (6.2697, -75.6026),
    ("Quepos", "CRI"): (9.4128, -84.0649),
    ("Prague", "CZE"): (50.0875, 14.4214),
    ("Svatý Mikuláš", "CZE"): (49.9909, 15.3505),
    ("Berlin", "DEU"): (52.52, 13.405),
    ("Cologne", "DEU"): (50.9364, 6.9528),
    ("Hamburg", "DEU"): (53.55, 10),
    ("Munich", "DEU"): (48.1375, 11.575),
    ("Schliersee", "DEU"): (47.7346, 11.862),
    ("Schwangau", "DEU"): (47.5797, 10.7589),
    ("Schwangau-Horn", "DEU"): (47.5757, 10.7306),
    ("Copenhagen", "DNK"): (55.6761, 12.5683),
    ("La Boca", "DOM"): (19.7002, -70.3643),
    ("Puerto Plata", "DOM"): (19.7977, -70.6933),
    ("Cotopaxi National Park", "ECU"): (-0.6537, -78.4462),
    ("Giza", "EGY"): (29.987, 31.2118),
    ("Luxor", "EGY"): (25.6967, 32.6444),
    ("Barcelona", "ESP"): (41.3833, 2.1833),
    ("Palma", "ESP"): (39.5667, 2.65),
    ("Ronda", "ESP"): (36.7421, -5.1666),
    ("Seville", "ESP"): (37.3886, -5.995),
    ("Keava", "EST"): (58.945, 24.9018),
    ("Lalibela", "ETH"): (12.0361, 39.0457),
    ("Bonifacio", "FRA"): (41.3872, 9.1591),
    ("Chamonix", "FRA"): (45.9231, 6.8697),
    ("Chenonceaux", "FRA"): (47.3331, 1.0692),
    ("Domme", "FRA"): (44.8023, 1.214),
    ("Giuncaggio", "FRA"): (42.2166, 9.3671),
    ("L'Île-Rousse", "FRA"): (42.6345, 8.9381),
    ("Les Baux-de-Provence", "FRA"): (43.7439, 4.7953),
    ("Massiges", "FRA"): (49.187, 4.7489),
    ("Paris", "FRA"): (48.8567, 2.3522),
    ("Saint-Jean-Cap-Ferrat", "FRA"): (43.69, 7.3327),
    ("Saint-Rémy-de-Provence", "FRA"): (43.79, 4.8325),
    ("Saint-Tropez", "FRA"): (43.2727, 6.6405),
    ("Scherwiller", "FRA"): (48.2862, 7.4195),
    ("Toulouse", "FRA"): (43.6045, 1.444),
    ("Épernay", "FRA"): (49.0426, 3.9529),
    ("Belfast", "GBR"): (54.5967, -5.93),
    ("Edinburgh", "GBR"): (55.9533, -3.1892),
    ("Glasgow", "GBR"): (55.8611, -4.25),
    ("Ledbury", "GBR"): (52.0339, -2.4235),
    ("London", "GBR"): (51.5072, -0.1275),
    ("Peckforton", "GBR"): (53.1044, -2.6926),
    ("St Ninian's Isle", "GBR"): (59.9739, -1.3458),
    ("Stonehaven", "GBR"): (56.964, -2.2088),
    ("Woodstock", "GBR"): (51.8742, -1.3553),
    ("Tbilisi", "GEO"): (41.7225, 44.7925),
    ("Accra", "GHA"): (5.55, -0.2),
    ("Doryumu", "GHA"): (5.9007, 0.0232),
    ("Athens", "GRC"): (37.9842, 23.7281),
    ("Nea Kallikrateia", "GRC"): (40.3107, 23.0632),
    ("Rio", "GRC"): (38.3019, 21.7826),
    ("Thessaloniki", "GRC"): (40.6403, 22.9356),
    ("Humåtak", "GUM"): (13.3101, 144.6679),
    ("Hong Kong", "HKG"): (22.3, 114.2),
    ("Dubrovnik", "HRV"): (42.6403, 18.1083),
    ("Prapratno", "HRV"): (42.8172, 17.6768),
    ("Split", "HRV"): (43.5116, 16.44),
    ("Budapest", "HUN"): (47.4925, 19.0514),
    ("Bangil", "IDN"): (-7.599, 112.7782),
    ("Cisarua", "IDN"): (-6.6958, 106.951),
    ("Denpasar", "IDN"): (-8.6653, 115.2176),
    ("Kubu", "IDN"): (-0.4641, 109.3281),
    ("Lembang", "IDN"): (-7.1177, 107.855),
    ("Magelang", "IDN"): (-7.5136, 110.2145),
    ("Nusa Dua", "IDN"): (-8.8017, 115.2239),
    ("Pecatu", "IDN"): (-8.8208, 115.1136),
    ("Surabaya", "IDN"): (-7.2458, 112.7378),
    ("Yogyakarta", "IDN"): (-7.7953, 110.3673),
    ("Agra", "IND"): (27.18, 78.02),
    ("Alleppey", "IND"): (9.4939, 76.321),
    ("Amber", "IND"): (26.9888, 75.8559),
    ("Bikaner", "IND"): (28.0159, 73.3171),
    ("Chennai", "IND"): (13.0825, 80.275),
    ("Delhi", "IND"): (28.61, 77.23),
    ("Hyderabad", "IND"): (17.3617, 78.4747),
    ("Jaipur", "IND"): (26.915, 75.82),
    ("Jodhpur", "IND"): (26.2968, 73.0351),
    ("Kochi", "IND"): (9.9312, 76.2673),
    ("Kolkata", "IND"): (22.5675, 88.37),
    ("Mumbai", "IND"): (19.0761, 72.8775),
    ("Ramnagar", "IND"): (29.3948, 79.1269),
    ("Vypin", "IND"): (10.0781, 76.206),
    ("Clifden", "IRL"): (53.4885, -10.0211),
    ("Dublin", "IRL"): (53.35, -6.2603),
    ("Grindavík", "ISL"): (63.8442, -22.4317),
    ("Hrunamannahreppur", "ISL"): (64.4329, -19.7124),
    ("Reykjavík", "ISL"): (64.1458, -21.9425),
    ("Art & J.J. chose to split their 0", "ITA"): (45.0689, 7.6931),
    ("Calatafimi-Segesta", "ITA"): (37.9041, 12.8686),
    ("Corbetta", "ITA"): (45.4659, 8.9201),
    ("Cortina d'Ampezzo", "ITA"): (46.5685, 12.1323),
    ("Florence", "ITA"): (43.7714, 11.2542),
    ("Naples", "ITA"): (40.8358, 14.2486),
    ("Orvieto", "ITA"): (42.7186, 12.1088),
    ("Palermo", "ITA"): (38.1111, 13.3517),
    ("Rome", "ITA"): (41.8933, 12.4828),
    ("Sant'Agata Bolognese", "ITA"): (44.6637, 11.1333),
    ("Syracuse", "ITA"): (37.0692, 15.2875),
    ("Tremezzo", "ITA"): (45.9835, 9.2185),
    ("Turin", "ITA"): (45.0703, 7.6869),
    ("Venice", "ITA"): (45.4375, 12.3358),
    ("Port Antonio", "JAM"): (18.1758, -76.4526),
    ("The next day", "JAM"): (18.1758, -76.4526),
    ("Amman", "JOR"): (31.9497, 35.9328),
    ("Petra", "JOR"): (30.3258, 35.4746),
    ("Kyoto", "JPN"): (35.0116, 135.7681),
    ("Minoh", "JPN"): (34.827, 135.4705),
    ("Nagano", "JPN"): (36.1144, 138.0319),
    ("Osaka", "JPN"): (34.6939, 135.5022),
    ("Tokyo", "JPN"): (35.6897, 139.6922),
    ("Yamanakako", "JPN"): (35.4187, 138.8768),
    ("Yokosuka", "JPN"): (35.2815, 139.672),
    ("Almaty", "KAZ"): (43.2364, 76.9457),
    ("Phnom Penh", "KHM"): (11.5694, 104.9211),
    ("Siem Reap", "KHM"): (13.3618, 103.859),
    ("Seoul", "KOR"): (37.5667, 126.9783),
    ("Kuwait City", "KWT"): (29.3697, 47.9783),
    ("Luang Prabang", "LAO"): (19.89, 102.1347),
    ("Colombo", "LKA"): (6.9344, 79.8428),
    ("Mount Lavinia", "LKA"): (6.8317, 79.8627),
    ("Sigiriya", "LKA"): (7.9567, 80.7599),
    ("Rumšiškės", "LTU"): (54.867, 24.219),
    ("Macau", "MAC"): (22.19, 113.54),
    ("Atlas Mountains", "MAR"): (31.0596, -7.9151),
    ("Fez", "MAR"): (34.0347, -5.0162),
    ("Hajar", "MAR"): (33.2286, -8.5197),
    ("Marrakesh", "MAR"): (31.63, -8.0089),
    ("Tangier", "MAR"): (35.7626, -5.8295),
    ("Antananarivo", "MDG"): (-18.91, 47.525),
    ("Mexico City", "MEX"): (19.4333, -99.1333),
    ("Puente de Ixtla", "MEX"): (18.5783, -99.3105),
    ("Puerto Vallarta", "MEX"): (20.6458, -105.2222),
    ("Tulum", "MEX"): (20.4296, -87.6529),
    ("Gżira", "MLT"): (35.9078, 14.4961),
    ("Ulaanbaatar", "MNG"): (47.9219, 106.9153),
    ("Maputo", "MOZ"): (-25.9662, 32.5675),
    ("Bel Ombre", "MUS"): (-20.5028, 57.4009),
    ("Lilongwe", "MWI"): (-13.9864, 33.7681),
    ("Senga Bay", "MWI"): (-13.766, 34.6107),
    ("George Town", "MYS"): (5.4144, 100.3292),
    ("Gombak", "MYS"): (3.3, 101.7),
    ("Kota Kinabalu", "MYS"): (5.978, 116.0729),
    ("Kuala Lumpur", "MYS"): (3.1478, 101.6953),
    ("Sepilok", "MYS"): (5.8656, 117.9493),
    ("Tunku Abdul Rahman National Park", "MYS"): (6.0187, 116.0266),
    ("Erongo Region", "NAM"): (-22.0278, 15.3894),
    ("Khomas Region", "NAM"): (-22.8, 17),
    ("Usakos", "NAM"): (-21.997, 15.5874),
    ("Amsterdam", "NLD"): (52.3728, 4.8936),
    ("Durgerdam", "NLD"): (52.3779, 4.9905),
    ("Giethoorn", "NLD"): (52.7411, 6.0774),
    ("Muiden", "NLD"): (52.3333, 5.0667),
    ("Ransdorp", "NLD"): (52.3937, 4.9946),
    ("The Hague", "NLD"): (52.08, 4.31),
    ("Zoutkamp", "NLD"): (53.337, 6.3011),
    ("Ankenesstranda", "NOR"): (68.4217, 17.3789),
    ("Vestvågøy", "NOR"): (68.1607, 13.7841),
    ("Voss", "NOR"): (60.6837, 6.4079),
    ("Ålesund", "NOR"): (62.4802, 6.5551),
    ("Auckland", "NZL"): (-36.8521, 174.7632),
    ("John Keoghan", "NZL"): (-37.195, 174.903),
    ("Mount Somers", "NZL"): (-43.7056, 171.4024),
    ("Paengaroa", "NZL"): (-37.8223, 176.4116),
    ("Pukekohe", "NZL"): (-37.195, 174.903),
    ("Windwhistle", "NZL"): (-43.515, 171.712),
    ("Jabrin", "OMN"): (22.92, 57.25),
    ("Muscat", "OMN"): (23.5889, 58.4083),
    ("Panama City", "PAN"): (8.9711, -79.5347),
    ("Cusco", "PER"): (-13.5169, -71.9786),
    ("Huanchaco", "PER"): (-8.08, -79.1205),
    ("Otuzco", "PER"): (-7.8415, -78.5257),
    ("El Nido", "PHL"): (11.18, 119.3905),
    ("Manila", "PHL"): (14.5958, 120.9772),
    ("Naic", "PHL"): (14.3192, 120.7643),
    ("Pasay", "PHL"): (14.5437, 120.9947),
    ("Kraków", "POL"): (50.0469, 19.9972),
    ("Sopot", "POL"): (54.443, 18.5613),
    ("Sułoszowa", "POL"): (50.2672, 19.733),
    ("Warsaw", "POL"): (52.23, 21.0111),
    ("Cabo Espichel", "PRT"): (38.414, -9.2222),
    ("Lisbon", "PRT"): (38.7253, -9.15),
    ("Sintra", "PRT"): (38.8355, -9.3522),
    ("Vila Nova de Gaia", "PRT"): (41.1292, -8.6057),
    ("Asunción", "PRY"): (-25.28, -57.6344),
    ("Bora Bora", "PYF"): (-16.5043, -151.7367),
    ("Motu Piti A'au", "PYF"): (-16.521, -151.7029),
    ("Bran", "ROU"): (45.5163, 25.3716),
    ("Bucharest", "ROU"): (44.4325, 26.1039),
    ("Mogoșoaia", "ROU"): (44.5333, 26),
    ("Krasnoyarsk", "RUS"): (56.0089, 92.8719),
    ("Moscow", "RUS"): (55.7558, 37.6178),
    ("Novosibirsk", "RUS"): (55.05, 82.95),
    ("Pushkin", "RUS"): (59.6878, 30.3407),
    ("Saint Petersburg", "RUS"): (59.9607, 30.1587),
    ("Gorée Island", "SEN"): (14.6672, -17.3984),
    ("Miss Singapore Universe 2001", "SGP"): (1.2903, 103.852),
    ("Singapore", "SGP"): (1.2903, 103.852),
    ("Ljubljana", "SVN"): (46.0514, 14.5061),
    ("Socerb", "SVN"): (45.5895, 13.8592),
    ("Copenhagen", "SWE"): (55.6761, 12.5683),
    ("Häggvik", "SWE"): (59.4438, 17.9329),
    ("Riksgränsen", "SWE"): (68.4149, 18.1205),
    ("Stockholm", "SWE"): (59.3294, 18.0686),
    ("Anse Volbert", "SYC"): (-4.3162, 55.7475),
    ("Amphawa", "THA"): (13.425, 99.9553),
    ("Ao Nang", "THA"): (7.7212, 98.7655),
    ("Ao Phang Nga National Park", "THA"): (8.2388, 98.5061),
    ("Bangkok", "THA"): (13.7525, 100.4942),
    ("Chiang Dao District", "THA"): (19.5358, 98.9462),
    ("Chiang Mai", "THA"): (18.7953, 98.9986),
    ("Krabi", "THA"): (8.1112, 99.1097),
    ("Mueang Nonthaburi", "THA"): (13.8538, 100.4941),
    ("Mueang Phuket", "THA"): (7.8666, 98.3373),
    ("Phuket", "THA"): (7.9366, 98.3529),
    ("Sam Phran", "THA"): (13.7258, 100.2139),
    ("Buccoo", "TTO"): (11.1829, -60.803),
    ("El Djem", "TUN"): (35.3219, 10.6834),
    ("Jebil National Park", "TUN"): (33.0727, 9.0814),
    ("Istanbul", "TUR"): (41.0064, 28.9759),
    ("Taipei", "TWN"): (25.0375, 121.5637),
    ("Dar es Salaam", "TZA"): (-6.8161, 39.2803),
    ("Lake Manyara National Park", "TZA"): (-3.583, 35.7812),
    ("Ngorongoro Crater", "TZA"): (-3.1766, 35.5788),
    ("Zanzibar City", "TZA"): (-6.1665, 39.2074),
    ("Kampala", "UGA"): (0.3136, 32.5811),
    ("Kyiv", "UKR"): (50.45, 30.5241),
    ("Montevideo", "URY"): (-34.9056, -56.1842),
    ("Punta Ballena", "URY"): (-34.8901, -55.0401),
    ("Absarokee", "USA"): (45.5191, -109.4443),
    ("Alameda", "USA"): (37.609, -121.8991),
    ("Atlanta", "USA"): (33.7489, -84.39),
    ("Beverly Hills", "USA"): (34.0731, -118.3994),
    ("Carson", "USA"): (33.8317, -118.2817),
    ("Chicago", "USA"): (41.8819, -87.6278),
    ("Dallas", "USA"): (32.7792, -96.8089),
    ("Detroit", "USA"): (42.3317, -83.0458),
    ("Fort Lauderdale", "USA"): (26.1223, -80.1434),
    ("Fort McDowell", "USA"): (33.6367, -111.6746),
    ("Garrison", "USA"): (41.3815, -73.9482),
    ("Girdwood", "USA"): (60.9632, -149.1337),
    ("Huntsville", "USA"): (34.6933, -86.5608),
    ("Juneau", "USA"): (58.3, -134.4161),
    ("Kualoa Valley", "USA"): (21.5211, -157.8385),
    ("Lancaster", "USA"): (40.038, -76.3057),
    ("Las Vegas", "USA"): (36.1692, -115.1406),
    ("Lewiston", "USA"): (43.1728, -79.0353),
    ("Marathon", "USA"): (24.7137, -81.0904),
    ("Miami", "USA"): (25.7742, -80.1936),
    ("Middleburg", "USA"): (38.969, -77.7355),
    ("Mokulau", "USA"): (20.6404, -156.1098),
    ("Morrison", "USA"): (39.6536, -105.1911),
    ("Mount Vernon", "USA"): (38.708, -77.0861),
    ("Nashville", "USA"): (36.1622, -86.7744),
    ("New Orleans", "USA"): (29.9761, -90.0783),
    ("New York City", "USA"): (40.7127, -74.006),
    ("Page", "USA"): (36.9147, -111.4558),
    ("Philadelphia", "USA"): (39.9528, -75.1636),
    ("Phoenix", "USA"): (33.4483, -112.0739),
    ("Portland", "USA"): (45.5202, -122.6742),
    ("Rancho Palos Verdes", "USA"): (33.7583, -118.3642),
    ("Redmond", "USA"): (47.6694, -122.1239),
    ("Salt Lake City", "USA"): (40.7608, -111.8911),
    ("San Francisco", "USA"): (37.7775, -122.4164),
    ("Santa Ynez", "USA"): (34.6119, -120.0883),
    ("Sausalito", "USA"): (37.8592, -122.4853),
    ("Seattle", "USA"): (47.6038, -122.3301),
    ("Southampton", "USA"): (40.8843, -72.3898),
    ("Trapper Creek", "USA"): (62.3081, -150.3508),
    ("Waikapu", "USA"): (20.855, -156.5035),
    ("Charlotte Amalie", "VIR"): (18.3369, -64.9622),
    ("Cái Bè", "VNM"): (10.3348, 106.0336),
    ("Cần Thơ", "VNM"): (10.0362, 105.7873),
    ("Da Nang", "VNM"): (16.0685, 108.224),
    ("Hanoi", "VNM"): (21, 105.85),
    ("Ho Chi Minh City", "VNM"): (10.7756, 106.7019),
    ("Hoa Lư", "VNM"): (20.2498, 105.9565),
    ("Hạ Long Bay", "VNM"): (20.9084, 107.0683),
    ("Phố Vác", "VNM"): (20.8141, 105.7755),
    ("Soweto", "ZAF"): (-26.2678, 27.8585),
    ("Stellenbosch", "ZAF"): (-33.9367, 18.8614),
    ("Livingstone District", "ZMB"): (-17.8074, 25.7861),
    ("Harare", "ZWE"): (-17.8292, 31.0522),
    ("Mashonaland East Province", "ZWE"): (-17.7927, 31.7678),
    ("Victoria Falls", "ZWE"): (-17.9244, 25.8567),
}

# Specific overrides for legs where itinerary parsing captured greeters or narrative artifacts
LEG_CITY_OVERRIDES: dict[tuple[int, int], str] = {
    (2, 8): "Sydney",
    (3, 10): "Singapore",
    (7, 11): "Port Antonio",
    (13, 4): "Pukekohe",
    (16, 11): "Shanghai",
    (20, 4): "Turin",
}

ISO_TO_COUNTRY: dict[str, str] = {
    "ARG": "Argentina",
    "ARM": "Armenia",
    "AUS": "Australia",
    "AUT": "Austria",
    "AZE": "Azerbaijan",
    "BHR": "Bahrain",
    "BGD": "Bangladesh",
    "BRB": "Barbados",
    "BEL": "Belgium",
    "BOL": "Bolivia",
    "BWA": "Botswana",
    "BRA": "Brazil",
    "BGR": "Bulgaria",
    "BFA": "Burkina Faso",
    "KHM": "Cambodia",
    "CAN": "Canada",
    "CHL": "Chile",
    "CHN": "China",
    "COL": "Colombia",
    "CRI": "Costa Rica",
    "HRV": "Croatia",
    "CZE": "Czech Republic",
    "DNK": "Denmark",
    "DOM": "Dominican Republic",
    "ECU": "Ecuador",
    "EGY": "Egypt",
    "EST": "Estonia",
    "ETH": "Ethiopia",
    "FIN": "Finland",
    "FRA": "France",
    "PYF": "French Polynesia",
    "GEO": "Georgia",
    "DEU": "Germany",
    "GHA": "Ghana",
    "GRC": "Greece",
    "GTM": "Guatemala",
    "HUN": "Hungary",
    "ISL": "Iceland",
    "IND": "India",
    "IDN": "Indonesia",
    "IRL": "Ireland",
    "ITA": "Italy",
    "JAM": "Jamaica",
    "JPN": "Japan",
    "JOR": "Jordan",
    "KAZ": "Kazakhstan",
    "KEN": "Kenya",
    "KWT": "Kuwait",
    "LAO": "Laos",
    "LTU": "Lithuania",
    "MDG": "Madagascar",
    "MYS": "Malaysia",
    "MUS": "Mauritius",
    "MEX": "Mexico",
    "MCO": "Monaco",
    "MNG": "Mongolia",
    "MAR": "Morocco",
    "MOZ": "Mozambique",
    "NAM": "Namibia",
    "NLD": "Netherlands",
    "NZL": "New Zealand",
    "NOR": "Norway",
    "OMN": "Oman",
    "PAN": "Panama",
    "PRY": "Paraguay",
    "PER": "Peru",
    "PHL": "Philippines",
    "POL": "Poland",
    "PRT": "Portugal",
    "ROU": "Romania",
    "RUS": "Russia",
    "SEN": "Senegal",
    "SYC": "Seychelles",
    "SGP": "Singapore",
    "ZAF": "South Africa",
    "KOR": "South Korea",
    "ESP": "Spain",
    "LKA": "Sri Lanka",
    "SWE": "Sweden",
    "CHE": "Switzerland",
    "TWN": "Taiwan",
    "TZA": "Tanzania",
    "THA": "Thailand",
    "TUR": "Turkey",
    "UGA": "Uganda",
    "UKR": "Ukraine",
    "ARE": "United Arab Emirates",
    "GBR": "United Kingdom",
    "USA": "United States",
    "URY": "Uruguay",
    "VIR": "U.S. Virgin Islands",
    "VNM": "Vietnam",
    "ZMB": "Zambia",
    "ZWE": "Zimbabwe",
}

COUNTRY_NAME_TO_ISO: dict[str, str] = {
    name.lower(): iso for iso, name in ISO_TO_COUNTRY.items()
}

_DYNAMIC_CACHE: dict[tuple[str, str], tuple[float, float]] = {}
_CACHE_LOADED = False


def load_geocoding_cache(
    cache_file: Path | str = CACHE_PATH,
) -> dict[tuple[str, str], tuple[float, float]]:
    """Load dynamic geocoding cache from disk."""
    global _CACHE_LOADED
    p = Path(cache_file)
    if not p.exists():
        _CACHE_LOADED = True
        return _DYNAMIC_CACHE
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        for key, coords in data.items():
            if "|" in key and isinstance(coords, (list, tuple)) and len(coords) == 2:
                c, iso = key.split("|", 1)
                _DYNAMIC_CACHE[(c.strip(), iso.strip().upper())] = (
                    float(coords[0]),
                    float(coords[1]),
                )
    except Exception as e:
        logger.warning("Could not read geocoding cache from %s: %s", p, e)
    _CACHE_LOADED = True
    return _DYNAMIC_CACHE


def save_geocoding_cache(cache_file: Path | str = CACHE_PATH) -> None:
    """Persist dynamic geocoding cache to disk."""
    p = Path(cache_file)
    p.parent.mkdir(parents=True, exist_ok=True)
    serializable = {
        f"{city}|{iso}": [lat, lon]
        for (city, iso), (lat, lon) in _DYNAMIC_CACHE.items()
    }
    p.write_text(json.dumps(serializable, indent=2, sort_keys=True), encoding="utf-8")


def update_geocoding_cache(
    city: str,
    country_iso: str,
    lat: float,
    lon: float,
    cache_file: Path | str = CACHE_PATH,
) -> None:
    """Manually add or update coordinates in dynamic cache and save to disk."""
    if not _CACHE_LOADED:
        load_geocoding_cache(cache_file)
    _DYNAMIC_CACHE[(city.strip(), country_iso.strip().upper())] = (
        round(lat, 4),
        round(lon, 4),
    )
    save_geocoding_cache(cache_file)


def fetch_online_coordinates(
    city: str,
    country_iso: str | None = None,
    timeout: float = 10.0,
    client: httpx.Client | None = None,
) -> tuple[float, float] | None:
    """Fetch WGS84 coordinates from OpenStreetMap Nominatim with Wikipedia fallback."""
    if not city or not city.strip():
        return None

    city_clean = city.strip()
    iso_upper = country_iso.strip().upper() if country_iso else ""
    country_name = ISO_TO_COUNTRY.get(iso_upper, "")
    query = f"{city_clean}, {country_name}" if country_name else city_clean

    headers = {
        "User-Agent": "TheAmazingRaceDataset/0.3.1 (https://github.com/nicholaswilde/the-amazing-race)"
    }
    close_client = False
    if client is None:
        client = httpx.Client(timeout=timeout, headers=headers)
        close_client = True

    try:
        # 1. OpenStreetMap Nominatim
        nominatim_url = "https://nominatim.openstreetmap.org/search"
        resp = client.get(
            nominatim_url,
            params={"q": query, "format": "json", "limit": 1},
        )
        if resp.status_code == 200:
            data = resp.json()
            if data and isinstance(data, list) and len(data) > 0:
                first = data[0]
                lat = round(float(first["lat"]), 4)
                lon = round(float(first["lon"]), 4)
                return lat, lon

        # 2. Wikipedia API coordinates search fallback
        wiki_url = "https://en.wikipedia.org/w/api.php"
        resp = client.get(
            wiki_url,
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": query,
                "gsrlimit": 1,
                "prop": "coordinates",
                "format": "json",
            },
        )
        if resp.status_code == 200:
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                coords = page.get("coordinates")
                if coords and len(coords) > 0:
                    lat = round(float(coords[0]["lat"]), 4)
                    lon = round(float(coords[0]["lon"]), 4)
                    return lat, lon
    except Exception as e:
        logger.debug("Online geocoding lookup failed for '%s': %s", query, e)
    finally:
        if close_client:
            client.close()

    return None


def get_city_coordinates(
    city: str | None,
    country_iso: str | None = None,
    season: int | None = None,
    leg_number: int | None = None,
    allow_network: bool = True,
    cache_file: Path | str = CACHE_PATH,
) -> tuple[float, float] | None:
    """Retrieve WGS84 (latitude, longitude) coordinates for a city and country."""
    if not city:
        return None

    if not _CACHE_LOADED:
        load_geocoding_cache(cache_file)

    if (
        season is not None
        and leg_number is not None
        and (season, leg_number) in LEG_CITY_OVERRIDES
    ):
        city = LEG_CITY_OVERRIDES[(season, leg_number)]

    city_clean = city.strip()
    iso_clean = country_iso.strip().upper() if country_iso else None
    if iso_clean and len(iso_clean) > 3 and iso_clean.lower() in COUNTRY_NAME_TO_ISO:
        iso_clean = COUNTRY_NAME_TO_ISO[iso_clean.lower()]

    # 1. Static dictionary lookup
    if iso_clean:
        pair = (city_clean, iso_clean)
        if pair in CITY_COORDINATES:
            return CITY_COORDINATES[pair]

    # 2. Dynamic cache lookup
    if iso_clean:
        pair = (city_clean, iso_clean)
        if pair in _DYNAMIC_CACHE:
            return _DYNAMIC_CACHE[pair]

    # 3. Case-insensitive exact pair lookup
    if iso_clean:
        for (c, iso), coords in CITY_COORDINATES.items():
            if c.lower() == city_clean.lower() and iso.upper() == iso_clean:
                return coords
        for (c, iso), coords in _DYNAMIC_CACHE.items():
            if c.lower() == city_clean.lower() and iso.upper() == iso_clean:
                return coords

    # 4. Fallback to city-only match across static coordinates
    for (c, _iso), coords in CITY_COORDINATES.items():
        if c.lower() == city_clean.lower():
            return coords

    # 5. Fallback to city-only match across dynamic cache
    for (c, _iso), coords in _DYNAMIC_CACHE.items():
        if c.lower() == city_clean.lower():
            return coords

    # 6. Fetch online if enabled
    if allow_network:
        coords = fetch_online_coordinates(city_clean, iso_clean)
        if coords:
            key_iso = iso_clean or ""
            _DYNAMIC_CACHE[(city_clean, key_iso)] = coords
            try:
                save_geocoding_cache(cache_file)
            except Exception as e:
                logger.warning("Failed saving geocoding cache: %s", e)
            return coords

    return None


def ensure_legs_geocoded(
    legs: list[dict[str, Any]] | pd.DataFrame,
    allow_network: bool = True,
    cache_file: Path | str = CACHE_PATH,
) -> int:
    """Ensure all leg destinations in legs list or DataFrame are geocoded.

    Returns the number of newly geocoded destinations.
    """
    if isinstance(legs, pd.DataFrame):
        if legs.empty:
            return 0
        city_col = None
        for col in ["destination_city", "dest_city", "city", "destination"]:
            if col in legs.columns:
                city_col = col
                break
        if not city_col:
            return 0

        country_col = None
        for col in ["destination_country", "dest_country", "country_iso", "country"]:
            if col in legs.columns:
                country_col = col
                break

        count = 0
        cols_to_use = [city_col, country_col] if country_col else [city_col]
        unique_pairs = legs[cols_to_use].drop_duplicates()

        for _, row in unique_pairs.iterrows():
            c = str(row[city_col]).strip() if pd.notna(row[city_col]) else None
            iso = (
                str(row[country_col]).strip()
                if country_col and pd.notna(row[country_col])
                else None
            )
            if not c or c.lower() in ("nan", "none", ""):
                continue
            before_len = len(_DYNAMIC_CACHE)
            coords = get_city_coordinates(
                c, iso, allow_network=allow_network, cache_file=cache_file
            )
            if coords and len(_DYNAMIC_CACHE) > before_len:
                count += 1
        return count

    if not isinstance(legs, list):
        return 0

    count = 0
    from tar_dataset.processors.builder import parse_route_header

    for leg in legs:
        if not isinstance(leg, dict):
            continue

        city = None
        country = None

        if "route_header" in leg:
            itinerary = leg.get("itinerary", [])
            _, dest_iso, parsed_city, _ = parse_route_header(
                leg.get("route_header"), itinerary
            )
            city = parsed_city
            country = dest_iso
        else:
            for c_key in ["destination_city", "dest_city", "city"]:
                if leg.get(c_key):
                    city = str(leg[c_key]).strip()
                    break
            for iso_key in [
                "destination_country",
                "dest_country",
                "country_iso",
                "country",
            ]:
                if leg.get(iso_key):
                    country = str(leg[iso_key]).strip()
                    break

        if not city:
            continue

        before_len = len(_DYNAMIC_CACHE)
        coords = get_city_coordinates(
            city, country, allow_network=allow_network, cache_file=cache_file
        )
        if coords and len(_DYNAMIC_CACHE) > before_len:
            count += 1

    return count
