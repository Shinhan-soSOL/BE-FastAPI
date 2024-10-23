import asyncio
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

KAFKA_BOOTSTRAP_SERVERS= (os.environ["KAFKA_BOOTSTRAP_SERVER1"],
                          os.environ["KAFKA_BOOTSTRAP_SERVER2"],
                          os.environ["KAFKA_BOOTSTRAP_SERVER3"])
KAFKA_TOPIC="kafka"
KAFKA_CONSUMER_GROUP="trading"
loop = asyncio.get_event_loop()

