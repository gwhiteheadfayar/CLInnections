import requests
import re
import json
import curses
import random
from datetime import datetime

def fetch_daily_data():
    #parse the date for requested JSON format
    today = datetime.today().strftime('%Y-%m-%d')
    
    #connections URL that uses today's date
    url = f"https://www.nytimes.com/svc/connections/v2/{today}.json"
    
    try:
        response = requests.get(url) #request JSON data
        response.raise_for_status() #check for error during fetch
        #the JSON response from the API should be parsed directly, no need to do anything since it's already JSON
        game_data = response.json()
        return game_data
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch daily data: {str(e)}")
    except ValueError as e:
        raise Exception(f"Failed to parse JSON data: {str(e)}")

def initialize_game(data):
    categories = data['categories']
    words = [card['content'] for category in categories for card in category['cards']]
    random.shuffle(words)
    return categories, words
    
def remove_guessed_words(words, guessed_words):
    return [word for word in words if word not in guessed_words]

def display_game(stdscr, words, selected, correct_guesses, mistakes, current_index):
    stdscr.clear()
    height, width = stdscr.getmaxyx()

    title = "NYT Connections"
    stdscr.addstr(1, (width - len(title)) // 2, title, curses.A_BOLD)

    for i, word in enumerate(words):
        row = 3 + (i // 4) * 2
        col = (width - 60) // 2 + (i % 4) * 15
        
        if i in selected:
            stdscr.addstr(row, col, word.center(14), curses.A_REVERSE)
        elif i == current_index:
            stdscr.addstr(row, col, word.center(14), curses.A_BOLD)
        else:
            stdscr.addstr(row, col, word.center(14))

    for i, (title, guess, difficulty) in enumerate(correct_guesses):
        row = 12 + i
        color = {
            "yellow": curses.color_pair(1),
            "green": curses.color_pair(2),
            "blue": curses.color_pair(3),
            "purple": curses.color_pair(4),
        }[difficulty]
        stdscr.addstr(row, 2, f"Group {i+1}: {', '.join(guess)}", color)

    mistake_str = f"Mistakes: {'X' * mistakes}{' ' * (3 - mistakes)}"
    stdscr.addstr(height - 3, 2, mistake_str)

    instructions = [
        "Arrow keys: Move selection",
        "Space: Select/Deselect word",
        "Enter: Submit guess",
        "S: Shuffle words",
        "Q: Quit game"
    ]
    for i, instruction in enumerate(instructions):
        stdscr.addstr(height - 7 + i, width - 30, instruction)

    stdscr.refresh()


def handle_input(stdscr):
    key = stdscr.getch()

    if key in [ord('q'), ord('Q')]:
        return 'quit'
    elif key in [ord('s'), ord('S')]:
        return 'shuffle'
    elif key == ord(' '):
        return 'toggle_selection'
    elif key == 10:  #index for enter key
        return 'submit_guess'
    elif key == curses.KEY_UP:
        return 'move_up'
    elif key == curses.KEY_DOWN:
        return 'move_down'
    elif key == curses.KEY_LEFT:
        return 'move_left'
    elif key == curses.KEY_RIGHT:
        return 'move_right'
    else:
        return None

def get_selected_index(current_index, action, words):
    num_rows = (len(words) + 3) // 4 #get number of rows based on number of remaining words
    row = current_index // 4
    col = current_index % 4

    if action == 'move_up':
        row = max(0, row - 1)
    elif action == 'move_down':
        row = min(num_rows - 1, row + 1)
    elif action == 'move_left':
        col = max(0, col - 1)
    elif action == 'move_right':
        col = min(3, col + 1)

    new_index = row * 4 + col
    return min(new_index, len(words) - 1)

def check_guess(selected_words, categories):
    selected_set = set(selected_words)
    
    for i, category in enumerate(categories):
        category_words = set(card['content'] for card in category['cards'])
        if selected_set == category_words:
            difficulty = ["yellow", "green", "blue", "purple"][i]
            return category['title'], list(category_words), difficulty

    return None


def get_selected_words(words, selected_indices):
    return [words[i] for i in selected_indices]

def main(stdscr):
    curses.curs_set(0)
    stdscr.clear()

    #color pairs for each category
    curses.start_color()
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    
    try:
        data = fetch_daily_data()
        categories, words = initialize_game(data)
        
        selected = set()
        correct_guesses = []
        mistakes = 0
        current_index = 0

        while True:
            display_game(stdscr, words, selected, correct_guesses, mistakes, current_index)
            action = handle_input(stdscr)

            if action == 'quit':
                break
                
            elif action == 'shuffle':
                random.shuffle(words)
                
            elif action == 'toggle_selection':
                if current_index in selected:
                    selected.remove(current_index)
                else:
                    selected.add(current_index)

            elif action == 'submit_guess':
                result = check_guess([words[i] for i in selected], categories)
                
                if result:
                    title, guessed_words, difficulty = result
                    correct_guesses.append((title, guessed_words, difficulty))
                    words = remove_guessed_words(words, guessed_words)
                    selected.clear()
                    
                    if len(correct_guesses) == 4:
                        break
                else:
                    mistakes += 1
                    
                    if mistakes >= 4:
                        break
                    
            elif action in ['move_up', 'move_down', 'move_left', 'move_right']:
                current_index = get_selected_index(current_index, action, words)
            
        stdscr.clear()
        if len(correct_guesses) == 4:
            stdscr.addstr(10, 20, "Congratulations! You've completed the puzzle!")
        elif mistakes > 3:
            stdscr.addstr(10, 20, "Game Over. You've made 4 mistakes.")
        else:
            stdscr.addstr(10, 20, "Thanks for playing!")
        
        stdscr.refresh()
        stdscr.getch()

    except Exception as e:
        stdscr.clear()
        stdscr.addstr(10, 20, f"An error occurred: {str(e)}")
        stdscr.refresh()
        stdscr.getch()


if __name__ == "__main__":
    curses.wrapper(main)