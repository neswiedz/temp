## posiada ograniczenie po zgadniecie pierwszej litery traktuje jak zgadniecei calego wyrazu
import random

lives_remaining = 14
guessed_letters = ''
words = ['kurczak', 'pies', 'kot', 'mysz', 'zyrafa']

def play():
    word = pick_a_word()
    print(word)
    while True:
        guess = get_guess(word)
        if process_guess(guess, word):
            print('Wygrales, gratulacje!')
            break
        if lives_remaining == 0:
            print('Przegrales!!!')
            print('Zgadywane slowo to: ' + word)
            break

def pick_a_word():
    word_position = random.randint(0,len(words)-1)
    return words[word_position]

def get_guess(word):
    print_word_with_blanks(word)
    print('Pozostalo prob: ' + str(lives_remaining))
    guess = input(' Odgadujesz litere lub cale slowo?')
    return guess

def print_word_with_blanks(word):
    display_word = ''
    for letter in word:
        if guessed_letters.find(letter) > -1:
            # litera znaleziona
            display_word = display_word + letter
        else:
            # litera nie znaleziona
            display_word = display_word + '-'
    print(display_word)

def process_guess(guess, word):
    if len(guess) > 1:
        return whole_word_guess(guess, word)
    else:
        return single_letter_guess(guess, word)

def whole_word_guess(guess, word):
    global lives_remaining
    if guess.lower() == word.lower():
        return True
    else:
        lives_remaining = lives_remaining - 1
        return False
    
def single_letter_guess(guess, word):
    global lives_remaining
    global guessed_letters
    if word.find(guess) == -1:
        #odgadniecie literyt nieprawidlowe
        lives_remaining = lives_remaining - 1
    guessed_letters = guessed_letters + guess
    if all_letters_guessed(word):
        return True
    return False

def all_letters_guessed(word):
    for letter in word:
        if guessed_letters.find(letter) == -1:
            return False
        return True

play()
