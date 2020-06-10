import requests
from bs4 import BeautifulSoup, NavigableString, Tag
#from pathlib import Path
#import json
import pandas as pd


WIKI_BASE_URL = 'https://stt.wiki/wiki/'
SUBFOLDER_NAME = 'Star Trek Timelines'
ITEMS_FILE_NAME = 'items'

RARITY_TO_RARITY_NAME = {0: 'Basic', 1: 'Common', 2: 'Uncommon', 3: 'Rare', 4: 'Super Rare'}
RARITY_NAME_TO_RARITY = {'Basic': 0, 'Common': 1, 'Uncommon': 2, 'Rare': 3, 'Super Rare': 4}

DROP_TABLE_COLUMNS = ['Mission', 'Code', 'Type', 'Level', 'Cost', 'Cost/Unit']


'''
def read_game_data_from_file():
    print('Reading player data from file...')
    player = None
    filepath = Path.home().joinpath(SUBFOLDER_NAME, PLAYER_JSON_FILENAME)
    if filepath.exists():
        with open(filepath) as f:
            player = json.load(f)

    if player is not None and len(player) < 1:
        player = None

    return player


def get_game_data(authtoken):
    print('Getting player data...')
    form = {'client_api': CLIENT_API_VERSION, ACCESS_TOKEN: authtoken}
    resp = requests.get(PLAYER_URL, data=form)
    resp.raise_for_status()
    return json.loads(resp.content)


def write_game_data_to_file(player):
    print('Writing player data to file...')
    filepath = Path.home().joinpath(SUBFOLDER_NAME, PLAYER_JSON_FILENAME)
    with open(filepath, 'w') as f:
        json.dump(player, f, indent=3)

def get_game_data_age():
    filepath = Path.home().joinpath(SUBFOLDER_NAME, PLAYER_JSON_FILENAME)
    if filepath.exists():
        last_modified = os.path.getmtime(filepath)
        return (time.time()-os.path.getmtime(filepath))/SECONDS_PER_DAY
    else:
        return 99999999

'''


def scrape_page(item_name, *, debug=False):
    item_name = item_name.title().replace(' ', '_')
    print(f'Scraping wiki for {item_name}...')
#    headers = {'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8'}
    resp = requests.get(WIKI_BASE_URL+item_name)   # headers=headers)
    resp.raise_for_status()
    return BeautifulSoup(resp.content, 'html.parser')


class HTMLTableParser:
    """
    Credit for the original code for this class (before modifications):
    https://srome.github.io/Parsing-HTML-Tables-in-Python-with-BeautifulSoup-and-pandas/
    """

    def parse_url(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        return [(table['id'], self.parse_html_table(table)) for table in soup.find_all('table')]

    def parse_soup(self, soup):
        return [self.parse_html_table(table) for table in soup.find_all('table')]

    def parse_html_table(self, table):
        n_columns = 0
        n_rows = 0
        column_names = []

        # Find number of rows and columns
        # we also find the column titles if we can
        for row in table.find_all('tr'):

            # Determine the number of rows in the table
            td_tags = row.find_all('td')
            if len(td_tags) > 0:
                n_rows += 1
                if n_columns == 0:
                    # Set the number of columns for our table
                    n_columns = len(td_tags)

            # Handle column names if we find them
            th_tags = row.find_all('th')
            if len(th_tags) > 0 and len(column_names) == 0:
                for th in th_tags:
                    column_names.append(th.get_text().strip())

        parsed_columns = ['Cost','Code','Type','Mission', 'Level']

        assert len(column_names) > 0
        original_col_count = len(column_names)
        columns = column_names if len(column_names) > 0 else range(0, n_columns)
        columns.extend(parsed_columns)
        df = pd.DataFrame(columns=columns,
                          index=range(0, n_rows))
        row_marker = 0
        for row in table.find_all('tr'):
            column_marker = 0
            columns = row.find_all('td')
            for column in columns:
                data = column.get_text().strip()
                offset = data.find('Statistical Strength')
                if offset > 0:
                    # Cost/Unit column
                    data = data[:offset]
                offset = data.find(' [edit]')
                if offset > 0:
                    # From column
                    data = data[:offset]
                    for a in column('a'):
                        if 'title' in a.attrs:
                            title = a['title']
                            if title.find('Chrons') > 0:
                                # Cost
                                cost = title[:title.find(' ')]
                                df.iat[row_marker, original_col_count + 0] = str(int(cost))
                            elif title.startswith('Away Team') or title.startswith('Space Battle'):
                                # Mission type and code aka number
                                mission_type = title[:title.find(' ', 6)]
                                mission_code = title[title.find(' ', 6)+1:]
                                offset = mission_code.find(' (')
                                if offset > 0:
                                    mission_code = mission_code[:offset]
                                df.iat[row_marker, original_col_count + 1] = mission_code
                                df.iat[row_marker, original_col_count + 2] = mission_type
                            else:
                                # Mission name
                                df.iat[row_marker, original_col_count + 3] = title
                    for img in column('img'):
                        if 'title' in img.attrs:
                            title = img['title']
                            if title in ['Normal', 'Elite', 'Epic']:
                                # Mission difficulty aka level
                                df.iat[row_marker, original_col_count + 4] = title
                df.iat[row_marker, column_marker] = data
                column_marker += 1
            if len(columns) > 0:
                row_marker += 1

        if 'From' in column_names:
            df.drop(['From', 'Units', 'Runs/Unit', 'Runs'], axis=1, inplace=True)

        if 'Cost/Unit' in column_names:
            df['Cost/Unit'] = df['Cost/Unit'].astype(float)

        return df


if __name__ == "__main__":
    soup = scrape_page('clothing pattern')

    parser = HTMLTableParser()
    tables = parser.parse_soup(soup)
    bad_tables = []
    for i in range(len(tables)):
        if 'Item' not in tables[i].columns:
            bad_tables.append(i)
    for i in sorted(bad_tables, reverse=True):
        del tables[i]

    results = {}

    for df in tables:
        rarity = df.at[0, 'Item'].count('★')
        df.sort_values(by='Cost/Unit', axis=0, inplace=True)
        df = df[DROP_TABLE_COLUMNS]
        results[rarity] = df

    for rarity in sorted(results.keys()):
        print(f'Rarity: {rarity}')
        print(results[rarity].to_string(max_colwidth=40))
        print()
