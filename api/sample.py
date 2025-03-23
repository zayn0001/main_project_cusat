from TTS.api import TTS


tts = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", gpu=False)


AUDIO_SAVE_PATH = "input_audio.mp3"
ANSWER_PATH = "final_answer.wav"

answer = "Your birthday is on April four"

tts.tts_to_file(
            text=answer,
            file_path=ANSWER_PATH,
            speaker_wav=[AUDIO_SAVE_PATH],  
            language="en"
        )