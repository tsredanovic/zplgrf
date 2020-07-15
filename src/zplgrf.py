import base64
import re

import zlib
from PIL import Image

"""
Data compression scheme recognized by the Zebra printer.
A comma (,) fills the line, to the right, with zeros (0) until the specified line byte is filled.
An exclamation mark (!) fills the line, to the right, with ones (1) until the specified line byte is filled.
A colon (:) denotes repetition of the previous line.
"""
repeat_values = [',', '!', ':']

"""
Data compression scheme recognized by the Zebra printer.
The following represent the repeat counts on a subsequent Hexadecimal value.
Sending M6 to the printer is identical to sending the following hexadecimal data: 6666666.
Several repeat values can be used together to achieve any value desired. vMB or MvB will send 327 hexadecimal B’s to the printer.
"""
repeat_counts = {
    'G': 1,
    'H': 2,
    'I': 3,
    'J': 4,
    'K': 5,
    'L': 6,
    'M': 7,
    'N': 8,
    'O': 9,
    'P': 10,
    'Q': 11,
    'R': 12,
    'S': 13,
    'T': 14,
    'U': 15,
    'V': 16,
    'W': 17,
    'X': 18,
    'Y': 19,
    'g': 20,
    'h': 40,
    'i': 60,
    'j': 80,
    'k': 100,
    'l': 120,
    'm': 140,
    'n': 160,
    'o': 180,
    'p': 200,
    'q': 220,
    'r': 240,
    's': 260,
    't': 280,
    'u': 300,
    'v': 320,
    'w': 340,
    'x': 360,
    'y': 380,
    'z': 400,
}

"""
Reversed repeat_counts.
"""
counts_repeat = dict([(value, key) for key, value in repeat_counts.items()])

"""
List of valid hexadecimal characters.
"""
hex_chars = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']

"""
PIL colors.
"""
color_black = (0, 0, 0, 255)
color_white = (255, 255, 255, 255)


def size_byte_to_bit(byte_size):
    """
    Calculates size in bits from size in bytes (1 byte = 8 bits).

    :param byte_size: size in bytes
    :return: size in bits
    """
    return byte_size * 8


def size_bit_to_byte(bit_size):
    """
    Calculates size in bytes from size in bits (1 byte = 8 bits).

    :param bit_size: size in bits
    :return: size in bytes
    """
    return int(bit_size / 8)


def size_byte_to_char(byte_size):
    """
    Calculates size in chars from size in bytes (1 byte = 2 chars).

    :param byte_size: size in bytes
    :return: size in chars
    """
    return byte_size * 2


def find_commands(zpl, cmd_start, cmd_end='^'):
    """
        Finds (start, end) indexes of all defined commands inside zpl code.

        :param zpl: zpl code (string)
        :return: (start, end) indexes of all defined commands inside zpl code
        """
    cmd_start = '\{}'.format(cmd_start) if cmd_start.startswith('^') else cmd_start
    cmd_end = '\{}'.format(cmd_end) if cmd_end.startswith('^') else cmd_end
    starts = sorted([match.start() for match in re.finditer(cmd_start, zpl)])
    possible_ends = sorted([match.start() for match in re.finditer(cmd_end, zpl)])
    cmds_indexes = []
    for start in starts:
        for possible_end in possible_ends:
            if possible_end > start:
                cmds_indexes.append((start, possible_end))
                break
    return cmds_indexes


def extract_command(zpl, index):
    """
    Extracts command based on (start, end) inside zpl code.

    :param zpl: zpl code (string)
    :param index: (start, end) index of command
    :return: extracted command
    """
    return zpl[index[0]:index[1]]


def extract_commands(zpl, indexes):
    """
    Extracts all commands based on (start, end) inside zpl code.

    :param zpl: zpl code (string)
    :param indexes: (start, end) indexes of commands
    :return: extracted commands
    """
    cmds = []
    for start_stop_index in indexes:
        cmds.append(zpl[start_stop_index[0]:start_stop_index[1]])
    return cmds


def write_zpl(dg_cmd, upper_lext_x=0, upper_left_y=0, magnify_x=1, magnify_y=1):
    """
    Generates zpl code with ~DG command
    
    :param dg_cmd: ~DG command
    :param upper_lext_x: upper left x-axis location (in dots)
    :param upper_left_y: upper left y-axis location (in dots)
    :param magnify_x: magnification factor on the x-axis
    :param magnify_y: magnification factor on the y-axis
    :return: zpl code
    """""
    device, image_name, extension, bytes_total, bytes_per_row, data = break_dg_command(dg_cmd)
    xg_cmd = '^XG{}{}{},{},{}'.format(device, image_name, extension, magnify_x, magnify_y)
    fo_cmd = '^FO{},{}{}^FS'.format(upper_lext_x, upper_left_y, xg_cmd)
    return '{}^XA{}^XZ'.format(dg_cmd, fo_cmd)


def break_dg_command(dg_cmd):
    """
    Extracts ~DG command parameters:
        dox,t,w,data
        d - device to store image (optional, default is `R:`)
        o - image name
        x - extension (optional, always is `.GRF`)
        t - total number of bytes in graphic
        w - number of bytes per row
        data - ASCII hexadecimal string defining image (possibly compressed)

    :param dg_cmd: ~DG command (string)
    :return: device, image_name, extension, bytes_total, bytes_per_row, data from ~DG command
    """
    dg_cmd_parts = dg_cmd[3:].split(",", 3)
    dox = dg_cmd_parts[0]
    dox_parts = dox.split('.')
    if ':' not in dox_parts[0]:
        device = 'R:'
        image_name = dox_parts[0]
    else:
        do_parts = dox_parts[0].split(':')
        device = do_parts[0] + ':'
        image_name = do_parts[1]
    extension = '.GRF'

    bytes_total = int(dg_cmd_parts[1])
    bytes_per_row = int(dg_cmd_parts[2])
    data = dg_cmd_parts[3]

    return device, image_name, extension, bytes_total, bytes_per_row, data


def break_gf_command(gf_cmd):
    """
    Extracts ^GF command parameters:
        a,b,c,d,data
        a - compression type
            = A - ASCII hexadecimal
            = B - binary
            = C - compressed binary
        b - binary byte count
        c - graphic field count
        d - bytes per row
        data - ASCII hexadecimal string defining image (possibly compressed)

    :param gf_cmd: ^GF command (string)
    :return: compression_type, binary_byte_count, graphic_field_count, bytes_per_row, data from ^GF command
    """
    gf_cmd_parts = gf_cmd[3:].split(",", 4)
    compression_type = gf_cmd_parts[0]
    binary_byte_count = int(gf_cmd_parts[1])
    graphic_field_count = int(gf_cmd_parts[2])
    bytes_per_row = int(gf_cmd_parts[3])
    data = gf_cmd_parts[4]

    return compression_type, binary_byte_count, graphic_field_count, bytes_per_row, data


def break_fd_command(fd_cmd):
    """
    Extracts ^FD command parameters:
        a - data string

    :param fd_cmd: ^FD command (string)
    :return: data from ^FD command
    """
    data = fd_cmd[3:]
    return data


def break_lh_command(lh_cmd):
    """
    Extracts ^LH command parameters:
        x - x-axis position (in pixels)
        y - y-axis position (in pixels)

    :param lh_cmd: ^LH command (string)
    :return: x, y from ^LH command
    """
    x_y = lh_cmd[3:].split(',')
    return int(x_y[0]), int(x_y[1])


def break_ft_command(ft_cmd):
    """
    Extracts ^FT command parameters:
        x - x-axis position (in pixels)
        y - y-axis position (in pixels)

    :param ft_cmd: ^FT command (string)
    :return: x, y from ^FT command
    """
    x_y = ft_cmd[3:].split(',')
    return int(x_y[0]), int(x_y[1])


def break_aat_command(aat_cmd):
    """
    Extracts ^A@ command parameters:
        x - x-axis position (in pixels)
        y - y-axis position (in pixels)

    :param aat_cmd: ^A@ command (string)
    :return: field_orientation, char_height, width, font_drive, font_name from ^A@ command
    """
    parts = aat_cmd[3:].split(',')
    field_orientation = parts[0]
    char_height = int(parts[1])
    width = int(parts[2])
    font = parts[3]
    font_drive = 'R:'
    if ':' in font:
        font_drive = '{}:'.format(font.split(':')[0])
        font_name = font.split(':')[1]
    else:
        font_name = font
    return field_orientation, char_height, width, font_drive, font_name


def build_dg_command(bytes_total, bytes_per_row, data, image_name, extension='.GRF', device='R:'):
    """
    Generates ~DG command from parameters:
        dox,t,w,data
        d - device to store image (optional, default is `R:`)
        o - image name
        x - extension (optional, always is `.GRF`)
        t - total number of bytes in graphic
        w - number of bytes per row
        data - ASCII hexadecimal string defining image (possibly compressed)

    :param bytes_total: total number of bytes in graphic
    :param bytes_per_row: number of bytes per row
    :param data: ASCII hexadecimal string defining image
    :param image_name: image name
    :param extension: extension (optional, always is `.GRF`)
    :param device: device to store image (optional, default is `R:`)
    :return: ~DG command (string)
    """
    return '~DG{}{}{},{},{},{}'.format(device, image_name, extension, bytes_total, bytes_per_row, data)


def clean(data):
    """
    Removes new lines, carriage returns and tabs from data.

    :param data: ~DG command data
    :return: cleaned ~DG command data
    """
    return data.replace('\n', '').replace('\r', '').replace('\t', '')


def check_for_compression(data):
    """
    Checks if any repetition specific character is in data.

    :param data: ~DG command data
    :return: is ~DG command data compressed or not
    """
    compression_chars = repeat_values + list(repeat_counts.keys())
    for data_char in data:
        if data_char in compression_chars:
            return True
    return False


def check_for_z64_compression(data):
    """
    Checks if data starts with :Z64:.

    :param data: ^GF command data
    :return: is ^GF command data compressed or not
    """
    if data.startswith(':Z64:'):
        return True
    return False


def decompress(data, bytes_per_row):
    """
    Decompresses ~DG command data:
        Values from `repeat_counts` represent the repeat counts on a subsequent hexadecimal value.
        Several repeat values can be used together to achieve any value desired. vMB or MvB will result in 327 hexadecimal B.
        A comma (,) fills the line, to the right, with zeros (0) until the specified line byte is filled.
        An exclamation mark (!) fills the line, to the right, with ones (1) until the specified line byte is filled.
        A colon (:) denotes repetition of the previous line.

    :param data: compressed ~DG command data
    :param bytes_per_row: row width (in bytes) for ~DG command data
    :return: decompressed ~DG command data
    """
    chars_per_row = size_byte_to_char(bytes_per_row)

    lines = []
    current_line = ''
    current_repeats = 0
    for char_i, char in enumerate(data):
        # process repeat value character
        if char in repeat_values:
            if char == ',':
                fill_0_count = chars_per_row - len(current_line)
                current_line = current_line + fill_0_count * '0'
            elif char == '!':
                fill_F_count = chars_per_row - len(current_line)
                current_line = current_line + fill_F_count * 'F'
            elif char == ':':
                current_line = lines[-1]

        # precess repeat count character
        elif char in list(repeat_counts.keys()):
            current_repeats += repeat_counts[char]

        # process hex character
        elif char in hex_chars:
            current_repeats = current_repeats if current_repeats > 0 else 1
            current_line = current_line + current_repeats * char
            current_repeats = 0

        if len(current_line) >= chars_per_row:
            lines.append(current_line[:chars_per_row])
            current_line = current_line[chars_per_row:]

    return ''.join(lines)


def decompress_z64(data):
    """
    Decompresses ^GF command data:
        `:Z64:` is removed from the start, CRC (error detection code) is removed from the end.
        Remaining data is base64 decoded.
        Decoded data is decompressed with zlib.

    :param data: compressed ^GF command data
    :return: decompressed ^GF command data
    """
    base64_encoded_data = data.split(':')[2]
    decoded_data = base64.b64decode(base64_encoded_data)
    decompressed_data = zlib.decompress(decoded_data)
    return decompressed_data.hex().upper()


def substrings_of_same_consecutive_chars(string):
    """
    Breaks string into a list of substrings of same consecutive characters.

    :param string: string
    :return: list of substrings of same consecutive characters
    """
    substrings = []
    substring = []
    for char_i in range(len(string)):
        char = string[char_i]
        if char_i == 0:
            substring = [char]
            continue
        previous_char = string[char_i - 1]
        if char == previous_char:
            substring.append(char)
        else:
            substrings.append(''.join(substring))
            substring = [char]
    substrings.append(''.join(substring))
    return substrings


def compress(data, bytes_per_row):
    """
    Compresses ~DG command data:
        Values from `repeat_counts` represent the repeat counts on a subsequent hexadecimal value.
        Several repeat values can be used together to achieve any value desired. vMB or MvB will result in 327 hexadecimal B.
        A comma (,) fills the line, to the right, with zeros (0) until the specified line byte is filled.
        An exclamation mark (!) fills the line, to the right, with ones (1) until the specified line byte is filled.
        A colon (:) denotes repetition of the previous line.

    :param data: decompressed ~DG command data
    :param bytes_per_row: row width (in bytes) for ~DG command data
    :return: compressed ~DG command data
    """
    chars_per_row = size_byte_to_char(bytes_per_row)
    lines = [data[i:i + chars_per_row] for i in range(0, len(data), chars_per_row)]

    repeats_values = sorted(list(repeat_counts.values()), reverse=True)

    compressed_lines = []
    for line_i in range(len(lines)):
        line = lines[line_i]

        # check if current line is the same as previous line
        if line_i != 0:
            if line == lines[line_i-1]:
                compressed_lines.append(':')
                continue

        # break string into a list of substrings of same consecutive characters
        sublines = substrings_of_same_consecutive_chars(line)

        # check if current line is full of either F or 0
        if len(sublines) == 1:
            if line[0] == '0':
                compressed_lines.append(',')
            elif line[0] == 'F':
                compressed_lines.append('!')
            continue

        # compress sublines
        compressed_sublines = []
        for subline_i in range(len(sublines)):
            subline = sublines[subline_i]

            if subline_i == len(sublines) - 1:
                if subline[0] == '0':
                    compressed_sublines.append(',')
                elif subline[0] == 'F':
                    compressed_sublines.append('!')
                continue

            subline_len = len(subline)
            highest_repeats = []
            while subline_len > 0:
                for repeats_value in repeats_values:
                    if repeats_value <= subline_len:
                        highest_repeats.append(counts_repeat[repeats_value])
                        subline_len -= repeats_value
            compressed_subline = '{}{}'.format(''.join(highest_repeats), subline[0])
            compressed_sublines.append(compressed_subline)

        compressed_line = ''.join(compressed_sublines)

        compressed_lines.append(compressed_line)

    return ''.join(compressed_lines)


def hex_char_to_bits(hex_char):
    """
    Turns a valid hexadecimal character to a string of 4 bits.

    :param hex_char: hexadecimal character
    :return: string of 4 bits
    """
    return bin(int(hex_char, 16))[2:].zfill(4)


def bits_to_hex_char(bits):
    """
    Turns a string of 4 bits to a valid hexadecimal character.

    :param bits: string of 4 bits
    :return: hexadecimal character
    """
    return hex(int(bits, 2))[2:].upper()


def chars_to_bits(data):
    """
    Turns a string of hexadecimal characters to a string of bits.

    :param data: string of hexadecimal characters
    :return: string of bits
    """
    data_bits = ''
    for hex_char in data:
        data_bits += hex_char_to_bits(hex_char)
    return data_bits


def bits_to_chars(data_bits):
    """
    Turns a string of bits to a string of hexadecimal characters.

    :param data_bits: string of bits
    :return: string of hexadecimal characters
    """
    data = []
    four_bits = []
    for bit in data_bits:
        four_bits.append(bit)
        if len(four_bits) % 4 == 0:
            data.append(bits_to_hex_char(''.join(four_bits)))
            four_bits = []
    return ''.join(data)


def bits_to_image(bits_total, bits_per_row, bits):
    """
    Generates a PIL image from bits.

    :param bits_total: total number of bits
    :param bits_per_row: number of bits per row
    :param bits: bits to generate image from
    :return: PIL image
    """
    height = int((bits_total / bits_per_row))

    image = Image.new("RGBA", (bits_per_row, height), color_white)
    pixels = image.load()

    for y in range(height):
        for x in range(bits_per_row):
            i = y * bits_per_row + x
            current_color = color_black if bits[i] == '1' else color_white
            pixels[x, y] = current_color

    return image


def image_to_bits(image):
    """
    Generates a string of bits from PIL image.

    :param image: PIL image
    :return: total number of bits, number of bits per row, bits generated from image
    """
    image.convert('1')
    bits_per_row = image.size[0]
    height = image.size[1]
    bits_total = height * bits_per_row
    pixels = image.load()
    bits = []
    for y in range(height):
        for x in range(bits_per_row):
            bits.append('1' if pixels[x, y] == color_black else '0')
    return bits_total, bits_per_row, ''.join(bits)
