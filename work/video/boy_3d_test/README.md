# Тест: 3D-мальчик через бесплатные нейросети (Hugging Face)

Проверка бесплатного конвейера для 3D-сериала: исходный 2D-кадр со спящим мальчиком
переделан в 3D (стиль Pixar) и оживлён. Без ключей и оплаты, через публичные Spaces на Hugging Face.

| Файл | Что это |
|---|---|
| `boy3d_frame.png` | 3D-версия опорного кадра |
| `scene01_3d.mp4` | Сцена 3.5 с: будильник, мальчик морщится и тянет одеяло (720p, 24 fps) |
| `src/edit3d.py` | 2D → 3D: Space `prithivMLmods/Qwen-Image-Edit-2511-LoRAs-Fast`, LoRA `Pixar-Inspired-3D` |
| `src/i2v.py` | Картинка → видео: Space `prithivMLmods/Wan2.2-Fast` (Wan 2.2), ~26 с на клип |
| `src/veo.py` | Генерация через Google Veo (Gemini API), нужен `GEMINI_API_KEY`; не проверялся |

## Запуск

```bash
pip install gradio_client
python src/edit3d.py reference_frame_01.png boy3d.png "Transform into a Pixar-inspired 3D animated film still ..."
python src/i2v.py boy3d.png scene.mp4 "3D Pixar-style animation. The boy slowly blinks ..." 3.5
# плавность и 720p
ffmpeg -i scene.mp4 -vf "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc,scale=720:-2:flags=lanczos" -crf 18 scene_720p24.mp4
```

## Известные проблемы
- Цифры на экране телефона «плывут» между кадрами: надписи лучше дорисовывать при монтаже.
- На 3D-кадре у мальчика открыты глаза (в оригинале спит), нужно поправить промпт.
- Клип 3.5 с; длиннее: цепочкой, последний кадр → первый кадр следующего.
- Анонимный лимит GPU на Hugging Face не известен; с бесплатным токеном HF больше.
