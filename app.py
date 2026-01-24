import requests
import json
import termcolor
from io import StringIO
import string
import pandas
import tkinter.filedialog
from pathlib import Path
from os import path

'''COMPARISONS = [
    ["auto_coral_l1"], ["autoReef", "trough"],
    ["auto_coral_l2"]: ["autoReef", "tba_botRowCount"],
    ["auto_coral_l3"]: ["autoReef", "tba_midRowCount"],
    ["auto_coral_l4"]: ["autoReef", "tba_topRowCount"],
    ["tele_coral_l1"]: ["teleopReef", "trough"],
    ["tele_coral_l2"]: ["teleopReef", "tba_botRowCount"],
    ["tele_coral_l3"]: ["teleopReef", "tba_midRowCount"],
    ["tele_coral_l4"]: ["teleopReef", "tba_topRowCount"],
    ["auto_algae_processor", "tele_algae_processor"]: ["wallAlgaeCount"]
]'''

COMPARISONS = [
    {
        "data_values": ["auto_leave"],
        "data_possible_values": ["0", "1"],
        "data_mode": "validate_by_robot",
        "tba_values": [["autoLineRobot1"], ["autoLineRobot2"], ["autoLineRobot3"]],
        "tba_possible_values": ["No", "Yes"]
    },
    {
        "data_values": ["auto_coral_l1"],
        "tba_values": [["autoReef", "trough"]],
        "tolerance": 5
    },
    {
        "data_values": ["auto_coral_l2"],
        "tba_values": [["autoReef", "tba_botRowCount"]],
        "tolerance": 5
    },
    {
        "data_values": ["auto_coral_l3"],
        "tba_values": [["autoReef", "tba_midRowCount"]],
        "tolerance": 5
    },
    {
        "data_values": ["auto_coral_l4"],
        "tba_values": [["autoReef", "tba_topRowCount"]],
        "tolerance": 5
    },
     {
        "data_values": ["tele_coral_l1"],
        "tba_values": [["teleopReef", "trough"]],
        "tolerance": 5
    },
    {
        "data_values": ["tele_coral_l2"],
        "tba_values": [["teleopReef", "tba_botRowCount"]],
        "tolerance": 5
    },
    {
        "data_values": ["tele_coral_l3"],
        "tba_values": [["teleopReef", "tba_midRowCount"]],
        "tolerance": 5
    },
    {
        "data_values": ["tele_coral_l4"],
        "tba_values": [["teleopReef", "tba_topRowCount"]],
        "tolerance": 5
    },
    {
        "data_values": ["auto_algae_processor", "tele_algae_processor"],
        "data_mode": "sum",
        "tba_values": [["wallAlgaeCount"]],
        "tolerance": 5
    },
    {
        "data_values": ["auto_algae_net", "tele_algae_net"],
        "data_mode": "sum",
        "tba_values": [["netAlgaeCount"]],
        "tolerance": 5
    },
    {
        "data_values": ["climb"],
        "data_possible_values": ["no_climb", "park_climb", "shallow_climb", "deep_climb"],
        "data_mode": "validate_by_robot",
        "tba_values": [["endGameRobot1"], ["endGameRobot2"], ["endGameRobot3"]],
        "tba_possible_values": ["None", "Parked", "ShallowCage", "DeepCage"]
    }
]

programDirectory = Path(__file__).parent
configPath = programDirectory / "config.json"

if path.exists(configPath):
    try:
        file = open(configPath)
        tbaKey = json.loads(file.read())["tbaKey"]
        file.close()
    except:
        tbaKey = None
else:
    tbaKey = None

def dropDataTypes(dataFrame):
    types = dataFrame.iloc[0].values.tolist()
    csv = dataFrame.drop(0).to_csv(sep=",", index=False)
    return pandas.read_csv(StringIO(csv), sep=",", engine="python"), types

def tbaRequest(url):
    return json.loads(requests.get("https://www.thebluealliance.com/api/v3/" + url, headers={"X-TBA-Auth-Key": tbaKey}).text)

def dropNonNumeric(originalValue):
    numbersOnly = ""
    for i in range(len(originalValue)):
        if originalValue[i] in string.digits:
            numbersOnly += originalValue[i]
    return int(numbersOnly)

def prepareScoutedData(data, valuesToCompare):
    dataValue = 0
    if "data_mode" in valuesToCompare:
        if valuesToCompare["data_mode"] == "sum":
            for key in valuesToCompare["data_values"]:
                dataValue += data[key].sum(skipna=True)
        if valuesToCompare["data_mode"] == "difference":
            dataValue = data[valuesToCompare["data_values"][0]].sum(skipna=True)
            for key in range(1, len(valuesToCompare["data_values"])):
                dataValue -= data[valuesToCompare["data_values"][key]].sum(skipna=True)
    else:
        dataValue = data[valuesToCompare["data_values"][0]].sum(skipna=True)
    return dataValue

def getScoutedDataFromTeam(data, team, valuesToCompare):
    data = data[data["team_number"] == team]
    if (len(data) != 0):
        dataValue = data[valuesToCompare["data_values"][0]].tolist()[0]
        return dataValue
    else:
        return None

def getTBAValue(tbaData, dataToGet):
    tbaData = tbaData.copy()
    for value in dataToGet:
        tbaData = tbaData[value]
    return tbaData

def prepareTBAData(data, valuesToCompare):
    tbaValue = 0
    if ("tba_mode" in valuesToCompare):
        if valuesToCompare["tba_mode"] == "sum":
            for value in valuesToCompare["tba_values"]:
                tbaValue += getTBAValue(data, value)
        if valuesToCompare["tba_mode"] == "difference":
            tbaValue = getTBAValue(data, valuesToCompare["tba_values"][0])
            for value in range(1, len(valuesToCompare["tba_values"])):
                tbaValue -= getTBAValue(data, valuesToCompare["tba_values"][value])
    else:
        tbaValue = getTBAValue(data, valuesToCompare["tba_values"][0])
    return tbaValue

def validateData(tbaJson, dataFrame):
    tbaJson = sorted(tbaJson, key=lambda x: x["match_number"])
    for match in tbaJson:
        matchData = dataFrame[dataFrame["match_number"] == match["match_number"]]
        if (match["comp_level"] == "qm" and match["post_result_time"] != None):
            errors = []
            redTbaTeams = list(map(dropNonNumeric, match["alliances"]["red"]["team_keys"]))
            blueTbaTeams = list(map(dropNonNumeric, match["alliances"]["blue"]["team_keys"]))
            dataTeams = list(map(int, matchData["team_number"].tolist()))
            redTeamError = False
            blueTeamError = False
            nonExistentTeamError = False
            for team in redTbaTeams:
                if not team in dataTeams:
                    errors.append((1, f"{team} from the red alliance has no data for this match"))
                    redTeamError = True
            for team in blueTbaTeams:
                if not team in dataTeams:
                    errors.append((2, f"{team} from the blue alliance has no data for this match"))
                    blueTeamError = True
            for team in dataTeams:
                if not (team in redTbaTeams or team in blueTbaTeams):
                    nonExistentTeamError = True
                    errors.append((0, f"{team} did not participate in this match"))
            if redTeamError or blueTeamError:
                errors.append((0, "One or more teams has no data for this match. Validation is based on data from remaning teams"))
            if redTeamError or blueTeamError or nonExistentTeamError:
                errors.append((0, f"These teams participated in this match: {", ".join(list(map(str, redTbaTeams + blueTbaTeams)))}"))
            breakDownRed = match["score_breakdown"]["red"]
            redTeamData = matchData[matchData["team_number"].isin(redTbaTeams)]
            breakDownBlue = match["score_breakdown"]["blue"]
            blueTeamData = matchData[matchData["team_number"].isin(blueTbaTeams)]
            for comparison in COMPARISONS:
                if ("data_mode" not in comparison or comparison["data_mode"] != "validate_by_robot"):
                    dataValue = float(prepareScoutedData(redTeamData, comparison))
                    tbaValue = float(prepareTBAData(breakDownRed, comparison))
                    if tbaValue != 0:
                        precentError = abs((dataValue - tbaValue) / tbaValue) * 100
                    else:
                        precentError = 100
                    if (precentError > comparison["tolerance"]) and (dataValue != tbaValue):
                        errors.append((1, f"Red's {", ".join(comparison["data_values"])} total has a {precentError}% error compared to the value provided by TBA"))
                        errors.append((1, f"\tOur total {dataValue}"))
                        errors.append((1, f"\tTBA's total {tbaValue}"))
                else:
                    for team in range(len(redTbaTeams)):
                        dataValue = getScoutedDataFromTeam(redTeamData, redTbaTeams[team], comparison)
                        if dataValue != None:
                            tbaValue = getTBAValue(breakDownRed, comparison["tba_values"][team])
                            tbaValue = comparison["data_possible_values"][comparison["tba_possible_values"].index(str(tbaValue))]
                            if (str(dataValue) != str(tbaValue)):
                                errors.append((1, f"{redTbaTeams[team]}'s {", ".join(comparison["data_values"])} does not match the value provided by TBA"))
                                errors.append((1, f"\tOur {", ".join(comparison["data_values"])} {dataValue}"))
                                errors.append((1, f"\tTBA's {", ".join(comparison["data_values"])} {tbaValue}"))
            for comparison in COMPARISONS:
                if ("data_mode" not in comparison or comparison["data_mode"] != "validate_by_robot"):
                    dataValue = float(prepareScoutedData(redTeamData, comparison))
                    tbaValue = float(prepareTBAData(breakDownRed, comparison))
                    if tbaValue != 0:
                        precentError = abs((dataValue - tbaValue) / tbaValue) * 100
                    else:
                        precentError = 100
                    if (precentError > comparison["tolerance"]) and (dataValue != tbaValue):
                        errors.append((2, f"Blue's {", ".join(comparison["data_values"])} total has a {precentError}% error compared to the value provided by TBA"))
                        errors.append((2, f"\tOur total {dataValue}"))
                        errors.append((2, f"\tTBA's total {tbaValue}"))
                else:
                    for team in range(len(blueTbaTeams)):
                        dataValue = getScoutedDataFromTeam(blueTeamData, blueTbaTeams[team], comparison)
                        if dataValue != None:
                            tbaValue = getTBAValue(breakDownBlue, comparison["tba_values"][team])
                            tbaValue = comparison["data_possible_values"][comparison["tba_possible_values"].index(str(tbaValue))]
                            if (str(dataValue) != str(tbaValue)):
                                errors.append((2, f"{blueTbaTeams[team]}'s {", ".join(comparison["data_values"])} does not match the value provided by TBA"))
                                errors.append((2, f"\tOur {", ".join(comparison["data_values"])} {dataValue}"))
                                errors.append((2, f"\tTBA's {", ".join(comparison["data_values"])} {tbaValue}"))
            if (len(errors) == 0):
                print(termcolor.colored(f"Match #{match["match_number"]} Ok", "green"))
            else:
                print(termcolor.colored(f"Match #{match["match_number"]} Error", "yellow"))
                for error in errors:
                    if error[0] == 0:
                        print(termcolor.colored(f"\t{error[1]}", "yellow"))
                    elif error[0] == 1:
                        print(termcolor.colored(f"\t{error[1]}", "red"))
                    elif error[0] == 2:
                        print(termcolor.colored(f"\t{error[1]}", "blue"))
                input("Press enter to continue")

print("Coalition Data Validator")

if tbaKey != None:
    table = print("Select data file")
    filePath = tkinter.filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if filePath != "":
        data = dropDataTypes(pandas.read_csv(filePath))[0]
        eventKey = input("Enter event key: ")
        tbaMatchData = None
        print("Reterving match data from TBA. Please wait...")
        try:
            tbaMatchData = tbaRequest(f"/event/{eventKey}/matches")
        except:
            print(termcolor.colored("Error reterving match data", "red"))
            input()
        if tbaMatchData != None:
            validateData(tbaMatchData, data)
            input("Press enter to finish")
else:
    print(termcolor.colored("Please provide a TBA API key in config.json", "red"))
    input()