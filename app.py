from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Base URLs for the APIs
MOBILE_INFO_API_BASE = "https://random-remove-batch-tea.trycloudflare.com/search?mobile="
AADHAR_INFO_API_BASE = "https://random-remove-batch-tea.trycloudflare.com/search?aadhar="
AADHAR_FAMILY_API_BASE = "https://family-tau-three.vercel.app/fetch?key=taitaninfo&aadhaar="

def wrap_text(text, max_length=50):
    """Wrap long text into multiple lines"""
    if not text or len(text) <= max_length:
        return text
    
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 <= max_length:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines)

def format_entry(entry):
    """Format a single entry with wrapped text"""
    formatted = {}
    for key, value in entry.items():
        if isinstance(value, str) and len(value) > 50:
            formatted[key] = wrap_text(value, max_length=50)
        else:
            formatted[key] = value
    return formatted

@app.route('/info', methods=['GET'])
def get_details():
    mobile_number = request.args.get('number')

    if not mobile_number:
        return jsonify({"error": "Mobile number is required"}), 400

    all_results = {}
    found_aadhar_numbers = set()

    # 1. MOBILE INFO (TOP)
    all_results['MOBILE_INFO'] = {}
    try:
        mobile_info_url = f"{MOBILE_INFO_API_BASE}{mobile_number}"
        mobile_response = requests.get(mobile_info_url)
        mobile_response.raise_for_status()
        mobile_data = mobile_response.json()

        # Check if mobile_data has a 'data' key that contains the list
        data_list = None
        if isinstance(mobile_data, dict) and 'data' in mobile_data:
            data_list = mobile_data['data']
        elif isinstance(mobile_data, list):
            data_list = mobile_data

        if data_list and isinstance(data_list, list):
            # Format each entry with text wrapping
            formatted_data = [format_entry(entry) for entry in data_list]
            all_results['MOBILE_INFO'] = formatted_data
            
            # Extract Aadhaar numbers
            for entry in data_list:
                if 'id' in entry and isinstance(entry['id'], (int, str)):
                    potential_aadhar = str(entry['id'])
                    if len(potential_aadhar) == 12 and potential_aadhar.isdigit():
                        found_aadhar_numbers.add(potential_aadhar)

        else:
            all_results['MOBILE_INFO'] = {"warning": "No data found"}

    except requests.exceptions.RequestException as e:
        all_results['MOBILE_INFO'] = {"error": str(e)}

    # 2. AADHAAR INFO (MIDDLE)
    all_results['AADHAAR_INFO'] = []
    if found_aadhar_numbers:
        for aadhar_num in found_aadhar_numbers:
            try:
                aadhar_info_url = f"{AADHAR_INFO_API_BASE}{aadhar_num}"
                aadhar_response = requests.get(aadhar_info_url)
                aadhar_response.raise_for_status()
                aadhar_personal_data = aadhar_response.json()
                
                # Format data if it's a list
                if isinstance(aadhar_personal_data, list):
                    formatted_personal = [format_entry(entry) for entry in aadhar_personal_data]
                elif isinstance(aadhar_personal_data, dict):
                    formatted_personal = format_entry(aadhar_personal_data)
                else:
                    formatted_personal = aadhar_personal_data
                
                all_results['AADHAAR_INFO'].append({
                    "aadhaar_number": aadhar_num,
                    "details": formatted_personal
                })
            except requests.exceptions.RequestException as e:
                all_results['AADHAAR_INFO'].append({
                    "aadhaar_number": aadhar_num,
                    "error": str(e)
                })
    else:
        all_results['AADHAAR_INFO'] = {"status": "No valid Aadhaar numbers found"}

    # 3. FAMILY INFO (BOTTOM)
    all_results['FAMILY_INFO'] = []
    if found_aadhar_numbers:
        for aadhar_num in found_aadhar_numbers:
            try:
                aadhar_family_url = f"{AADHAR_FAMILY_API_BASE}{aadhar_num}"
                family_response = requests.get(aadhar_family_url)
                family_response.raise_for_status()
                family_data = family_response.json()
                
                # Format family data
                formatted_family = family_data
                if isinstance(family_data, dict):
                    formatted_family = {}
                    for key, value in family_data.items():
                        if isinstance(value, list):
                            formatted_family[key] = [format_entry(item) if isinstance(item, dict) else item for item in value]
                        elif isinstance(value, dict):
                            formatted_family[key] = format_entry(value)
                        else:
                            formatted_family[key] = value
                
                all_results['FAMILY_INFO'].append({
                    "aadhaar_number": aadhar_num,
                    "family_details": formatted_family
                })
            except requests.exceptions.RequestException as e:
                all_results['FAMILY_INFO'].append({
                    "aadhaar_number": aadhar_num,
                    "error": str(e)
                })
    else:
        all_results['FAMILY_INFO'] = {"status": "No family info available"}

    return jsonify(all_results)

if __name__ == '__main__':
    app.run(debug=True)
l
