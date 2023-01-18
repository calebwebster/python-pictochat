from utils.find_nth import find_nth


def find_num_lines(string, wrap_length, add_extra=False):
    """
    Return the number of lines a string will require when word wrapped
    to a certain length.

    :param str string: string to wrap
    :param int wrap_length: maximum length of each line
    :param bool add_extra: set to true to display long words on a new line.
    :return: number of lines the string will occupy once wrapped
    :rtype: int

    This function requires find_nth().
    """
    sp_num = 1  # Number of next space (used in find_nth())
    num_lines = 1  # Number of lines
    char_pos = 0  # Index of char in current line

    for x in range(len(string)):
        char = string[x]
        if char == " ":
            sp_num += 1
            next_sp = find_nth(" ", string, sp_num)
            if next_sp == -1:
                next_word = string[x + 1:]
            else:
                next_word = string[x + 1:next_sp]
            chars_left = (wrap_length - 1) - char_pos
            # If a word fits on one line, but there is not enough
            # space on the current line, start a new line.
            # If a word is too long for a line but add_extra == true,
            # start a new line.
            if len(next_word) > wrap_length and add_extra or wrap_length >= len(next_word) > chars_left:
                num_lines += 1
                char_pos = -1
        # If the current line is full and char is not the last
        # character, start a new line.
        elif char_pos == (wrap_length - 1) and x != len(string) - 1:
            num_lines += 1
            char_pos = -1
        char_pos += 1

    return num_lines


if __name__ == '__main__':
    # print(find_num_lines("Abominable Strawberry Government", 10))
    print(find_num_lines(
        "Guest 1: hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh5 6", 77, True))
