from PIL import ImageDraw, ImageFont

from zplgrf import *


def closest_index(from_indexes, to_index):
    lowest_distance_listpos = (float("inf"), None)
    for i, from_index in enumerate(from_indexes):
        distance = to_index[0] - from_index[0]
        if 0 < distance < lowest_distance_listpos[0]:
            lowest_distance_listpos = (distance, i)
    closest_index = from_indexes[lowest_distance_listpos[1]]
    return closest_index


input_zpl_file_path = './zpl_gf/pila2_ex_0.zpl'

# Read ZPL code from a file
with open(input_zpl_file_path, 'r') as in_file:
    zpl = in_file.read()

# Find and extract ^GF commands
gf_cmds_indexes = find_commands(zpl, cmd_start='^GF', cmd_end='^')
gf_cmds = extract_commands(zpl, gf_cmds_indexes)
for gf_cmd in gf_cmds:
    # Extract parameters from ^GF commands
    compression_type, binary_byte_count, graphic_field_count, bytes_per_row, data = break_gf_command(gf_cmd)
    data = clean(data)
    # Check for compression and decompress if needed
    is_compressed = check_for_z64_compression(data)
    if is_compressed:
        data = decompress_z64(data)
    # Generate a PIL image
    data_bits = chars_to_bits(data)
    bits_total = size_byte_to_bit(binary_byte_count)
    bits_per_row = size_byte_to_bit(bytes_per_row)
    image = bits_to_image(bits_total, bits_per_row, data_bits)

fd_cmds_indexes = find_commands(zpl, cmd_start='^FD', cmd_end='^')
lh_cmds_indexes = find_commands(zpl, cmd_start='^LH', cmd_end='^')
ft_cmds_indexes = find_commands(zpl, cmd_start='^FT', cmd_end='^')
aat_cmds_indexes = find_commands(zpl, cmd_start='^A@', cmd_end='^')

for fd_cmd_index in fd_cmds_indexes:
    fd_cmd = extract_command(zpl, fd_cmd_index)
    fd_data = break_fd_command(fd_cmd)

    closest_lh_cmd_index = closest_index(lh_cmds_indexes, fd_cmd_index)
    lh_cmd = extract_command(zpl, closest_lh_cmd_index)
    lh_x, lh_y = break_lh_command(lh_cmd)
    closest_ft_cmd_index = closest_index(ft_cmds_indexes, fd_cmd_index)
    ft_cmd = extract_command(zpl, closest_ft_cmd_index)
    ft_x, ft_y = break_ft_command(ft_cmd)
    fd_data_pos = (lh_x + ft_x, lh_y + ft_y)

    closest_aat_cmd_index = closest_index(aat_cmds_indexes, fd_cmd_index)
    aat_cmd = extract_command(zpl, closest_aat_cmd_index)
    field_orientation, char_height, width, font_drive, font_name = break_aat_command(aat_cmd)

    draw = ImageDraw.Draw(image)
    font_path = './fonts/AndaleMono.ttf'
    font_size = int(60 * char_height / 57)
    font = ImageFont.truetype(font_path, font_size)
    draw.text(
        xy=(fd_data_pos[0], fd_data_pos[1] - char_height * (43/57)),
        text=fd_data,
        fill=(0, 0, 0),
        font=font
    )

image.save('./img/pila2_ex_0.png')
