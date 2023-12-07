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
        payload = msg.get("payload", {})  # Use get to avoid KeyError if "payload" is missing
        event_type = msg.get("type")

        if event_type == "event1":
            process_event1(payload)
        elif event_type == "event2":
            process_event2(payload)

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

def get_event1_by_index(index):
    return get_event_by_index(index, 'event1')

def get_event2_by_index(index):
    return get_event_by_index(index, 'event2')

def get_event_by_index(index, event_type):
    hostname = "%s:%d" % (app_config["events"]["hostname"], app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    logger.info(f"Retrieving {event_type} at index {index}")
    
    try:
        count = 0
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
            if msg.get('type') == event_type:
                if count == index:
                    return msg['payload'], 200
                count += 1
    except:
        logger.error("No more messages found")
        logger.error(f"Could not find {event_type} at index {index}")
        return {"message": "Not Found"}, 404

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    # Start Kafka consumer thread
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()

    # Start the Flask app
    app.run(port=8110)
