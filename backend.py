from flask import Flask, request, jsonify
import redis

app = Flask(__name__)

# Connect to Redis on Alpine VM
r = redis.Redis(host='192.168.56.103', port=6379, decode_responses=True)

@app.route('/tasks', methods=['GET', 'POST'])
def manage_tasks():
    if request.method == 'POST':
        task = request.json.get('task')
        if task:
            r.rpush('tasks', task)
            return jsonify({"status": "success", "task": task}), 201
    
    # GET method
    tasks = r.lrange('tasks', 0, -1)
    return jsonify(tasks)

if __name__ == '__main__':
    # Host 0.0.0.0 makes it accessible to other VMs
    app.run(host='0.0.0.0', port=5001)
