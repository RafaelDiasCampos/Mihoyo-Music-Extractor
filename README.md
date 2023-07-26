# Mihoyo Music Extractor

This is a simple tool to extract music files from Mihoyo games (currently tested on Genshin Impact and Star Rail).

## How it works

The tool first downloads both the full 1.0 version of the game and the pre-install files for all subsequent versions, directly from Mihoyo servers (the urls can be found at `Game\versions.txt`).

After downloading all the versions of the game, the tool extracts the `.pck` and `.pck.hdiff` files that contain the compressed music files.

In sequence, for every game version, the tool:

1. Copies the music files to the `current` folder.
2. Applies `hpatchz.exe` to all `.hdiff` files.
3. Extracts all music from the `.pck` files using `quickbms.exe`.
4. Remove music files that were already included previously.
5. Convert the music from `.wem` file format to `.ogg` using `ww2ogg.exe`.
6. Improves the quality of the music files by running `revorb.exe`.
7. Copies the music to a folder corresponding to the version.

## How to use

```console
user:~$ pip install -r requirements.txt
user:~$ python unpack.py
```

If everything goes well, the tool should download the versions to the `zip` folder,
extract them to the `extracted` folder and copy the music to the `processed` folder.

If you're getting errors related to downloading the version zips, download them manually and copy them to the `zip` folder, without renaming the files.