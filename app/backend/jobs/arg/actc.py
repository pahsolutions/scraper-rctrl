import time
from selenium.webdriver.support.ui import WebDriverWait
from app.common.tools import api_request, clean_duplicate, clean_duplicate_ch, get_id_link_ACTC, get_link_ACTC, logger
from app.common.tools import parse_float, parse_int, run_chrome, compareEvents


def load_ACTC(params, upd=False):
    ret = {}
    params["urlBase"] = "https://www.actc.org.ar"

    data = api_request("get", params["urlApi"] + "/org/find/actc")
    if(data and len(data["categories"]) > 0):
        cats = data["categories"]
        for it in range(0, len(cats)):
            print(cats[it]["idRCtrl"])
            params["catId"] = cats[it]["_id"]
            params["catRCtrl"] = cats[it]["idLeague"]
            params["catOrigen"] = cats[it]["idRCtrl"]
            params["chTypes"] = cats[it]["chTypes"]
            if(upd):
                ans = update_ACTC(params)
            else:
                ans = create_ACTC(params)
            ret[cats[it]["idLeague"]] = ans
    return ret


def create_ACTC(params):
    ret = {}

    driver = run_chrome()

    url = "/" + params["catOrigen"] + "/pilotos.html"
    driver.get(params["urlBase"] + url)

    d_scrap = get_drivers(driver, params)
    # ret["drivers"] = d_scrap
    t_scrap = get_teams(d_scrap, params)
    # ret["teams"] = t_scrap
    t_base = api_request(
        "get", params["urlApi"] + "/team/ids/" + params["catId"] + "/" + params["year"])
    t_clean = clean_duplicate("idTeam", t_scrap, t_base)
    # ret["teams"] = api_request(
    #     "post", params["urlApi"] + "/team/create", t_clean)
    ret["teams"] = api_request(
        "put", params["urlApi"] + "/team/update/0", t_clean)

    time.sleep(5)
    d_base = api_request(
        "get", params["urlApi"] + "/driver/ids/" + params["catId"] + "/" + params["year"])
    d_clean = clean_duplicate("idPlayer", d_scrap, d_base)
    # ret["drivers"] = api_request(
    #     "post", params["urlApi"]+"/driver/create", d_clean)
    ret["drivers"] = api_request(
        "put", params["urlApi"] + "/driver/update/0", d_clean)

    url = "/" + params["catOrigen"] + "/calendario/" + params["year"] + ".html"
    driver.get(params["urlBase"] + url)

    e_scrap = get_events(driver, params)
    # ret["events"] = events
    time.sleep(5)
    c_base = api_request(
        "get", params["urlApi"] + "/circuit/ids/actc")
    c_clean = clean_duplicate("idCircuit", e_scrap[0], c_base)
    ret["circuits"] = api_request(
        "post", params["urlApi"] + "/circuit/create", c_clean)

    time.sleep(5)
    e_base = api_request(
        "get", params["urlApi"] + "/event/ids/" + params["catId"] + "/" + params["year"])
    e_clean = clean_duplicate("idEvent", e_scrap[1], e_base)
    ret["events"] = api_request(
        "post", params["urlApi"] + "/event/create", e_clean)

    url = "/" + params["catOrigen"] + "/campeonato/" + params["year"] + ".html"
    driver.get(params["urlBase"] + url)

    time.sleep(5)
    ch_base = api_request(
        "get", params["urlApi"] + "/champ/ids/" + params["catId"] + "/" + params["year"])
    chd_scrap = get_champD(driver, params)
    chd_clean = clean_duplicate_ch("idChamp", chd_scrap, ch_base)
    ret["champD"] = api_request(
        "post", params["urlApi"] + "/champ/create", chd_clean)

    driver.close()

    return ret


def update_ACTC(params):
    ret = {}

    # CHAMPIONSHIPS
    driver = run_chrome()

    chd_base = api_request(
        "get", params["urlApi"] + "/champ/cat/" + params["catId"] + "/" +
        params["year"] + "/D")

    url = "/" + params["catOrigen"] + "/campeonato/" + params["year"] + ".html"
    driver.get(params["urlBase"] + url)

    time.sleep(3)
    if(chd_base):
        champId = chd_base["_id"]
        sumPoints = chd_base.get("sumPoints", 0)
        chd_scrap = get_champD(driver, params)
        if(len(chd_scrap) > 0 and chd_scrap.get("sumPoints", 0) > sumPoints):
            ret["champD"] = api_request(
                "put", params["urlApi"] + "/champ/update/" + champId, chd_scrap)

    # EVENTS AND CIRCUITS
    if(params["updType"] == "events" or params["updType"] == "all"):
        time.sleep(3)
        e_base = api_request(
            "get", params["urlApi"] + "/event/cat/" + params["catId"] + "/" +
            params["year"])

        url = "/" + params["catOrigen"] + \
            "/calendario/" + params["year"] + ".html"
        driver.get(params["urlBase"] + url)

        e_scrap = get_events(driver, params)

        ret["events"] = e_base

        time.sleep(3)
        c_base = api_request(
            "get", params["urlApi"] + "/circuit/ids/actc")
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
        items = WebDriverWait(driver, 30).until(
            lambda d: d.find_elements_by_xpath(
                "//div[@class='driver-listing']/ul/li/a")
        )
        for it in range(0, len(items)):
            linkDriver = items[it].get_attribute("href")
            idDriver = get_id_link_ACTC(params, linkDriver, "D")
            team = items[it].find_element_by_xpath(
                ".//div[@class='team']").text
            strPlayer = items[it].find_element_by_xpath(
                ".//h2").text
            thumb = params["urlBase"] + items[it].find_element_by_xpath(
                ".//figure/img").get_attribute("data-original")
            if("avatar-torso" in thumb):
                thumb = ""
            pilot = {
                "idPlayer": params["catRCtrl"].upper() + "-" + idDriver,
                "idCategory": params["catRCtrl"],
                "idRCtrl": idDriver,
                "strPlayer": strPlayer.replace("<br>", "", 2).replace(
                    ",", ", ").strip(),
                "strNumber": items[it].find_element_by_xpath(
                    ".//div[@class='car-data']/span").text,
                "idTeam": params["catRCtrl"].upper() + "-" + team.replace(" ", "_", 10),
                "strTeam": team,
                "numSeason": parse_int(params["year"]),
                "strThumb": thumb,
                "strCutout": thumb,
                "strFanart4": params["urlBase"] + items[it].find_element_by_xpath(
                    ".//div[@class='logo']/img").get_attribute("data-original"),
                "strRSS": linkDriver,
            }
            pilots.append(pilot)
        logger(pilots)
        print("::: PROCESS FINISHED :::")
        return pilots
    except Exception as e:
        logger(e, True, "Drivers", pilots)
        return "::: ERROR DRIVERS :::"


def get_teams(data, params):
    teams = []
    teamList = []
    try:
        print("::: TEAMS")
        for i in range(0, len(data)):
            team = {
                "idTeam": data[i]["idTeam"],
                "strTeam": data[i]["strTeam"],
                "idCategory": params["catRCtrl"],
                "idRCtrl": data[i]["idTeam"],
                "numSeason": parse_int(params["year"]),
                "strGender": "T",
                "strRSS": data[i]["strRSS"],
            }
            if(data[i]["idTeam"] not in teamList):
                teams.append(team)
                teamList.append(data[i]["idTeam"])
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
                "//div[@class='info-race']")
        )
        for it in range(0, len(items)):
            linkEvent = get_link_ACTC(items[it])
            # linkEvent = items[it].find_element_by_xpath(
            #     "//a[@class='more-txt']").get_attribute("href")
            idEvent = get_id_link_ACTC(params, linkEvent, "E")
            linkCircuit = items[it].find_element_by_xpath(
                ".//figure[@class='cont-circuit']/a").get_attribute("href")
            idCircuit = get_id_link_ACTC(params, linkCircuit, "C")
            strCircuit = items[it].find_element_by_xpath(
                ".//div[@class='hd']/p").text
            strDate = items[it].find_element_by_xpath(
                ".//div[@class='date']").text
            linkDriver, strResult = "", ""
            try:
                linkDriver = items[it].find_element_by_xpath(
                    ".//ul[@class='pos']/li[1]/a").get_attribute("href")
                strResult = items[it].find_element_by_xpath(
                    ".//ul[@class='pos']/li[1]/a").text
            except Exception:
                linkDriver = ""
            idDriver = get_id_link_ACTC(params, linkDriver, "D")
            event = {
                "idEvent": params["catRCtrl"].upper() + "-" + params["year"] + "-" + str(it + 1) + "-" + strDate.replace(" ", "-", 9),
                "strEvent": items[it].find_element_by_xpath(
                    ".//div[@class='hd']/h2").text,
                "idCategory": params["catRCtrl"],
                "idRCtrl": idEvent,
                "intRound": str(it + 1),
                "strDate": strDate,
                "idWinner": idDriver,
                "strResult": strResult,
                "idCircuit": idCircuit,
                "strCircuit": strCircuit,
                "numSeason": parse_int(params["year"]),
                "strSeason": params["year"],
                "strPostponed": "",
                "strRSS": linkEvent,
            }
            events.append(event)
            thumb = items[it].find_element_by_xpath(
                ".//figure[@class='cont-circuit']/a/img").get_attribute(
                    "data-original")
            circuit = {
                "idCircuit": event["idCircuit"],
                "strCircuit": strCircuit,
                "idRCtrl": event["idCircuit"],
                "strLeague": "actc",
                "strCountry": "Argentina",
                "numSeason": parse_int(params["year"]),
                "intSoccerXMLTeamID": "ARG",
                "strLogo": params["urlBase"] + thumb,
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
            linkDriver = get_link_ACTC(tds[2])
            idDriver = get_id_link_ACTC(params, linkDriver, "D")
            line = {
                "idPlayer": idDriver,
                "position": parse_int(tds[0].text.replace("°", "")),
                "totalPoints": parse_float(tds[5].text),
                "cups": parse_int(tds[3].text),
            }
            points += line["totalPoints"]
            data.append(line)
        champ = {
            "idChamp": params["catRCtrl"].upper() + "-" + params["year"] + "-D",
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
