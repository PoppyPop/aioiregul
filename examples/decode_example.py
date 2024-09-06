"""
Example script for decoding IRegul server responses.

This script demonstrates parsing the undocumented IRegul API response format.
"""

import pprint
import re
from dataclasses import dataclass
from itertools import groupby
from operator import itemgetter


def is_numeric(n: str) -> bool:
    """Check if a string can be converted to a number."""
    try:
        float(n)
        return True
    except ValueError:
        return False


@dataclass
class IRegulDataZone:
    """IRegul zone data."""

    typeGrp: int
    consigne_normal: float
    consigne_reduit: float
    consigne_horsgel: float
    mode_select: int
    mode: int


@dataclass
class IRegulDataInput:
    """IRegul input data."""

    typeGrp: int
    valeur: int


@dataclass
class IRegulDataOutput:
    """IRegul output data."""

    typeGrp: int
    valeur: int


@dataclass
class IRegulDataMesure:
    """IRegul measurement data."""

    typeGrp: int
    valeur: float


class IRegulDataMem:
    """IRegul memory data."""

    def __init__(self) -> None:
        """Initialize IRegul memory data."""
        self.data: dict[str, str | int | bool] = {}

    def __setitem__(self, key: str, value: str | int | bool) -> None:
        """Set item in memory data."""
        self.data[key] = value


if __name__ == "__main__":
    # Example response from old API format
    with open("examples/502-OLD.txt", encoding="utf-8") as f:
        old502 = f.read()

    msg = old502

    dataindex = msg.find("{")
    enddataindex = msg.rfind("}")
    msgdate = msg[0:dataindex]

    print(f"Message date: {msgdate}")

    baseplit = msg[dataindex + 1 : enddataindex]
    datatable = baseplit.split("#")
    responsecode = datatable.pop(0)

    print(f"Response code: {responsecode}")

    propervalue = []
    for value in datatable:
        match = re.search(r"^(?P<type>\w+)@(?P<typeGrp>\d+)&(?P<name>.+)\[(?P<value>.+)\]$", value)
        if match:
            propervalue.append(match.groupdict())

    propervalue.sort(key=itemgetter("type"))
    grouped_data = groupby(propervalue, key=itemgetter("type"))

    final = []

    for type_key, group in grouped_data:
        group_list = list(group)
        grouped_by_grp = groupby(group_list, key=itemgetter("typeGrp"))

        for grp, items in grouped_by_grp:
            item_dict = {"type": type_key, "typeGrp": grp}
            for item in items:
                name = item["name"]
                value = item["value"]
                if is_numeric(value):
                    item_dict[name] = float(value)
                elif value == "True":
                    item_dict[name] = True
                elif value == "False":
                    item_dict[name] = False
                else:
                    item_dict[name] = value
            final.append(item_dict)

    pprint.pp(final)

    # Type legend:
    # Z = Zone
    # C = Config
    # J = Options
    # mem = Memory
    # B = Modbus
    # M = Mesure (Measurement)
    # I = Entree (Input)
    # O = Sortie (Output)
    # P = Parametre/Probe
    # A = Application data
