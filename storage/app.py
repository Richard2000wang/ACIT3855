from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread
import json
from datetime import datetime
import connexion
from connexion import NoContent
import json
import yaml
import logging
import uuid

# Initialize Kafka producer
with open('app_conf.yaml', 'r') as f:
    app_config = yaml.safe_load(f)

kafka_config = app_config.get('events', {})
client = KafkaClient(hosts=f"{kafka_config['hostname']}:{kafka_config['port']}")
topic = client.topics[str.encode(kafka_config['topic'])]
producer = topic.get_sync_producer()

def generate_trace_id():
    return str(uuid.uuid4())

entry = []
MAX_EVENTS = 10
EVENT_FILE = "events.json"

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
        "received timestamp": current_datetime_str,
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
        "received timestamp": current_datetime_str,
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
import connexion
from connexion import NoContent
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import ReportCovid, RecoveryReport, Base
from datetime import datetime
import yaml
import json
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread
import logging

# Load configuration from app_conf.yaml
with open('app_conf.yaml', 'r') as f:
    app_config = yaml.safe_load(f)

# Extract database connection details from the configuration
DB_USER = app_config['datastore']['user']
DB_PASSWORD = app_config['datastore']['password']
DB_HOST = app_config['datastore']['hostname']
DB_PORT = app_config['datastore']['port']
DB_NAME = app_config['datastore']['db']

# Create the database engine
DB_ENGINE = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
DB_SESSION = sessionmaker(bind=DB_ENGINE)

DATA_STORAGE_BASE_URL = "http://localhost:8090"

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('basicLogger')

def process_messages():
    """ Process event messages """
    hostname = "%s:%d" % (app_config["events"]["hostname"], app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    # Create a consumer on a consumer group, that only reads new messages
    # (uncommitted messages) when the service re-starts (i.e., it doesn't
    # read all the old messages from the history in the message queue).
    consumer = topic.get_simple_consumer(consumer_group=b'event_group', reset_offset_on_start=False,
                                         auto_offset_reset=OffsetType.LATEST)

    # This is blocking - it will wait for a new message
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info("Message: %s" % msg)
        payload = msg["payload"]
        
    try:
        msg_type = msg["type"]
        if msg_type == "event1":
            process_event1(payload)
        elif msg_type == "event2":
            process_event2(payload)
    except KeyError as e:
        logger.error("KeyError: %s" % e)
    # Handle the case where "type" key is missing


        # Commit the new message as being read
        consumer.commit_offsets()

def process_event1(payload):
    current_datetime = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    report_covid = ReportCovid(
        patient_id=payload['patient_id'],
        age=payload['age'],
        city=payload['city'],
        date_created=current_datetime,
        date_handwritten=payload['date_handwritten'],
        vaccinated_status=payload['vaccinated_status'],
    )

    session = DB_SESSION()
    session.add(report_covid)
    session.commit()
    session.close()

def process_event2(payload):
    current_datetime = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    recovery_report = RecoveryReport(
        patient_id=payload['patient_id'],
        hospital_visit=payload['hospital_visit'],
        date_created=current_datetime,
        date_handwritten=payload['date_handwritten'],
        recovery_status=payload['recovery_status'],
    )

    session = DB_SESSION()
    session.add(recovery_report)
    session.commit()
    session.close()

t1 = Thread(target=process_messages)
t1.setDaemon(True)
t1.start()

def report_covid(body):
    current_datetime = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")  # Use a simpler format without microseconds
    
    report_covid = ReportCovid(
        patient_id=body['patient_id'],
        age=body['age'],
        city=body['city'],
        date_created=current_datetime,
        date_handwritten=body['date_handwritten'],
        vaccinated_status=body['vaccinated_status'],
    )

    session = DB_SESSION()
    session.add(report_covid)
    session.commit()
    session.close()

    return NoContent, 201  # Return a successful response

def report_recovery(body):
    current_datetime = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")  # Use a simpler format without microseconds
    
    recovery_report = RecoveryReport(
        patient_id=body['patient_id'],
        hospital_visit=body['hospital_visit'],
        date_created=current_datetime,
        date_handwritten=body['date_handwritten'],
        recovery_status=body['recovery_status'],
    )

    session = DB_SESSION()
    session.add(recovery_report)
    session.commit()
    session.close()

    return NoContent, 201  # Return a successful response

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    # Start Kafka consumer thread
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()

    # Start the Flask app
    app.run(port=8090)


