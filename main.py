from flask import Flask, render_template_string, jsonify
from kafka import KafkaConsumer
import threading
import json
import time
import logging
import datetime

# Configure logging for debugging.
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Global list to store CDC events (for demo purposes; consider a bounded store for production).
cdc_events = []

# Update this topic to match your Debezium connector configuration.
topic_name = 'demo_server.demo_db.users'


def safe_deserializer(message):
    """ Safely deserialize a Kafka message. """
    try:
        if message is None:
            return None
        return json.loads(message.decode('utf-8'))
    except Exception as e:
        logging.error("Deserialization error: %s", e)
        return None


def consume_messages():
    consumer = KafkaConsumer(
        topic_name,
        bootstrap_servers=['kafka:9092'],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id="flask-consumer-group",
        value_deserializer=safe_deserializer
    )
    logging.info("Consumer subscribed to topic: %s", topic_name)
    while True:
        try:
            records = consumer.poll(timeout_ms=5000)
            if records:
                for tp, messages in records.items():
                    for message in messages:
                        if message.value is not None:
                            logging.info("Received message from topic: %s, partition: %s, offset: %s",
                                         message.topic, message.partition, message.offset)
                            logging.info("Raw message content: %s",
                                         json.dumps(message.value, indent=2))
                            event = {
                                'topic': message.topic,
                                'partition': message.partition,
                                'offset': message.offset,
                                'data': message.value
                            }
                            cdc_events.append(event)
                        else:
                            logging.warning("Received a tombstone (null) message from topic: %s, partition: %s, offset: %s",
                                            message.topic, message.partition, message.offset)
            else:
                logging.info("No new messages in this cycle.")
        except Exception as e:
            logging.error("Error during message consumption: %s", e)
        time.sleep(1)


# Start consumer in a background thread.
consumer_thread = threading.Thread(target=consume_messages, daemon=True)
consumer_thread.start()

# Custom filter: convert millisecond timestamp to a human-readable datetime string.


@app.template_filter('timestamp_to_datetime')
def timestamp_to_datetime(ts):
    try:
        return datetime.datetime.fromtimestamp(ts / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return 'N/A'


# HTML template with an extra column "Inserted Data" and a modal popup for details.
template = """
<!DOCTYPE html>
<html>
<head>
    <title>CDC Events Report</title>
    <!-- Bootstrap CSS for neat design -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        pre { margin: 0; font-size: 0.9em; }
    </style>
</head>
<body>
  <div class="container mt-4">
    <h1>CDC Events Report</h1>
    <table class="table table-striped table-bordered">
        <thead class="thead-dark">
            <tr>
                <th>Operation</th>
                <th>Topic</th>
                <th>Partition</th>
                <th>Offset</th>
                <th>Database</th>
                <th>Table</th>
                <th>Action</th>
                <th>Timestamp</th>
                <th>User / Source</th>
                <th>Readable Summary</th>
                <th>Inserted Data</th>
                <th>Details</th>
            </tr>
        </thead>
        <tbody>
            {% for event in events %}
            <tr>
                <!-- Operation -->
                <td>{{ event.data.op if event.data and event.data.op else 'N/A' }}</td>
                <!-- Topic -->
                <td>{{ event.topic if event.topic else 'N/A' }}</td>
                <!-- Partition -->
                <td>{{ event.partition if event.partition is defined else 'N/A' }}</td>
                <!-- Offset -->
                <td>{{ event.offset if event.offset is defined else 'N/A' }}</td>
                <!-- Database -->
                <td>{{ event.data.source.db if event.data and event.data.source and event.data.source.db else 'N/A' }}</td>
                <!-- Table -->
                <td>{{ event.data.source.table if event.data and event.data.source and event.data.source.table else 'N/A' }}</td>
                <!-- Action -->
                <td>
                    {% set op = event.data.op if event.data and event.data.op else 'N/A' %}
                    {% if op == 'c' %}
                        Insert
                    {% elif op == 'u' %}
                        Update
                    {% elif op == 'd' %}
                        Delete
                    {% elif op == 'r' %}
                        Snapshot
                    {% else %}
                        {{ op }}
                    {% endif %}
                </td>
                <!-- Timestamp -->
                <td>{{ event.data.ts_ms | timestamp_to_datetime if event.data and event.data.ts_ms else 'N/A' }}</td>
                <!-- User / Source -->
                <td>{{ event.data.source.connector if event.data and event.data.source and event.data.source.connector else 'N/A' }}</td>
                <!-- Readable Summary -->
                <td>
                    {% if event.data.after %}
                        ID: {{ event.data.after.id }},
                        Name: {{ event.data.after.name }},
                        Email: {{ event.data.after.email }}
                    {% else %}
                        N/A
                    {% endif %}
                </td>
                <!-- Inserted Data -->
                <td>
                    {% if event.data.after %}
                        <pre>{{ event.data.after | tojson(indent=2) }}</pre>
                    {% else %}
                        N/A
                    {% endif %}
                </td>
                <!-- Details Button -->
                <td>
                    <button class="btn btn-primary btn-sm" onclick='showDetails({{ event.data | tojson }})'>View</button>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
  </div>

  <!-- Modal Popup for detailed JSON -->
  <div class="modal fade" id="detailsModal" tabindex="-1" role="dialog">
    <div class="modal-dialog modal-lg" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Event Details</h5>
          <button type="button" class="close" data-dismiss="modal">&times;</button>
        </div>
        <div class="modal-body">
          <pre id="modalContent"></pre>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Scripts for modal functionality -->
  <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
  <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
  <script>
    function showDetails(data) {
        document.getElementById('modalContent').textContent = JSON.stringify(data, null, 2);
        $('#detailsModal').modal('show');
    }
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(template, events=cdc_events)


@app.route("/api/events")
def api_events():
    return jsonify(cdc_events)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
