import React from "react";

// Define props for the Camera component
interface CameraProps {
  isOn: boolean;
}

// Update the Camera component to accept the isOn prop
function Camera({ isOn }: CameraProps) {
  // The URL of the new Flask video streaming endpoint
  const videoStreamUrl = "http://localhost:5000/api/video_feed";

  const videoContainerStyle = {
    width: "640px",
    height: "480px",
    borderRadius: "12px",
    background: "#000",
    textAlign: "center" as const,
    marginTop: "20px",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  };

  const videoImageStyle = {
    width: "100%", 
    height: "100%", 
    borderRadius: "12px",
    // We only need the background property if it's OFF
  };

  return (
    <div style={{ textAlign: "center", marginTop: "20px" }}>
      <div style={videoContainerStyle}>
        {isOn ? (
          /* If camera is ON, show the live stream image */
          <img
            src={videoStreamUrl}
            style={videoImageStyle}
            alt="Live ingredient detection stream"
          />
        ) : (
          /* If camera is OFF, show a black screen with text */
          <div style={{...videoImageStyle, background: "#000", color: "#fff", lineHeight: "480px"}}>
            CAMERA OFF
          </div>
        )}
      </div>
    </div>
  );
}

export default Camera;