"use client";
import { useEffect, useRef, useState } from "react";

export default function Ask() {
  const [transcript, setTranscript] = useState<string>(""); // To store live transcript
  const [isRecording, setIsRecording] = useState<boolean>(false); // State for recording status
  const recognitionRef = useRef<any>(null); // Ref to store recognition instance
  const transcriptRef = useRef<string>(""); // Ref to store the latest transcript

  // Get answer from backend
  const getAnswer = async (): Promise<string> => {
    try {
      const response = await fetch("/api/py/get-answer", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: transcript }),
      });
      
      if (!response.ok) {
        console.error("Error from backend:", response.statusText);
        return "I do not know the answer to that question";
      }

      const data = await response.json();
      return (data.answer as string) || "No answer available.";
    } catch (error) {
      console.error("Error getting answer:", error);
      return "No answer available.";
    }
  };

  // Initialize speech recognition
  useEffect(() => {
    if (!("SpeechRecognition" in window || "webkitSpeechRecognition" in window)) {
      console.error("Speech Recognition API is not supported in this browser.");
      return;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    recognitionRef.current = new SpeechRecognition();
    recognitionRef.current.continuous = true;
    recognitionRef.current.interimResults = true;
    recognitionRef.current.lang = "en-US";

    // Process results
    recognitionRef.current.onresult = (event: any) => {
      let interimTranscript = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          transcriptRef.current += event.results[i][0].transcript + " ";
          setTranscript(transcriptRef.current);
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }
      setTranscript(transcriptRef.current + interimTranscript); // Show interim + final results
    };

    recognitionRef.current.onerror = (event: { error: any }) => {
      console.error("Speech recognition error:", event.error);
    };

    return () => {
      recognitionRef.current.stop();
    };
  }, []);

  // Speak the answer using SpeechSynthesis
  const speakAnswer = (text: string) => {
    const synth = window.speechSynthesis;
    if (!synth) {
      console.error("SpeechSynthesis API is not supported in this browser.");
      return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.rate = 1; // Speed (1 is normal, 0.5 is slower, 2 is faster)
    utterance.pitch = 1; // Pitch of voice
    utterance.volume = 1; // Volume (0.0 to 1.0)

    synth.speak(utterance);
  };

  // Start or stop recording
  const toggleRecording = async () => {
    if (isRecording) {
      recognitionRef.current.stop();
      setTranscript("Processing... Please wait.");
      const answer = await getAnswer();
      console.log("Final Transcription:", transcript);
      console.log("Final Answer:", answer);
      setTranscript(answer); // Display answer in the UI

      // Speak the answer aloud
      speakAnswer(answer);

      transcriptRef.current = ""; // Reset for next query
    } else {
      transcriptRef.current = ""; // Reset on start
      setTranscript("");
      recognitionRef.current.start();
    }
    setIsRecording(!isRecording);
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-900 p-4">
      <div className="w-[500px] bg-white shadow-lg rounded-lg p-6 text-center">
        <h2 className="text-2xl font-bold mb-4 text-black">
          Ask Page - Voice Transcription
        </h2>

        {/* Transcription Box */}
        <div className="h-[200px] bg-gray-100 p-4 border border-gray-300 rounded overflow-y-auto mb-4 text-black text-left">
          {transcript || "Ask away..."}
        </div>

        {/* Record Button */}
        <button
          onClick={toggleRecording}
          className={`w-full px-6 py-3 rounded text-white text-lg font-semibold ${
            isRecording
              ? "bg-red-600 hover:bg-red-700"
              : "bg-blue-600 hover:bg-blue-700"
          } transition duration-200`}
        >
          {isRecording ? "Stop Recording" : "Start Recording"}
        </button>
      </div>
    </main>
  );
}
