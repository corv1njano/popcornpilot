from flask import Flask, render_template, request, jsonify
import json
import os
import get_titles

app = Flask(__name__, template_folder=os.path.dirname(os.path.abspath(__file__)), static_folder=os.path.dirname(os.path.abspath(__file__)))

# Sicherstellen, dass alle Dateien im gleichen Ordner wie app.py gespeichert sind
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANSWER_FILE = os.path.join(BASE_DIR, "answer.json")
SPEECH_QUERY_FILE = os.path.join(BASE_DIR, "speech_query.txt")
INDEX_FILE = os.path.join(BASE_DIR, "index.html")
STYLES_FILE = os.path.join(BASE_DIR, "styles.css")

# Stelle sicher, dass speech_query.txt existiert
if not os.path.exists(SPEECH_QUERY_FILE):
    with open(SPEECH_QUERY_FILE, "w", encoding="utf-8") as f:
        f.write("")

# Funktion zum Laden der JSON-Daten
def load_answer_data():
    if os.path.exists(ANSWER_FILE):
        with open(ANSWER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Filter: Nur Einträge behalten, die einen Namen haben
        valid_entries = [entry for entry in data if entry.get("name")]

        return valid_entries
    return []

# Speichert den Sprachbefehl in speech_query.txt und startet die get_search_result function.
def save_speech_query(query):
    with open(SPEECH_QUERY_FILE, "w", encoding="utf-8") as f:
        f.write(query)

    get_titles.get_search_result()

# Hauptseite rendern
@app.route("/")
def index():
    return render_template("index.html")

# API zum Empfangen von Sprachdaten
@app.route("/speech_input", methods=["POST"])
def speech_input():
    data = request.json
    speech_text = data.get("speech", "").strip()

    # Entfernt einen Punkt am Ende, falls vorhanden
    if speech_text.endswith("."):
        speech_text = speech_text[:-1]

    if speech_text:
        save_speech_query(speech_text)

        # Automatische Suche in answer.json
        data = load_answer_data()
        results = [entry for entry in data if entry.get("name") not in [None, ""] and speech_text in entry["name"]]
        
        return jsonify({"message": "Speech input saved!", "query": speech_text, "results": results})

    return jsonify({"error": "No speech input received"}), 400

# API zum Durchsuchen von answer.json basierend auf Suchanfrage
@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "")
    data = load_answer_data()
    results = [entry for entry in data if entry.get("name") not in [None, ""] and query in entry["name"]]
    
    return jsonify(results)

@app.route("/random_movies", methods=["GET"])
def showallrandommovies():
    get_titles.get_random_titles()  # Holt zufällige Filme

    # Lade die Antwort aus answer.json
    data = load_answer_data()
    
    return jsonify(data)


@app.route("/filter", methods=["GET"])
def filter_movies():
    genres = request.args.getlist("genre")  # Liste der ausgewählten Genres
    year_filter = request.args.get("year", "")

    data = load_answer_data()

    filtered_results = [
        movie for movie in data
        if (not genres or all(genre.lower() in (g.lower() for g in movie.get("genres", [])) for genre in genres))  # Falls keine Genres ausgewählt sind, werden alle zugelassen
        and (not year_filter or str(movie.get("year", "")) == year_filter)  # Falls kein Jahr ausgewählt ist, wird es ignoriert
    ]

    return jsonify(filtered_results)


if __name__ == "__main__":  
    app.run(debug=True)
