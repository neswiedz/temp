def stats(numbers):
    numbers.sort()
    return (numbers[0],numbers[-1])
## [0] - pierwszy element listy, [-1] - ostatni element, [-2]- przedostatnie element...

list=[5,45,12,1,78]
min, max = stats(list)
print(min)
print(max)
