import logging
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

import re
from redbox import EmailBox


# -------------------------------------------------------------------------------------------------
#   Initialization
# -------------------------------------------------------------------------------------------------

app = FastAPI(debug=True)
logger = logging.getLogger("uvicorn.error")


# -------------------------------------------------------------------------------------------------
#   Check email and update total
# -------------------------------------------------------------------------------------------------


@app.get("/data/update")
def update():

    box = EmailBox(host=IMAPPATH, port=993)
    box.username = USERNAME
    box.password = PASSWORD
    box.update()

    for msg in box.inbox.search(from_="Capital One", subject="A new transaction"):
        amount = re.findall("\$[0-9]{1,3}\.[0-9]{2}", msg.text_body)[0].replace("$", "")
        print(msg.date, amount)

        # msg.delete()

    return {"status": "success"}


# -------------------------------------------------------------------------------------------------
#   Get current total
# -------------------------------------------------------------------------------------------------


@app.get("/data/total")
def total():

    return {"total": 33.33}


# -------------------------------------------------------------------------------------------------
#   Reset current total
# -------------------------------------------------------------------------------------------------


@app.get("/data/reset")
def reset():

    return {"status": "success"}


# -------------------------------------------------------------------------------------------------
#   Main
# -------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=80, workers=1, log_level=LOGLEVEL)
