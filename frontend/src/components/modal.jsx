import React from 'react'




const Modal = ({src, onClose}) => {


  if (!src) return null;

  return (
    <div
      className="fixed inset-0 bg-black/60 flex justify-center items-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-white p-4 rounded-xl max-w-3xl"
        onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside
      >
        <img
          src={src}
          alt="expanded"
          className="max-h-[80vh] object-contain rounded-md"
        />

        <button
          className="mt-4 px-4 py-2 bg-black text-white rounded-md w-full"
          onClick={onClose}
        >
          Close
        </button>
      </div>
    </div>
  )
}

export default Modal