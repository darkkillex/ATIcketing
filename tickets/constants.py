# tickets/constants.py

# Valore comune per "Altro"
OTHER_CODE = "OTHER"

# ICT
ICT_CATEGORY_CHOICES = [
    ("HW", "Problemi Hardware"),
    ("SW", "Problemi Software"),
    ("BKW", "BKW"),
    ("EUREKA", "Eureka"),
    ("ACCOUNT", "Account utente"),
    (OTHER_CODE, "Altro"),
]

# Magazzino (WH)
WH_CATEGORY_CHOICES = [
    ("DPI", "DPI"),
    ("CONSUMABLES", "Materiali di consumo"),
    (OTHER_CODE, "Altro"),
]

# Piano Turni (SP)
SP_CATEGORY_CHOICES = [
    ("FERIE", "Ferie"),
    ("PERMESSI", "Permessi"),
    ("CAMBIO_TURNO", "Cambio turno"),
    (OTHER_CODE, "Permessi specifici (altro)"),
]
