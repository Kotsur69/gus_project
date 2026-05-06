# Analiza Rynku Pracy i Wynagrodzeń w Polsce

**Projekt Zaliczeniowy — WSB Merito 2024/2025**  
Autor: Mateusz Mazur (nr albumu: 137683)

## Opis

Aplikacja webowa Flask prezentująca interaktywną analizę statystyczną rynku pracy i wynagrodzeń w Polsce na podstawie danych Głównego Urzędu Statystycznego (GUS) za lata 2015–2024.

## Funkcjonalności

- **System logowania** — rejestracja, logowanie, wylogowanie z hashowaniem haseł (Werkzeug)
- **7 interaktywnych wykresów Plotly** — dostępnych wyłącznie po zalogowaniu
- **Analiza danych GUS** — wynagrodzenia nominalne/realne, bezrobocie regionalne, PKD, luka płacowa
- **Responsywny dark-mode UI** — estetyka cyberpunk, fonty Outfit + JetBrains Mono

## Stos technologiczny

| Technologia | Zastosowanie |
|------------|-------------|
| Python 3.11+ | Backend + analiza danych |
| Flask 3.x | Framework webowy |
| Flask-Login | Sesje użytkowników |
| Flask-SQLAlchemy | ORM (SQLite) |
| pandas | Przetwarzanie danych |
| Plotly | Wizualizacje interaktywne |
| Werkzeug | Hashowanie haseł |

## Instalacja i uruchomienie

```bash
# 1. Klonowanie / rozpakowanie projektu
cd gus_project

# 2. Instalacja zależności
pip install -r requirements.txt

# 3. Uruchomienie serwera
python app.py

# 4. Otwórz w przeglądarce
# http://localhost:5000
```

## Struktura projektu

```
gus_project/
├── app.py                  # Główna aplikacja Flask
├── requirements.txt        # Zależności Python
├── README.md
├── data/
│   ├── wynagrodzenia_polska.csv   # Wynagrodzenia brutto + CPI + bezrobocie
│   ├── bezrobocie_woj.csv         # Stopa bezrobocia wg województw
│   ├── zatrudnienie_pkd.csv       # Zatrudnienie i wynagrodzenia wg PKD
│   └── luka_placowa.csv           # Gender pay gap
├── templates/
│   ├── base.html           # Szablon bazowy (nav, CSS, footer)
│   ├── index.html           # Strona główna (landing page)
│   ├── login.html           # Formularz logowania
│   ├── register.html        # Formularz rejestracji
│   ├── dashboard.html       # Dashboard z wykresami (wymaga logowania)
│   └── methodology.html     # Opis metodologii i bibliografia
└── instance/
    └── users.db             # Baza danych SQLite (tworzona automatycznie)
```

## Źródła danych

- [GUS — Bank Danych Lokalnych](https://bdl.stat.gov.pl)
- [GUS — Komunikaty i Obwieszczenia](https://stat.gov.pl)
- [Eurostat — Earnings Statistics](https://ec.europa.eu/eurostat)

## Licencja

Projekt akademicki — WSB Merito 2024/2025.
