# run with
#  ~/Workspaces/BGG statistics$ pipenv run python main.py
#
# install new modules with
#  ~/Workspaces/BGG statistics$ pipenv install matplotlib

import requests
import xml.etree.ElementTree as ET
import datetime
import os.path
import matplotlib.pyplot as plt


def get_xml_page(page_number):
    url = 'https://boardgamegeek.com/xmlapi2/plays?username=yzemaze&page='
    url = url + str(page_number)
    response = requests.get(url, timeout=10)
    return response.text


def write_to_file(str_content, file_name):
    local_file = open(file_name, "w")
    local_file.write(str_content)
    local_file.close()


def create_file_name(index):
    return f'Plays_{index:0>4}.xml'


def get_and_write_xml(index):
    file_content = get_xml_page(index)
    if file_content.count('<play id') > 0:
        file_name = create_file_name(index)
        write_to_file(file_content, file_name)
        print(file_name + " was written")
        return True
    else:
        return False


def update_xml_files_from_web():
    for i in range(1, 100):
        success = get_and_write_xml(i)
        if not success:
            return


def does_xml_exist(index):
    file_name = create_file_name(index)
    return os.path.exists(file_name) and os.path.isfile(file_name)


def read_xml_files():
    for i in range(1, 100):
        success = does_xml_exist(i)
        if not success:
            return i
    return 99


def date_from_str(date):
    y, m, d = [int(x) for x in date.split('-')]
    return datetime.datetime(y, m, d)


def get_date_list_since(start):
    end = datetime.datetime.today()
    delta = end - start
    date_list = []
    for x in range(delta.days):
        date_list.append(start + datetime.timedelta(days=x))
    return date_list


class Play:

    def __init__(self, date, name):
        self.date = date
        self.name = name


def add_xml_to_plays(index, plays):
    file_name = f'Plays_{index:0>4}.xml'
    tree = ET.parse(file_name)
    root = tree.getroot()

    for child in root:
        for i in range(int(child.attrib['quantity'])):
            name = child[0].attrib['name']
            date = child.attrib['date']
            plays.append(Play(date, name))


def count_per_game_from_plays(plays):
    count_per_game = dict()
    for play in plays:
        count_per_game.update(
            {play.name: count_per_game.get(play.name, 0) + 1})
    return count_per_game


def read_plays():
    number_of_xml_files = read_xml_files()
    plays = list()
    for i in range(1, number_of_xml_files):
        add_xml_to_plays(i, plays)
    return plays


def get_first_play_date(plays):
    first_date = datetime.datetime.today()
    for play in plays:
        if date_from_str(play.date) < first_date:
            first_date = date_from_str(play.date)
    return first_date


def count_per_game_from_plays_since(plays, date):
    count_per_game = dict()
    for play in plays:
        if (date_from_str(play.date) <= date):
            count_per_game.update(
                {play.name: count_per_game.get(play.name, 0) + 1})
    return count_per_game


def print_counts(count_per_game, amount):
    count_per_game_list = list(count_per_game.items())
    count_per_game_list.sort(key=lambda x: (x[0]))
    count_per_game_list.sort(key=lambda x: (x[1]), reverse=True)
    print_amount = amount
    if print_amount == 0:
        print_amount = len(count_per_game_list)
    else:
        print_amount = min(print_amount, len(count_per_game_list))
    for index in range(print_amount):
        entry = count_per_game_list[index]
        print(f'{index+1}\t{entry[1]}\t{entry[0]}')


def calc_total_plays(count_per_game):
    total_plays = 0
    for game in count_per_game:
        total_plays += count_per_game[game]
    return total_plays


def calc_h_index(count_per_game):
    counts = list(count_per_game.values())
    counts.sort(reverse=True)
    h = 0
    for count in counts:
        if count <= h:
            return h
        h += 1
    return h


def calc_count_more_than(count_per_game, threshold):
    total_count = 0
    for count in count_per_game.values():
        if count >= threshold:
            total_count += 1
    return total_count


def plot_counts_and_games_and_h():
    plays = read_plays()
    dates_for_plot = get_date_list_since(get_first_play_date(plays))
    total_plays_for_plot = []
    distinct_games_for_plot = []
    h_indices_for_plot = []
    for date in dates_for_plot:
        # Calculate counts per game for this date.
        # Could be done incrementally instead of from scratch every time.
        count_per_game = count_per_game_from_plays_since(plays, date)
        # Calculate total plays for this date.
        total_plays_for_plot.append(calc_total_plays(count_per_game))
        # Calculate distinct games played for this date.
        distinct_games_for_plot.append(len(count_per_game))
        # Calculate h index for this date.
        h_indices_for_plot.append(calc_h_index(count_per_game))

    fig, ax_1 = plt.subplots()

    color = 'tab:red'
    ax_1.set_xlabel('time')
    ax_1.set_ylabel('h index', color=color)
    ax_1.plot(dates_for_plot, h_indices_for_plot, color=color)
    ax_1.tick_params(axis='y', labelcolor=color)

    ax_2 = ax_1.twinx()
    color = 'tab:blue'
    ax_2.set_ylabel('games/plays played', color=color)
    ax_2.plot(dates_for_plot, total_plays_for_plot, color=color)
    ax_2.plot(dates_for_plot, distinct_games_for_plot, color='tab:green')
    ax_2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()
    plt.title('BGG history')
    plt.show()


def get_h_games(count_per_game, h):
    h_games = []
    for game in count_per_game:
        if (count_per_game[game] >= h):
            h_games.append(game)
    return h_games


def print_h_index_history():
    plays = read_plays()
    max_h = 0
    for date in get_date_list_since(get_first_play_date(plays)):
        # Calculate counts per game for this date.
        # Could be done incrementally instead of from scratch every time.
        count_per_game = count_per_game_from_plays_since(plays, date)
        # Calculate h index for this date.
        h = calc_h_index(count_per_game)
        if (h > max_h):
            max_h = h
            h_games = sorted(get_h_games(count_per_game, h))
            print(f'{date.strftime("%Y-%m-%d")}, H: {h}, {len(h_games)} games: {h_games}')


def print_specific_stats(name_part):
    count_per_game = count_per_game_from_plays(read_plays())
    count_per_game_list = list(count_per_game.items())
    count_per_game_list.sort(key=lambda x: (x[0]))
    count_per_game_list.sort(key=lambda x: (x[1]), reverse=True)
    for index in range(len(count_per_game_list)):
        entry = count_per_game_list[index]
        if name_part.lower() in entry[0].lower():
            print(f'{index + 1}\t{entry[1]}\t{entry[0]}')


def print_stats():
    plays = read_plays()
    count_per_game = count_per_game_from_plays(plays)
    print(f'Current H index: {calc_h_index(count_per_game)}')
    dime_count = calc_count_more_than(count_per_game, 10)
    print(f'Current # dimes: {dime_count}')
    print(f'Current # fives: {calc_count_more_than(count_per_game, 5)}')
    print_counts(count_per_game, dime_count)


def get_bool_input(question):
    input_text = question + ' (Y/y) for yes. --> '
    answer = input(input_text)
    return answer.lower() == 'y'


def get_string_input(question):
    input_text = question + ' --> '
    return input(input_text)


def main():
    if get_bool_input('Update play history?'):
        update_xml_files_from_web()
        plays = read_plays()
        print(f'Found {len(plays)} plays.')

    if get_bool_input('Plot graphs?'):
        plot_counts_and_games_and_h()

    if get_bool_input('Print H-index history?'):
        print_h_index_history()

    if get_bool_input('Print stats?'):
        print_stats()

    while get_bool_input('Print specific stat?'):
        print_specific_stats(get_string_input('Game name?'))


if __name__ == "__main__":
    main()
