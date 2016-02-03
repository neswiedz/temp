##3_2_double_dice
##rzut dwoma kostkami, jesli wynik taki sam badz suma rowna 7 lub 11 to odpowiedni komunikat
import random
for x in range(1,11):
    throw_1 = random.randint(1,6)
    throw_2 = random.randint(1,6)
    total=throw_1 + throw_2
    print(total)
    if(total==7):
        print('wyrzucono 7')
    if(total==11):
        print('wyrzucono 11')
    if throw_1==throw_2:
        print('wyrzucono takie same liczby')
    if (total<4):
        print('pech')
    if(total>10):
        print('szczescie')
    else:
        print('mniej niz 10')

##rzuca do momentu wyrzucenia dwoch szostek
while True:
    throw_1=random.randint(1,6)
    throw_2=random.randint(1,6)
    total=throw_1 + throw_2
    print(total)
    if throw_1==6 and throw_2 ==6:
        break
print('wyrzucono dwie szustki')
        
book_name = 'tekst'
print(book_name + ' dodatkowy_tekst')
print(len(book_name))
numbers=[123,34,55,321,9]
numbers[1:3]
##[34,55] wyswietla o jeden mniej niz koncowy adres
numbers[0]
## 123
##sortowanie lancucha
numbers.sort()
##wyrzucenie jedengo z elementow lancucha drugiego
print('pierwotna lista')
for item in numbers:
    print(item)
numbers.pop(1)
print('lista po wyrzuceniu drugiego elementu')
for item in numbers:
    print(item)

