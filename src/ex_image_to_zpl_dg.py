from zplgrf import *

input_img_file_path = './img/000.png'

# Read image from a file
image = Image.open(input_img_file_path)

# Generate a ~DG command with compressed data from PIL image
bits_total, bits_per_row, data_bits = image_to_bits(image)
bytes_total = size_bit_to_byte(bits_total)
bytes_per_row = size_bit_to_byte(bits_per_row)
data = bits_to_chars(data_bits)
data = compress(data, bytes_per_row)
dg_cmd = build_dg_command(bytes_total, bytes_per_row, data, '000')
# Generate ZPL code with generated ~DG command
zpl = write_zpl(dg_cmd, 20, 20, 1, 1)

output_zpl_file_path = './zpl/example.zpl'
with open(output_zpl_file_path, 'w') as out_file:
    out_file.write(zpl)
