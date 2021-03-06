import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from app.common.tools import api_request, clean_duplicate, get_id_link_AUVO, logger, parse_float
from app.common.tools import parse_int, run_chrome, compareEvents


def load_AUVO(params, upd=False):
    ret = {}
    params["urlBase"] = "http://www.auvo.com.uy"

    data = api_request("get", params["urlApi"] + "/org/find/auvo")
    if(data and len(data["categories"]) > 0):
        cats = data["categories"]
        for it in range(0, len(cats)):
            print(cats[it]["idRCtrl"])
            params["catId"] = cats[it]["_id"]
            params["catRCtrl"] = cats[it]["idLeague"]
            params["catOrigen"] = cats[it]["idRCtrl"]
            if(upd):
                ans = update_AUVO(params)
            else:
                ans = run_script_AUVOCat(params)
            ret[cats[it]["idLeague"]] = ans
    return ret


def run_script_AUVOCat(params):
    ret = {}

    driver = run_chrome()

    url = "https://speedhive.mylaps.com/Sessions/5866106"

    driver.get("https://speedhive.mylaps.com")
    driver.get("https://speedhive.mylaps.com/Organizations/95827")
    driver.get("https://speedhive.mylaps.com/Events/1814191")
    if(params["catRCtrl"] == 'uyst'):
        driver.get(url + "5866106")
    elif(params["catRCtrl"] == 'uyse'):
        driver.get(url + "5866101")
    elif(params["catRCtrl"] == 'uyth'):
        driver.get(url + "5865717")
    elif(params["catRCtrl"] == 'uyss'):
        driver.get(url + "5865709")
    else:
        driver.close()
        return ret

    d_scrap = get_drivers(driver, params)
    # ret["drivers"] = data
    d_base = api_request("get", params["urlApi"] + "/driver/ids/" + params["catId"]
                         + "/" + params["year"])
    d_clean = clean_duplicate("idPlayer", d_scrap, d_base)
    # ret["drivers"] = api_request(
    #     "post", params["urlApi"]+"/driver/create", d_clean)
    ret["drivers"] = api_request(
        "put", params["urlApi"] + "/driver/update/0", d_clean)

    # time.sleep(5)
    # t_data = get_teams(driver, params)
    # ret["teams"] = api_request(
    # "post", params["urlApi"]+"/team/create", t_data)

    ans = create_AUVO(params)
    ret["events"] = ans

    driver.close()

    return ret


def create_AUVO(params):
    ret = {}

    driver = run_chrome()

    url = "/calendario"
    driver.get(params["urlBase"] + url)

    e_scrap = get_events(driver, params)
    # ret["circuits"] = e_scrap[0]
    # ret["events"] = e_scrap[1]
    c_base = api_request(
        "get", params["urlApi"] + "/circuit/ids/auvo")
    c_clean = clean_duplicate("idCircuit", e_scrap[0], c_base)
    ret["circuits"] = api_request(
        "post", params["urlApi"] + "/circuit/create", c_clean)

    time.sleep(5)
    e_base = api_request("get", params["urlApi"] + "/event/ids/" + params["catId"]
                         + "/" + params["year"])
    e_clean = clean_duplicate("idEvent", e_scrap[1], e_base)
    ret["events"] = api_request(
        "post", params["urlApi"] + "/event/create", e_clean)

    driver.close()

    return ret


def update_AUVO(params):
    ret = {}

    driver = run_chrome()

    # CHAMPIONSHIPS

    # EVENTS AND CIRCUITS
    if(params["updType"] == "events" or params["updType"] == "all"):
        time.sleep(3)
        e_base = api_request(
            "get", params["urlApi"] + "/event/cat/" + params["catId"] + "/" +
            params["year"])

        url = "/calendario"
        driver.get(params["urlBase"] + url)

        e_scrap = get_events(driver, params)

        ret["events"] = e_base

        time.sleep(3)
        c_base = api_request(
            "get", params["urlApi"] + "/circuit/ids/auvo")
        c_clean = clean_duplicate("idCircuit", e_scrap[0], c_base)
        ret["circuits"] = api_request(
            "post", params["urlApi"] + "/circuit/create", c_clean)

        compared = compareEvents(e_base, e_scrap[1])
        ret["compared"] = compared

        if(len(compared["news"]) > 0):
            time.sleep(5)
            ret["newEvents"] = api_request(
                "post", params["urlApi"] + "/event/create", compared["news"])

        upds = compared["updated"]
        clds = compared["cancelled"]
        items = []
        for it in range(0, len(upds)):
            time.sleep(2)
            items.append(api_request(
                "put", params["urlApi"] + "/event/update/" + upds[it]["id"],
                upds[it]["new"]))
        for it in range(0, len(clds)):
            time.sleep(2)
            items.append(api_request(
                "put", params["urlApi"] + "/event/update/" + clds[it]["id"],
                clds[it]["new"]))
        ret["updEvents"] = items

    # DRIVERS AND TEAMS
    if(params["updType"] == "drivers" or params["updType"] == "all"):
        time.sleep(5)
        url = "/" + params["catOrigen"] + "/pilotos.html"
        driver.get(params["urlBase"] + url)

        d_scrap = get_drivers(driver, params)
        t_scrap = get_teams(d_scrap, params)

        ret["teams"] = api_request(
            "put", params["urlApi"] + "/team/update/0", t_scrap)

        time.sleep(5)
        ret["drivers"] = api_request(
            "put", params["urlApi"] + "/driver/update/0", d_scrap)

    driver.close()

    return ret


def get_drivers(driver, params):
    pilots = []
    try:
        print("::: DRIVERS")
        items = WebDriverWait(driver, 30, 1, (NoSuchElementException)).until(
            lambda d: d.find_elements_by_xpath(
                "//div[@id='session-results']/a")
        )
        for it in range(0, len(items)):
            tds = items[it].find_elements_by_xpath(
                ".//div")
            strPlayer = tds[1].text
            strNumber = tds[3].text
            idPlayer = strNumber + "_" + strPlayer.replace(" ", "_", 9)
            pilot = {
                "idPlayer": params["catRCtrl"].upper() + "-"
                + idPlayer,
                "idCategory": params["catRCtrl"],
                "idRCtrl": idPlayer,
                "strPlayer": strPlayer,
                "strNumber": strNumber,
                "numSeason": parse_int(params["year"]),
            }
            pilots.append(pilot)
        logger(pilots)
        print("::: PROCESS FINISHED :::")
        return pilots
    except Exception as e:
        logger(e, True, "Drivers", pilots)
        return "::: ERROR DRIVERS :::"


def get_driversST(driver, params):
    pilots = []
    try:
        print("::: DRIVERS")
        items = WebDriverWait(driver, 30).until(
            lambda d: d.find_elements_by_xpath(
                "//article[contains(@class, 'list-pilotos')]/a")
        )
        for it in range(0, len(items)):
            linkDriver = items[it].get_attribute("href")
            idDriver = get_id_link_AUVO(params, linkDriver, "D")
            txt = idDriver.split("_")
            strPlayer = ""
            strNumber = txt[0]
            for t in range(1, len(txt)):
                strPlayer += txt[t] + " "
            thumb = items[it].find_element_by_xpath(
                ".//img").get_attribute("src"),
            pilot = {
                "idPlayer": params["catRCtrl"].upper() + "-"
                + idDriver,
                "idCategory": params["catRCtrl"],
                "idRCtrl": idDriver,
                "strPlayer": strPlayer,
                "strNumber": strNumber,
                "numSeason": parse_int(params["year"]),
                "strThumb": thumb.replace(".png", "-253x300.png"),
                "strCutout": thumb,
                "strRSS": linkDriver,
            }
            pilots.append(pilot)
        logger(pilots)
        print("::: PROCESS FINISHED :::")
        return pilots
    except Exception as e:
        logger(e, True, "Drivers", pilots)
        return "::: ERROR DRIVERS :::"


def get_teamsST(driver, params):
    teams = []
    try:
        print("::: TEAMS")
        items = WebDriverWait(driver, 30).until(
            lambda d: d.find_elements_by_xpath(
                "//article/a")
        )
        for it in range(0, len(items)):
            linkTeam = items[it].get_attribute("href")
            thumb = items[it].find_element_by_xpath(
                ".//img").get_attribute("src"),
            idTeam = get_id_link_AUVO(params, thumb, "T")
            txt = idTeam.split("_")
            strTeam = ""
            for t in range(2, len(txt)):
                strTeam += txt[t] + " "
            team = {
                "idTeam": idTeam,
                "strTeam": "",
                "idCategory": params["catRCtrl"],
                "idRCtrl": idTeam,
                "numSeason": parse_int(params["year"]),
                "strGender": "T",
                "strThumb": thumb.replace(".jpg", "-300x189.jpg"),
                "strCutout": thumb,
                "strRSS": linkTeam,
            }
            teams.append(team)
        logger(teams)
        print("::: PROCESS FINISHED :::")
        return teams
    except Exception as e:
        logger(e, True, "Teams", teams)
        return "::: ERROR TEAMS :::"


def get_events(driver, params):
    data = []
    events = []
    circuits = []
    circList = []
    try:
        print("::: EVENTS")
        items = WebDriverWait(driver, 30).until(
            lambda d: d.find_elements_by_xpath(
                "//article")
        )
        for it in range(0, len(items)):
            thumb = items[it].find_element_by_xpath(
                ".//div[@class='post-calendario-img']/img").get_attribute(
                    "src")
            tds = items[it].find_elements_by_xpath(
                ".//a")
            linkEvent = tds[0].get_attribute("href")
            idEvent = get_id_link_AUVO(params, linkEvent, "E")
            linkCircuit = tds[11].get_attribute("href")
            if(linkCircuit == ""):
                linkCircuit = thumb
            idCircuit = "AUVO-" + params["year"] + "-" + str(it + 1)
            strCircuit = "AUVO-" + str(it + 1)
            event = {
                "idEvent": params["catRCtrl"].upper() + "-" +
                params["year"] + "-" + str(it + 1) + "-" + idEvent,
                "strEvent": "Fecha #" + str(it + 1),
                "idCategory": params["catRCtrl"],
                "idRCtrl": idEvent,
                "intRound": str(it + 1),
                "idCircuit": idCircuit,
                "strCircuit": "AUVO",
                "numSeason": parse_int(params["year"]),
                "strSeason": params["year"],
                "strPostponed": "",
                "strRSS": linkEvent,
            }
            events.append(event)
            circuit = {
                "idCircuit": event["idCircuit"],
                "strCircuit": strCircuit,
                "idRCtrl": event["idCircuit"],
                "strLeague": "auvo",
                "strCountry": "Uruguay",
                "numSeason": parse_int(params["year"]),
                "intSoccerXMLTeamID": "URY",
                "strLogo": linkCircuit,
            }
            if(circuit["idCircuit"] not in circList):
                circuits.append(circuit)
                circList.append(circuit["idCircuit"])
        data.append(circuits)
        data.append(events)
        logger(data)
        print("::: PROCESS FINISHED :::")
        return data
    except Exception as e:
        logger(e, True, "Events", [events, circuits])
        return "::: ERROR EVENTS :::"


def get_champD(driver, params):
    champ = {}
    data = []
    try:
        print("::: CHAMPIONSHIP DRIVERS")
        items = WebDriverWait(driver, 30).until(
            lambda d: d.find_elements_by_xpath(
                "//table[@id='table-hidden-content']/tbody/tr")
        )
        points = 0
        for it in range(0, len(items)):
            tds = items[it].find_elements_by_xpath("./td")
            linkDriver = ""
            idDriver = get_id_link_AUVO(
                params["urlBase"], params, linkDriver, "D")
            line = {
                "idPlayer": idDriver,
                "position": parse_int(tds[0].text.replace("°", "")),
                "totalPoints": parse_float(tds[5].text),
                "cups": parse_int(tds[3].text),
            }
            points += line["totalPoints"]
            data.append(line)
        champ = {
            "idChamp": params["catRCtrl"].upper() + "-" + params["year"] - "D",
            "numSeason": parse_int(params["year"]),
            "strSeason": params["year"],
            "idCategory": params["catRCtrl"],
            "idRCtrl": params["catOrigen"],
            "data": data,
            "sumPoints": points,
            "typeChamp": "D"
        }
        logger(champ)
        print("::: PROCESS FINISHED :::")
        return champ
    except Exception as e:
        logger(e, True, "Championship", champ)
        return "::: ERROR CHAMP DRIVERS :::"
