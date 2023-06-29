import logging
import uvicorn
import fileinput
from fastapi import FastAPI

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
#   Function to save updated value
# -------------------------------------------------------------------------------------------------

def update(sum: str):
    '''
    Function to update .env file with latest total
    '''

    with fileinput.FileInput(ENV_FILE, inplace = True) as f:
    for line in f:
        if line.startswith('ACCTOTAL'):
            print(f'ACCTOTAL={sum}', end = '\n')
        else:
            print(line, end ='')


# -------------------------------------------------------------------------------------------------
#   Check email and update total
# -------------------------------------------------------------------------------------------------

@app.get("/total")
def update():

    total = env.float('ACCTOTAL')
    logger.debug(f"Retrieved value {total} from config")

    # --------------------  Login to IMAP outlook  --------------------
    logger.debug("Connecting to IMAP email box to pull notifications")
    box = EmailBox(host=env('IMAPPATH'), port=env('IMAPPORT'))
    box.username = env('USERNAME')
    box.password = env('PASSWORD')
    box.update()
    logger.debug("IMAP email box connected")

    # --------------------  Parse mailbox notifications  --------------------
    for msg in box.inbox.search(from_="Capital One", subject="A new transaction"):
        amount = re.findall("\$[0-9]{1,3}\.[0-9]{2}", msg.text_body)[0].replace("$", "")
        total += amount
        logger.info(f"Notification amount found: {amount} Added to current total: {total}")
        # msg.delete()
        logger.debug("Notification message has been deleted")

    # --------------------  Update .env file  --------------------
    logger.debug(f"Updated to a total of: {total)")
    update(total)

    # --------------------  Return value  --------------------
    return total


# -------------------------------------------------------------------------------------------------
#   Main
# -------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("run:app", host="0.0.0.0", port=8000)
