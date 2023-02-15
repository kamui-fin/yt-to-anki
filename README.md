# Youtube Subs2SRS

An anki addon that generates a full-fledged deck with audio and pictures from a youtube link using subtitles with the click of a button.
This eliminates the need for having to download a video, or the accompanying subtitles, retiming them, and dealing with TSV files to import.
For those of you familiar with Subs2SRS, consider this to be the Youtube version.

`yt2srs` offers several features:

- Supports all languages
- Fallback to automatically generated subs if man-made captions could not be found
- Set a limit to how many cards are generated
- Choose the dimensions of the pictures
- Fast card generation

## Installation

1. In `Tools > Addons`, click `Get addon` and use the code `964531817`
2. Restart Anki for changes to take place

If you are a Linux or Mac user, make sure to install `ffmpeg` using your package manager.

## Usage

1. Enter the youtube link for the video
2. Set an output folder for the audio and screenshots to go (can also be used for condensed audio)
3. Choose the appropriate note type and fields for the card data
4. Specify the subtitle language (default: English)
5. Hit generate. After a bit, refresh your decks and you should see a deck named after the title of the video

## Development

Before moving on, be sure you have `python` and `poetry` setup.

1. Clone the repository

```
git clone https://github.com/kamui-fin/yt2srs.git
cd yt2srs
```

2. Install dependencies

```
poetry install
```

3. If you are on windows, you need to create a top-level directory called `ffmpeg` with [`ffmpeg.exe`](https://github.com/BtbN/FFmpeg-Builds/releases) inside
4. Bundle everything (or update the bundle)

```
poetry run invoke package-dev
```

5. Create a symlink of `dist/` inside of your Anki data's `addons21/` folder

```
ln -s ./dist ~/.local/share/Anki2/addons21/yt2srs
```

6. Now you can use the `dev` command for simultaneously running anki with the updated bundle

```
poetry run invoke dev
```

7. For running lint and unit test tasks:

```
poetry run invoke check
```

## Contributing

All contributions are gladly welcomed! Feel free to open an issue or create a pull request if you have any new changes/ideas in mind.
