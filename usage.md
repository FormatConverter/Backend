# Convert

## Audio
```bash
curl -X POST -F "file=@yourfile.wav" -F "output_format=mp3" -F "codec=pcm_s16le" -F "bitrate=192k" -F "sample_rate=44100" -F "channels=2" -F "volume=1.5" http://localhost:5050/audio/convert_audio
```
### Parameters for Audio Conversion

#### codec: The audio codec to use. Examples:
```bash
-F "codec=pcm_s16le"       # Linear PCM
-F "codec=aac"             # Advanced Audio Codec
-F "codec=mp3"             # MPEG Layer-3
```
#### bitrate: The bitrate of the audio file. Examples:
```bash
-F "bitrate=192k"          # Set bitrate to 192 kbps
-F "bitrate=128k"          # Set bitrate to 128 kbps
```
#### sample_rate: The sample rate of the audio file. Examples:
```bash
-F "sample_rate=44100"     # Set sample rate to 44.1 kHz
-F "sample_rate=48000"     # Set sample rate to 48 kHz
```
#### channels: The number of audio channels. Examples:
```bash
-F "channels=2"            # Stereo audio
-F "channels=1"            # Mono audio
```
#### volume: Adjust the volume level. Examples:
```bash
-F "volume=1.5"            # Increase volume by 50%
-F "volume=0.8"            # Decrease volume by 20%
```

## Image
```bash
curl -X POST -F "file=@yourfile.jpg" -F "output_format=png" -F "width=500" -F "height=800" -F "quality=2" http://localhost:5050/image/convert_image
```

### Parameters for Image Conversion

#### width: Resize the image to a specified width. Examples:
```bash
-F "width=500"             # Resize width to 500 pixels
```

#### height: Resize the image to a specified height. Examples:
```bash
-F "height=800"            # Resize height to 800 pixels
```

#### quality: Set the quality of the output image. Examples:
```bash
-F "quality=1"             # Low quality
-F "quality=2"             # Medium quality
-F "quality=3"             # High quality
```

## Transcription

### Audio Transcription

```bash
curl -X POST -F "file=@yourfile.mp3" http://localhost:5050/transcribe/transcribe_audio
```

### Video Transcription

```bash
curl -X POST -F "file=@yourfile.mp4" http://localhost:5050/transcribe/transcribe_video
```

### Optional Parameters for Transcription

#### input_language: Specify the language of the input file. Examples:

```bash
-F "input_language=en"     # English
-F "input_language=es"     # Spanish
```

#### output_language: Specify the language of the transcription output. Examples:

```bash
-F "output_language=en"    # English
-F "output_language=fr"    # French
```

#### save_file: Save the transcription file. Examples:

```bash
-F "save_file=true"        # Save file to the server
```

#### save_format: Specify the format of the saved transcription. Examples:

```bash
-F "save_format=txt"       # Save as TXT
-F "save_format=docx"      # Save as DOCX
-F "save_format=pdf"       # Save as PDF
-F "save_format=json"      # Save as JSON
```

### Example with optional parameters

```bash
curl -X POST -F "file=@korean.mp3" \
-F "input_language=ko" \
-F "output_language=en" \
-F "save_file=true" \
-F "save_format=txt" \
--output transcription.txt \ 
http://localhost:5050/transcribe/transcribe_audio
```

```bash
curl -X POST -F "file=@test.mp4" \
-F "input_language=en" \
-F "output_language=ko" \
-F "save_file=true" \
-F "save_format=json" \
--output transcription.json \
http://localhost:5050/transcribe/transcribe_video

```


## Translation
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"text": "Hello, how are you?", "from_code": "en", "to_code": "es"}' \
  http://localhost:5050/transcribe/translate_text
```
### Parameters for Translation

#### from_code: Specify the language of the original text. Examples:
```bash
-d '{"from_code": "en"}'   # English
-d '{"from_code": "zh"}'   # Chinese
```
#### to_code: Specify the language of the translation output. Examples:
```bash
-d '{"to_code": "es"}'     # Spanish
-d '{"to_code": "de"}'     # German
```

## Download
```bash
curl -O http://127.0.0.1:5050/download/example.wav
```

## Save Transcription

### Save as TXT
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"text": "This is the transcribed text.", "format": "txt"}' \
  http://localhost:5050/transcribe/save_transcription \
  --output transcription.txt
```
### Save as DOCX
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"text": "This is the transcribed text.", "format": "docx"}' \
  http://localhost:5050/transcribe/save_transcription \
  --output transcription.docx
```
### Save as PDF
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"text": "This is the transcribed text.", "format": "pdf"}' \
  http://localhost:5050/transcribe/save_transcription \
  --output transcription.pdf
```
### Save as JSON
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"text": "This is the transcribed text.", "format": "json"}' \
  http://localhost:5050/transcribe/save_transcription \
  --output transcription.json
```

test commit

