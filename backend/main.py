import qr
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()
# holds all processed menus. Put them in a db if ya want!
result_cache = {}
# determines if menus should be processed in "paper saving" mode
# (aka only one item per category, nice for testing)
paper_save_setting = True

async def enqueue(menu_url):
    await qr.run_main(menu_url, paper_save_setting, result_cache[menu_url]["menu"])

@app.get("/")
async def main_query(bg: BackgroundTasks, menu_url: str = None):
    print(f"fetching url: {menu_url}")
    if menu_url is None:
        print("No url provided!")
        return {"error": "no url"}
    existing = result_cache.get(menu_url)
    if existing is not None:
        if existing.get("menu") is not None:
            return existing
        else :
            return { "status" : "waiting" }
    result_cache[menu_url] = { "menu" : {} }
    print(f"enqueue {menu_url}!")
    bg.add_task(enqueue, menu_url)
    return { "status" : "waiting" }

# utility call to set paper_save mode on or off for this run of the server
@app.get("/mode")
async def paper_save_query(bg: BackgroundTasks, paper_save: str = None):
    global paper_save_setting, result_cache
    paper_save_setting = (paper_save == 'true')
    result_cache = {}
    return { "paper_save" : paper_save_setting }

# run with: uvicorn main:app --reload --host 0.0.0.0 --workers 4

