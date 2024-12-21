# Convert

## Audio
```bash
curl -X POST -F "file=@yourfile.wav" -F "output_format=mp3" -F "codec=pcm_s16le" -F "bitrate=192k" -F "sample_rate=44100" -F "channels=2" -F "volume=1.5" http://localhost:5050/audio/convert_audio
```

## Image
```bash
curl -X POST -F "file=@yourfile.jpg" -F "output_format=png" -F "width=500" -F "height=800" -F "quality=2" http://localhost:5050/image/convert_image
```

## Transcription
```bash
curl -X POST -F "file=@yourfile.wav" http://localhost:5050/transcribe/transcribe_audio
```

## Translation
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"text": "Hello, how are you?", "from_code": "en", "to_code": "es"}' \
  http://localhost:5050/transcribe/translate_text
```

### Supported Languages

```
Arabic, Azerbaijani, Chinese, Dutch, English, Finnish, French, German, Hindi, Hungarian, Indonesian, Irish, Italian, Japanese, Korean, Polish, Portuguese, Russian, Spanish, Swedish, Turkish, Ukranian, Vietnamese
```

# Download

```bash
curl -O http://127.0.0.1:5050/download/example.wav
```