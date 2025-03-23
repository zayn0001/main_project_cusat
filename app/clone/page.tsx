"use client";
import { useState, useRef } from "react";

export default function Clone() {
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [audioBlob, setAudioBlob] = useState<Blob>();
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunksRef.current.push(event.data);
      }
    };

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
      setAudioBlob(audioBlob);
    };

    mediaRecorderRef.current = mediaRecorder;
    mediaRecorder.start();
    setIsRecording(true);
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const uploadAudio = async () => {
    if (!audioBlob) {
      alert("No audio to upload!");
      return;
    }

    const formData = new FormData();
    formData.append("audio", audioBlob, "voice_clone.wav");

    try {
      const response = await fetch("/api/py/clone-voice", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        alert("Voice cloned and saved successfully! 🎉");
      } else {
        alert("Failed to clone voice. ❌");
      }
    } catch (error) {
      console.error("Error cloning voice:", error);
      alert("Error uploading audio.");
    }

    //setAudioBlob(undefined);
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-900 p-4">
      <div className="w-[500px] bg-white shadow-lg rounded-lg p-6 text-center">
        <h2 className="text-2xl font-bold mb-4 text-black">Clone Your Voice</h2>
        <h5 className="text-sm font-bold mb-4 text-black">
          Hello! I&apos;m really excited to be here today and share a little bit
          about myself. I&apos;ve always been curious about how technology shapes
          the world around us, and that curiosity led me to explore everything
          from artificial intelligence to web development. In my free time, I
          enjoy reading science fiction, experimenting with new coding
          techniques, and occasionally getting lost in a good video game. Life
          is all about learning and growing, and I believe that every challenge
          is an opportunity to discover something new. So, let&apos;s embark on this
          journey together, and see where curiosity takes us next!
        </h5>
        <button
          onClick={isRecording ? stopRecording : startRecording}
          className={`w-full px-6 py-3 rounded text-white text-lg font-semibold ${
            isRecording
              ? "bg-red-600 hover:bg-red-700"
              : "bg-blue-600 hover:bg-blue-700"
          } transition duration-200`}
        >
          {isRecording ? "Stop Recording" : "Start Recording"}
        </button>

        {audioBlob && (
          <div className="mt-4">
            <audio controls>
              <source src={URL.createObjectURL(audioBlob)} type="audio/wav" />
            </audio>
            <button
              className="w-full px-6 py-3 mt-4 rounded text-white text-lg font-semibold bg-green-600 hover:bg-green-700"
              onClick={uploadAudio}
            >
              Upload & Clone Voice
            </button>
          </div>
        )}
      </div>
    </main>
  );
}
