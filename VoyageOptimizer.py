import GameData
from VoyageEstimator import voyage_estimator_redux as voyage_estimator, time_format
import pandas as pd

PS_ODDS = 0.35
SS_ODDS = 0.25
OS_ODDS = 0.1
PS_OS_RATIO = int(PS_ODDS*100) / (OS_ODDS*100)      # avoids float precision errors
SS_OS_RATIO = int(SS_ODDS*100) / (OS_ODDS*100)      # avoids float precision errors

SCI_SEAT1 = 'Chief Science Officer'
SCI_SEAT2 = 'Deputy Science Officer'
MED_SEAT1 = 'Chief Medical Officer'
MED_SEAT2 = 'Ship\'s Counselor'
CMD_SEAT1 = 'First Officer'
CMD_SEAT2 = 'Helm Officer'
DIP_SEAT1 = 'Communications Officer'
DIP_SEAT2 = 'Diplomat'
ENG_SEAT1 = 'Chief Engineer'
ENG_SEAT2 = 'Engineer'
SEC_SEAT1 = 'Chief Security Officer'
SEC_SEAT2 = 'Tactical Officer'
SCI_COL = 'sci'
MED_COL = 'med'
CMD_COL = 'cmd'
DIP_COL = 'dip'
ENG_COL = 'eng'
SEC_COL = 'sec'
SEAT_SKILL_MAP = {SCI_SEAT1: SCI_COL, SCI_SEAT2: SCI_COL, MED_SEAT1: MED_COL, MED_SEAT2: MED_COL,
                  CMD_SEAT1: CMD_COL, CMD_SEAT2: CMD_COL, DIP_SEAT1: DIP_COL, DIP_SEAT2: DIP_COL,
                  ENG_SEAT1: ENG_COL, ENG_SEAT2: ENG_COL, SEC_SEAT1: SEC_COL, SEC_SEAT2: SEC_COL}
SEAT_LIST = SEAT_SKILL_MAP.keys()
SEAT_LIST_ORDERED = [CMD_SEAT1, CMD_SEAT2, DIP_SEAT1, DIP_SEAT2, SEC_SEAT1, SEC_SEAT2,
                     SCI_SEAT1, SCI_SEAT2, ENG_SEAT1, ENG_SEAT2, MED_SEAT1, MED_SEAT2]
SKILL_SEAT_MAP = {SCI_COL: [SCI_SEAT1, SCI_SEAT2], ENG_COL: [ENG_SEAT1, ENG_SEAT2], CMD_COL: [CMD_SEAT1, CMD_SEAT2],
                  MED_COL: [MED_SEAT1, MED_SEAT2], DIP_COL: [DIP_SEAT1, DIP_SEAT2], SEC_COL: [SEC_SEAT1, SEC_SEAT2]}
SKILL_LIST = SKILL_SEAT_MAP.keys()

CREW_ID_COL = 'crew_id'
VOYTOTAL_COL = 'voytotal'
VOYTOTAL_WEIGHTED_COL = 'voytotal_w'
PRISEC_COL = 'prisec'
SKILLMAX_COL = 'skillmax'
SCORE_COL = 'score'


class Seats:

    @staticmethod
    def __calc_voy_score(skill_totals, primary, secondary):
        adj_voy_score = 0
        for skill in SKILL_LIST:
            if skill == primary:
                adj_voy_score += skill_totals[skill] * PS_OS_RATIO
            elif skill == secondary:
                adj_voy_score += skill_totals[skill] * SS_OS_RATIO
            else:
                adj_voy_score += skill_totals[skill]
        return int(adj_voy_score)

    @staticmethod
    def pretty_skill_totals_for_bot_static(skill_totals, primary, secondary, am):
        pri = skill_totals[primary]
        sec = skill_totals[secondary]
        others = ' '.join([str(value) if index != primary and index != secondary else ''
                           for index, value in skill_totals.iteritems()])
        others = ' '.join(others.split())       # remove any multiple consecutive spaces
        return f'-d voytime {pri} {sec} {others} {am}'

    @staticmethod
    def pretty_skill_totals_static(skill_totals, *, primary=None, secondary=None, voy_score=None):
        if voy_score is None and primary is not None and secondary is not None:
            voy_score = Seats.__calc_voy_score(skill_totals, primary, secondary)
        pairs = [f'{index}: {value:5}' for index, value in skill_totals.iteritems()]
        return ', '.join(pairs) + (f', adj. score: {voy_score}' if voy_score is not None else '')

    def pretty_skill_totals_for_bot(self, primary, secondary, am):
        return Seats.pretty_skill_totals_for_bot_static(self.skill_totals, primary, secondary, am)

    def pretty_skill_totals(self):
        return Seats.pretty_skill_totals_static(self.skill_totals, voy_score=self.adj_voy_score)

    def __get_df_val(self, crew_id, col):
        return self.__df[self.__df[CREW_ID_COL] == crew_id].iloc[0][col]

    def __get_df_skills(self, crew_id):
        cols = list(self.__df.columns)
        cols.remove('traits')
        return self.__df[self.__df[CREW_ID_COL] == crew_id].iloc[0][SKILL_LIST]

    def __update_voy_score(self):
        self.adj_voy_score = Seats.__calc_voy_score(self.skill_totals, self.ps, self.ss)
        return self.adj_voy_score

    def __init__(self, voyageDF, primary, secondary):
        assert type(voyageDF) is pd.DataFrame, type(voyageDF)

        self.seats = {seat: None for seat in SEAT_LIST}
        self.__df = voyageDF
        self.skill_totals = pd.Series({skill: 0 for skill in SKILL_LIST})
        self.ps = primary
        self.ss = secondary
        self.adj_voy_score = 0

    def __str__(self):
        max_len = max([len(seat) for seat in SEAT_LIST])
        s = ''
        for seat in SEAT_LIST_ORDERED:
            if self.seats[seat] is not None:
                name = self.__get_df_val(self.seats[seat], 'name')
            else:
                name = 'None'
            s += f'{seat:{max_len}}: {name}\n'
        return s

    def assign(self, seat, crew_id, debug=False):
        # if another crew was in this seat, remove it and deduct skills
        if self.seats[seat] is not None:
            old_crew_id = self.seats[seat]
            if debug:
                print('Removing {} from {}', old_crew_id, seat)
                print('Before: ', self.pretty_skill_totals())
                print('Crew:   ', Seats.pretty_skill_totals_static(self.__get_df_skills(old_crew_id),
                                                                   primary=self.ps, secondary=self.ss))
            self.skill_totals -= self.__get_df_skills(old_crew_id)
            if debug:
                print('After:  ', self.pretty_skill_totals())

        for s, c in self.seats.items():
            if c == crew_id:
                if debug:
                    print(f'Removing {c} from {s}')
                    print('Before: ', self.pretty_skill_totals())
                    print('Crew:   ', Seats.pretty_skill_totals_static(self.__get_df_skills(self.seats[s]),
                                                                       primary=self.ps, secondary=self.ss))
                self.skill_totals -= self.__get_df_skills(self.seats[s])
                if debug:
                    print('After:  ', self.pretty_skill_totals())
                self.seats[s] = None
                break

#        print(f'Assigning {crew_id} to {seat}')
        assert self.seats[seat] is None
        self.seats[seat] = crew_id
        if debug:
            print('Before: ', self.pretty_skill_totals())
            print('Crew:   ', Seats.pretty_skill_totals_static(self.__get_df_skills(crew_id),
                                                               primary=self.ps, secondary=self.ss))
        self.skill_totals += self.__get_df_skills(crew_id)
        if debug:
            print('After:  ', self.pretty_skill_totals())

    def is_crew_assigned(self, crew):
        for k, v in self.seats.items():
            if v == crew:
                return True

        return False


class Optimizer:

    def __init__(self, game_data, primary, secondary, startAm):
        self.crew_count = len(game_data.crew_data.crew)
        self.df = game_data.crew_data.voyDF
        self.primary = primary
        self.secondary = secondary
        self.startAm = startAm
        self.__crew_scores_calculated = False

    def __calc_duration(self, seats):
        ps = None
        ss = None
        os = []
        for skill in SKILL_LIST:
            if skill == self.primary:
                ps = seats.skill_totals[skill].item()
            elif skill == self.secondary:
                ss = seats.skill_totals[skill].item()
            else:
                os.append(seats.skill_totals[skill].item())
        assert ps is not None
        assert ss is not None
        assert len(os) == 4, os

        return voyage_estimator(ps, ss, *os, self.startAm)

    def __calc_weighted_voytotal(self, crew_skills):
        '''

        :param crew_skills: a row from the PlayerData DF, aka a pandas Series, with the crew's skills
        :return: weighted voyage total for the crew member
        '''
        return int(sum([crew_skills[s] * PS_OS_RATIO if s == self.primary else
                        crew_skills[s] * SS_OS_RATIO if s == self.secondary else
                        crew_skills[s]
                    for s in SKILL_LIST]))

    def __calc_prisec_sum(self, crew_skills):
        '''

        :param crew_skills: a row from the PlayerData DF, aka a pandas Series, with the crew's skills
        :return: sum of primary + secondary skills for the crew member
        '''
        return int(sum([crew_skills[s] * PS_OS_RATIO if s == self.primary else
                        crew_skills[s] * SS_OS_RATIO if s == self.secondary else
                        0
                    for s in SKILL_LIST]))

    def __calc_scores(self):
        '''
        Add columns to the DataFrame for each of the strategies.  Note that the SkillMax strategy uses the existing
        skill columns, so there's no new column created for it.
        '''

        if self.__crew_scores_calculated:
            return

        # Simple voyage total strategy
        self.df[VOYTOTAL_COL] = self.df[SKILL_LIST].apply(sum, axis=1)

        # Weighted voyage total strategy
#        self.df[VOYTOTAL_WEIGHTED_COL] = self.df[SKILL_LIST].apply(lambda x: self.calc_weighted_voytotal(x), axis=1)
        self.df[VOYTOTAL_WEIGHTED_COL] = self.df[SKILL_LIST].apply(self.__calc_weighted_voytotal, axis=1)

        # Primary/Secondary (prisec) skill strategy
#        self.df[PRISEC_COL] = self.df[SKILL_LIST].apply(lambda x: self.calc_prisec_sum(x), axis=1)
        self.df[PRISEC_COL] = self.df[SKILL_LIST].apply(self.__calc_prisec_sum, axis=1)

        self.__crew_scores_calculated = True

    def optimize_crew_skillmax_strategy(self):
        print(f'Optimizing {self.primary}/{self.secondary}/{self.startAm} voyage with {self.crew_count} '
              f'crew using SkillMax strategy...')
        seats = Seats(self.df, self.primary, self.secondary)
        self.__calc_scores()

        # Pick the two crew with the highest voyage score in the seat's skill
        for skill in SKILL_SEAT_MAP:
            self.df.sort_values(by=skill, ascending=False, inplace=True)
            seats.assign(SKILL_SEAT_MAP[skill][0], self.df.iloc[0][CREW_ID_COL])
            seats.assign(SKILL_SEAT_MAP[skill][1], self.df.iloc[1][CREW_ID_COL])

        return seats, self.__calc_duration(seats)

    def optimize_crew_voytotal_strategy(self, use_weighted=False):
        print(f'Optimizing {self.primary}/{self.secondary}/{self.startAm} voyage with {self.crew_count} '
              f'crew using VoyTotal strategy...')
        seats = Seats(self.df, self.primary, self.secondary)
        self.__calc_scores()

        if use_weighted:
            col_to_use = VOYTOTAL_WEIGHTED_COL
        else:
            col_to_use = VOYTOTAL_COL

        # Pick the two crew with the highest voyage score eligible to sit in each seat
        self.df.sort_values(by=col_to_use, ascending=False, inplace=True)
        for skill in SKILL_SEAT_MAP:
            used_crew = set(seats.seats.values()).difference({None})
            tempDF = self.df[(self.df[skill] > 0) & (~ self.df[CREW_ID_COL].isin(used_crew))]
            seats.assign(SKILL_SEAT_MAP[skill][0], tempDF.iloc[0][CREW_ID_COL])
            seats.assign(SKILL_SEAT_MAP[skill][1], tempDF.iloc[1][CREW_ID_COL])

        return seats, self.__calc_duration(seats)

    def optimize_crew_prisec_strategy(self):
        print(f'Optimizing {self.primary}/{self.secondary}/{self.startAm} voyage with {self.crew_count} '
              f'crew using PriSec strategy...')
        seats = Seats(self.df, self.primary, self.secondary)
        self.__calc_scores()

        # Pick the two crew with the highest pri+sec score eligible to sit in each seat, starting with NON-pri/sec seats
        self.df.sort_values(by=PRISEC_COL, ascending=False, inplace=True)
        for skill in SKILL_SEAT_MAP:
            # Do the other skill seats first
            if skill != self.primary and skill != self.secondary:
                used_crew = set(seats.seats.values()).difference({None})
                tempDF = self.df[(self.df[skill] > 0) & (~ self.df[CREW_ID_COL].isin(used_crew))]
                seats.assign(SKILL_SEAT_MAP[skill][0], tempDF.iloc[0][CREW_ID_COL])
                seats.assign(SKILL_SEAT_MAP[skill][1], tempDF.iloc[1][CREW_ID_COL])

        # Then do the secondary skill seats
        used_crew = set(seats.seats.values()).difference({None})
        tempDF = self.df[(self.df[self.secondary] > 0) & (~ self.df[CREW_ID_COL].isin(used_crew))]
        seats.assign(SKILL_SEAT_MAP[self.secondary][0], tempDF.iloc[0][CREW_ID_COL])
        seats.assign(SKILL_SEAT_MAP[self.secondary][1], tempDF.iloc[1][CREW_ID_COL])

        # Then do the primary skill seats
        used_crew = set(seats.seats.values()).difference({None})
        tempDF = self.df[(self.df[self.primary] > 0) & (~ self.df[CREW_ID_COL].isin(used_crew))]
        seats.assign(SKILL_SEAT_MAP[self.primary][0], tempDF.iloc[0][CREW_ID_COL])
        seats.assign(SKILL_SEAT_MAP[self.primary][1], tempDF.iloc[1][CREW_ID_COL])

        return seats, self.__calc_duration(seats)


if __name__ == "__main__":
    sample_config = ['sec', 'cmd', 2700]
    game_data = GameData.load_game_data(max_days_old=7)
    opt = Optimizer(game_data, *sample_config)

    results = {SKILLMAX_COL: opt.optimize_crew_skillmax_strategy(),
               VOYTOTAL_WEIGHTED_COL: opt.optimize_crew_voytotal_strategy(use_weighted=True),
               VOYTOTAL_COL: opt.optimize_crew_voytotal_strategy(use_weighted=False),
               PRISEC_COL: opt.optimize_crew_prisec_strategy()}

    for strategy, (seats, durations) in results.items():
        print()
        print(strategy)
        print(seats)
        print(seats.pretty_skill_totals())
        print(seats.pretty_skill_totals_for_bot(*sample_config))
        print(', '.join([time_format(t) for t in durations]))
