import time
from selenium.webdriver.support.ui import WebDriverWait
from ...tools import api_request, get_id_link_CARX, logger, parse_float
from ...tools import parse_int, run_chrome


def load_CARX(params):
    ret = {}
    params["urlBase"] = "http://carxrallycross.com"

    data = api_request("get", params["urlApi"]+"/org/find/carx")
    if(len(data["categories"]) > 0):
        cats = data["categories"]
        for it in range(0, len(cats)):
            print(cats[it]["idRCtrl"])
            params["catRCtrl"] = cats[it]["idLeague"]
            params["catOrigen"] = cats[it]["idRCtrl"]
            ans = run_script_CARX(params)
            ret[cats[it]["idLeague"]] = ans
    return ret


def run_script_CARX(params):
    ret = {}

    driver = run_chrome()

    url = "/pilotos/"
    driver.get(params["urlBase"] + url)

    data = get_drivers(driver, params)
    # ret["drivers"] = data
    ret["drivers"] = api_request(
        "post", params["urlApi"]+"/driver/create", data)

    url = "/calendario/"
    driver.get(params["urlBase"] + url)

    time.sleep(5)
    events = get_events(driver, params)
    # ret["events"] = events
    ret["circuits"] = api_request(
        "post", params["urlApi"]+"/circuit/create", events[0])

    time.sleep(5)
    ret["events"] = api_request(
        "post", params["urlApi"]+"/event/create", events[1])

    url = "/campeonato-" + params["catOrigen"] + "/"
    driver.get(params["urlBase"] + url)

    time.sleep(5)
    champ = get_champD(driver, params)
    # ret["champD"] = champ
    ret["drivers_extra"] = api_request(
        "post", params["urlApi"]+"/driver/create", champ[0])

    time.sleep(5)
    ret["champD"] = api_request(
        "post", params["urlApi"]+"/champ/create", champ[1])

    driver.close()

    return ret


def get_drivers(driver, params):
    pilots = []
    try:
        print("::: DRIVERS")
        items = WebDriverWait(driver, 30).until(
            lambda d: d.find_elements_by_xpath(
                "//div[contains(@class, 'kf_roster_dec6')]")
        )
        for it in range(0, len(items)):
            linkDriver = items[it].find_element_by_xpath(
                ".//h3/a").get_attribute("href")
            idDriver = get_id_link_CARX(params, linkDriver, "D")
            thumb = items[it].find_element_by_xpath(
                ".//figure/img").get_attribute("src")
            pilot = {
                "idPlayer": params["catRCtrl"].upper() + "-" + idDriver,
                "idCategory": params["catRCtrl"],
                "idRCtrl": idDriver,
                "strPlayer": items[it].find_element_by_xpath(
                    ".//h3/a").text.title(),
                "strNumber": items[it].find_element_by_xpath(
                    ".//div[@class='text']/span").text,
                "numSeason": parse_int(params["year"]),
                "strThumb": thumb.replace(".jpg", "-300x300.jpg"),
                "strCutout": thumb.replace(".jpg", "-180x180.jpg"),
                "strRender": thumb,
                "strFanart4": items[it].find_element_by_xpath(
                    ".//div[@class='cntry-flag']/img").get_attribute("src"),
                "strRSS": linkDriver,
            }
            pilots.append(pilot)
        logger(pilots)
        print("::: PROCESS FINISHED :::")
        return pilots
    except Exception as e:
        logger(e, True, "Drivers", pilots)
        return "::: ERROR DRIVERS :::"


def get_events(driver, params):
    data = []
    events = []
    circuits = []
    circList = []
    try:
        print("::: EVENTS")
        items = WebDriverWait(driver, 30).until(
            lambda d: d.find_elements_by_xpath(
                "//tbody/tr")
        )
        for it in range(0, len(items)):
            tds = items[it].find_elements_by_xpath("./td")
            idEvent = tds[2].text.replace(" ", "_", 20)
            event = {
                "idEvent": params["catRCtrl"].upper() + "-" + params["year"] +
                "-" + str(it+1) + "-" + idEvent,
                "strEvent": tds[2].text,
                "idCategory": params["catRCtrl"],
                "idRCtrl": str(it+1) + "_" + idEvent,
                "intRound": str(it+1),
                "strDate": tds[1].text,
                "idCircuit": "CARX_" + idEvent,
                "strCircuit": tds[2].text,
                "numSeason": parse_int(params["year"]),
                "strSeason": params["year"],
            }
            events.append(event)
            circuit = {
                "idCircuit": event["idCircuit"],
                "strCircuit": event["strEvent"],
                "idRCtrl": event["idCircuit"],
                "strCountry": "Argentina",
                "numSeason": parse_int(params["year"]),
                "intSoccerXMLTeamID": "ARG",
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
    pilots = []
    data = []
    ret = []
    try:
        print("::: CHAMPIONSHIP DRIVERS")
        items = WebDriverWait(driver, 30).until(
            lambda d: d.find_elements_by_xpath("//tbody/tr")
        )
        points = 0
        for it in range(1, len(items)):
            tds = items[it].find_elements_by_xpath("./td")
            nameDriver = tds[2].text
            text = nameDriver.split(",")
            idDriver = text[1].strip().replace(
                " ", "-", 9) + "-" + text[0].strip()
            line = {
                "idPlayer": idDriver.lower(),
                "position": parse_int(tds[0].text),
                "totalPoints": parse_float(tds[len(tds)-1].text),
            }
            points += line["totalPoints"]
            data.append(line)
            pilot = {
                "idPlayer": params["catRCtrl"].upper() + "-" +
                idDriver.lower(),
                "idCategory": params["catRCtrl"],
                "idRCtrl": idDriver.lower(),
                "strPlayer": (text[1].strip() + " " + text[0].strip()).title(),
                "strNumber": tds[1].text,
                "numSeason": parse_int(params["year"]),
            }
            pilots.append(pilot)
        champ = {
            "idChamp": params["catRCtrl"].upper()+"-"+params["year"],
            "numSeason": parse_int(params["year"]),
            "strSeason": params["year"],
            "idCategory": params["catRCtrl"],
            "idRCtrl": params["catOrigen"],
            "data": data,
            "sumPoints": points,
            "typeChamp": "D"
        }
        ret.append(pilots)
        ret.append(champ)
        logger(ret)
        print("::: PROCESS FINISHED :::")
        return ret
    except Exception as e:
        logger(e, True, "Championship", [pilots, champ])
        return "::: ERROR CHAMP DRIVERS :::"