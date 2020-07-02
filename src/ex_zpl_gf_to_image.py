from zplgrf import *

input_zpl_file_path = './zpl_gf/example.zpl'

# Read ZPL code from a file
with open(input_zpl_file_path, 'r') as in_file:
    zpl = in_file.read()

# Find and extract ^GFA commands
gf_cmds_indexes = find_gf_commands(zpl)
gf_cmds = extract_commands(zpl, gf_cmds_indexes)
for gf_cmd in gf_cmds:
    # Extract parameters from ^GFA commands
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
    image.save('./img/gf_cmd_format.png')
