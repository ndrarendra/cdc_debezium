from flask import Flask, render_template, request, jsonify
from kafka import KafkaConsumer
import threading
import json
import logging
import datetime
import time
from collections import deque

app = Flask(__name__)

# Keep the last 1000 events in memory
cdc_events = deque(maxlen=1000)

logging.basicConfig(level=logging.INFO)

def safe_deserializer(message):
    """Safely deserialize a Kafka message from JSON."""
    try:
        return json.loads(message.decode('utf-8')) if message else None
    except Exception as e:
        logging.error("Deserialization error: %s", e)
        return None

def kafka_consumer():
    """Continuously polls Kafka for CDC events and appends them to cdc_events."""
    while True:
        try:
            consumer = KafkaConsumer(
                'demo_server.demo_db.users',    # Your topic name
                'demo_server_all.demo_db.employees',
                bootstrap_servers=['kafka:9092'],
                auto_offset_reset='earliest',
                group_id="flask-group",
                value_deserializer=safe_deserializer
            )
            logging.info("Kafka Consumer connected to topic: demo_server.demo_db.users")

            for message in consumer:
                if not message.value:
                    continue

                value = message.value  # The JSON dict from Debezium

                # Debezium's top-level fields for MySQL: 'op', 'before', 'after', etc.
                op = value.get('op')  # "c", "u", "d", or "r"
                source = value.get('source', {})
                database = source.get('db', 'N/A')
                table = source.get('table', 'N/A')
                ts_ms = value.get('ts_ms', int(time.time() * 1000))

                # If 'op' is 'd', we use 'before', otherwise 'after'
                if op == 'd':
                    data = value.get('before', {})
                else:
                    data = value.get('after', {})

                event = {
                    'topic': message.topic,
                    'partition': message.partition,
                    'offset': message.offset,
                    'database': database,
                    'table': table,
                    'op': op,
                    'ts_ms': ts_ms,
                    'data': data
                }

                logging.info(f"Received message: {event}")
                cdc_events.append(event)

        except Exception as e:
            logging.error("Kafka consumer error: %s", e)
            time.sleep(5)

@app.template_filter('format_ts')
def format_ts(ts):
    """Convert ms-based UNIX timestamp into YYYY-MM-DD HH:MM:SS."""
    return datetime.datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d %H:%M:%S')

@app.route("/")
def index():
    """Displays the events in a table, with optional filters."""
    db_filter = request.args.get('database', '')
    table_filter = request.args.get('table', '')
    op_filter = request.args.get('op', '')

    filtered_events = [
        e for e in cdc_events
        if (db_filter.lower() in e['database'].lower() if db_filter else True)
        and (table_filter.lower() in e['table'].lower() if table_filter else True)
        and (op_filter == e['op'] if op_filter else True)
    ]
    return render_template("index.html", events=filtered_events)

@app.route("/api/events")
def api_events():
    """Return a JSON representation of the events."""
    return jsonify(list(cdc_events))

if __name__ == "__main__":
    consumer_thread = threading.Thread(target=kafka_consumer, daemon=True)
    consumer_thread.start()
    app.run(debug=True, host='0.0.0.0', port=5000)
