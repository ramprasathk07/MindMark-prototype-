import logging
import os
from datetime import datetime

os.makedirs("logs", exist_ok=True)
current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = f"log_{current_time}.log"
log_file_path = os.path.join("logs", log_file)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  
        logging.FileHandler(log_file_path)
    ]
)

logger = logging.getLogger("AppLogger")
