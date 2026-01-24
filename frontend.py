from flask import Flask, render_template_string, request, redirect
import requests

app = Flask(__name__)

# Backend API URL (Kali VM)
# REPLACE WITH YOUR KALI VM IP
BACKEND_URL = "http://192.168.56.101:5001/tasks"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Microservice Task Manager</title></head>
<body style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h1>Distributed Task Manager</h1>
    <form action="/" method="POST">
        <input type="text" name="task" placeholder="Enter new task" required>
        <button type="submit">Add Task</button>
    </form>
    <ul>
        {% for task in tasks %}
            <li>{{ task }}</li>
        {% endfor %}
    </ul>
    <hr>
    <p><small>Frontend: Mint | Backend: Kali | DB: Alpine</small></p>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        task = request.form.get('task')
        # Send task to Backend Service
        requests.post(BACKEND_URL, json={'task': task})
        return redirect('/')
    
    # Get tasks from Backend Service
    response = requests.get(BACKEND_URL)
    tasks = response.json()
    return render_template_string(HTML_TEMPLATE, tasks=tasks)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
