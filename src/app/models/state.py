from .. import db

class State(db.Model):
    __tablename__ = "states"

    state_name = db.Column(db.String(50), primary_key=True)  # ex. california
    ocd_id = db.Column(db.String(100), unique=True, nullable=True)  # 'ocd-division/country:us/state:ca'
    fips_code = db.Column(db.String(2), unique=True, nullable=True)  # '06'

    def __init__(self, state_name: str, ocd_id: str = None, fips_code: str = None):
        self.state_name = state_name
        self.ocd_id = ocd_id
        self.fips_code = fips_code

    def __repr__(self):
        return f"<State {self.state_name}>"