export const TUNISIA_DATA = {
  "Tunis": [
    "Tunis", "Le Bardo", "Le Kram", "La Goulette", "Carthage",
    "Sidi Bou Said", "La Marsa", "Sidi Hassine", "Cité El Khadra",
    "El Menzah", "Ettahrir", "Ezzouhour", "El Omrane",
    "El Omrane Supérieur", "Bab Bhar", "Bab Souika",
    "Djebel Jelloud", "Médina", "Séjoumi", "Kabaria", "Hraïria"
  ],
  "Ariana": [
    "Ariana", "La Soukra", "Raoued", "Kalâat el-Andalous",
    "Sidi Thabet", "Ettadhamen", "Mnihla"
  ],
  "Ben Arous": [
    "Ben Arous", "El Mourouj", "Hammam Lif", "Hammam Chott",
    "Bou Mhel el-Bassatine", "Ezzahra", "Radès", "Mégrine",
    "Mohamedia", "Fouchana", "Mornag", "Khalidia"
  ],
  "Manouba": [
    "Manouba", "Den Den", "Douar Hicher", "Oued Ellil",
    "Mornaguia", "Borj El Amri", "Djedeida", "Tebourba", "El Battan"
  ],
  "Nabeul": [
    "Nabeul", "Dar Chaabane", "Béni Khiar", "Korba",
    "Menzel Temime", "Kelibia", "El Haouaria", "Takelsa",
    "Soliman", "Menzel Bouzelfa", "Béni Khalled", "Grombalia",
    "Bou Argoub", "Hammamet"
  ],
  "Zaghouan": [
    "Zaghouan", "Zriba", "Bir Mcherga", "Djebel Oust",
    "El Fahs", "Nadhour"
  ],
  "Bizerte": [
    "Bizerte", "Sejnane", "Mateur", "Menzel Bourguiba",
    "Tinja", "Ghar al Milh", "Menzel Jemil",
    "Menzel Abderrahmane", "El Alia", "Ras Jebel",
    "Metline", "Raf Raf"
  ],
  "Béja": [
    "Béja", "Nefza", "Téboursouk", "Testour",
    "Goubellat", "Majaz al Bab"
  ],
  "Jendouba": [
    "Jendouba", "Bou Salem", "Tabarka", "Aïn Draham",
    "Fernana", "Ghardimaou"
  ],
  "Kef": [
    "El Kef", "Nebeur", "Sakiet Sidi Youssef", "Tajerouine",
    "Kalaat es Senam", "Kalâat Khasba", "Jérissa",
    "El Ksour", "Dahmani", "Sers"
  ],
  "Siliana": [
    "Siliana", "Bou Arada", "Gaâfour", "El Krib",
    "Maktar", "Rouhia", "Kesra", "Bargou"
  ],
  "Sousse": [
    "Sousse", "Hammam Sousse", "Akouda", "Kalâa Kebira",
    "Hergla", "Enfidha", "Bouficha", "M'saken",
    "Kalâa Seghira", "Messaadine"
  ],
  "Monastir": [
    "Monastir", "Ouerdanin", "Sahline", "Zéramdine",
    "Jemmal", "Bembla", "Moknine", "Ksar Hellal",
    "Teboulba", "Bekalta"
  ],
  "Mahdia": [
    "Mahdia", "Bou Merdes", "Ouled Chamekh", "Chorbane",
    "Ksour Essef", "Chebba", "Melloulech", "Salakta", "El Jem"
  ],
  "Sfax": [
    "Sfax", "Sakiet Ezzit", "Sakiet Eddaier", "Agareb",
    "Jebeniana", "El Hencha", "Ghraiba",
    "Bir Ali Ben Khalifa", "Kerkennah"
  ],
  "Kairouan": [
    "Kairouan", "Sbikha", "Haffouz", "El Alaa",
    "Nasrallah", "El Oueslatia", "Bouhajla"
  ],
  "Kasserine": [
    "Kasserine", "Sbeitla", "Thala", "Feriana",
    "Foussana", "Hidra"
  ],
  "Sidi Bouzid": [
    "Sidi Bouzid", "Bir El Hafey", "Meknassy",
    "Mezzouna", "Regueb", "Ouled Haffouz"
  ],
  "Gabès": [
    "Gabès", "Ghannouch", "El Hamma", "Matmata",
    "Nouvelle Matmata", "Mareth", "Oudhref", "Metouia"
  ],
  "Medenine": [
    "Medenine", "Houmt Souk", "Midoun", "Zarzis",
    "Ben Gardane", "Beni Khedache", "Ajim"
  ],
  "Tataouine": [
    "Tataouine", "Ghomrassen", "Remada", "Dehiba", "Bir Lahmar"
  ],
  "Gafsa": [
    "Gafsa", "El Ksar", "Métlaoui", "Redeyef",
    "Moulares", "Om Larayes"
  ],
  "Tozeur": [
    "Tozeur", "Nefta", "Degache", "Hazoua"
  ],
  "Kebili": [
    "Kebili", "Douz", "Souk Lahad", "El Faouar"
  ],
};

export const GOVERNORATES = Object.keys(TUNISIA_DATA);

export const ALL_CITIES = Object.values(TUNISIA_DATA).flat();

export const BUSINESS_TYPES = [
  // Restauration & Alimentation
  "Restaurant", "Café", "Lounge", "Fast-food", "Pizzeria",
  "Sandwicherie", "Snack", "Pâtisserie", "Boulangerie",
  "Boucherie", "Épicerie", "Supermarché", "Traiteur",

  // Hôtellerie & Tourisme
  "Hôtel", "Maison d'hôtes", "Auberge",
  "Résidence touristique", "Agence de voyage",

  // Santé & Médical
  "Pharmacie", "Parapharmacie", "Clinique", "Cabinet médical",
  "Dentiste", "Opticien", "Laboratoire d'analyses",
  "Vétérinaire", "Cabinet de kinésithérapie", "Radiologie",

  // Sport & Bien-être
  "Salle de sport", "Piscine", "Club sportif", "Centre de fitness",

  // Beauté & Soins
  "Salon de coiffure", "Institut de beauté", "Hammam",
  "Spa", "Centre d'esthétique", "Onglerie",

  // Formation & Éducation
  "Centre de formation", "École de langue", "Auto-école",
  "Académie de musique", "Académie de danse", "Crèche",

  // Finance & Juridique
  "Banque", "Assurance", "Agence immobilière",
  "Cabinet juridique", "Cabinet comptable",
  "Bureau de change", "Notaire",

  // Marketing & Tech
  "Agence de communication", "Agence digitale",
  "Société informatique", "Espace coworking",

  // Automobile
  "Garage", "Lavage auto", "Station-service",
  "Vente de pièces auto", "Concessionnaire",

  // Événementiel & Arts
  "Salle des fêtes", "Studio photo", "Imprimerie",
  "Librairie", "Papeterie",

  // Mode & Accessoires
  "Bijouterie", "Vêtements", "Chaussures",
  "Maroquinerie", "Lingerie", "Articles de sport",

  // Électronique & Maison
  "Électroménager", "Informatique", "Téléphonie",
  "Meubles", "Décoration", "Matériaux de construction",
  "Quincaillerie", "Droguerie", "Fleuriste",

  // Services aux entreprises
  "Transport", "Logistique", "Grossiste",
  "Bureau d'études", "Cabinet d'architecture",

  // Artisanat & BTP
  "Menuiserie", "Plomberie", "Électricité",
  "Climatisation", "Peinture", "Carrelage", "Ferronnerie",
];
