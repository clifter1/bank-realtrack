"""
Core API script for service
"""

# -------------------------------------------------------------------------------------------------
#   Core Modules
# -------------------------------------------------------------------------------------------------

import logging
import os
import re


# -------------------------------------------------------------------------------------------------
#   3rd Party Modules
# -------------------------------------------------------------------------------------------------

import environs
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from imap_tools import MailBox, AND
import uvicorn


# -------------------------------------------------------------------------------------------------
#   Global Variables
# -------------------------------------------------------------------------------------------------

ENV_FILE = ".env"


# -------------------------------------------------------------------------------------------------
#   Initialization
# -------------------------------------------------------------------------------------------------

# ----------  Parse .env configs and start FastAPI  ----------
env = environs.Env()
env.read_env(ENV_FILE, recurse=True)
app = FastAPI(title="Bank Tracking Application")
api = FastAPI(title="Bank Backend API")
app.mount("/api", api)
app.mount("/", StaticFiles(directory="static", html=True), name="static")


# ----------  Log filtering class  ----------
class EndpointFilter(logging.Filter):
    """
    Filter class to parse out logs that are not needed
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Core filter function
        """

        if record.args:
            if len(record.args) >= 4:
                verb = record.args[1]
                path = record.args[2]
                domain = record.args[0]
                status = record.args[4]

                # ----------  Ignore valid docker healthcheck call  -----------
                if "127.0.0.1" in domain:
                    if path == "/api/health" and verb == "GET" and status == 200:
                        return False
        return True


# ----------  Start logging service  ----------
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())
logger = logging.getLogger("uvicorn.error")
logger.setLevel(env("LOGLEVEL").upper())

# ----------  Seed Database (if not found)  ----------
app.db = os.path.join(env("DATADIRS"), env("DATABASE"))
os.makedirs(env("DATADIRS"), exist_ok=True)
if not os.path.isfile(app.db):
    with open(app.db, "w") as fp:
        fp.write("0.00")


# -------------------------------------------------------------------------------------------------
#   Serve basic web component
# -------------------------------------------------------------------------------------------------


@api.get("/retrieve")
async def index(request: Request):
    """
    API endpoint to return current total
    """

    # --------------------  Read DATABASE file  --------------------
    try:
        with open(app.db, "r") as fp:
            total = float(fp.read().rstrip())
    except Exception as err:
        errmsg = f"Unknown issue reading database: {err}"
        logger.error(errmsg)
        raise HTTPException(status_code=500, detail=errmsg)
    else:
        return {"total": total}


# -------------------------------------------------------------------------------------------------
#   Check email and update totals
# -------------------------------------------------------------------------------------------------


@api.get("/update")
def update():
    """
    API endpoint for tallying up the notifications sent to the email account
    """

    # --------------------  Read DATABASE file  --------------------
    try:
        with open(app.db, "r") as fp:
            total = float(fp.read().rstrip())
    except Exception as err:
        errmsg = f"Unknown issue reading database: {err}"
        logger.error(errmsg)
        raise HTTPException(status_code=500, detail=errmsg)
    else:
        logger.debug(f"Starting total: {total}")

    # --------------------  Parse mailbox notifications  --------------------
    logger.debug("Searching mailbox for specified notifications")
    try:
        all_messages = []
        with MailBox(env("IMAPPATH")).login(env("USERNAME"), env("PASSWORD")) as mailbox:
            # ----------  Parse email and add to total  ----------
            for msg in mailbox.fetch(AND(from_="Capital One", subject="A new transaction")):
                amount = re.findall("\$[0-9]{1,3}\.[0-9]{2}", msg.text)[0].replace("$", "")
                total = round(total + float(amount), 2)
                all_messages.append(msg.uid)
                logger.debug(f"Notification total {amount} added")

            # ----------  Delete all found email  ----------
            mailbox.delete(all_messages)
            logger.info(f"Total email found, parsed, and pruged: {len(all_messages)}")
    except Exception as err:
        logger.error(f"Issue searching mailbox: {err}")
        raise HTTPException(status_code=504, detail="Unknown issue parsing inbox")

    # --------------------  Write to DATABASE file  --------------------
    logger.debug(f"Current new total: {total}")
    try:
        with open(app.db, "w") as fp:
            fp.write(str(total))
    except Exception as err:
        logger.error(f"Issue saving {total} to {env('DATABASE')}: {err}")
    else:
        logger.debug(f"New total saved to {env('DATABASE')}")

    # --------------------  Return value  --------------------
    return {"total": total}


# -------------------------------------------------------------------------------------------------
#   Reset DB Function
# -------------------------------------------------------------------------------------------------


@api.get("/reset")
def reset(request: Request):
    """
    API Endpoint for resetting the current count
    """

    # --------------------  IP Restricted  --------------------
    if request.client.host != "127.0.0.1":
        raise HTTPException(status_code=405, detail="Access Denied")

    # --------------------  Read DATABASE file  --------------------
    try:
        with open(app.db, "r") as fp:
            total = float(fp.read().rstrip())
    except Exception as err:
        errmsg = f"Unknown issue reading database: {err}"
        logger.error(errmsg)
        raise HTTPException(status_code=500, detail=errmsg)

    # --------------------  Reste DATABASE file  --------------------
    try:
        logger.info(f"Total was reset for the month. Last month total: {total}")
        with open(app.db, "w") as fp:
            fp.write("0.00")
    except Exception as err:
        errmsg = f"Issue resetting the database: {err}"
        logger.error(errmsg)
        raise HTTPException(status_code=500, detail=errmsg)
    else:
        logger.debug("Database reset complete")
        return {"total": 0.00}


# -------------------------------------------------------------------------------------------------
#   Health Check
# -------------------------------------------------------------------------------------------------


@api.get("/health")
def health(request: Request):
    """
    API Endpoint for Docker health checks
    """

    # --------------------  IP Restricted  --------------------
    if request.client.host != "127.0.0.1":
        raise HTTPException(status_code=405, detail="Access Denied")

    # --------------------  Read DATABASE file  --------------------
    try:
        with open(app.db, "r") as fp:
            total = float(fp.read().rstrip())
    except FileNotFoundError:
        logger.warn(f"Database file {env('DATABASE')} was not found in health check")
    except Exception as err:
        errmsg = f"Unknown issue reading database durring health check: {err}"
        logger.error(errmsg)
        raise HTTPException(status_code=500, detail=errmsg)

    logger.debug(f"Found database with {total} value durring health check")
    return {"status": "successful"}


# -------------------------------------------------------------------------------------------------
#   Main
# -------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    """
    Main - Uvicorn setup and port configurations
    """

    uvicorn.run("run:app", host="0.0.0.0", port=env.int("WEBSPORT"), log_level=env("LOGLEVEL"))
