from enum import Enum

class JurisdictionLevel(str, Enum):
    city = "city"
    county = "county"
    state = "state"

class Branch(str, Enum):
    legislative = "legislative"
    executive = "executive"
    judicial = "judicial"

class BodyType(str, Enum):
    council     = "council"
    committee   = "committee"
    department  = "department"
    board       = "board"
    agency      = "agency"
    mayor       = "mayor"


class SourceType(str, Enum):
    council_file   = "council_file"
    bill           = "bill"
    agenda         = "agenda"
    minutes        = "minutes"
    vote_roll      = "vote_roll"
    executive_order= "executive_order"
    press_release  = "press_release"
    report         = "report"
    budget         = "budget"
    lawsuit_docket = "lawsuit_docket"
    election_notice= "election_notice"
