import sys
import heapq
import random
from collections import deque, defaultdict
from graphviz import Graph
import os
import shutil
from colorama import Fore, Back, Style, init
from pyfiglet import Figlet

# Initialize colorama
init(autoreset=True)

# Add these helper functions
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_centered(text):
    cols, _ = shutil.get_terminal_size()
    print(text.center(cols))

def print_block(title, content, color=Fore.WHITE):
    cols, _ = shutil.get_terminal_size()
    block_width = min(60, cols - 5)

    # Ensure content is a list of lines
    if isinstance(content, str):
        content = content.split('\n')
    
    # Top border
    print(color + '╭' + '─' * (block_width-2) + '╮')
    
    # Title
    title_text = f" {title} "
    print(color + '│' + title_text.center(block_width-2, '·') + '│')
    
    # Content
    if isinstance(content, list):
        content = '\n'.join(content)
    for line in str(content).split('\n'):
        print(color + '│ ' + line.ljust(block_width-3) + '│')
    
    # Bottom border
    print(color + '╰' + '─' * (block_width-2) + '╯' + Style.RESET_ALL)

def print_header():
    clear_screen()
    cols, _ = shutil.get_terminal_size()
    f = Figlet(font='slant', width=cols)
    print(Fore.CYAN + f.renderText('Word Ladder'))
    print(Fore.YELLOW + "           ~ A Magical Word Transformation Game ~")
    print()

def print_success(message):
    print(Fore.GREEN + '✨ ' + message + ' ✨')

def print_error(message):
    print(Fore.RED + '⚠ ' + message)

def print_warning(message):
    print(Fore.YELLOW + '⚠ ' + message)

def load_dictionary(file_path):
    word_dict = defaultdict(set)
    with open(file_path, 'r') as f:
        for line in f:
            word = line.strip().lower()
            if word.isalpha():
                word_dict[len(word)].add(word)
    return word_dict

def get_neighbors(word, word_dict, banned_letters=None, banned_words=None):
    neighbors = []
    length = len(word)
    same_length_words = word_dict.get(length, set())
    banned_letters = banned_letters or set()
    banned_words = banned_words or set()
    
    for i in range(length):
        original_char = word[i]
        for c in 'abcdefghijklmnopqrstuvwxyz':
            if c == original_char or c in banned_letters:
                continue
            new_word = word[:i] + c + word[i+1:]
            if new_word in same_length_words and new_word not in banned_words:
                neighbors.append(new_word)
    return neighbors

def visualize_game_state(current_path,target_word, explored_nodes=None, algorithm_path=None, banned_letters=None):
    dot = Graph(engine='neato', format='png', strict=True)
    dot.attr(overlap='false', splines='true', layout='neato',
    label=f"Word Ladder: {current_path[0].upper()} → {target_word.upper()}\n\n",
             fontsize='20', labelloc='t')
    
    

    # Add player's path with target styling
    for i, word in enumerate(current_path):
        if word == target_word:
            dot.node(word, color='gold', style='filled', 
                    label=f"{word.upper()}\ng:{i}\nh:0", shape='doublecircle')
        else:
            color = 'green' if i == len(current_path)-1 else 'lightblue'
            dot.node(word, color=color, style='filled',
                    label=f"{word.upper()}\ng:{i}\nh:{sum(c1 != c2 for c1,c2 in zip(word, target_word))}")
        if i > 0:
            dot.edge(current_path[i-1], current_path[i])
    
    # Add AI-suggested path with cost labels
    if algorithm_path:
        for i in range(len(algorithm_path)-1):
            g = i
            h = sum(c1 != c2 for c1, c2 in zip(algorithm_path[i], algorithm_path[-1]))
            dot.node(algorithm_path[i], color='pink', style='filled',
                    label=f"{algorithm_path[i].upper()}\ng:{g}\nh:{h}\nf:{g+h}")
            dot.edge(algorithm_path[i], algorithm_path[i+1], color='red')
    
    # Add target node
    if current_path:
        target = current_path[-1]
        dot.node(target, color='gold', style='filled', 
                label=f"{target.upper()}\ng:{len(current_path)-1}\nh:0")
    
    # Highlight banned letters
    if banned_letters:
        nodes = set()
        for line in dot.body:
            if line.strip().startswith('node'):
                node_id = line.split('[')[0].strip().strip('"')
                nodes.add(node_id)
        
        for node in nodes:
            if any(c in banned_letters for c in node):
                dot.node(node, color='red', style='striped', fillcolor='red:yellow',
                       label=f"{node.upper()}\nBANNED", fontcolor='black')
    dot.render('word_ladder', view=True, cleanup=True)

def bfs(start, target, word_dict, banned_letters=None,move_limit=None):
    """Breadth-First Search with g(n) = depth"""
    if start == target:
        return [start], set()
    
    visited = set()
    queue = deque([[start]])
    visited.add(start)
    explored = set([start])
    
    while queue:
        path = queue.popleft()
        current_word = path[-1]
        
        # Check move limit
        if move_limit and (len(path)-1 > move_limit):
            continue

        for neighbor in get_neighbors(current_word, word_dict, banned_letters):
            explored.add(neighbor)
            if neighbor == target:
                return path + [neighbor], explored
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])
    return None, explored

def ucs(start, target, word_dict, banned_letters=None,move_limit=None):
    """Uniform Cost Search with g(n) = path cost"""
    if start == target:
        return [start], set()
    
    frontier = []
    heapq.heappush(frontier, (0, start, [start]))
    cost_so_far = {start: 0}
    explored = set()
    
    while frontier:
        current_cost, current_word, path = heapq.heappop(frontier)
        explored.add(current_word)

        # Check move limit
        if move_limit and (current_cost > move_limit):
            continue
        
        if current_word == target:
            return path, explored
        
        for neighbor in get_neighbors(current_word, word_dict, banned_letters):
            new_cost = current_cost + 1
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                heapq.heappush(frontier, (new_cost, neighbor, path + [neighbor]))
                explored.add(neighbor)
    
    return None, explored

def a_star(start, target, word_dict, banned_letters=None, move_limit=None):
    """A* Search with f(n) = g(n) + h(n)"""
    if start == target:
        return [start], set()
    
    def heuristic(word):
        return sum(c1 != c2 for c1, c2 in zip(word, target))
    
    frontier = []
    heapq.heappush(frontier, (0 + heuristic(start), 0, start, [start]))
    cost_so_far = {start: 0}
    explored = set()
    
    while frontier:
        f, g, current_word, path = heapq.heappop(frontier)
        explored.add(current_word)

        # Check move limit
        if move_limit and (g > move_limit):
            continue
        
        if current_word == target:
            return path, explored
        
        if g > cost_so_far.get(current_word, float('inf')):
            continue
        
        for neighbor in get_neighbors(current_word, word_dict, banned_letters):
            new_g = g + 1
            if neighbor not in cost_so_far or new_g < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_g
                new_f = new_g + heuristic(neighbor)
                heapq.heappush(frontier, (new_f, new_g, neighbor, path + [neighbor]))
                explored.add(neighbor)
    
    return None, explored

def main():
    try:
        word_dict = load_dictionary('words.txt')
    except FileNotFoundError:
        print_error("Dictionary file 'words.txt' not found.")
        return

    challenges = {
        'beginner': {'length': 3, 'banned_letters': set(),'banned_words': set(), 'moves': 6},
        'advanced': {'length': 5, 'banned_letters': set(),'banned_words': set(), 'moves': 10},
        'challenge': {'length': 5, 'banned_letters': {'a'},'banned_words': {'apple', 'grape'}, 'moves': 12}
    }

    while True:
        print_header()
        print_block("Game Modes", [
            Fore.CYAN + "1. Beginner Mode   " + Fore.WHITE + "(3 letters)                           ",
            Fore.CYAN + "2. Advanced Mode   " + Fore.WHITE + "(5 letters)                           ",
            Fore.CYAN + "3. Challenge Mode  " + Fore.WHITE + "(5 letters, special restrictions)     ",
            "\n" + Fore.MAGENTA + "Press Q to quit                                          "
        ], Fore.BLUE)

        mode = input(Fore.YELLOW + "\n  Enter your choice (1-3): ").strip().lower()
        
        if mode == 'q':
            print_centered(Fore.RED + "Thanks for playing! Goodbye! 👋\n\n\n")
            return

        mode_config = {
            '1': 'beginner',
            '2': 'advanced',
            '3': 'challenge'
        }.get(mode)

        if not mode_config:
            print_error("Invalid choice! Please select 1-3")
            input(Fore.YELLOW + "Press Enter to continue...")
            continue

        config = challenges[mode_config]
        length = config['length']
        banned_letters = config['banned_letters']
        banned_words = config['banned_words']
        
        # Filter valid words
        possible_words = word_dict.get(length, set())
        valid_words = [word for word in possible_words 
            if (not any(c in banned_letters for c in word) 
                and (word not in banned_words))]
        
        # Find valid word pair
        start, target = None, None
        for _ in range(100):
            start = random.choice(valid_words)
            target = random.choice(valid_words)
            if start != target:
                solution, _ = bfs(start, target, word_dict, banned_letters)
                if solution:
                    break
        else:
            print_error("Couldn't find valid word pair")
            return

        current = start.lower()
        path = [current]
        steps = 0
        score = 0
        num_incorrect = 0

        
        visualize_game_state(path,target, banned_letters=banned_letters)

        while steps < config['moves']:
            
            
            # Game status block
            status = [
                f"{Fore.CYAN}Current Word: {Fore.WHITE}{current.upper()}       \t\t",
                f"{Fore.CYAN}Target Word:  {Fore.WHITE}{target.upper()}       \t\t",
                f"{Fore.YELLOW}Moves Left:   {Fore.WHITE}{config['moves'] - steps}          \t\t",
                f"{Fore.GREEN}Current Score: {Fore.WHITE}{score}"
            ]
            
            if banned_letters:
                status.append(f"{Fore.RED}Banned Letters: {', '.join(banned_letters).upper()}       \t")
            if banned_words:
                status.append(f"{Fore.RED}Banned Words:   {', '.join(w.upper() for w in banned_words)}    \t")
            
            print_block("Game Status", status, Fore.BLUE)
            
            # Path visualization
            path_display = ' → '.join([
                (Fore.GREEN + word.upper() + Fore.WHITE) if word == current 
                else (Fore.YELLOW + word.upper() + Fore.WHITE) 
                for word in path
            ])
            print_block("Transformation Path", path_display, Fore.GREEN)
            
            # Actions block
            print_block("Available Actions", [
                Fore.CYAN + "1. Make a move  \t",
                Fore.CYAN + "2. Get AI hint  \t",
                Fore.CYAN + "3. Quit game    \t",
                Fore.MAGENTA + "\t\nEnter your choice (1-3):"
            ], Fore.BLUE)

            choice = input(Fore.YELLOW + "  Your choice: ").strip().lower()

            if choice == '1':
                next_word = input(Fore.YELLOW + "  Enter next word: ").strip().lower()
                error = None
                
                # Validation checks
                if next_word == current:
                    error = "Same word! Try again."
                elif len(next_word) != len(current):
                    error = f"Must be {len(current)} letters!"
                else:
                    diff = sum(1 for a, b in zip(current, next_word) if a != b)
                    if diff != 1:
                        error = "Change exactly one letter!"
                    elif next_word not in word_dict[len(next_word)]:
                        error = "Invalid dictionary word!"
                    elif any(c in banned_letters for c in next_word):
                        error = "Contains banned letters!"
                    elif next_word in banned_words:
                        error = "This word is banned!"
                
                if error:
                    print_error(error)
                    num_incorrect +=1
                    score -=3
                    input(Fore.YELLOW + "Press Enter to continue...")
                    continue
                else:
                    # Update game state
                    current = next_word
                    path.append(current)
                    steps +=1
                    score +=10
                    
                    visualize_game_state(path, target, banned_letters=banned_letters)
                    
                    if current == target.lower():
                        
                        print_success(f"Success in {steps} steps!")
                        optimal_path, _ = bfs(start, target, word_dict, banned_letters)
                        move_limit = config['moves']
                        if steps < move_limit:
                            multiplier = 1 + (move_limit - steps) * 0.5
                        else:
                            multiplier = 1.0
                        total_score = score * multiplier
                        score_details = [
                            f"Correct Guesses: {steps} x 10 = {steps * 10}",
                            f"Incorrect Guesses: {num_incorrect} x (-3) = {num_incorrect * -3}",
                            f"Subtotal: {score}",
                            f"Multiplier (for {steps} moves vs {move_limit} limit): {multiplier}x",
                            f"Total Score: {total_score:.1f}"
                        ]
                        if optimal_path:
                            optimal_steps = len(optimal_path) - 1
                            print_block("Optimal Path", 
                                       f"{' → '.join(w.upper() for w in optimal_path)}\n"
                                       f"Optimal Steps: {optimal_steps}", 
                                       Fore.GREEN)
                        print_block("Scoring Details", score_details, Fore.GREEN)
                        input(Fore.YELLOW + "Press Enter to continue...")
                        break

            elif choice == '2':
                
                print_block("AI Algorithms", [
                    Fore.CYAN + "1. Breadth-First Search (BFS)   \t",
                    Fore.CYAN + "2. Uniform Cost Search (UCS)    \t",
                    Fore.CYAN + "3. A* Search    \t"
                ], Fore.BLUE)
                
                algo = input(Fore.YELLOW + "  Select algorithm (1-3): ").strip()
                solvers = {'1': bfs, '2': ucs, '3': a_star}
                solver = solvers.get(algo)
                
                if solver:
                    # In main game loop when calling solvers:
                    solution, explored = solver(current, target, word_dict, banned_letters, 
                           move_limit=config['moves'])
                    if solution:
                        
                        path_details = [
                            f"{word.upper()} (g:{step}, h:{sum(c1 != c2 for c1,c2 in zip(word, target))})"
                            for step, word in enumerate(solution)
                        ]
                        print_block(f"{solver.__name__.upper()} Solution",
                                   " → ".join(path_details), Fore.GREEN)
                        visualize_game_state(path, target, 
                                           algorithm_path=solution,
                                           banned_letters=banned_letters)
                    else:
                        print_error("No path found!")
                    input(Fore.YELLOW + "Press Enter to continue...")
                else:
                    print_error("Invalid algorithm choice!")
                    input(Fore.YELLOW + "Press Enter to continue...")

            elif choice == '3':
                print_centered(Fore.RED + "Thanks for playing! Goodbye! 👋")
                return

            else:
                print_error("Invalid choice! Please select 1-3")
                input(Fore.YELLOW + "Press Enter to continue...")

        # Game over handling
        if current != target.lower():
            
            print_block("Game Over", [
                Fore.RED + "Time's up!",
                f"{Fore.CYAN}Final Word: {Fore.WHITE}{current.upper()}",
                f"{Fore.CYAN}Target Was: {Fore.WHITE}{target.upper()}",
                f"{Fore.RED}Final Score: {score}"
            ], Fore.RED)
            input(Fore.YELLOW + "\nPress Enter to return to main menu...")

if __name__ == "__main__":
    main()
