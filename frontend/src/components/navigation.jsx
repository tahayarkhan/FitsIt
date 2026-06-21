import React, { useState } from "react";
import Upload from "./upload";
import Items from "./items";
import Recommendations from "./recommendations";

const Navigation = () => {

  const [wardrobeKey, setWardrobeKey] = useState(0)
  const [activeTab, setActiveTab] = useState("+");

  const tabs = ["+", "Items", "Outfits", "Wardrobe"];

  return (
    <>
    <nav className="self-center bg-black mt-10 px-6 py-2 rounded-full w-4/5 h-full md:w-3/5 lg:w-1/2">
      <div className="flex justify-center gap-4">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`rounded-full px-4 py-1.5 text-sm font-normal transition-colors
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
        {activeTab === "+" && <Upload onSuccess={() => setWardrobeKey((k) => k + 1)} />}
        {activeTab === "Items" && <Items refreshTrigger={wardrobeKey}/>}
        {activeTab === "Outfits" && <Recommendations refreshTrigger={wardrobeKey} />}
        {/* {activeTab === "Wardrobe" && <Wardrobe />} */}
    </div>
    </>
    
  );
};

export default Navigation;