from zplgrf import *

input_zpl_file_path = './zpl/example.zpl'

# Read ZPL code from a file
with open(input_zpl_file_path, 'r') as in_file:
    zpl = in_file.read()

# Find and extract ~DG commands
dg_cmds_indexes = find_dg_commands(zpl)
dg_cmds = extract_commands(zpl, dg_cmds_indexes)
for dg_cmd in dg_cmds:
    # Extract parameters from ~DG commands
    device, image_name, extension, bytes_total, bytes_per_row, data = break_dg_command(dg_cmd)
    data = clean(data)
    # Check for compression and decompress if needed
    is_compressed = check_for_compression(data)
    if is_compressed:
        data = decompress(data, bytes_per_row)
    # Generate a PIL image
    data_bits = chars_to_bits(data)
    bits_total = size_byte_to_bit(bytes_total)
    bits_per_row = size_byte_to_bit(bytes_per_row)
    image = bits_to_image(bits_total, bits_per_row, data_bits)
    image.save('./img/001.png'.format(image_name))
