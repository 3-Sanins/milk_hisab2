from flask import Flask, render_template, request, jsonify
import re
from datetime import datetime
import pickle,os,csv
#import pymysql as mysql

app = Flask(__name__)

def convert_hindi_words_to_numbers(text):
    """
    Converts Hindi number words (like "chaubees") to digits (like "24").
    Uses `word2number` to intelligently convert numbers written as words.
    """
    try:
        # Split the text into words
        words = text.lower().split()
        converted_text = []
        temp_phrase = []

        for word in words:
            temp_phrase.append(word)
            try:
                # Try converting the phrase to a number
                num = w2n.word_to_num(" ".join(temp_phrase))
                converted_text.append(str(num))  # Replace words with numeric digits
                temp_phrase = []  # Reset after conversion
            except ValueError:
                continue  # Keep adding words until we detect a number

        # Add remaining words that couldn't be converted
        if temp_phrase:
            converted_text.extend(temp_phrase)

        return " ".join(converted_text)

    except Exception as e:
        pass

def update(R, amt2):
    with open("templates/hisab.csv", "r") as f, open("templates/temp.csv", "w", newline="") as fw:
        read = csv.reader(f)
        writ = csv.writer(fw)
        for r in read:
            if r[:2] == R[:2]:  # Date aur Shift match kare toh update karein
                r[2] = amt2
            writ.writerow(r)

    os.remove("templates/hisab.csv")
    os.rename("templates/temp.csv", "templates/hisab.csv")

def extract_data(text):
    """
    Extracts date, shift (morning/evening), and amount from the provided text.
    Expected format:
      - Date: "24 March" -> Converted to "24-03-2025"
      - Shift: "subah" (morning) / "shaam" (evening)
      - Amount: "289.97"
    """
    date = None
    shift = None
    amount = None

    list_of_words = text.split()
    for word in list_of_words:
        digit=convert_hindi_words_to_numbers(word)
        if digit:
            text=text.replace(word,digit)
    text=" ".join(list_of_words)


    # Dictionary to convert Hindi month names to numerical format
    month_map = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12"
    }

    # Extract date pattern (e.g., "24 March" or "24 march")
    date_pattern = re.search(r'(\d{1,2})\s+([A-Za-z]+)', text, re.IGNORECASE)
    if date_pattern:
        day = date_pattern.group(1)
        month_name = date_pattern.group(2).lower()

        if month_name in month_map:
            month = month_map[month_name]
            year = datetime.now().year  # Assume current year
            date = f"{year}-{month}-{day}"  # New format: YYYY-MM-DD

    # Extract shift: "subah" (morning) or "shaam" (evening)
    if "subah" in text.lower():
        shift = "morning"
    elif "shaam" in text.lower() or "sham" in text.lower():
        shift = "evening"

    # Extract amount (supports decimal values)
    amount_pattern = re.search(r'(\d+\.\d+)', text)
    if amount_pattern:
        amount = amount_pattern.group(1)

    if date and shift and amount:
        f=open("templates/hisab.csv","a+",newline="\r\n")
        f.seek(0)
        read=csv.reader(f)
        found=0
        for r in read:
            if len(r)<2:
                continue
            if r[0]==date and r[1]==shift:
                f.close()
                update(r,amount)
                found=1
                break
        if found==0:
            csvw=csv.writer(f)
            csvw.writerow([date,shift,amount])
            f.close()
                

    return date, shift, amount


@app.route('/select_month', methods=['GET', 'POST'])
def select_month():
    total_value = 0  # Placeholder for total value
    data_table = []  # Placeholder for nested tuple

    if request.method == 'POST':
        selected_month = request.form['month']
        if len(selected_month) == 1:
            selected_month = "0" + selected_month
        fr=open("templates/hisab.csv","a+",newline="\r\n")
        fr.seek(0)
        read=csv.reader(fr)
        for r in read:
            if len(r)<2:
                continue
            if selected_month in r[0]:
                data_table.append(r)
                total_value=total_value+float(r[2])
        fr.close()

        return render_template('select_month.html', total=total_value, data=data_table, selected_month=selected_month)

    return render_template('select_month.html', total=None, data=None, selected_month=None)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    text = data.get('text', '')
    date, shift, price = extract_data(text)
    return jsonify({
        'date': date,
        'shift': shift,
        'price': price,
        'original_text': text
    })

if __name__ == '__main__':
    app.run(debug=True)
