"""
Find Nth
2020
This function finds the nth occurence of an item inside an iterable.
Parameters: to_find, iterable, n
Return: index of nth occurence (integer)
"""


class ZerothOccurenceError(Exception):
    def __init__(self, msg="Cannot find 0th occurence of item in iterable. To find the first occurence, set n=1."):
        super().__init__(msg)


def find_nth(to_find, iterable, n=1):
    """
    Return the nth occurence of an item inside an iterable.
    If the item is not found, return -1.
    n cannot be 0.
    :param iterable: list, string, dict, etc. to search
    :param to_find: item to find
    :param n: number of occurence to return
    :return: index of nth occurence of item inside iterable
    """
    occurences = []
    try:
        for x in range(len(iterable)):
            if iterable[x:x + len(to_find)] == to_find:
                occurences.append(x)
    except TypeError:  # Thing to search must be iterable type
        raise TypeError(f"Cannot search {iterable}. Must be iterable data type.")
    if not isinstance(n, int):  # n must be an integer
        raise ValueError(f"Error while finding occurence. n must be an integer.")
    if n == 0:
        raise ZerothOccurenceError
    if n > len(occurences) or n < -len(occurences):
        return -1
    if n < 0:
        return occurences[n]
    return occurences[n - 1]


if __name__ == '__main__':
    string = """The mitochondria is the powerhouse of the cell."""
    assert find_nth('T', string, 1) == 0
    assert find_nth('e', string, 3) == 27
    assert find_nth('.', string, 1) == 46
    assert find_nth('invalid', string, 1) == -1
    assert find_nth('c', string, -1) == 42
    assert find_nth('c', string, 2) == 42
