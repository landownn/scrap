# Plan projektu: „Jak media mówią o AI?”

## 1) Dane (The Guardian API)

**Cel:** zebrać ok. 500–3000 artykułów o AI wraz z metadanymi (data, dział/sekcja, tytuł, lead, pełny tekst).

**Słowa-klucze (query):**
- "artificial intelligence" OR AI OR "machine learning" OR ChatGPT OR OpenAI OR "large language model" OR LLM

**Pola do zapisania w DataFrame:**
- `id` / `url`
- `date`
- `sectionName`
- `type`
- `title`
- `trailText` (lead)
- `bodyText` (pełny tekst)
- *(opcjonalnie)* `tags`

**Uwaga dot. źródeł PL:**
- Dla mediów po polsku zwykle zostaje RSS (czasem ukryte) i scrapowanie, co zwiększa tarcie prawne/techniczne.
- Guardian API to szybka i legalna ścieżka na zaliczenie.

## 2) Czyszczenie i normalizacja tekstu

**Pipeline:**
1. Połącz `title + trailText + bodyText`.
2. Zmień na lowercase.
3. Usuń HTML/URL, znaki specjalne, nadmiar spacji.
4. Tokenizacja.
5. Stopwords (ENG).
6. Lematyzacja (spaCy) lub stemming (Snowball) — lematyzacja jest czytelniejsza w raporcie.
7. Filtr długości tokenu (np. `len >= 3`).
8. *(Opcjonalnie)* bigramy/trigramy (gensim `Phrases`).

## 3) N-gramy (wyniki do slajdów)

- Unigramy i bigramy dla całego korpusu.
- Dodatkowo: top n-gramy per dział (np. “technology”, “business”, “politics”).
- *(Opcjonalnie)* top n-gramy per okres (miesiąc/kwartał), jeśli danych jest wystarczająco dużo.

## 4) Topic modeling (tematy/narracje)

**Rekomendacja:**
- **BERTopic** jako główne “narracje” (wysoka jakość wyników przy mniejszym dłubaniu).
- **LDA** jako “sanity check” (opcjonalnie; bardziej „kursowy”, ale wymaga lepszej normalizacji).

## 5) „Twist” projektu: ramy (risk/benefit/regulation)

Zdefiniuj 3–5 ramek, każda po 10–20 słów. Przykładowe ramy:

**RISK/HARM:**
- risk, threat, dangerous, bias, harm, misinformation, deepfake, security, surveillance, fraud, manipulation, dystopia

**BENEFIT/PRODUCTIVITY:**
- benefit, boost, efficiency, productivity, automate, assist, tool, innovation, breakthrough, optimize, improve, growth

**WORK/JOBS:**
- jobs, layoffs, workforce, workers, skills, reskill, unemployment, replace, hiring, wage

**REGULATION/GOV:**
- regulation, law, policy, government, eu, compliance, oversight, ban, standards, accountability, safety

**(Opcjonalnie) ETHICS/VALUES:**
- ethics, fairness, transparency, responsibility, trust, consent

### Wskaźniki

**Prosty i czytelny sposób liczenia:**
- `frame_score = liczba trafień słów z ramy / liczba wszystkich tokenów`
- Alternatywnie: przelicz na 1000 słów (czytelniejsze porównania).

**Agregacje:**
- Średnia/mediana per `sectionName`.
- Trend w czasie (tydzień/miesiąc).
- Porównanie działów (np. “business” vs “politics” vs “technology”).

### Bonus metodologiczny

- Lematyzuj słowa w ramach tak samo jak tekst, aby np. “regulate/regulation” było spójne.
- Przetestuj 2 wersje słowników i pokaż stabilność wyników.
