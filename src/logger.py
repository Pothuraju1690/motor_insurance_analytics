
from pathlib import Path
import logging

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_LOG_DIR = ROOT_DIR / "logs"
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "pipeline.log"


def setup_logger(name="motor_insurance_pipeline", log_file=None, log_dir=None):
    """Configure and return a logger, with optional custom file output."""
    root_dir = ROOT_DIR
    if log_dir is not None:
        target_dir = Path(log_dir)
        if not target_dir.is_absolute():
            target_dir = root_dir / target_dir
    else:
        target_dir = DEFAULT_LOG_DIR

    if log_file is not None:
        target_log = Path(log_file)
        if not target_log.is_absolute():
            target_log = root_dir / target_log
    else:
        target_log = target_dir / "pipeline.log"

    target_log.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(target_log, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def log_pipeline_step(message):
    """Write a pipeline progress message to the shared logger."""
    setup_logger().info(message)


def log_error(message):
    """Write an error message to the shared logger."""
    setup_logger().error(message)