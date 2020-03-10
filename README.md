# ZPL GRF Extractor

This project contains the utilities to work with GRF images from ZPL (Zebra Programming Languages).

Currently supports:
- Finding and extracting ~DG commands from ZPL code
- Extracting parameters from ~DG commands
- Checking for compression in ~DG commands
- Decompression of ~DG commands
- Generation of PIL images from ~DG commands
- Generation of ~DG commands from PIL images
- Compression of ~DG commands
- Generation of ZPL code with ~DG commands

## Init project

```bash
python3 -m venv ./venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Examples

### Extracting `~DG` commands from ZPL code and generating PIL images
```python
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
```

### Generating ZPL code from a PIL image
```python
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
```

## ZPL
Manual for Zebra Programming Language can be found [here](https://www.zebra.com/content/dam/zebra/manuals/printers/common/programming/zpl-zbi2-pm-en.pdf). This project utilizes `~DG` command explained on page 158 and possible compression explained on page 1582.