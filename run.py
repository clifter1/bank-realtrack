"""
Core API script for service
"""

import logging
import uvicorn
import socket
from fastapi import FastAPI, HTTPException

import re
import environs
from redbox import EmailBox


# -------------------------------------------------------------------------------------------------
#   Global Variables
# -------------------------------------------------------------------------------------------------

ENV_FILE = ".env"


# -------------------------------------------------------------------------------------------------
#   Initialization
# -------------------------------------------------------------------------------------------------

env = environs.Env()
env.read_env(ENV_FILE, recurse=True)
app = FastAPI(debug=True)
logger = logging.getLogger("uvicorn.error")
logger.setLevel(env("LOGLEVEL").upper())


# -------------------------------------------------------------------------------------------------
#   Check email and update total
# -------------------------------------------------------------------------------------------------


@app.get("/total")
def update():
    """
    API endpoint for tallying up the notifications sent to the email account
    """

    # --------------------  Read to DATABASE file  --------------------
    try:
        total = float(open(env("DATABASE"), "r").read().rstrip())
    except FileNotFoundError:
        logger.warn(f"Database file {env('DATABASE')} was not found, default set to 0.00")
        total = 0.00
    except Exception as err:
        errmsg = f"Unknown issue reading database: {err}"
        logger.warn(errmsg)
        raise HTTPException(status_code=500, detail=errmsg)
    else:
        logger.debug(f"Starting total: {total}")

    # --------------------  Login to IMAP account  --------------------
    try:
        logger.debug("Connecting to IMAP email box")
        box = EmailBox(host=env("IMAPPATH"), port=env("IMAPPORT"))
        box.username = env("USERNAME")
        box.password = env("PASSWORD")
        box.update()
    except socket.gaierror as err:
        logger.error(f"Issue connecting to {env('IMAPPATH')} with: {err}")
        raise HTTPException(status_code=504, detail="Issue conncting to IMAP server")
    except Exception as err:
        raise HTTPException(status_code=504, detail=f"Unknown issue with IMAP server: {err}")
    else:
        logger.info("IMAP email box connected")

    # --------------------  Parse mailbox notifications  --------------------
    logger.debug("Searching mailbox for specific notifications")
    try:
        for msg in box.inbox.search(from_="Capital One", subject="A new transaction"):
            amount = re.findall("\$[0-9]{1,3}\.[0-9]{2}", msg.text_body)[0].replace("$", "")
            total = round(total + float(amount), 2)
            logger.info(f"Notification amount found: {amount}")
            # msg.delete()
            logger.debug("Notification message has been deleted")
    except Exception as err:
        logger.error(f"Issue searching mailbox: {err}")
        raise HTTPException(status_code=504, detail="Unknown issue parsing inbox")

    # --------------------  Write to DATABASE file  --------------------
    logger.debug(f"Current new total: {total}")
    try:
        open(env("DATABASE"), "w").write(str(total))
    except Exception as err:
        logger.error(f"Issue saving {total} to {env('DATABASE')}: {err}")
    else:
        logger.debug(f"New total saved to {env('DATABASE')}")

    # --------------------  Return value  --------------------
    return {"total": total}


# -------------------------------------------------------------------------------------------------
#   Reset DB Function
# -------------------------------------------------------------------------------------------------

@app.get("/reset")
def reset():
    """
    API Endpoint for resetting the current count
    """

    empty = 0.00

    try:
        logger.info(f"Setting total to {empty} for new month")
        open(env("DATABASE"), "w").write(str(empty))
    except Exception as err:
        errmsg = f"Issue resetting the database: {err}"
        logger.error(errmsg)
        raise HTTPException(status_code=500, detail=errmsg)
    else:
        logger.debug("Database reset complete")
        return {"total": empty}


# -------------------------------------------------------------------------------------------------
#   Health Check
# -------------------------------------------------------------------------------------------------

@app.get("/health")
def health():
    """
    API Endpoint for Docker health checks
    """

    # --------------------  Read to DATABASE file  --------------------
    try:
        total = float(open(env("DATABASE"), "r").read().rstrip())
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

    uvicorn.run("run:app", host="0.0.0.0", port=80)
