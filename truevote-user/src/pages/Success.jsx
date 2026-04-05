import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function Success() {
  const navigate = useNavigate();
  const epic = localStorage.getItem("epic");

  useEffect(() => {
    if (!epic) {
      navigate("/");
    }
  }, [epic, navigate]);

  return (
    <div className="min-h-screen bg-blue-600 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-lg shadow-md p-8 text-center">
        <h1 className="text-3xl font-bold mb-2">Registration Successful</h1>
        <p className="text-gray-700 mb-2">Your EPIC ID</p>
        <p className="text-2xl font-semibold mb-6 break-all">{epic || "Not Available"}</p>
        <p className="text-gray-700 mb-6">Use this EPIC at voting booth</p>

        <button
          type="button"
          onClick={() => navigate("/")}
          className="w-full bg-blue-600 text-white rounded-lg shadow-md py-3 font-semibold"
        >
          Register Another
        </button>
      </div>
    </div>
  );
}
