
class ZerothOccurenceError(Exception):
    def __init__(self, msg="Cannot find 0th occurence of item in iterable. To find the first occurence, set n=1."):
        super().__init__(msg)


def find_nth(to_find, iterable, n=1):
    occurences = []
    try:
        for x in range(len(iterable)):
            if iterable[x:x + len(to_find)] == to_find:
                occurences.append(x)
    except TypeError:  # Thing to search must be iterable type
        raise TypeError(
            f"Cannot search {iterable}. Must be iterable data type.")
    if not isinstance(n, int):  # n must be an integer
        raise ValueError(
            f"Error while finding occurence. n must be an integer.")
    if n == 0:
        raise ZerothOccurenceError
    if n > len(occurences) or n < -len(occurences):
        return -1
    if n < 0:
        return occurences[n]
    return occurences[n - 1]
