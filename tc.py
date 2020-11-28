from selenium.webdriver.support.ui import WebDriverWait
from tools import getIdLinkTC, parseFloat, parseInt, runChrome
import requests


def loadTC(params):
    ret = {}
    urlBase = "https://#CAT#.com.ar"

    r = requests.get(params["urlApi"]+"/org/find/tc")
    data = r.json()
    if(len(data["categories"]) > 0):
        cats = data["categories"]
        for it in range(0, len(cats)):
            print(cats[it]["idRCtrl"])
            params["catRCtrl"] = cats[it]["idLeague"]
            params["catOrigen"] = cats[it]["idRCtrl"]
            params["urlBase"] = urlBase.replace(
                "#CAT#", params["catOrigen"])
            ans = runScriptTC(params)
            ret[cats[it]["idLeague"]] = ans
    return ret


def runScriptTC(params):
    ret = {}

    driver = runChrome()

    # Params
    urlBase = params["urlBase"]
    url = "/equipos.php?accion=pilotos"
    urlApi = params["urlApi"]
    driver.get(urlBase + url)

    data = getDrivers(driver, params)

    r = requests.post(urlApi+"/team/create", json=data[1])
    print(r.json())
    ret["teams"] = r.json()

    r = requests.post(urlApi+"/driver/create", json=data[0])
    print(r.json())
    ret["drivers"] = r.json()

    url = "/carreras.php?evento=calendario"
    driver.get(urlBase + url)

    events = getEvents(driver, params)

    r = requests.post(urlApi+"/circuit/create", json=events[1])
    print(r.json())
    ret["circuits"] = r.json()

    r = requests.post(urlApi+"/event/create", json=events[0])
    print(r.json())
    ret["events"] = r.json()

    url = "/estadisticas.php?accion=posiciones"
    driver.get(urlBase + url)

    champ = getChampD(driver, data[0], params)
    r = requests.post(urlApi+"/champ/create", json=champ)
    print(r.json())
    ret["champD"] = r.json()

    champ = getChampT(driver, data[1], params)
    r = requests.post(urlApi+"/champ/create", json=champ)
    print(r.json())
    ret["champT"] = r.json()

    champ = getChampC(driver, params)

    r = requests.post(urlApi+"/team/create", json=champ[1])
    print(r.json())
    ret["teamsC"] = r.json()

    r = requests.post(urlApi+"/champ/create", json=champ[0])
    print(r.json())
    ret["champC"] = r.json()

    driver.close()

    return ret


def getDrivers(driver, params):
    try:
        data = []
        pilots = []
        teams = []
        print("::: DRIVERS")
        items = WebDriverWait(driver, 30).until(
            lambda d: d.find_elements_by_xpath(
                "//div[contains(@class, 'pilotos_listado')]/div[contains(@class, 'col-md-4 col-sm-6 col-xs-12 m_t_15')]")
        )
        print(str(len(items)))
        for it in range(0, len(items)):
            team = {}
            brand = items[it].find_elements_by_xpath(
                ".//div/h3[@class='imagen_marca']/img")
            if(len(brand) > 0):
                linkTeam = items[it].find_element_by_xpath(
                    ".//img[@class='borde_gris']").get_attribute("src")
                idTeam = getIdLinkTC(params, linkTeam, "T")
                team = {
                    "idTeam": params["catRCtrl"].upper() + "-" + idTeam,
                    "strTeam": items[it].find_element_by_xpath(
                        ".//div[@class='overlay']/p").text,
                    "idCategory": params["catRCtrl"],
                    "idRCtrl": idTeam,
                    "numSeason": parseInt(params["year"]),
                    "strTeamLogo": brand[0].get_attribute("src"),
                    "strTeamBadge":  linkTeam,
                    "strTeamFanart4":  brand[0].get_attribute("src")
                }
                teams.append(team)
            else:
                linkDriver = items[it].find_element_by_xpath(
                    ".//a").get_attribute("href")
                linkImg = items[it].find_element_by_xpath(
                    ".//a/img").get_attribute("src")
                if("no-piloto" in linkImg):
                    linkImg = ""
                idDriver = getIdLinkTC(params, linkDriver, "D")
                pilot = {
                    "idPlayer": params["catRCtrl"].upper() + idDriver,
                    "idCategory": params["catRCtrl"],
                    "idRCtrl": idDriver,
                    "strPlayer": items[it].find_element_by_xpath(
                        ".//div[@class='overlay']/p").text,
                    "strNumber": items[it].find_element_by_xpath(
                        ".//div[@class='overlay']/h3").text,
                    "idTeam": team["idTeam"],
                    "strTeam": team["strTeam"],
                    "numSeason": parseInt(params["year"]),
                    "strThumb": linkImg,
                    "strCutout": linkImg,
                    "strFanart4": team["strTeamFanart4"],
                    "strRSS": linkDriver,
                }
                pilots.append(pilot)
        data.append(pilots)
        data.append(teams)
        print(data)
        print("::: PROCESS FINISHED :::")
        return data
    except Exception as e:
        print(e)
        return "::: ERROR DRIVERS :::"


def getTeams(data, params):
    try:
        teams = []
        teamList = []
        print("::: TEAMS")
        for i in range(0, len(data)):
            team = {
                "idTeam": data[i]["idTeam"],
                "strTeam": data[i]["strTeam"],
                "idCategory": params["catRCtrl"],
                "idRCtrl": data[i]["idTeam"],
                "numSeason": parseInt(params["year"]),
                "strRSS": data[i]["strRSS"],
            }
            if(data[i]["idTeam"] not in teamList):
                teams.append(team)
                teamList.append(data[i]["idTeam"])
        print(teams)
        print("::: PROCESS FINISHED :::")
        return teams
    except Exception as e:
        print(e)
        return "::: ERROR TEAMS :::"


def getEvents(driver, params):
    try:
        data = []
        events = []
        circuits = []
        circList = []
        print("::: EVENTS")
        items = WebDriverWait(driver, 30).until(
            lambda d: d.find_elements_by_xpath("//div[@class='box-fechas']")
        )
        for it in range(0, len(items)):
            linkEvent = items[it].find_element_by_xpath(
                ".//a[@class='button_bg']").get_attribute("href")
            idEvent = getIdLinkTC(params, linkEvent, "E")
            linkCircuit = items[it].find_element_by_xpath(
                ".//img[@class='imagen_autodromo']").get_attribute("src")
            idCircuit = getIdLinkTC(params, linkCircuit, "C")
            event = {
                "idEvent": params["catRCtrl"].upper() + "-" + params["year"] +
                "-" + str(it+1) + "-" + idEvent,
                "strEvent": items[it].find_element_by_xpath(".//h3").text,
                "idCategory": params["catRCtrl"],
                "idRCtrl": idEvent,
                "intRound": str(it+1),
                "strDate": items[it].find_element_by_xpath(
                    ".//h2/span[@class='gris']").text,
                "idCircuit": idCircuit,
                "strCircuit": "",
                "numSeason": parseInt(params["year"]),
                "strSeason": params["year"],
                "strPostponed": "",
                "strRSS": linkEvent,
            }
            events.append(event)
            circuit = {
                "idCircuit": event["idCircuit"],
                "strCircuit": event["strEvent"],
                "idRCtrl": event["idCircuit"],
                "strCountry": "Argentina",
                "numSeason": parseInt(params["year"]),
                "intSoccerXMLTeamID": "ARG",
                "strLogo": linkCircuit,
            }
            if(circuit["idCircuit"] not in circList):
                circuits.append(circuit)
                circList.append(circuit["idCircuit"])
        data.append(events)
        data.append(circuits)
        print(data)
        print("::: PROCESS FINISHED :::")
        return data
    except Exception as e:
        print(e)
        return "::: ERROR EVENTS :::"


def getChampD(driver, pilots, params):
    try:
        champ = {}
        data = []
        print("::: CHAMPIONSHIP DRIVERS")
        items = WebDriverWait(driver, 30).until(
            lambda d: d.find_elements_by_xpath(
                "//div[@id='tabs-1']/div/ul[@class='puntajes']")
        )
        points = 0
        for it in range(0, len(items)):
            tds = items[it].find_elements_by_xpath("./li")
            nameDriver = tds[2].find_element_by_xpath("./span").text
            idDriver = ""
            for p in range(0, len(pilots)):
                if(pilots[p]["strPlayer"].upper() == nameDriver.upper()):
                    idDriver = pilots[p]["idRCtrl"]
                    break
            line = {
                "idPlayer": idDriver,
                "position": parseInt(tds[0].text.replace("°", "")),
                "totalPoints": parseFloat(tds[3].text),
            }
            points += line["totalPoints"]
            data.append(line)
        champ = {
            "idChamp": params["catRCtrl"].upper()+"-"+params["year"]+"-D",
            "numSeason": parseInt(params["year"]),
            "strSeason": params["year"],
            "idCategory": params["catRCtrl"],
            "idRCtrl": params["catOrigen"],
            "data": data,
            "sumPoints": points,
            "typeChamp": "D"
        }
        print("::: PROCESS FINISHED :::")
        return champ
    except Exception as e:
        print(e)
        return "::: ERROR CHAMP DRIVERS :::"


def getChampT(driver, pilots, params):
    try:
        champ = {}
        data = []
        print("::: CHAMPIONSHIP TEAMS")
        items = WebDriverWait(driver, 30).until(
            lambda d: d.find_elements_by_xpath(
                "//div[@id='tabs-2']/div/ul[@class='puntajes']")
        )
        points = 0
        for it in range(0, len(items)):
            tds = items[it].find_elements_by_xpath("./li")
            nameTeam = tds[2].find_element_by_xpath("./span").text
            idTeam = ""
            for p in range(0, len(pilots)):
                if(pilots[p]["strTeam"].upper() == nameTeam.upper()):
                    idTeam = pilots[p]["idRCtrl"]
                    break
            line = {
                "idTeam": idTeam,
                "position": parseInt(tds[0].text.replace("°", "")),
                "totalPoints": parseFloat(tds[3].text),
            }
            points += line["totalPoints"]
            data.append(line)
        champ = {
            "idChamp": params["catRCtrl"].upper()+"-"+params["year"]+"-T",
            "numSeason": parseInt(params["year"]),
            "strSeason": params["year"],
            "idCategory": params["catRCtrl"],
            "idRCtrl": params["catOrigen"],
            "data": data,
            "sumPoints": points,
            "typeChamp": "T"
        }
        print("::: PROCESS FINISHED :::")
        return champ
    except Exception as e:
        print(e)
        return "::: ERROR CHAMP TEAMS :::"


def getChampC(driver, params):
    try:
        ret = []
        champ = {}
        teams = []
        data = []
        print("::: CHAMPIONSHIP CONSTRUCTOR")
        items = WebDriverWait(driver, 30).until(
            lambda d: d.find_elements_by_xpath(
                "//div[@id='tabs-2']/div/ul[@class='puntajes']")
        )
        points = 0
        for it in range(0, len(items)):
            tds = items[it].find_elements_by_xpath("./li")
            strTeam = tds[2].find_element_by_xpath("./span").text
            idTeam = params["catRCtrl"].upper() + "-C-" + strTeam.lower()
            linkTeam = tds[1].find_element_by_xpath(
                "./img").get_attribute("src")
            team = {
                "idTeam": idTeam,
                "strTeam": strTeam,
                "idCategory": params["catRCtrl"],
                "idRCtrl": idTeam,
                "numSeason": parseInt(params["year"]),
                "strTeamLogo": linkTeam,
                "strTeamBadge":  linkTeam,
                "strTeamFanart4":  linkTeam
            }
            teams.append(team)
            line = {
                "idTeam": idTeam,
                "position": parseInt(tds[0].text.replace("°", "")),
                "totalPoints": parseFloat(tds[3].text),
            }
            points += line["totalPoints"]
            data.append(line)
        champ = {
            "idChamp": params["catRCtrl"].upper()+"-"+params["year"]+"-T",
            "numSeason": parseInt(params["year"]),
            "strSeason": params["year"],
            "idCategory": params["catRCtrl"],
            "idRCtrl": params["catOrigen"],
            "data": data,
            "sumPoints": points,
            "typeChamp": "T"
        }
        print("::: PROCESS FINISHED :::")
        ret.append(champ)
        ret.append(teams)
        return ret
    except Exception as e:
        print(e)
        return "::: ERROR CHAMP CONSTRUCTOR :::"
