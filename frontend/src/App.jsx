import { useCallback, useEffect, useState } from "react";

import './App.css';


export default function App() {
  const [hover, setHover] = useState(false);
  const [files, setFiles] = useState([]);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | ready | uploading | processing | success | error
  const [message, setMessage] = useState("");

  const API_BASE = "https://videosplice.onrender.com";

  const handleBrowse = (e) => {
    const picked = Array.from(e.target.files || []).filter((f) => f.type.startsWith("video/"));
    setFiles(picked);
    setStatus(picked.length ? "ready" : "idle");
    setMessage(picked.length ? "File selected: " + picked[0].name : "");
  };

  const handleSubmit = async () => {
    if (!files.length || status === "uploading") return;
    setStatus("uploading");
    setMessage("Uploading and processing video... This may take a few minutes.");

    try {
      const form = new FormData();
      form.append("file", files[0]);

      const res = await fetch(`${API_BASE}/api/process`, {
        method: "POST",
        body: form,
      });

      if (!res.ok) throw new Error("Upload failed");
      const data = await res.json();
      
      if (data.status === "success") {
        setStatus("success");
        setMessage("Processing complete! Downloading...");
        
        // Trigger download
        const downloadUrl = `${API_BASE}${data.download_url}`;
        const anchor = document.createElement("a");
        anchor.href = downloadUrl;
        anchor.download = `${data.job_id}.zip`;
        anchor.style.display = "none";
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);
        
        setMessage("Download started! Check your downloads folder.");
      } else {
        setStatus("error");
        setMessage(`Processing failed: ${data.error || data.message}`);
      }
      
    } catch (err) {
      console.error(err);
      setStatus("error");
      setMessage("Upload failed — see console.");
    }
  };

  const statusColor = {
    success: "text-green-400",
    error: "text-red-400",
    uploading: "text-blue-400",
    processing: "text-yellow-400",
  }[status];

  return (
    <div className="app-container">
      <h1 className="text-4xl font-bold mb-6">AI Porn Editor for Quickie</h1>

      <label htmlFor="file-input" className="px-8 py-4 bg-blue-700 rounded-xl text-white font-semibold text-lg cursor-pointer hover:bg-blue-600">
        {files.length ? "Change Video File" : "Import Video File"}
        <input
          id="file-input"
          type="file"
          accept="video/*"
          onChange={handleBrowse}
          className="hidden"
        />
      </label>

      <button
        onClick={handleSubmit}
        disabled={status === "uploading" || !files.length}
        className="px-6 py-3 bg-green-600 rounded-lg font-semibold text-white disabled:bg-gray-600"
      >
        {status === "uploading" ? "Uploading…" : "Submit"}
      </button>

      {status !== "idle" && message && (
        <p className={`mt-4 text-center text-lg font-medium ${statusColor}`}>{message}</p>
      )}
    </div>
  );
}
