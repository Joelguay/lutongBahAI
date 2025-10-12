import React from "react";

function Camera() {
  // The URL of the new Flask video streaming endpoint
  const videoStreamUrl = "http://localhost:5000/api/video_feed";

  return (
    <div style={{ textAlign: "center", marginTop: "20px" }}>
      {/* We use an <img> tag to display the MJPEG stream */}
      <img
        src={videoStreamUrl}
        style={{
          width: "640px", // Adjusted for a common camera resolution
          height: "480px", // Adjusted for a common camera resolution
          borderRadius: "12px",
          background: "#000",
        }}
      />
    </div>
  );
}

//     startCamera();

//     return () => {
//       if (videoRef.current?.srcObject) {
//         (videoRef.current.srcObject as MediaStream)
//           .getTracks()
//           .forEach((track) => track.stop());
//       }
//     };
//   }, []);

//   return (
//     <div style={{ textAlign: "center", marginTop: "20px" }}>
//       <video
//         ref={videoRef}
//         autoPlay
//         playsInline
//         style={{
//           width: "480px",
//           height: "360px",
//           borderRadius: "12px",
//           background: "#000",
//         }}
//       />
//     </div>
//   );
// }

export default Camera;
