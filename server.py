from flask import Flask, request, jsonify
import subprocess
from bs4 import BeautifulSoup
import pandas as pd
import mysql.connector
from mysql.connector import Error
import time
import os
app = Flask(__name__)
import time

def fetch_html(url):
    try:
        result = subprocess.run(['node', 'fetchAndExtract.js', url], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
        else:
            print("Error executing the JavaScript code:", result.stderr)
            return None
    except Exception as e:
        print("Exception occurred:", e)
        return None

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    try:
        html_content = fetch_html(url)
        soup = BeautifulSoup(html_content, 'html.parser')
        tbody = soup.find('table', {'id': 'table'})
        if tbody is None:
            raise ValueError("No tbody found in table")
        rows = tbody.find_all('tr')[1:]
        data = []
        headers = ['CIN','Company','RoC','Status']
        headers.append('URL')
        for row in rows:
            cells = row.find_all('td')
            cin = cells[0].text.strip()
            company_name_tag = cells[1].find('a')
            company_name = company_name_tag.text.strip() if company_name_tag else cells[1].text.strip()
            company_url = company_name_tag['href'] if company_name_tag else ''
            roc = cells[2].text.strip()
            status = cells[3].text.strip()
            data.append([cin, company_name, roc, status, company_url])
        df = pd.DataFrame(data, columns=headers)
        df_json = df.to_json(orient='records')
        return jsonify(df_json)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)