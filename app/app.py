
from flask import Flask, request, jsonify, render_template
import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from query_engine import QueryEngine, CDPComparator

from response_generator import ResponseGenerator

app = Flask(__name__)


query_engine = QueryEngine('../data/index')
comparator = CDPComparator(query_engine)
response_generator = ResponseGenerator()

@app.route('/')
def index():
    """Render the chat interface"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process chat messages"""
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    

    if comparator.is_comparison_question(user_message):
        result = comparator.compare_cdps(user_message)
    else:
        
        result = query_engine.query(user_message)
    

    response = response_generator.generate_response(user_message, result)
    
    return jsonify({
        'response': response,
        'raw_result': result
    })

if __name__ == '__main__':
    app.run(debug=True)