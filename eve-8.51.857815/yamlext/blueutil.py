#Embedded file name: yamlext\blueutil.py
import yaml
import blue
import pytelemetry.zoning as telemetry

@telemetry.ZONE_FUNCTION
def ReadYamlFile(path):
    """
    Returns data from the yaml file read from path or None
    if the file does not exist.
    """
    telemetry.APPEND_TO_ZONE(path)
    data = None
    if blue.paths.exists(path):
        rf = blue.ResFile()
        rf.Open(path)
        yamlStr = rf.read()
        rf.close()
        data = yaml.load(yamlStr, Loader=yaml.CLoader)
    return data
