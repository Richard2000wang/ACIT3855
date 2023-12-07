import connexion
from connexion import NoContent
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import ReportCovid, RecoveryReport, Base
from datetime import datetime
import yaml
import logging
import logging.config
from apscheduler.schedulers.background import BackgroundScheduler
import json
import requests

# Load configuration from app_conf.yml
with open('app_conf.yaml', 'r') as f:
    app_config = yaml.safe_load(f)
    print("App Config:", app_config)

# Load logging configuration from log_conf.yml
with open('log_conf.yaml', 'r') as f:
    log_config = yaml.safe_load(f.read())
logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

# Extract database connection details from the configuration
DB_USER = app_config['datastore']['user']
DB_PASSWORD = app_config['datastore']['password']
DB_HOST = app_config['datastore']['hostname']
DB_PORT = app_config['datastore']['port']
DB_NAME = app_config['datastore']['db']

# Create the database engine
DB_ENGINE = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
Base.metadata.create_all(DB_ENGINE)  # Create tables based on models
DB_SESSION = sessionmaker(bind=DB_ENGINE)

DATA_STORAGE_BASE_URL = "http://localhost:8090"

def report_covid(body):
    report_covid = ReportCovid(
        patient_id=body['patient_id'],
        age=body['age'],
        city=body['city'],
        date_created=datetime.strptime(body['date_created'], "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S"),
        date_handwritten=body['date_handwritten'],
        vaccinated_status=body['vaccinated_status'],
    )

    session = DB_SESSION()
    session.add(report_covid)
    session.commit()
    session.close()

    return NoContent, 201  # Return a successful response

def report_recovery(body):
    recovery_report = RecoveryReport(
        patient_id=body['patient_id'],
        hospital_visit=body['hospital_visit'],
        date_created=datetime.strptime(body['date_created'], "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S"),
        date_handwritten=body['date_handwritten'],
        recovery_status=body['recovery_status'],
    )

    session = DB_SESSION()
    session.add(recovery_report)
    session.commit()
    session.close()

    return NoContent, 201  # Return a successful response

def get_covid_events(timestamp):
    """Gets new COVID infection events after the timestamp."""
    session = DB_SESSION()
    timestamp_datetime = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    events = session.query(ReportCovid).filter(ReportCovid.date_created >= timestamp_datetime)
    results_list = [event.to_dict() for event in events]
    session.close()
    return results_list, 200

def get_recovery_events(timestamp):
    """Gets new COVID recovery events after the timestamp."""
    session = DB_SESSION()
    timestamp_datetime = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    events = session.query(RecoveryReport).filter(RecoveryReport.date_created >= timestamp_datetime)
    results_list = [event.to_dict() for event in events]
    session.close()
    return results_list, 200

def populate_stats():
    """ Periodically update stats """
    logger.info("Start Periodic Processing")

    try:
        # Read current statistics from data.json file
        with open('data.json', 'r') as json_file:
            stats = json.load(json_file)
    except FileNotFoundError:
        # If the file doesn't exist, use default values for the stats
        stats = {
            "num_covid_cases": 0,
            "num_recovery_cases": 0,
            "last_updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        }

    current_datetime = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z" if app_config.get(
        'timezone', 'UTC') == 'UTC' else datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

    # Query COVID events from the last update to the current datetime
    covid_events, _ = get_covid_events(stats["last_updated"])
    recovery_events, _ = get_recovery_events(stats["last_updated"])

    # Log the number of events received
    logger.info(f"Received {len(covid_events)} new COVID events")
    logger.info(f"Received {len(recovery_events)} new recovery events")

    # Update statistics based on new events
    stats["num_covid_cases"] += len(covid_events)
    stats["num_recovery_cases"] += len(recovery_events)
    stats["last_updated"] = current_datetime

    # Write updated statistics to data.json file
    with open('data.json', 'w') as json_file:
        json.dump(stats, json_file, indent=2)

    # Log updated statistics
    logger.debug(f"Stats dictionary: {stats}")
    for event in covid_events:
        logger.debug(f"COVID event dictionary:")
        for key, value in event.items():
            logger.debug(f"  {key}: {value}")
    for event in recovery_events:
        logger.debug(f"Recovery event dictionary:")
        for key, value in event.items():
            logger.debug(f"  {key}: {value}")

    logger.info("Periodic Processing has ended")

def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats, 'interval', seconds=app_config['scheduler']['period_sec'])
    sched.start()

    # Call the app.run() here to start the server
    app.run(port=8100)

def get_stats():
    """Gets current statistics."""
    app.logger.info("Request for statistics has started")

    stats = {
    "num_covid_cases": 0,
    "num_recovery_cases": 0,
    "last_updated": "1970-01-01T00:00:00"
}

    timestamp_datetime = datetime.strptime(stats["last_updated"], "%Y-%m-%dT%H:%M:%S.%fZ")
    # Convert statistics to the required format
    formatted_stats = {
        "num_covid_cases": stats.get("num_covid_cases", 0),
        "num_recovery_cases": stats.get("num_recovery_cases", 0),
        "last_updated": stats.get("last_updated", "")
    }

    app.logger.debug(f"Current statistics: {formatted_stats}")
    app.logger.info("Request for statistics has completed")

    return formatted_stats, 200

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    # Run our standalone gevent server
    init_scheduler()
    app.run(port=8100)
