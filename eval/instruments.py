"""USD exchange contract specs. Fees/exposure are research estimates, not broker rules.
QM = 500 barrels (half CL), QG = 2,500 MMBtu (quarter NG); not micros.
FX point values use quoted USD prices; JPY tick refers to decimal USD/JPY quotation.
Sources to confirm before live use: CME contract specifications and broker fee schedule.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Instrument:
    tick: float
    point_value: float
    weight: float
    family: str
    fee: float
    available_from: str = "1900-01-01"

    @property
    def tick_value(self):
        return self.tick * self.point_value

    def costs(self, stressed=False):
        return (2 if stressed else 1) * self.tick, self.fee * (1.5 if stressed else 1)


# symbol: minimum tick, dollars/point, standard equivalents, family, estimated $/side,
# actual product launch date for micro/reduced contracts (no synthetic backfill).
_ROWS = {
    'ES': (.25, 50, 1, 'equity', 2.5), 'MES': (.25, 5, .1, 'equity', .75, '2019-05-06'),
    'NQ': (.25, 20, 1, 'equity', 2.5), 'MNQ': (.25, 2, .1, 'equity', .75, '2019-05-06'),
    'YM': (1, 5, 1, 'equity', 2.5), 'MYM': (1, .5, .1, 'equity', .75, '2019-05-06'),
    'RTY': (.1, 50, 1, 'equity', 2.5), 'M2K': (.1, 5, .1, 'equity', .75, '2019-05-06'),
    'NKD': (5, 5, 1, 'equity', 3),
    'CL': (.01, 1000, 1, 'energy', 2.5), 'MCL': (.01, 100, .1, 'energy', .75, '2021-07-12'),
    'QM': (.025, 500, .5, 'energy', 2.5, '2002-06-17'),
    'NG': (.001, 10000, 1, 'energy', 2.5), 'MNG': (.001, 1000, .1, 'energy', .75, '2023-11-06'),
    'QG': (.005, 2500, .25, 'energy', 2.5, '2002-06-17'),
    'RB': (.0001, 42000, 1, 'energy', 2.5), 'HO': (.0001, 42000, 1, 'energy', 2.5),
    'GC': (.1, 100, 1, 'metals', 2.5), 'MGC': (.1, 10, .1, 'metals', .75, '2010-10-04'),
    'SI': (.005, 5000, 1, 'metals', 2.5), 'SIL': (.005, 1000, .2, 'metals', 1.5, '2013-06-17'),
    'HG': (.0005, 25000, 1, 'metals', 2.5), 'MHG': (.0005, 2500, .1, 'metals', .75, '2022-05-02'),
    'PL': (.1, 50, 1, 'metals', 2.5),
    '6E': (.00005, 125000, 1, 'fx', 2.5), 'M6E': (.0001, 12500, .1, 'fx', .75, '2009-03-23'),
    '6B': (.0001, 62500, 1, 'fx', 2.5), 'M6B': (.0001, 6250, .1, 'fx', .75, '2009-03-23'),
    '6A': (.0001, 100000, 1, 'fx', 2.5), 'M6A': (.0001, 10000, .1, 'fx', .75, '2009-03-23'),
    '6C': (.00005, 100000, 1, 'fx', 2.5), '6J': (.0000005, 12500000, 1, 'fx', 2.5),
    '6S': (.0001, 125000, 1, 'fx', 2.5), '6N': (.0001, 100000, 1, 'fx', 2.5),
    '6M': (.00001, 500000, 1, 'fx', 2.5),
    'MBT': (5, .1, .1, 'crypto', 1.5, '2021-05-03'),
    'MET': (.5, .1, .1, 'crypto', 1.5, '2021-12-06'),
    'ZB': (1/32, 1000, 1, 'rates', 2.5), 'UB': (1/32, 1000, 1, 'rates', 2.5),
    'ZT': (1/256, 2000, 1, 'rates', 2.5), 'ZF': (1/128, 1000, 1, 'rates', 2.5),
    'ZN': (1/64, 1000, 1, 'rates', 2.5), 'TN': (1/64, 1000, 1, 'rates', 2.5),
    'ZC': (.25, 50, 1, 'grains', 2.5), 'ZS': (.25, 50, 1, 'grains', 2.5),
    'ZW': (.25, 50, 1, 'grains', 2.5), 'ZL': (.01, 600, 1, 'grains', 2.5),
    'HE': (.025, 400, 1, 'livestock', 2.5), 'LE': (.025, 400, 1, 'livestock', 2.5),
}
SPECS = {symbol: Instrument(*row) for symbol, row in _ROWS.items()}
BASE, STRESS = False, True
MAX_EXPOSURE = 5.0
