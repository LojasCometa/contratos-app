import React, { useRef } from "react";

export default function AssinaturaPad({ onConfirm }) {
  const canvasRef = useRef(null);

  const limpar = () => {
    const ctx = canvasRef.current.getContext("2d");
    ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
  };

  const confirmar = () => {
    const dataURL = canvasRef.current.toDataURL("image/png");
    onConfirm(dataURL);
  };

  return (
    <div>
      <canvas
        ref={canvasRef}
        width={400}
        height={150}
        style={{ border: "1px solid #000", background: "#fff" }}
      />
      <br />
      <button onClick={limpar}>Limpar</button>
      <button onClick={confirmar}>Confirmar</button>
    </div>
  );
}
