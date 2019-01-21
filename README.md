# Hotspur command

The backend for Hotspur, the only on-the-fly cryoEM micrograph
processing system named after a knight.

## Overview

Hotspur comprises a system of collection processors and collection
parsers. Processors run commands, and parsers take the output of
those commands and enter them into a database that hotspur_web reads
for the frontend. The processors and parsers are launched from the
config file, created for each microscope session. The config file
also contains microscope parameters such as the Cs and pixel size.

## Usage

While collecting data, there are some essential conventions to follow
with SerialEM.

| Item        | Where to put it |
| ----------- | --------------- |
| Micrographs | In a subdirectory named after the current grid |
| Low Mag Montages | In the project directory, named `{grid}_lmm.mrc` |
| Medium Mag Montages | In the project directory, named `{grid}_mmm.mrc` |
| Navigator | Make one navigator per grid, and call it `{grid}.nav` |

For example:
```
├── grid12
│   ├── CountRef_s_28_0001.dm4
│   ├── s_30_0001.mrc
│   ├── s_31_0001.mrc
│   ├── s_32_0001.mrc
├── grid9
│   ├── CountRef_s_28_0001.dm4
│   └── s_31_0001.mrc
├── grid9_lmm.mrc
├── grid9_lmm.mrc.mdoc
├── grid9_mmm.mrc
├── grid9_mmm.mrc.mdoc
├── grid12_lmm.mrc
├── grid12_lmm.mrc.mdoc
├── grid12_mmm.mrc
├── grid12_mmm.mrc.mdoc
├── grid12.nav
└── grid9.nav
```

After you have obtained your first micrograph you can use it to auto-initialize hotspur:
```
$ cd /.../raw_data/user/session
$ module load hotspur
$ hotspur_initialize --micrograph {grid}/{micrograph}.mrc config.py
```

This should convert the gain reference, and read pixel size, dose rate, and detector
mode from the micrograph. In order for the dose rate to be correct, it might be best
to acquire the first micrograph over a hole. We still highly recommend opening the
config file to ensure that the motioncor2, gctf, and ctffind commands have the correct
values.

You can then launch hotspur
```
$ module load tmux
$ tmux
$ hotspur --config config.py
```
Hotspur will launch collection processors for each of the commands specified
in the processes list at the bottom of the config file, as well as
the parsers as specified in the parser dictionary of that same config file.

## Contributing
**Adding programs to hotspur**

To add a new program, only two components are needed: a collection parser and an
updated config template. The collection parser, added to `collection_parser.py`,
and imported into `collection_processor.py` should extend Parser and read the
output of the new program into the hotspur database for display on the frontend.

Add the new parser to the `parser` dictionary in `config.py`, then add a `CommandProcessor`
to run the new program to the `processes` list.
