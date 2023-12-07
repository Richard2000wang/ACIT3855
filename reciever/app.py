from datetime import datetime
import connexion
from connexion import NoContent
import json
import yaml
import logging
import uuid
from pykafka import KafkaClient

# Initialize Kafka producer
client = KafkaClient(hosts='ec2-44-210-173-19.compute-1.amazonaws.com:9092')
topic = client.topics[str.encode('events')]
producer = topic.get_sync_producer()

def generate_trace_id():
    return str(uuid.uuid4())

entry = []
MAX_EVENTS = 10
EVENT_FILE = "events.json"

with open('app_conf.yaml', 'r') as f:
    app_config = yaml.safe_load(f)

with open('log_conf.yaml', 'r') as f:
    log_config = yaml.safe_load(f.read())

logging.basicConfig(
    level=log_config.get('root', {}).get('level', 'INFO'),
    format=log_config.get('formatters', {}).get('simple', {}).get('format', None)
)

logger = logging.getLogger('basicLogger')

# Use the correct Kafka topic name
topic_name = "events"
topic = client.topics[str.encode(topic_name)]


def report_covid(body):
    trace_id = generate_trace_id()
    logger.info(f"Received event REPORT request with a trace id of {trace_id}")

    current_datetime = datetime.now()
    current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    
    # Construct Kafka message
    msg = {
        "type": "event1",
        "datetime": current_datetime_str,
        "payload": {
            "age": body['age'],
            "patient_id": body['patient_id'],
            "city": body['city'],
            "vaccinated_status": body['vaccinated_status'],
            "date_handwritten": body['date_handwritten']
        }
    }
    
    # Convert message to JSON
    msg_str = json.dumps(msg)
    
    # Produce message to Kafka topic
    producer.produce(msg_str.encode('utf-8'))

    # Log the event
    entry.insert(0, {
        "recieved timestamp": current_datetime_str,
        "request_data": f"{body['age']} years old Patient {body['patient_id']} located in {body['city']}"
                        + f" caught COVID with {body['vaccinated_status']} vaccines on {body['date_handwritten']}"
    })
    
    # Write event data to file
    write_into_json(EVENT_FILE, entry)

    logger.info(f"Returned event REPORT response (Id: {trace_id}) with status 201")
    return NoContent, 201

def report_recovery(body):
    trace_id = generate_trace_id()
    logger.info(f"Received event RECOVERY request with a trace id of {trace_id}")

    current_datetime = datetime.now()
    current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    
    # Construct Kafka message
    msg = {
        "type": "event2",
        "datetime": current_datetime_str,
        "payload": {
            "patient_id": body['patient_id'],
            "hospital_visit": body['hospital_visit'],
            "date_handwritten": body['date_handwritten'],
            "recovery_status": body['recovery_status']
        }
    }
    
    # Convert message to JSON
    msg_str = json.dumps(msg)
    
    # Produce message to Kafka topic
    producer.produce(msg_str.encode('utf-8'))

    # Log the event
    entry.insert(0, {
        "recieved timestamp": current_datetime_str,
        "request_data": f"Patient {body['patient_id']} had a hospital visit: {body['hospital_visit']},"
                        + f" and successfully recovered from COVID on {body['date_handwritten']}: {body['recovery_status']}"
    })
    
    # Write event data to file
    write_into_json(EVENT_FILE, entry)

    logger.info(f"Returned event RECOVERY response (Id: {trace_id}) with status 201")
    return NoContent, 201

# Writes event data to the file
def write_into_json(data_file, data_write):
    with open(data_file, 'w') as file:
        if len(entry) > MAX_EVENTS:
            entry.pop()
        json.dump(data_write, file, indent=2)

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8080)
