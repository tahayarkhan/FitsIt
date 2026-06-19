import React, { useState } from "react";

const Navigation = () => {
  const [activeTab, setActiveTab] = useState("+");

  const tabs = ["+", "Items", "Outfits", "Wardrobe"];

  return (
    <nav className="self-center bg-black my-5 px-6 py-2 rounded-bl-full w-3/4 h-full">
      <div className="flex justify-center gap-4">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`rounded-md px-4 py-2 text-sm font-normal transition-colors
              ${
                activeTab === tab
                  ? "bg-white text-black"
                  : "text-gray-300 hover:bg-white/10 hover:text-white"
              }`}
          >
            {tab}
          </button>
        ))}
      </div>
    </nav>
  );
};

export default Navigation;