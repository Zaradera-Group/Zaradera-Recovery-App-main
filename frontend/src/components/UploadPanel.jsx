import { useRef, useState } from "react";
import { uploadSheet } from "../api";

export default function UploadPanel({ onUploaded }) {
  const inputRef = useRef(null);
  const [status, setStatus] = useState("idle"); // idle | uploading | done | error
  const [message, setMessage] = useState("");
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [uploadDate, setUploadDate] = useState("");

  async function handleFileChange(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    setStatus("uploading");
    setMessage("");
    try {
      const result = await uploadSheet(file, uploadDate || undefined);
      setStatus("done");
      setMessage(
        `Loaded ${result.row_count} loans for ${result.upload_date}` +
          (result.disappeared_loans
            ? ` — ${result.disappeared_loans} loan(s) from last week are no longer in the sheet.`
            : ".")
      );
      onUploaded();
    } catch (err) {
      setStatus("error");
      setMessage(err.message || "Upload failed.");
    } finally {
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  const today = new Date().toLocaleDateString("en-CA", { timeZone: "Africa/Lagos" });

  return (
    <div className="upload-panel">
      <div className="upload-controls">
        <button
          type="button"
          className="date-toggle-button"
          onClick={() => setShowDatePicker((v) => !v)}
          title="Upload for a different date (e.g. catching up on a missed week)"
        >
          {uploadDate ? `For ${uploadDate}` : "Today ▾"}
        </button>
        <label className="upload-button">
          {status === "uploading" ? "Uploading…" : "Upload weekly sheet"}
          <input
            ref={inputRef}
            type="file"
            accept=".xlsx"
            onChange={handleFileChange}
            disabled={status === "uploading"}
            hidden
          />
        </label>
      </div>

      {showDatePicker && (
        <div className="date-picker-row">
          <label htmlFor="upload-target-date">Sheet is for:</label>
          <input
            id="upload-target-date"
            type="date"
            max={today}
            value={uploadDate}
            onChange={(e) => setUploadDate(e.target.value)}
          />
          {uploadDate && (
            <button type="button" className="link-button" onClick={() => setUploadDate("")}>
              Reset to today
            </button>
          )}
        </div>
      )}

      {message && (
        <p className={`upload-message ${status === "error" ? "upload-message-error" : ""}`}>
          {message}
        </p>
      )}
    </div>
  );
}
