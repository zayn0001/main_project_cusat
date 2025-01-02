"use client";
import { useDebugValue, useEffect, useRef, useState } from "react";

export default function Record() {
  const [descriptions, setDescriptions] = useState<string[]>([]);
  const [transcript, setTranscript] = useState<string>("");
  const [isListening, setIsListening] = useState<boolean>(true);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  // Ref to store the latest descriptions array
  const descriptionsRef = useRef<string[]>([]);
  const transcriptRef = useRef<string>("");


  useEffect(() => {
    const cameraInterval = setInterval(async () => {
      const description = await captureFrameDescription();
      console.log(description);

      // Update state and ref
      setDescriptions((prev) => {
        const updatedDescriptions = [...prev, description];
        descriptionsRef.current = updatedDescriptions; // Keep ref in sync
        return updatedDescriptions;
      });
    }, 60000); // Capture frame every 10 seconds

    const summaryInterval = setInterval(async () => {
      console.log("Summarizing descriptions:", descriptionsRef.current);
      const summaryk = await summarizeDescriptions(descriptionsRef.current);
      console.log(summaryk);
      // Clear the ref and state
      descriptionsRef.current = [];
      setDescriptions([]);



      //console.log("Summarizing descriptions:", descriptionsRef.current);
      const transcripttotal = await summarizeTranscript(transcriptRef.current);
      console.log(transcripttotal);
      // Clear the ref and state
      transcriptRef.current = "";
      setTranscript("")
    }, 600000); // Summarize every 1 minute

    return () => {
      clearInterval(cameraInterval);
      clearInterval(summaryInterval);
    };
  }, []);

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
          setTranscript((prev) => {
            const updatedTransript = prev + event.results[i][0].transcript + " ";
            transcriptRef.current = updatedTransript
            return transcriptRef.current
          });
          
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

  const captureFrameDescription = async (): Promise<string> => {
    if (!videoRef.current) {
      console.error("Video feed is not available.");
      return "No video feed available.";
    }
  
    try {
      // Create a canvas to capture the current frame
      const canvas = document.createElement("canvas");
      const video = videoRef.current;
  
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
  
      const context = canvas.getContext("2d");
      if (!context) {
        console.error("Failed to get 2D context from canvas.");
        return "Error capturing frame.";
      }
  
      // Draw the current video frame onto the canvas
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
  
      // Convert the canvas content to a data URL
      const imageBlob = await new Promise<Blob | null>((resolve) =>
        canvas.toBlob(resolve, "image/jpeg")
      );
      if (!imageBlob) {
        console.error("Failed to create image blob.");
        return "Error capturing frame.";
      }
  
      // Prepare the form data for the API request
      const formData = new FormData();
      formData.append("image", imageBlob, "frame.jpg");
  
      // Send the captured frame to the backend
      const response = await fetch("/api/py/describe-image", {
        method: "POST",
        body: formData,
      });
  
      if (!response.ok) {
        console.error("Error from backend:", response.statusText);
        return "Error describing frame.";
      }
  
      // Parse the response
      const data = await response.json();
      return data.description || "No description available.";
    } catch (error) {
      console.error("Error capturing frame description:", error);
      return "Error capturing frame description.";
    }
  };
  

  const summarizeDescriptions = async (descriptions: string[]): Promise<string> => {
    try {
      console.log("looooooo")
      console.log(descriptions)
      const response = await fetch("/api/py/summarize-descriptions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ descriptions }),
      });
  
      if (!response.ok) {
        console.error("Error from backend:", response.statusText);
        return "Error generating summary.";
      }
  
      const data = await response.json();
      return data.summary || "No summary available.";
    } catch (error) {
      console.error("Error summarizing descriptions:", error);
      return "Error summarizing descriptions.";
    }
  };

  const summarizeTranscript = async (transcript: string): Promise<string> => {
    try {
      console.log("looooooo")
      console.log(transcript)
      const response = await fetch("/api/py/summarize-transcript", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ transcript }),
      });
  
      if (!response.ok) {
        console.error("Error from backend:", response.statusText);
        return "Error generating summary.";
      }
  
      const data = await response.json();
      return data.summary || "No summary available.";
    } catch (error) {
      console.error("Error summarizing descriptions:", error);
      return "Error summarizing descriptions.";
    }
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
  <div className="h-[52%] flex items-center justify-center">
    {/* Using img to display wave.jpg */}
    <img src="/wave.jpg" alt="Audio Wave" className="w-full h-full object-contain" />
  </div>
  <div className="bg-white h-[40%] text-black p-4 overflow-y-auto border border-gray-300 rounded">
    <p>{transcript || "Live transcription will appear here..."}</p>
  </div>
</div>
    </main>
  );
}
