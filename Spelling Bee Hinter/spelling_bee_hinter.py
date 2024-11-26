#!/usr/bin/env python

"""
Script to download current Spelling Bee answer set and obtain a list of hints 
from ChatGPT based on the answers.
The script requires a config file called spelling_bee_config.py in the same 
directory defining a variable called OPENAI_API_KEY as a string to work 
correctly.
Example config file (note the API key is case senstive):
OPENAI_API_KEY = "MyOPenAIAPIKey"
"""

from openai import OpenAI
import requests
import re
import json

from spelling_bee_config import OPENAI_API_KEY

def main():

    SPELLING_BEE_URL = "https://www.nytimes.com/puzzles/spelling-bee"

    # Define regex to extract JSON-like data
    spelling_bee_regex = r'(?<=<script type="text\/javascript">window.gameData = ).+?(?=<\/script>)'

    def extract_data_from_website(url):
        # Function to obtain current Spelling Bee answers and return dict of answers
        try:
            response = requests.get(url)
            # Check for HTTP success status
            if response.status_code != 200:
                raise Exception(
                    f"Failed to fetch website. Status Code: {response.status_code}"
                )
            html = response.text
            matches = re.search(spelling_bee_regex, html)
            if matches:
                extracted_data = json.loads(matches.group(0))
                return extracted_data
            else:
                print("No matching data found.")
                return None
        except Exception as error:
            print("Error fetching or processing the website:", str(error))

    spelling_bee_data = extract_data_from_website(SPELLING_BEE_URL)
    todays_answers = spelling_bee_data["today"]["answers"]

    # Build the ChatGPT prompt
    chatgpt_client = OpenAI(api_key=OPENAI_API_KEY)

    chat_gpt_prompt = """For each of the following answer words provide a list of hints for a Spelling Bee word game. Hints should be no more than one line of text long. Provide only the hints in raw JSON format as follows: 
    {
    "spelling_bee_hints": {
    "word": "hint",
    }
    } with the dictionary being called spelling_bee_hints and each answer as a key. The output should take the format of a valid JSON object - Keys must be double-quoted strings and should always be followed by a colon and value. Values can be any valid data type such as strings, numbers, objects, arrays etc. Strings must also be double-quoted. Answers: \n"""
    answer_text = " ".join(todays_answers)
    chat_gpt_prompt = chat_gpt_prompt + answer_text

    completion = chatgpt_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": chat_gpt_prompt,
            }
        ]
    )
    spelling_bee_hints = completion.choices[0].message.content
    json_regex_pattern = r'{.*}'
    match = re.search(json_regex_pattern, spelling_bee_hints, re.DOTALL)
    spelling_bee_json = json.loads(match.group(0))

    # Alphabetical sort
    key_list = sorted(spelling_bee_json["spelling_bee_hints"].keys())
    # Sort by word length where first two letters are equal
    key_list = sorted(
        key_list,
        key=lambda word: (word[:2], len(word)) 
    )

    for key in key_list:
        print(f"[{key[0:2].upper()} {len(key)}]: {spelling_bee_json["spelling_bee_hints"][key]}")

if __name__ == "__main__":
    main()