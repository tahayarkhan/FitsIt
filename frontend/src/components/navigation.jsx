import React, { useState } from "react";
import Upload from "./upload";
import Items from "./items";
import Recommendations from "./recommendations";

const Navigation = () => {
  const [activeTab, setActiveTab] = useState("+");

  const tabs = ["+", "Items", "Outfits", "Wardrobe"];

  return (
    <>
    <nav className="self-center bg-black my-10 px-6 py-2 rounded-full w-3/4 h-full">
      <div className="flex justify-center gap-4">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`rounded-xl px-4 py-1.5 text-sm font-normal transition-colors
              ${
                activeTab === tab
                  ? "bg-white text-black"
                  : "text-gray-300 hover:bg-white/20 hover:text-white"
              }`}
          >
            {tab}
          </button>
        ))}
      </div>
    </nav>
    
    <div className="mt-6">
        {activeTab === "Add Item" && <Upload />}
        {activeTab === "Items" && <Items />}
        {activeTab === "Outfits" && <Recommendations />}
        {/* {activeTab === "Wardrobe" && <Wardrobe />} */}
    </div>
    </>
    
  );
};

export default Navigation;