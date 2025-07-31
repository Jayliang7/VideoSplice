import { useCallback, useEffect, useState } from "react";

import './App.css';

export default function App() {
  const [hover, setHover] = useState(false);
  const [files, setFiles] = useState([]);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | ready | uploading | processing | success | error
  const [message, setMessage] = useState("");

  const handleBrowse = (e) => {
    const picked = Array.from(e.target.files || []).filter((f) => f.type.startsWith("video/"));
    setFiles(picked);
    setStatus(picked.length ? "ready" : "idle");
    setMessage(picked.length ? "File selected: " + picked[0].name : "");
  };

  const handleSubmit = async () => {
    if (!files.length || status === "uploading") return;
    setStatus("uploading");
    setMessage("Uploading...");

    try {
      const form = new FormData();
      form.append("file", files[0]);

      const res = await fetch("http://localhost:8000/api/upload", {
        method: "POST",
        body: form,
      });

      if (!res.ok) throw new Error("Upload failed");
      const data = await res.json();
      setJobId(data.job_id);
      setStatus("processing");
      setMessage("Upload successful. Processing…");
    } catch (err) {
      console.error(err);
      setStatus("error");
      setMessage("Upload failed — see console.");
    }
  };

  useEffect(() => {
    if (!jobId || status !== "processing") return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/status/${jobId}`);
        if (!res.ok) throw new Error("Status check failed");
        const data = await res.json();

        if (data.state === "done") {
          setStatus("success");
          setMessage("Processing complete! Downloading...");

          const downloadUrl = `http://localhost:8000/api/download/${jobId}`;
          const anchor = document.createElement("a");
          anchor.href = downloadUrl;
          anchor.download = `${jobId}.zip`;
          anchor.style.display = "none";
          document.body.appendChild(anchor);
          anchor.click();
          document.body.removeChild(anchor);

          clearInterval(interval);
        } else if (data.state === "error") {
          setStatus("error");
          setMessage("Processing failed.");
          clearInterval(interval);
        }
      } catch (err) {
        console.error(err);
        setStatus("error");
        setMessage("Could not check status.");
        clearInterval(interval);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [jobId, status]);

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
