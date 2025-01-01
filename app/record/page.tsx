"use client";
import { useEffect, useRef, useState } from "react";

export default function Record() {
  const [descriptions, setDescriptions] = useState<string[]>([]);
  const [transcript, setTranscript] = useState<string>("");
  const [isListening, setIsListening] = useState<boolean>(true);
  const videoRef = useRef<HTMLVideoElement | null>(null); // Reference for the video element

  useEffect(() => {
    const cameraInterval = setInterval(() => {
      // Placeholder function to simulate capturing a frame and getting its description
      const description = captureFrameDescription();
      setDescriptions((prev) => [...prev, description]);
    }, 60000); // Capture frame every 1 minute

    const summaryInterval = setInterval(() => {
      // Placeholder function to summarize descriptions
      const summary = summarizeDescriptions(descriptions);
      console.log("Summary:", summary);
      setDescriptions([]); // Reset descriptions after summarizing
    }, 600000); // Generate summary every 10 minutes

    const transcriptInterval = setInterval(() => {
      // Placeholder function to store the transcript
      storeTranscript(transcript);
    }, 300000); // Store transcript every 5 minutes

    return () => {
      clearInterval(cameraInterval);
      clearInterval(summaryInterval);
      clearInterval(transcriptInterval);
    };
  }, [descriptions, transcript]);

  useEffect(() => {
    if (!((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition)) {
      console.error("Speech Recognition API is not supported in this browser.");
      return;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    const handleResult = (event: any) => {
      let interimTranscript = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          setTranscript((prev) => prev + event.results[i][0].transcript + " ");
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }
    };
    

    if (isListening) {
      recognition.start();
      recognition.onresult = handleResult;

      recognition.onerror = (event: { error: any; }) => {
        console.error("Speech recognition error:", event.error);
      };
    } else {
      recognition.stop();
    }

    return () => {
      recognition.stop();
    };
  }, [isListening]);

  // Access webcam and set the video feed
  useEffect(() => {
    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (error) {
        console.error("Error accessing camera:", error);
      }
    };

    startCamera();

    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream;
        const tracks = stream.getTracks();
        tracks.forEach(track => track.stop()); // Stop all media tracks
      }
    };
  }, []);

  const captureFrameDescription = (): string => {
    return "Frame description placeholder"; // Replace with actual logic
  };

  const summarizeDescriptions = (descriptions: string[]): string => {
    return `Summary of ${descriptions.length} descriptions.`; // Replace with actual logic
  };

  const storeTranscript = (text: string): void => {
    console.log("Transcript stored:", text); // Replace with actual storage logic
  };

  return (
    <main className="flex min-h-screen">
      {/* Left side: Camera feed and descriptions */}
      <div className="w-1/2 bg-black p-4">
        <h2 className="text-xl font-bold mb-4">Live Camera Feed</h2>
        <div className="aspect-video h-[50%] w-full bg-black mb-4">
          {/* Video element for live camera feed */}
          <video ref={videoRef} autoPlay muted className="w-full h-full object-cover"></video>
        </div>
        
        <div className=" bg-white h-[40%] text-black p-4 overflow-y-auto border border-gray-300 rounded">
          <h3 className="text-lg font-semibold">Description:</h3>
          <div className="text-black mt-2">
            {/* Show only the latest description */}
            {descriptions.length > 0 ? descriptions[descriptions.length - 1] : "No description available"}
          </div>
        </div>
      </div>


      {/* Right side: Audio transcription */}
      <div className="w-1/2 bg-black p-4">
        <h2 className="text-xl font-bold mb-4">Audio Transcription</h2>
        <div className="h-[52%]">
          audio recording logo
        </div>
        <div className=" bg-white h-[40%] text-black p-4 overflow-y-auto border border-gray-300 rounded">
          <p>{transcript || "Live transcription will appear here..."}</p>
        </div>
      </div>
    </main>
  );
}
