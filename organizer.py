import shutil,time,schedule,logging,datetime,smtplib,json
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


CONFIG_FILE = Path("config.json")

with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

SRC_FOLDER = Path.home() / config["source_folder"]
DEST_FOLDER = Path(config["destination_folder"])
FILE_TYPES = config["file_types"]
EMAIL = config["email"]


DEST_FOLDER.mkdir(parents=True, exist_ok=True)
LOG_FOLDER = Path("logs")
LOG_FOLDER.mkdir(exist_ok=True)

today = datetime.datetime.now().strftime("%Y-%m-%d")
log_file = LOG_FOLDER / f"Files_Organized_{today}.log"


logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.info("Organizer Started")


def handle_single_file(file_path):
    file = Path(file_path)

    if not file.exists() or not file.is_file():
        return

    for folder, extensions in FILE_TYPES.items():
        if file.suffix.lower() in extensions:

            dest_folder = DEST_FOLDER / folder
            dest_folder.mkdir(exist_ok=True)

            dest_file = dest_folder / file.name

            counter = 1
            while dest_file.exists():
                dest_file = dest_folder / f"{file.stem}_{counter}{file.suffix}"
                counter += 1

            try:
                shutil.move(str(file), str(dest_file))
                logging.info(f"{file.name} moved to {folder}")
            except Exception as e:
                logging.error(f"{file.name} failed: {e}")

            break


def send_email(report):
    message = MIMEMultipart()
    message["From"] = EMAIL["sender"]
    message["To"] = EMAIL["receiver"]
    message["Subject"] = f"Organizer Report - {today}"
    message.attach(MIMEText(report, "plain"))

    try:
        server = smtplib.SMTP(EMAIL["smtp_server"], EMAIL["smtp_port"])
        server.starttls()
        server.login(EMAIL["sender"], EMAIL["password"])
        server.sendmail(EMAIL["sender"], EMAIL["receiver"], message.as_string())
        server.quit()
        logging.info("Email sent successfully")
    except Exception as e:
        logging.error(f"Email sending failed: {e}")

def organize_files():
    logging.info("Organizer job started")
    moved_files = 0
    skipped_files = 0

    for folder, extensions in FILE_TYPES.items():
        folder_path = DEST_FOLDER / folder
        folder_path.mkdir(exist_ok=True)

        for ext in extensions:
            for file in SRC_FOLDER.glob(f"*{ext}"):
                try:
                    if not file.is_file():
                        continue

                    dest_file = folder_path / file.name
                    counter = 1
                    while dest_file.exists():
                        dest_file = folder_path / f"{file.stem}_{counter}{file.suffix}"
                        counter += 1

                    shutil.move(file, dest_file)
                    moved_files += 1
                    logging.info(f"{file.name} moved to {folder}")

                except Exception as e:
                    skipped_files += 1
                    logging.error(f"{file.name} failed: {e}")


    report = f"""
Organizer finished

Source Folder: {SRC_FOLDER}
Destination Folder: {DEST_FOLDER}
Files moved: {moved_files}
Files skipped: {skipped_files}
"""
    send_email(report)


class WatchHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            time.sleep(1)
            handle_single_file(event.src_path)

schedule.every(config["schedule_time"]).days.do(backup_and_notify)

if __name__ == "__main__":
    observer = Observer()
    event_handler = WatchHandler()

    observer.schedule(event_handler, path=str(SRC_FOLDER), recursive=False)

    observer.start()
    try:
        while True:
            schedule.run_pending()
            time.sleep(3)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
