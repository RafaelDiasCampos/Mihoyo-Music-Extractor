import requests
import os
import urllib
import shutil
import functools
import zipfile
import subprocess
import hashlib
import regex as re

folders = ['Genshin', 'Star Rail']

# Downloads the zip files from the urls in versions.txt
# This function doesn't always work due to the instability of the download links
def downloadZips(folder):
    with open(os.path.join(folder, 'versions.txt'), 'r') as urls:
        zipsfolder = os.path.join(folder, 'zips')
        os.makedirs(zipsfolder, exist_ok=True)
        for url in urls:
            url = url.strip()
            parsedUrl = urllib.parse.urlparse(url)
            filename = parsedUrl.path.split('/')[-1]

            if os.path.exists(os.path.join(zipsfolder, filename)):
                continue

            print(f'Downloading file {filename}')
            with requests.get(url, stream=True) as r:
                r.raw.read = functools.partial(r.raw.read, decode_content=True)
                with open(os.path.join(zipsfolder, filename), 'wb') as f:
                    shutil.copyfileobj(r.raw, f)

# Returns the version of the patch corresponding to the zip file
def getZipVersion(filename):
    startsWithNumberRegex = re.compile(r'^[0-9]')
    if filename.startswith('game_'):
        return filename[len('game_1.4.0_'):len('game_1.4.0_')+3]
    elif startsWithNumberRegex.match(filename):
        return filename[len('1.0.1_'):len('1.0.1_')+3]
    else:
        return filename[-len('1.0.1.zip'):-len('.1.zip')]

# Extracts the music files from all versions into the extracted folder
def extractZips(folder):
    zipsfolder = os.path.join(folder, 'zips')

    zipfiles = [{
        'filename': file,
        'version': getZipVersion(file)
    } for file in os.listdir(zipsfolder) if file.endswith('.zip')]

    zipfiles = sorted(zipfiles, key=lambda x: x['version'])

    extractFolder = os.path.join(folder, 'extracted')
    os.makedirs(extractFolder, exist_ok=True)
    for file in zipfiles:
        print(f'Extracting music from version {file["version"]}')

        with zipfile.ZipFile(os.path.join(zipsfolder, file['filename']), 'r') as archive:
            outputFolder = os.path.join(extractFolder, file['version'])
            os.makedirs(outputFolder, exist_ok=True)

            # Filters out all files that aren't music files
            musicFiles = [f for f in archive.namelist() if os.path.basename(f).startswith('Music') and ( os.path.basename(f).endswith('.pck') or os.path.basename(f).endswith('.pck.hdiff') )]

            for musicFile in musicFiles:
                outputFilename = os.path.basename(musicFile)
                outputFile = os.path.join(outputFolder, outputFilename)

                if os.path.exists(outputFile):
                    continue

                source = archive.open(musicFile)

                with open(outputFile, 'wb') as dest:
                    shutil.copyfileobj(source, dest)

# Extracts all music files
# After extracting, the files are processed and copied to the folder corresponding to their version
def extractMusic(folder):
    extractedFolder = os.path.join(folder, 'extracted')
    currentFolder = os.path.join(extractedFolder, 'current')
    processedFolder = os.path.join(folder, 'processed')
    os.makedirs(currentFolder, exist_ok=True)
    os.makedirs(processedFolder, exist_ok=True)

    versions = [f for f in os.listdir(extractedFolder) if os.path.isdir(os.path.join(extractedFolder, f)) and f != 'current']
    versions = sorted(versions)

    # If the processed file exists, only process the versions after the last processed version
    processedFile = os.path.join(currentFolder, 'processed.txt')
    if os.path.exists(processedFile):
        with open(processedFile, 'r') as f:
            processed = f.read().splitlines()
            lastProcessed = processed[-1]
            if lastProcessed in versions:
                lastProcessedIndex = versions.index(lastProcessed)
            else:
                lastProcessedIndex = -1
            if len(versions) >= lastProcessedIndex + 1:
                versions = versions[lastProcessedIndex + 1:]

    alreadyIncludedHashesFile = os.path.join(currentFolder, 'hashes.txt')
    if os.path.exists(alreadyIncludedHashesFile):
        with open(alreadyIncludedHashesFile, 'r') as f:
            alreadyIncludedHashes = [line.strip() for line in f.readlines()]
    else:
        alreadyIncludedHashes = []

    for version in versions:
        print(f'Processing music from version {version}')

        # Copies version files to the current folder
        versionFolder = os.path.join(extractedFolder, version)
        for file in os.listdir(versionFolder):
            shutil.copyfile(os.path.join(versionFolder, file), os.path.join(currentFolder, file))

        # Hdiff patches the files in the current folder
        patchedFolder = os.path.join(currentFolder, 'patched')
        os.makedirs(patchedFolder, exist_ok=True)

        hpatch = os.path.join('Tools', 'hpatchz.exe')
        hdiffFiles = [f for f in os.listdir(currentFolder) if f.endswith('.hdiff')]
        for file in hdiffFiles:
            pckFile = file[:-len('.hdiff')]
            print(f'Patching {pckFile}')
            subprocess.check_output([hpatch, '-f', os.path.join(currentFolder, pckFile), os.path.join(currentFolder, file), os.path.join(patchedFolder, pckFile)])
            os.remove(os.path.join(currentFolder, file))
            os.remove(os.path.join(currentFolder, pckFile))
            shutil.move(os.path.join(patchedFolder, pckFile), os.path.join(currentFolder, pckFile))

        # Use quickbms to extract the bnk from the pck files
        quickbms = os.path.join('Tools', 'quickbms.exe')
        wavescan = os.path.join('Tools', 'wavescan.bms')
        musicOutputFolder = os.path.join(currentFolder, 'output')
        os.makedirs(musicOutputFolder, exist_ok=True)

        print('Extracting music files')
        subprocess.run([quickbms, '-o', wavescan, currentFolder, musicOutputFolder], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) 

        # Check if the files have already been included
        musicFiles = [f for f in os.listdir(musicOutputFolder) if f.endswith('.wav') or f.endswith('.wem')]
        for file in musicFiles:
            sha256hash = hashlib.sha256()
            with open(os.path.join(musicOutputFolder, file), 'rb') as f:
                sha256hash.update(f.read())
            hash = sha256hash.hexdigest()

            if hash in alreadyIncludedHashes:
                os.remove(os.path.join(musicOutputFolder, file))
            else:
                alreadyIncludedHashes.append(hash)

        # Use ww2ogg to convert the files to ogg
        ww2ogg = os.path.join('Tools', 'ww2ogg.exe')
        codebooks = os.path.join('Tools', 'packed_codebooks_aoTuV_603.bin')

        musicFiles = [f for f in os.listdir(musicOutputFolder) if f.endswith('.wav') or f.endswith('.wem')]
        for file in musicFiles:
            print(f'Converting {file}')
            try:
                subprocess.check_output([ww2ogg, os.path.join(musicOutputFolder, file), '--pcb', codebooks])
            except:
                print(f'Failed to convert {file}. Ignoring...')
            os.remove(os.path.join(musicOutputFolder, file))

        # Run revorb on the ogg files
        revorb = os.path.join('Tools', 'revorb.exe')

        oggFiles = [f for f in os.listdir(musicOutputFolder) if f.endswith('.ogg')]
        for file in oggFiles:
            print(f'Running revorb on {file}')
            subprocess.check_output([revorb, os.path.join(musicOutputFolder, file)])

        # Copy the files to the version folder
        versionFolder = os.path.join(processedFolder, version)
        os.makedirs(versionFolder, exist_ok=True)

        for file in os.listdir(musicOutputFolder):
            shutil.move(os.path.join(musicOutputFolder, file), os.path.join(versionFolder, file))

        # Mark the version as processed
        with open(processedFile, 'a') as f:
            f.write(version + '\n')

        # Save the hashes
        with open(alreadyIncludedHashesFile, 'w') as f:
            for hash in alreadyIncludedHashes:
                f.write(hash + '\n')
            

def main():
    for folder in folders:
        print(f"----- Processing {folder} -----")
        downloadZips(folder)
        extractZips(folder)
        extractMusic(folder)

if __name__ == '__main__':
    main()