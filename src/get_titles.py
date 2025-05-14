import http.client
import json
import string
import random
import os
import urllib.parse
from dotenv import load_dotenv

# boolean, to display loader circle
loading = False

# load API credentials from .env file
load_dotenv()
API_HOST = os.getenv("API_HOST")
API_KEY = os.getenv("API_KEY")
print("API started...")

# connect to database
conn = http.client.HTTPSConnection(API_HOST)
headers = {
    'x-rapidapi-key': API_KEY,
    'x-rapidapi-host': API_HOST
}

# convert seconds to hours, minutes and seconds
# returns converted time as string, e.g. "1 Hr. 30 Min."
def convert_seconds(seconds):
    if seconds is None:
        return "Unknown duration"

    if seconds < 60:
        return f"{seconds} Sec."
    elif seconds < 3600:
        return f"{seconds // 60} Min."
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        hour_label = "Hr." if hours == 1 else "Hrs."
        return f"{hours} {hour_label} {minutes} Min." if minutes else f"{hours} {hour_label}"

# find keys in JSON
# returns value of found key
def find_key(data, target_key):
    results = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key == target_key:
                results.append(value)
            if isinstance(value, (dict, list)):
                results.extend(find_key(value, target_key))
    elif isinstance(data, list):
        for item in data:
            results.extend(find_key(item, target_key))
    return results

# generate a random two letter long query for database
# returns random query of tow letters, e.g. "bi"
def generate_random_query():
    letters = string.ascii_lowercase
    vowels = "aeiou"
    combination = [first + second for first in letters for second in vowels]
    return random.choice(combination)

# set up connection to database
# returns JSON data, empty JSON if connection failed
def retrieve_json_data():
    query = generate_random_query()
    print("Query:", query)
    conn.request("GET", f"/auto-complete?query={query}", headers=headers)
    
    res = conn.getresponse()
    response_code = res.status
    response_reason = res.reason
    
    if response_code == 200:
        print("Connection successfull:", response_code, response_reason)
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        print(json_data)
        with open('random_titles.json', 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
        conn.close()
        return json_data
    else:
        print("Connection failed:", response_code, response_reason)
        conn.close()
        return {}

# checks if data entries are valid titles
# returns True if valid, False if not
def validate_entry(key_index, json_data):
    entry = json_data["data"]["d"][key_index]
    return len(entry) == 8

# get title id from JSON data
# returns title ids if found, empty array if not matching titles found
def get_title_id(available_titles):
    titles = []
    for index, title in enumerate(available_titles["data"]["d"]):
        if validate_entry(index, available_titles):
            titles.append(title["id"])
    return titles

# gets 10 random titles from JSON data
# returns random titles
def get_random_titles():
    random_titles = []
    while len(random_titles) < 5:
        raw_json = retrieve_json_data()
        available_titles = get_title_id(raw_json)
        if len(available_titles) > 0:
            random_index = random.randint(0, len(available_titles) - 1)
            random_titles.append(available_titles[random_index])
    write_to_file(random_titles)

# get title related data
def get_genres(title_id):
    conn.request("GET", f"/title/get-genres?tconst={title_id}", headers=headers)
    res = conn.getresponse().read().decode("utf-8")
    json_data = json.loads(res)

    genres = find_key(json_data, "genre")  
    genres_as_text = [genre["text"] for genre in genres if isinstance(genre, dict) and "text" in genre]

    return genres_as_text

def get_video_id(title_id):
    conn.request("GET", f"/title/get-auto-start-hero-video-ids?tconst={title_id}", headers=headers)
    res = conn.getresponse().read().decode("utf-8")
    json_data = json.loads(res)

    title_data = find_key(json_data, "title")

    primary_video_id = (
        title_data[0]["primaryVideos"]["edges"][0]["node"]["id"]
        if title_data and isinstance(title_data, list) and len(title_data) > 0
        and isinstance(title_data[0], dict) and "primaryVideos" in title_data[0]
        and isinstance(title_data[0]["primaryVideos"], dict) and "edges" in title_data[0]["primaryVideos"]
        and isinstance(title_data[0]["primaryVideos"]["edges"], list) and len(title_data[0]["primaryVideos"]["edges"]) > 0
        and isinstance(title_data[0]["primaryVideos"]["edges"][0], dict) and "node" in title_data[0]["primaryVideos"]["edges"][0]
        and isinstance(title_data[0]["primaryVideos"]["edges"][0]["node"], dict) and "id" in title_data[0]["primaryVideos"]["edges"][0]["node"]
        else None
    )

    return primary_video_id

def get_runtime_and_episodes(title_id):
    conn.request("GET", f"/title/get-extend-details?tconst={title_id}", headers=headers)
    res = conn.getresponse().read().decode("utf-8")
    json_data = json.loads(res)

    title_data = find_key(json_data, "title")
    
    runtime_seconds = (
        title_data[0]["runtime"]["seconds"]
        if title_data and isinstance(title_data, list) and len(title_data) > 0
        and isinstance(title_data[0], dict) and "runtime" in title_data[0]
        and isinstance(title_data[0]["runtime"], dict) and "seconds" in title_data[0]["runtime"]
        else None
    )

    episodes = (
        title_data[0]["episodes"]["episodes"]["total"]
        if title_data and isinstance(title_data, list) and len(title_data) > 0
        and isinstance(title_data[0], dict) and "episodes" in title_data[0]
        and isinstance(title_data[0]["episodes"], dict) and "episodes" in title_data[0]["episodes"]
        and isinstance(title_data[0]["episodes"]["episodes"], dict) and "total" in title_data[0]["episodes"]["episodes"]
        else None
    )

    text_episode = " per episode" if episodes is not None and episodes > 0 else ""

    return episodes, f"{convert_seconds(runtime_seconds)}{text_episode}"

def get_details(video_id):
    conn.request("GET", f"/title/get-video-playback?viconst={video_id}", headers=headers)
    res = conn.getresponse()
    data = res.read()
    json_data = json.loads(data.decode("utf-8"))

    video_data = json_data["data"]["video"] if "data" in json_data and isinstance(json_data["data"], dict) and "video" in json_data["data"] and isinstance(json_data["data"]["video"], dict) else {}

    title_data = [video_data["primaryTitle"]] if "primaryTitle" in video_data and isinstance(video_data["primaryTitle"], dict) else []

    original_title = title_data[0]["originalTitleText"]["text"] if title_data and isinstance(title_data[0], dict) and "originalTitleText" in title_data[0] and "text" in title_data[0]["originalTitleText"] else None
    release_year = title_data[0]["releaseYear"]["year"] if title_data and isinstance(title_data[0], dict) and "releaseYear" in title_data[0] and "year" in title_data[0]["releaseYear"] else None
    title_type = title_data[0]["titleType"]["text"] if title_data and isinstance(title_data[0], dict) and "titleType" in title_data[0] and "text" in title_data[0]["titleType"] else None
    poster_url = title_data[0]["primaryImage"]["url"] if title_data and isinstance(title_data[0], dict) and "primaryImage" in title_data[0] and "url" in title_data[0]["primaryImage"] else None
    certificate_rating = title_data[0]["certificate"]["rating"] if title_data and isinstance(title_data[0], dict) and "certificate" in title_data[0] and "rating" in title_data[0]["certificate"] else None
    aggregate_rating = title_data[0]["ratingsSummary"]["aggregateRating"] if title_data and isinstance(title_data[0], dict) and "ratingsSummary" in title_data[0] and "aggregateRating" in title_data[0]["ratingsSummary"] else None

    playback_urls = video_data["playbackURLs"] if "playbackURLs" in video_data and isinstance(video_data["playbackURLs"], list) else []
    playback_url = playback_urls[1]["url"] if len(playback_urls) > 1 and isinstance(playback_urls[1], dict) and "url" in playback_urls[1] else None

    return original_title, release_year, poster_url, certificate_rating, aggregate_rating, playback_url, title_type

def get_plot(title_id):
    conn.request("GET", f"/title/get-plot?tconst={title_id}", headers=headers)
    res = conn.getresponse().read().decode("utf-8")
    json_data = json.loads(res)

    title_data = find_key(json_data, "title")

    plot_text = (
        title_data[0]["plot"]["plotText"]["plainText"]
        if title_data and isinstance(title_data, list) and len(title_data) > 0
        and isinstance(title_data[0], dict) and "plot" in title_data[0]
        and isinstance(title_data[0]["plot"], dict) and "plotText" in title_data[0]["plot"]
        and isinstance(title_data[0]["plot"]["plotText"], dict) and "plainText" in title_data[0]["plot"]["plotText"]
        else None
    )

    return plot_text

def get_title_infos(title_id):
    video_id = get_video_id(title_id)
    results = get_details(video_id)
    extra_details = get_runtime_and_episodes(title_id)

    title_object = {
        "id": title_id,
        "description": get_plot(title_id),
        "name": results[0],
        "year": results[1],
        "poster": results[2],
        "age": results[3],
        "rating": results[4],
        "trailer": results[5],
        "isMovie": results[6],
        "episodes": extra_details[0],
        "runtime": extra_details[1],
        "genres": get_genres(title_id),
    }
    return title_object

# write title object to file and palces file in current dir
def write_to_file(title_id):
    global loading
    loading = True
    title_ids = [title_id] if isinstance(title_id, str) else title_id

    title_objects = [get_title_infos(tid) for tid in title_ids]

    with open('answer.json', 'w', encoding='utf-8') as f:
        json.dump(title_objects, f, ensure_ascii=False, indent=4)
    loading = False

# get search results
# returns 3 search results 
def get_search_result():
    with open("speech_query.txt", "r", encoding="utf-8") as file:
        content = file.read()
    encoded_search_term = urllib.parse.quote(content)

    conn.request("GET", f"/search?searchTerm={encoded_search_term}", headers=headers)
    res = conn.getresponse().read().decode("utf-8")
    json_data = json.loads(res)

    edges = json_data.get("data", {}).get("mainSearch", {}).get("edges", [])
    ids = [
        edge["node"]["entity"]["id"]
        for edge in edges[:3]
        if isinstance(edge, dict) and "node" in edge and "entity" in edge["node"] and "id" in edge["node"]["entity"]
    ]
    write_to_file(ids)

print("API ended...")

conn.close()